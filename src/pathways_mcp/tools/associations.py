"""Tools for querying statistical associations between variables."""

from pathways_mcp.api import format_response, get_client


def _significance(pvalue: float) -> str | None:
    if pvalue <= 0.001:
        return "Highly Significant"
    if pvalue <= 0.01:
        return "Very Significant"
    if pvalue <= 0.05:
        return "Significant"
    return None


def _effective_pvalue(pvalue: float | None, categorical_pvalues: dict | None) -> float | None:
    """Return the smallest meaningful p-value across pvalue and categorical_pvalues.

    pvalue = 0 means 'not computed globally' for categorical variables — it is
    excluded. The effective p-value is the minimum of any non-zero value found.
    Returns None if no meaningful p-value exists (association should be skipped).
    """
    candidates: list[float] = []
    if pvalue and pvalue > 0:
        candidates.append(pvalue)
    if categorical_pvalues and isinstance(categorical_pvalues, dict):
        candidates.extend(v for v in categorical_pvalues.values() if isinstance(v, (int, float)) and v > 0)
    return min(candidates) if candidates else None


async def search_variable_associations(
    outcome_code: str | None = None,
    vulnerability_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Find statistical associations between health outcome variables and vulnerability factors.

    Associations are stored directly on the Variable collection as recursive
    many-to-many relations with pvalue and categorical_pvalues on the relation:
    - significant_vulnerabilities: vulnerability factor variables significantly
      associated with a given health outcome variable.
    - significant_outcomes: health outcome variables significantly associated
      with a given vulnerability factor variable.

    For categorical variables the global pvalue may be 0 (not computed) — the
    effective p-value is then the minimum across categorical_pvalues. Records
    with no meaningful p-value are excluded. Results are sorted by effective
    p-value ascending (strongest first).

    Each result includes a significance label:
    - "Significant"        (p ≤ 0.05)
    - "Very Significant"   (p ≤ 0.01)
    - "Highly Significant" (p ≤ 0.001)

    Typical workflow:
    1. Use search_variables or list_themes_and_domains to find relevant variable codes.
    2. Call with an outcome_code to discover which vulnerability factors are
       statistically associated with that health outcome.
    3. Or pass a vulnerability_code to see which outcomes it is associated with.

    Args:
        outcome_code: Health outcome variable code (e.g., "hb.1"). Returns the
            vulnerability factors significantly associated with this outcome.
        vulnerability_code: Vulnerability factor variable code (e.g., "hh.floor").
            Returns the health outcomes significantly associated with this vulnerability.
            If both are given, results are filtered to the intersection.
        limit: Maximum number of associations to return (default 50, max 100).
        offset: Number of records to skip for pagination (default 0).
    """
    if not outcome_code and not vulnerability_code:
        return format_response({
            "error": "missing_filter",
            "message": "Provide at least one of outcome_code or vulnerability_code.",
        })

    client = get_client()
    limit = min(limit, 100)

    if outcome_code:
        anchor_code = outcome_code
        relation_field = "significant_vulnerabilities"
    else:
        anchor_code = vulnerability_code
        relation_field = "significant_outcomes"

    result = await client.fetch_collection(
        "variables",
        filters={"code": {"$eq": anchor_code}},
        populate=[relation_field],
        page_size=1,
    )

    variables = result.get("data", [])
    if not variables:
        return format_response({
            "associations": [],
            "pagination": {"total": 0, "returned": 0, "offset": offset, "limit": limit},
        })

    associated = variables[0].get(relation_field) or []
    associations = []

    for v in associated:
        # Apply intersection filter if both codes were provided
        if outcome_code and vulnerability_code and v.get("code") != vulnerability_code:
            continue

        cat_pvalues = v.get("categorical_pvalues")
        effective = _effective_pvalue(v.get("pvalue"), cat_pvalues)
        if effective is None:
            continue

        entry = {
            "outcome_code": outcome_code or v.get("code"),
            "vulnerability_code": vulnerability_code or v.get("code"),
            "name": v.get("name_en"),
            "pvalue": v.get("pvalue"),
            "categorical_pvalues": cat_pvalues or None,
            "effective_pvalue": effective,
            "significance": _significance(effective),
        }

        # When looking up by outcome, the associated variable IS the vulnerability
        if outcome_code:
            entry["vulnerability_code"] = v.get("code")
            entry["outcome_code"] = outcome_code
        else:
            entry["outcome_code"] = v.get("code")
            entry["vulnerability_code"] = vulnerability_code

        associations.append(entry)

    associations.sort(key=lambda x: x["effective_pvalue"])
    total = len(associations)
    page = associations[offset: offset + limit]

    return format_response({
        "associations": page,
        "pagination": {
            "total": total,
            "returned": len(page),
            "offset": offset,
            "limit": limit,
        },
    })
