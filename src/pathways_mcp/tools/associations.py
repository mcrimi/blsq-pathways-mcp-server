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

    Uses the Variable Suggestions table, which stores pre-computed p-values
    linking health outcomes (e.g., anc.1sttri) to vulnerability factors
    (e.g., hh.computer). Results are sorted by p-value ascending (strongest
    associations first). p = 0 means no association or not calculated and is
    always excluded.

    Each result includes a significance description:
    - "Significant"        (p ≤ 0.05)
    - "Very Significant"   (p ≤ 0.01)
    - "Highly Significant" (p ≤ 0.001)

    Typical workflow:
    1. Use search_variables or list_themes_and_domains to find relevant variable codes.
    2. Call this tool with an outcome_code to discover which vulnerability factors
       are statistically associated with that health outcome.
    3. Or pass a vulnerability_code to see which outcomes it is associated with.

    Args:
        outcome_code: Filter by health outcome variable code (e.g., "anc.1sttri").
        vulnerability_code: Filter by vulnerability factor variable code (e.g., "hh.computer").
        limit: Maximum number of associations to return (default 50, max 100).
        offset: Number of records to skip for pagination (default 0).
    """
    client = get_client()
    limit = min(limit, 100)
    page = (offset // limit) + 1

    filters: dict = {
        "pvalue": {"$gt": "0"},
    }

    if outcome_code:
        filters["outcome"] = {"code": {"$eq": outcome_code}}

    if vulnerability_code:
        filters["vulnerability"] = {"code": {"$eq": vulnerability_code}}

    result = await client.fetch_collection(
        "variable-suggestions",
        filters=filters,
        populate=["outcome", "vulnerability"],
        page=page,
        page_size=limit,
        sort="pvalue:asc",
    )

    pagination = result.get("meta", {}).get("pagination", {})
    associations = []
    for row in result.get("data", []):
        pvalue = row.get("pvalue")
        outcome = row.get("outcome") or {}
        vuln = row.get("vulnerability") or {}

        associations.append({
            "outcome_code": outcome.get("code"),
            "outcome_name": outcome.get("name_en"),
            "vulnerability_code": vuln.get("code"),
            "vulnerability_name": vuln.get("name_en"),
            "pvalue": pvalue,
            "significance": _significance(pvalue) if pvalue else None,
        })

    output = {
        "associations": associations,
        "pagination": {
            "total": pagination.get("total", 0),
            "page": pagination.get("page", 1),
            "page_size": pagination.get("pageSize", limit),
            "page_count": pagination.get("pageCount", 1),
        },
    }

    return format_response(output)
