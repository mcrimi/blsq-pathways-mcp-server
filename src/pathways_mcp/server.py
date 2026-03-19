"""Pathways MCP Server — exposes the Pathways health segmentation platform via MCP tools."""

from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

from pathways_mcp.tools.segmentations import list_segmentations, get_segmentation
from pathways_mcp.tools.segments import list_segments, get_segment_profile
from pathways_mcp.tools.metrics import get_segment_metrics
from pathways_mcp.tools.variables import search_variables
from pathways_mcp.tools.reference import list_themes_and_domains, list_regions
from pathways_mcp.tools.geography import get_geographic_distribution
from pathways_mcp.prompts import segment_deep_dive
from pathways_mcp.resources import (
    load_lens,
    load_interventions,
    load_ethics,
    load_awihs_kenya,
    load_awihs_northern_nigeria,
    load_awihs_bihar_india,
)

# Load .env from project root if present
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

mcp = FastMCP(
    "pathways",
    instructions=(
        "Pathways is a health segmentation platform providing woman-centered data "
        "and insights for global health interventions and programatic investments. Use these tools and resources to explore "
        "segmentations, understand population segments and their vulnerability profiles, "
        "query health outcome metrics (linked to Themes), and vulnerability factor metrics "
        "(linked to Domains). Start with list_segmentations to discover available segmentations and their countries, "
        "then drill into segments and metrics."
        "Always begin data analysis by loading the Pathways analytical lens via load_lens tool or resource, this ensures correct interpretation of the data within the Pathways framework."
        "Before designing, evaluating, or discussing interventions/programatic investments, load the interventions framework with load_interventions tool or resource."
    ),
)

# Register all tools
mcp.tool()(list_segmentations)
mcp.tool()(get_segmentation)
mcp.tool()(list_segments)
mcp.tool()(get_segment_profile)
mcp.tool()(get_segment_metrics)
mcp.tool()(search_variables)
mcp.tool()(list_themes_and_domains)
mcp.tool()(list_regions)
mcp.tool()(get_geographic_distribution)

# Register resource tools
mcp.tool()(load_lens)
mcp.tool()(load_interventions)
mcp.tool()(load_ethics)
mcp.tool()(load_awihs_kenya)
mcp.tool()(load_awihs_northern_nigeria)
mcp.tool()(load_awihs_bihar_india)

# Register resources (URI-addressable)
mcp.resource("pathways://lens")(load_lens)
mcp.resource("pathways://interventions")(load_interventions)
mcp.resource("pathways://ethics")(load_ethics)
mcp.resource("pathways://awihs_kenya")(load_awihs_kenya)
mcp.resource("pathways://awihs_northern_nigeria")(load_awihs_northern_nigeria)
mcp.resource("pathways://awihs_bihar_india")(load_awihs_bihar_india)

# Register prompts
mcp.prompt()(segment_deep_dive)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
