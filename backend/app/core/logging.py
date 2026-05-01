"""P1-02: Structured logging via structlog."""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.core.config import Settings


def configure_logging(settings: "Settings") -> None:
    """Configure structlog + stdlib logging."""
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    # Shared processors for both structlog and stdlib
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.ENV == "dev":
        # Pretty-print in dev
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        # JSON in prod (parsed by log aggregators)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Suppress third-party Python warnings that litter the console
    import warnings, os
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    warnings.filterwarnings("ignore", message="PySoundFile failed")
    warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
    # Silence joblib loky physical core detection on Windows
    if not os.environ.get("LOKY_MAX_CPU_COUNT"):
        import multiprocessing
        os.environ["LOKY_MAX_CPU_COUNT"] = str(multiprocessing.cpu_count())
