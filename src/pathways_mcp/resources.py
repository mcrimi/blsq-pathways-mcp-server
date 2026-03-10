"""Pathways MCP resources — loaded from .md files in the resources/ directory."""

from pathlib import Path

_RESOURCES_DIR = Path(__file__).parent / "resources"


def load_lens() -> str:
    """Load the Pathways analytical lens (six-domain vulnerability framework).

    Load this resource at the start of EVERY query that involves vulnerability
    analysis, segment interpretation, intervention design, or qualitative life
    stories.

    Defines:
    - The six-domain vulnerability framework (Personal History, Household
      Dynamics, Economic Stability, Social Capital, Structural Environment,
      Biological Health)
    - Three temporal patterns of vulnerability (childhood launch,
      accumulation, intergenerational transmission)
    - The macro / meso / micro analytical lenses

    Also specifies what the Pathways approach forbids — including attributing
    poor health outcomes to individual behaviour, proposing one-size
    interventions, or ignoring structural forces.

    Load before any other Pathways resource. Do not generate segment analysis
    or intervention recommendations without first applying this lens.
    """
    return (_RESOURCES_DIR / "lens.md").read_text()


def load_interventions() -> str:
    """Load the Pathways intervention design framework.

    Load when the query involves designing, evaluating, prioritising, or
    critiquing programmes or interventions for women in specific Pathways
    segments.

    Covers:
    - Three intervention levels (Individual/Household, Community/Social
      Norms, Structural/Systems)
    - Segment-specific logic for identifying friction points in the
      Journey of Care
    - Four archetype-based intervention profiles
    - The transformative vs transactional distinction
    - Cross-sector integration requirements and monitoring principles

    Do not load for purely descriptive or contextual queries. Requires the
    lens resource to be applied first — the segment profile must be
    established before intervention logic can be applied correctly.
    """
    return (_RESOURCES_DIR / "interventions.md").read_text()


def load_ethics() -> str:
    """Load the Pathways ethical framework for data use and communication.

    Load when the query involves:
    - How to present or communicate Pathways findings about specific women
      or communities
    - Requests to use segment data in ways that may stigmatise, expose, or
      surveil vulnerable populations
    - Questions about consent, data governance, or cultural sensitivity
    - Any use of Walk in Her Shoes testimonies for advocacy, fundraising,
      or publication
    - AI-specific dilemmas about how to reason about or represent women's
      lives ethically
    """
    return (_RESOURCES_DIR / "ethics.md").read_text()


def load_awihs_kenya() -> str:
    """Load qualitative life stories from Kenya (Walk in Her Shoes).

    Load when the query involves qualitative life stories, contextual
    grounding, or segment analysis for Kenya.

    Covers three contrasting settings:
    - Tana River County (remote pastoralist, FGM/C, early marriage)
    - Turkana County (nomadic, extreme food insecurity, absent husbands)
    - Nairobi Mathare informal settlement (urban poverty, female-headed
      households)

    Use alongside the lens resource to move from population data to lived
    experience. Do not load for purely quantitative or non-Kenya queries.
    """
    return (_RESOURCES_DIR / "awihs_kenya.md").read_text()


def load_awihs_northern_nigeria() -> str:
    """Load qualitative life stories from Northern Nigeria (Walk in Her Shoes).

    Load when the query involves qualitative life stories, contextual
    grounding, or segment analysis for Northern Nigeria.

    Provides structural portraits of women's lives shaped by purdah, early
    marriage, limited mobility, and male gate-keeping of health decisions.

    Use alongside the lens resource to ground vulnerability analysis in
    lived realities. Do not load for purely quantitative or non-Nigeria
    queries.
    """
    return (_RESOURCES_DIR / "awihs_northern_nigeria.md").read_text()


def load_awihs_bihar_india() -> str:
    """Load qualitative life stories from Bihar, India (Walk in Her Shoes).

    Load when the query involves qualitative life stories, contextual
    grounding, or segment analysis for Bihar, India.

    Synthesises lived experiences from rural Bihar illuminating how caste,
    gender, economic precarity, and household power dynamics intersect to
    shape health-seeking behaviour.

    Use alongside the lens resource to move from segmentation data to human
    reality. Do not load for purely quantitative or non-Bihar queries.
    """
    return (_RESOURCES_DIR / "awihs_bihar_india.md").read_text()
