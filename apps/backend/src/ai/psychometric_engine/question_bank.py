"""
Psychometric assessment question bank.

Provides the static set of items used to assess the Big Five (OCEAN)
personality dimensions and RIASEC vocational interest types via a
5-point Likert scale.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.ai.psychometric_engine.dimensions import PsychometricDimension


class LikertQuestion(BaseModel):
    """A single 5-point Likert-scale assessment item."""

    id: str
    dimension: PsychometricDimension
    prompt: str
    reverse_scored: bool = False


# Likert scale labels presented to the user (1-5).
LIKERT_SCALE_LABELS: dict[int, str] = {
    1: "Strongly Disagree",
    2: "Disagree",
    3: "Neutral",
    4: "Agree",
    5: "Strongly Agree",
}


QUESTION_BANK: list[LikertQuestion] = [
    # --- Openness ---
    LikertQuestion(
        id="ocean_open_01",
        dimension=PsychometricDimension.OPENNESS,
        prompt="I enjoy exploring new ideas and unfamiliar concepts.",
    ),
    LikertQuestion(
        id="ocean_open_02",
        dimension=PsychometricDimension.OPENNESS,
        prompt="I prefer sticking to familiar methods rather than trying new approaches.",
        reverse_scored=True,
    ),
    LikertQuestion(
        id="ocean_open_03",
        dimension=PsychometricDimension.OPENNESS,
        prompt="I am curious about many different topics and subjects.",
    ),
    LikertQuestion(
        id="ocean_open_04",
        dimension=PsychometricDimension.OPENNESS,
        prompt="I enjoy thinking about abstract or theoretical ideas.",
    ),
    # --- Conscientiousness ---
    LikertQuestion(
        id="ocean_cons_01",
        dimension=PsychometricDimension.CONSCIENTIOUSNESS,
        prompt="I keep my workspace and schedule well organized.",
    ),
    LikertQuestion(
        id="ocean_cons_02",
        dimension=PsychometricDimension.CONSCIENTIOUSNESS,
        prompt="I often leave tasks unfinished or postpone them until the last minute.",
        reverse_scored=True,
    ),
    LikertQuestion(
        id="ocean_cons_03",
        dimension=PsychometricDimension.CONSCIENTIOUSNESS,
        prompt="I follow through on commitments even when it requires extra effort.",
    ),
    LikertQuestion(
        id="ocean_cons_04",
        dimension=PsychometricDimension.CONSCIENTIOUSNESS,
        prompt="I pay close attention to details and double-check my work.",
    ),
    # --- Extraversion ---
    LikertQuestion(
        id="ocean_extra_01",
        dimension=PsychometricDimension.EXTRAVERSION,
        prompt="I feel energized after spending time with a group of people.",
    ),
    LikertQuestion(
        id="ocean_extra_02",
        dimension=PsychometricDimension.EXTRAVERSION,
        prompt="I prefer working quietly on my own rather than in a team.",
        reverse_scored=True,
    ),
    LikertQuestion(
        id="ocean_extra_03",
        dimension=PsychometricDimension.EXTRAVERSION,
        prompt="I am comfortable starting conversations with people I don't know.",
    ),
    LikertQuestion(
        id="ocean_extra_04",
        dimension=PsychometricDimension.EXTRAVERSION,
        prompt="I enjoy being the center of attention in social situations.",
    ),
    # --- Agreeableness ---
    LikertQuestion(
        id="ocean_agree_01",
        dimension=PsychometricDimension.AGREEABLENESS,
        prompt="I try to be considerate of other people's feelings and needs.",
    ),
    LikertQuestion(
        id="ocean_agree_02",
        dimension=PsychometricDimension.AGREEABLENESS,
        prompt="I tend to assume the worst about people's intentions.",
        reverse_scored=True,
    ),
    LikertQuestion(
        id="ocean_agree_03",
        dimension=PsychometricDimension.AGREEABLENESS,
        prompt="I find it easy to cooperate and compromise with others.",
    ),
    LikertQuestion(
        id="ocean_agree_04",
        dimension=PsychometricDimension.AGREEABLENESS,
        prompt="I genuinely enjoy helping others solve their problems.",
    ),
    # --- Neuroticism ---
    LikertQuestion(
        id="ocean_neuro_01",
        dimension=PsychometricDimension.NEUROTICISM,
        prompt="I often feel anxious or worried about things that might go wrong.",
    ),
    LikertQuestion(
        id="ocean_neuro_02",
        dimension=PsychometricDimension.NEUROTICISM,
        prompt="I remain calm and composed even in stressful situations.",
        reverse_scored=True,
    ),
    LikertQuestion(
        id="ocean_neuro_03",
        dimension=PsychometricDimension.NEUROTICISM,
        prompt="My mood tends to fluctuate noticeably from day to day.",
    ),
    LikertQuestion(
        id="ocean_neuro_04",
        dimension=PsychometricDimension.NEUROTICISM,
        prompt="Criticism from others tends to affect me for a long time.",
    ),
    # --- Realistic (RIASEC) ---
    LikertQuestion(
        id="riasec_real_01",
        dimension=PsychometricDimension.REALISTIC,
        prompt="I enjoy working with tools, machines, or physical equipment.",
    ),
    LikertQuestion(
        id="riasec_real_02",
        dimension=PsychometricDimension.REALISTIC,
        prompt="I would rather build or repair something than discuss how it works.",
    ),
    LikertQuestion(
        id="riasec_real_03",
        dimension=PsychometricDimension.REALISTIC,
        prompt="I prefer practical, hands-on tasks over desk-based work.",
    ),
    # --- Investigative (RIASEC) ---
    LikertQuestion(
        id="riasec_inv_01",
        dimension=PsychometricDimension.INVESTIGATIVE,
        prompt="I enjoy analyzing data or solving complex puzzles.",
    ),
    LikertQuestion(
        id="riasec_inv_02",
        dimension=PsychometricDimension.INVESTIGATIVE,
        prompt="I like understanding the underlying reasons why things happen.",
    ),
    LikertQuestion(
        id="riasec_inv_03",
        dimension=PsychometricDimension.INVESTIGATIVE,
        prompt="I am drawn to scientific or research-based work.",
    ),
    # --- Artistic (RIASEC) ---
    LikertQuestion(
        id="riasec_art_01",
        dimension=PsychometricDimension.ARTISTIC,
        prompt="I enjoy expressing myself through writing, art, music, or design.",
    ),
    LikertQuestion(
        id="riasec_art_02",
        dimension=PsychometricDimension.ARTISTIC,
        prompt="I prefer open-ended tasks that allow for creative interpretation.",
    ),
    LikertQuestion(
        id="riasec_art_03",
        dimension=PsychometricDimension.ARTISTIC,
        prompt="I value originality and self-expression in my work.",
    ),
    # --- Social (RIASEC) ---
    LikertQuestion(
        id="riasec_soc_01",
        dimension=PsychometricDimension.SOCIAL,
        prompt="I find it rewarding to teach, mentor, or coach others.",
    ),
    LikertQuestion(
        id="riasec_soc_02",
        dimension=PsychometricDimension.SOCIAL,
        prompt="I am drawn to roles that involve directly helping or caring for people.",
    ),
    LikertQuestion(
        id="riasec_soc_03",
        dimension=PsychometricDimension.SOCIAL,
        prompt="I enjoy working as part of a team toward a shared goal.",
    ),
    # --- Enterprising (RIASEC) ---
    LikertQuestion(
        id="riasec_ent_01",
        dimension=PsychometricDimension.ENTERPRISING,
        prompt="I enjoy persuading or motivating others toward a goal.",
    ),
    LikertQuestion(
        id="riasec_ent_02",
        dimension=PsychometricDimension.ENTERPRISING,
        prompt="I am comfortable taking the lead on projects or decisions.",
    ),
    LikertQuestion(
        id="riasec_ent_03",
        dimension=PsychometricDimension.ENTERPRISING,
        prompt="I am interested in starting or growing a business.",
    ),
    # --- Conventional (RIASEC) ---
    LikertQuestion(
        id="riasec_conv_01",
        dimension=PsychometricDimension.CONVENTIONAL,
        prompt="I prefer clear instructions and well-defined procedures.",
    ),
    LikertQuestion(
        id="riasec_conv_02",
        dimension=PsychometricDimension.CONVENTIONAL,
        prompt="I enjoy organizing information, records, or data systematically.",
    ),
    LikertQuestion(
        id="riasec_conv_03",
        dimension=PsychometricDimension.CONVENTIONAL,
        prompt="I am comfortable with repetitive tasks that follow a consistent process.",
    ),
]


def get_questions_for_dimension(dimension: PsychometricDimension) -> list[LikertQuestion]:
    """Return all questions belonging to a given dimension."""
    return [q for q in QUESTION_BANK if q.dimension == dimension]


def get_question_by_id(question_id: str) -> LikertQuestion | None:
    """Return a single question by its identifier, or None if not found."""
    for question in QUESTION_BANK:
        if question.id == question_id:
            return question
    return None
