"""
Structured logging configuration using structlog.

Outputs machine-readable JSON in production and
human-readable colored output in development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.core.config.settings import get_settings


def add_app_context(
    logger: logging.Logger,
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """Add application-level context to every log entry."""
    _settings = get_settings()
    event_dict["app"] = _settings.APP_NAME
    event_dict["version"] = _settings.APP_VERSION
    event_dict["environment"] = _settings.ENVIRONMENT
    return event_dict


def drop_color_message_key(
    logger: logging.Logger,
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """Remove uvicorn's color_message field."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """
    Configure structlog for the application.

    Development: colored, human-readable console output.
    Production: JSON formatted output for log aggregators.
    """
    _settings = get_settings()

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
        drop_color_message_key,
    ]

    if _settings.is_development:
        processors: list[Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, _settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, _settings.LOG_LEVEL),
    )

    for noisy_logger in [
        "uvicorn.access",
        "sqlalchemy.engine",
        "transformers",
        "sentence_transformers",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """Return a structlog logger bound to the given name."""
    return structlog.get_logger(name)
