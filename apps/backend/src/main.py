"""
Career Intelligence Platform — FastAPI Application Entry Point.

This module wires together all routers, middleware, and lifecycle events.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from src.api.v1.endpoints.auth import router as auth_router
from src.core.config.settings import get_settings
from src.core.logging.setup import configure_logging, get_logger
from src.db.engine import check_database_connection

configure_logging()
logger = get_logger(__name__)
_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Startup: verify infrastructure connections.
    Shutdown: gracefully close connections.
    """
    logger.info(
        "Starting Career Intelligence Platform",
        version=_settings.APP_VERSION,
        environment=_settings.ENVIRONMENT,
    )

    db_ok = await check_database_connection()
    if not db_ok:
        logger.error("Database connection failed — check DATABASE_URL")
    else:
        logger.info("Database connection verified")

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down Career Intelligence Platform")


def create_application() -> FastAPI:
    """
    Application factory function.
    Returns a fully configured FastAPI instance.
    """
    app = FastAPI(
        title=_settings.APP_NAME,
        description=_settings.APP_DESCRIPTION,
        version=_settings.APP_VERSION,
        docs_url=_settings.DOCS_URL if _settings.docs_enabled else None,
        redoc_url=_settings.REDOC_URL if _settings.docs_enabled else None,
        openapi_url=_settings.OPENAPI_URL if _settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.CORS_ORIGINS,
        allow_credentials=_settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=_settings.CORS_ALLOW_METHODS,
        allow_headers=_settings.CORS_ALLOW_HEADERS,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred"},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router, prefix=_settings.API_V1_PREFIX)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check() -> dict[str, str]:
        db_status = "ok" if await check_database_connection() else "degraded"
        return {
            "status": "ok",
            "version": _settings.APP_VERSION,
            "environment": _settings.ENVIRONMENT,
            "database": db_status,
        }

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": _settings.APP_NAME,
            "version": _settings.APP_VERSION,
        }

    return app


app = create_application()
