# Pathways MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes the **Pathways** health segmentation platform as structured tools. Pathways provides woman-centered data and insights to help global health organizations design targeted interventions.

## What it does

This server connects to the Pathways Strapi CMS API and provides tools that let Claude (or any MCP client) explore population segmentation data:

| Tool | Description |
|---|---|
| `list_segmentations` | Discover available country studies (Senegal, Kenya, Nigeria, etc.) |
| `get_segmentation` | Full details and segments for a specific study |
| `list_segments` | Filter segments by vulnerability level or stratum (urban/rural) |
| `get_segment_profile` | Comprehensive "who are these women?" view with metrics by theme/domain |
| `get_segment_metrics` | Quantitative indicators for a segment, filterable by health theme |
| `search_variables` | Search indicators by name, theme, domain, or data type |
| `list_themes_and_domains` | Reference list of health themes and vulnerability domains |
| `list_regions` | Sub-national regions for a country |
| `get_geographic_distribution` | Geographic distribution of segments across regions |

**Example query this enables**: _"What is the best way to reach out to women in R4 in Tambacounda to improve family planning outcomes?"_

## Prerequisites

- Python 3.10+
- A Pathways API token (read-only Bearer token for the Strapi CMS)

## Installation

```bash
cd pathways-mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy the example env file and add your token:

```bash
cp .env.example .env
# Edit .env and set PATHWAYS_API_TOKEN
```

| Variable | Default | Description |
|---|---|---|
| `PATHWAYS_API_TOKEN` | _(required)_ | Strapi read-only API token |
| `PATHWAYS_API_URL` | `https://api.staging.withpathways.org` | Strapi API base URL |

## Running standalone

```bash
PATHWAYS_API_TOKEN=<your-token> python -m pathways_mcp.server
```

The server communicates over stdio using the MCP protocol. To test interactively, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

## Using with Claude

### Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pathways": {
      "command": "<path-to-repo>/pathways-mcp-server/.venv/bin/python",
      "args": ["-m", "pathways_mcp.server"],
      "cwd": "<path-to-repo>/pathways-mcp-server",
      "env": {
        "PATHWAYS_API_TOKEN": "<your-token>",
        "PATHWAYS_API_URL": "https://api.staging.withpathways.org"
      }
    }
  }
}
```

## Project structure

```
pathways-mcp-server/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── src/
    └── pathways_mcp/
        ├── __init__.py
        ├── __main__.py         # python -m entry point
        ├── server.py           # FastMCP server + tool registration
        ├── api.py              # Strapi API client (httpx, auth, pagination)
        └── tools/
            ├── __init__.py
            ├── segmentations.py
            ├── segments.py
            ├── metrics.py
            ├── variables.py
            ├── reference.py
            └── geography.py
```

## The Pathways Data Model

Understanding this hierarchy is key to understanding all the tools.

```
Geography (e.g., Senegal)
  └── Segmentation (e.g., SEN_2019DHS8_v1 — "Senegal 2019 DHS study")
        ├── Segments (e.g., R1, R2, R3, R4, U1, U2... — distinct groups of women)
        │     └── Metrics (a segment × variable pair = one data point)
        │
        └── Variables (the indicators measured, e.g., "Modern contraceptive use")
              ├── linked to Themes   → describe Health Outcomes
              └── linked to Domains  → describe Vulnerability Factors

Themes  = categories of Health Outcomes  (e.g., Maternal Health, Nutrition)
Domains = categories of Vulnerability Factors (e.g., Household Economics, Social Support)

Regions = sub-national administrative areas within a Geography
Geographic Distributions = what % of each region's population belongs to each segment
```

## The API Client (`api.py`)

This is the most important infrastructure file. It handles all HTTP communication.

### The `StrapiClient` class

When instantiated, it reads two environment variables — both are now required:
- `PATHWAYS_API_TOKEN` — the Bearer token (raises an error immediately if missing)
- `PATHWAYS_API_URL` — the base URL (raises an error immediately if missing; there is no default fallback)

```python
self._headers = {"Authorization": f"Bearer {token}"}
```

Every request includes this header, which Strapi uses to verify access.

### `fetch_collection` — one page of results

This is the main method. It:
1. Builds the query string parameters (filters, pagination, populate, fields)
2. Makes an async HTTP GET request using `httpx`
3. Returns the parsed JSON

```python
async with httpx.AsyncClient(...) as client:
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()
```

`resp.raise_for_status()` checks the HTTP status code. If the server returned a 4xx or 5xx error, it raises a Python exception immediately rather than silently returning broken data. Before calling that, the code also checks for specific codes to give actionable error messages:

```python
if resp.status_code == 403:
    raise RuntimeError("Access denied... Check your PATHWAYS_API_TOKEN.")
if resp.status_code == 404:
    raise RuntimeError(f"Endpoint '{endpoint}' not found on the Strapi API.")
```

A 403 means the token is wrong or expired. A 404 means the endpoint path itself doesn't exist — usually a typo in the collection name.

### `fetch_all` — auto-pagination

Some tools need all records, not just a page. `fetch_all` calls `fetch_collection` in a loop, advancing the page number on each iteration:

```python
while True:
    result = await self.fetch_collection(..., page=page, ...)
    data = result.get("data", [])
    all_data.extend(data)

    page_count = result["meta"]["pagination"]["pageCount"]

    if page >= page_count or len(all_data) >= max_records:
        break
    page += 1
```

Strapi tells you how many pages exist in the `meta.pagination.pageCount` field. The loop stops when you've fetched the last page, or when you've hit `max_records` (a safety cap to prevent fetching thousands of records if the data grows unexpectedly).

This is used by `get_segment_profile` for both its metrics fetch and variables fetch — both can be very large datasets.

### The `populate` parameter — what Strapi relations are

In relational databases, a **foreign key** is when one table stores only the ID of a record from another table — not the full data. For example, a `metrics` record stores a `variable_id: 42` rather than copying all the variable's fields.

Strapi works the same way. By default, when you fetch a metric, you get:

```json
{ "id": 1, "percentage": 0.34, "variable": null }
```

To get the actual variable data embedded in the response, you pass `populate`:

```python
populate=["variable", "categorical_level"]
```

Strapi then does a database JOIN behind the scenes and returns:

```json
{
  "id": 1,
  "percentage": 0.34,
  "variable": { "code": "fp.mod.use", "name_en": "Modern FP use", ... },
  "categorical_level": { "name_en": "Yes", ... }
}
```

Without populate, the tool code would have to make a separate API call for every variable — which would be hundreds of extra requests. Populate fetches them all in one go.

### The singleton pattern

```python
_client: StrapiClient | None = None

def get_client() -> StrapiClient:
    global _client
    if _client is None:
        _client = StrapiClient()
    return _client
```

The client is created once and reused across all tool calls. This avoids re-reading environment variables and re-allocating memory on every request.

### `RESPONSE_CHAR_LIMIT`

Set to 25,000 characters. All tool responses are truncated to this length before being returned to Claude:

```python
return json.dumps(output, indent=2)[:RESPONSE_CHAR_LIMIT]
```

This is a practical guard: MCP responses that are too large can cause problems for the AI client or hit context limits.

---
