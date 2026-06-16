"""
Psychometric dimension definitions.

Defines the trait dimensions measured by the assessment engine, based on
a Big Five (OCEAN) personality model extended with career-relevant
work-style and interest dimensions (RIASEC-inspired).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PsychometricDimension(StrEnum):
    """
    Trait dimensions scored by the psychometric engine.

    The first five map to the Big Five (OCEAN) model. The remaining
    dimensions are RIASEC-inspired vocational interest types used to
    inform career recommendations.
    """

    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"

    REALISTIC = "realistic"
    INVESTIGATIVE = "investigative"
    ARTISTIC = "artistic"
    SOCIAL = "social"
    ENTERPRISING = "enterprising"
    CONVENTIONAL = "conventional"


class DimensionMetadata(BaseModel):
    """Human-readable metadata describing a dimension."""

    dimension: PsychometricDimension
    display_name: str
    description: str
    low_label: str
    high_label: str


DIMENSION_METADATA: dict[PsychometricDimension, DimensionMetadata] = {
    PsychometricDimension.OPENNESS: DimensionMetadata(
        dimension=PsychometricDimension.OPENNESS,
        display_name="Openness to Experience",
        description=(
            "Reflects curiosity, creativity, and preference for novelty "
            "versus routine and familiarity."
        ),
        low_label="Practical and consistent",
        high_label="Curious and inventive",
    ),
    PsychometricDimension.CONSCIENTIOUSNESS: DimensionMetadata(
        dimension=PsychometricDimension.CONSCIENTIOUSNESS,
        display_name="Conscientiousness",
        description=("Reflects organization, dependability, and goal-directed behavior."),
        low_label="Flexible and spontaneous",
        high_label="Organized and disciplined",
    ),
    PsychometricDimension.EXTRAVERSION: DimensionMetadata(
        dimension=PsychometricDimension.EXTRAVERSION,
        display_name="Extraversion",
        description=(
            "Reflects sociability, assertiveness, and energy drawn from interacting with others."
        ),
        low_label="Reserved and independent",
        high_label="Outgoing and energetic",
    ),
    PsychometricDimension.AGREEABLENESS: DimensionMetadata(
        dimension=PsychometricDimension.AGREEABLENESS,
        display_name="Agreeableness",
        description=("Reflects cooperativeness, empathy, and concern for social harmony."),
        low_label="Direct and competitive",
        high_label="Cooperative and compassionate",
    ),
    PsychometricDimension.NEUROTICISM: DimensionMetadata(
        dimension=PsychometricDimension.NEUROTICISM,
        display_name="Emotional Sensitivity",
        description=(
            "Reflects tendency toward emotional reactivity versus stability under pressure."
        ),
        low_label="Calm and resilient",
        high_label="Sensitive and reactive",
    ),
    PsychometricDimension.REALISTIC: DimensionMetadata(
        dimension=PsychometricDimension.REALISTIC,
        display_name="Realistic (Doers)",
        description=(
            "Preference for hands-on, practical work involving tools, "
            "machines, or physical activity."
        ),
        low_label="Conceptual focus",
        high_label="Hands-on focus",
    ),
    PsychometricDimension.INVESTIGATIVE: DimensionMetadata(
        dimension=PsychometricDimension.INVESTIGATIVE,
        display_name="Investigative (Thinkers)",
        description=("Preference for analytical, intellectual, and research-oriented work."),
        low_label="Action-oriented",
        high_label="Analysis-oriented",
    ),
    PsychometricDimension.ARTISTIC: DimensionMetadata(
        dimension=PsychometricDimension.ARTISTIC,
        display_name="Artistic (Creators)",
        description=("Preference for creative, expressive, and unstructured work."),
        low_label="Structured preference",
        high_label="Creative preference",
    ),
    PsychometricDimension.SOCIAL: DimensionMetadata(
        dimension=PsychometricDimension.SOCIAL,
        display_name="Social (Helpers)",
        description=("Preference for work that involves teaching, helping, or caring for others."),
        low_label="Task-focused",
        high_label="People-focused",
    ),
    PsychometricDimension.ENTERPRISING: DimensionMetadata(
        dimension=PsychometricDimension.ENTERPRISING,
        display_name="Enterprising (Persuaders)",
        description=("Preference for leadership, persuasion, and business-oriented work."),
        low_label="Supportive role preference",
        high_label="Leadership role preference",
    ),
    PsychometricDimension.CONVENTIONAL: DimensionMetadata(
        dimension=PsychometricDimension.CONVENTIONAL,
        display_name="Conventional (Organizers)",
        description=("Preference for structured, detail-oriented, and process-driven work."),
        low_label="Ambiguity tolerant",
        high_label="Structure seeking",
    ),
}


# Dimensions scored on the Big Five model (Likert-based, with reverse scoring).
OCEAN_DIMENSIONS: frozenset[PsychometricDimension] = frozenset(
    {
        PsychometricDimension.OPENNESS,
        PsychometricDimension.CONSCIENTIOUSNESS,
        PsychometricDimension.EXTRAVERSION,
        PsychometricDimension.AGREEABLENESS,
        PsychometricDimension.NEUROTICISM,
    }
)

# Dimensions scored on the RIASEC vocational interest model.
RIASEC_DIMENSIONS: frozenset[PsychometricDimension] = frozenset(
    {
        PsychometricDimension.REALISTIC,
        PsychometricDimension.INVESTIGATIVE,
        PsychometricDimension.ARTISTIC,
        PsychometricDimension.SOCIAL,
        PsychometricDimension.ENTERPRISING,
        PsychometricDimension.CONVENTIONAL,
    }
)
