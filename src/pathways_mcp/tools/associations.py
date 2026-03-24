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


async def search_variable_associations(
    outcome_code: str | None = None,
    vulnerability_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Find statistical associations between health outcome variables and vulnerability factors.

    Associations are stored on the Variable collection:
    - significant_vulnerabilities: vulnerability factors significantly associated
      with a given health outcome variable.
    - significant_outcomes: health outcomes significantly associated with a given
      vulnerability factor variable.

    Each association record includes a p-value; p = 0 means no association and
    is always excluded. Results are sorted by p-value ascending (strongest first).

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
        outcome_code: Health outcome variable code (e.g., "anc.1sttri"). When provided,
            returns vulnerability factors associated with this outcome.
        vulnerability_code: Vulnerability factor variable code (e.g., "hh.computer").
            When provided, returns health outcomes associated with this vulnerability.
            If both outcome_code and vulnerability_code are given, results are filtered
            to the intersection.
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

    associations = []

    if outcome_code:
        # Fetch the outcome variable and populate its significant vulnerabilities
        result = await client.fetch_collection(
            "variables",
            filters={"code": {"$eq": outcome_code}},
            populate=[
                "significant_vulnerabilities.outcome",
                "significant_vulnerabilities.vulnerability",
            ],
            page_size=1,
        )
        variables = result.get("data", [])
        if not variables:
            return format_response({"associations": [], "pagination": {"total": 0}})

        for assoc in (variables[0].get("significant_vulnerabilities") or []):
            pvalue = assoc.get("pvalue")
            if not pvalue:
                continue
            outcome = assoc.get("outcome") or {}
            vuln = assoc.get("vulnerability") or {}
            # Apply vulnerability_code filter if both were provided
            if vulnerability_code and vuln.get("code") != vulnerability_code:
                continue
            associations.append({
                "outcome_code": outcome.get("code"),
                "outcome_name": outcome.get("name_en"),
                "vulnerability_code": vuln.get("code"),
                "vulnerability_name": vuln.get("name_en"),
                "pvalue": pvalue,
                "significance": _significance(pvalue),
            })

    else:
        # vulnerability_code only — fetch variable and populate its significant outcomes
        result = await client.fetch_collection(
            "variables",
            filters={"code": {"$eq": vulnerability_code}},
            populate=[
                "significant_outcomes.outcome",
                "significant_outcomes.vulnerability",
            ],
            page_size=1,
        )
        variables = result.get("data", [])
        if not variables:
            return format_response({"associations": [], "pagination": {"total": 0}})

        for assoc in (variables[0].get("significant_outcomes") or []):
            pvalue = assoc.get("pvalue")
            if not pvalue:
                continue
            outcome = assoc.get("outcome") or {}
            vuln = assoc.get("vulnerability") or {}
            associations.append({
                "outcome_code": outcome.get("code"),
                "outcome_name": outcome.get("name_en"),
                "vulnerability_code": vuln.get("code"),
                "vulnerability_name": vuln.get("name_en"),
                "pvalue": pvalue,
                "significance": _significance(pvalue),
            })

    associations.sort(key=lambda x: x["pvalue"])
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
