"""Pathways MCP prompts — loaded from .md files in the prompts/ directory."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def segment_deep_dive(segment_name: str, country: str) -> str:
    """Deep dive into a specific population segment using the Pathways methodology."""
    template = (_PROMPTS_DIR / "segment_deep_dive.md").read_text()
    return template.format(segment_name=segment_name, country=country)
