"""
Import all ORM models so Alembic can discover them for autogenerate.
When adding a new model, import it here.
"""

from src.db.models.base import Base
from src.db.models.profile import AssessmentSession, PsychometricScore, UserProfile
from src.db.models.user import RefreshToken, User, UserRole

__all__ = [
    "Base",
    "User",
    "UserRole",
    "RefreshToken",
    "UserProfile",
    "AssessmentSession",
    "PsychometricScore",
]
