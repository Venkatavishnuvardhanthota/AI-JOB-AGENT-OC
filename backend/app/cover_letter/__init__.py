"""
Legacy cover letter package — DEPRECATED.

Migration blocker: Still referenced by:
  - app/orchestrator/coordinator.py (CoverLetterExecutor)
  - app/application_package/validator.py (GeneratedCoverLetter import)
  - app/application_package/generator.py (GeneratedCoverLetter import)
  - tests/test_cover_letter.py (full test suite)

New AI-powered cover letter features are in:
  - app/ai/features/cover_letter.py (generate + assist via Prompt Registry)
  - app/services/cover_letter.py (async service with AI integration)

Remove this package only after the three references above are migrated.
"""

from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.dependencies import get_cover_letter_service
from app.cover_letter.exceptions import (
    CoverLetterCacheError,
    CoverLetterError,
    CoverLetterGenerationError,
    CoverLetterValidationError,
)
from app.cover_letter.schemas import (
    CoverLetterSection,
    GeneratedCoverLetter,
    PersonalizationData,
)

__all__ = [
    "GeneratedCoverLetter",
    "CoverLetterSection",
    "PersonalizationData",
    "CoverLetterConfig",
    "CoverLetterError",
    "CoverLetterGenerationError",
    "CoverLetterValidationError",
    "CoverLetterCacheError",
    "get_cover_letter_service",
]
