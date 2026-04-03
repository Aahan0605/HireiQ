"""
HireIQ — 360° Candidate Intelligence Platform
FastAPI Application Entry Point

Run:
    cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import sys
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.routes.candidates import router as candidates_router
from api.routes.jobs import router as jobs_router

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("hireiq")

# ─────────────────────────────────────────────────────────────
# ASCII art banner
# ─────────────────────────────────────────────────────────────
BANNER = r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗  ██╗██╗██████╗ ███████╗██╗ ██████╗                  ║
║   ██║  ██║██║██╔══██╗██╔════╝██║██╔═══██╗                 ║
║   ███████║██║██████╔╝█████╗  ██║██║   ██║                 ║
║   ██╔══██║██║██╔══██╗██╔══╝  ██║██║▄▄ ██║                 ║
║   ██║  ██║██║██║  ██║███████╗██║╚██████╔╝                 ║
║   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝ ╚══▀▀═╝                 ║
║                                                           ║
║   360° Candidate Intelligence Platform  v1.0.0            ║
║   ─────────────────────────────────────────────           ║
║   API:    http://0.0.0.0:8000                             ║
║   Docs:   http://0.0.0.0:8000/docs                        ║
║   Health: http://0.0.0.0:8000/health                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""


# ─────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    # Startup
    print(BANNER)
    logger.info("HireIQ v1.0 — Starting up")
    logger.info("All systems operational. Ready to evaluate candidates.")
    yield
    # Shutdown
    logger.info("HireIQ shutting down. Goodbye!")


# ─────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="HireIQ — 360° Candidate Intelligence Platform",
    description=(
        "AI-powered candidate evaluation engine combining resume parsing, "
        "external signal analysis (GitHub, LeetCode, Codeforces, CodeChef), "
        "claim verification, and bias auditing for fair hiring decisions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────────────
# CORS middleware
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev mode: allow all. Restrict in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Include routers
# ─────────────────────────────────────────────────────────────
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")


# ─────────────────────────────────────────────────────────────
# Root routes
# ─────────────────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/health", tags=["system"])
async def health_check_v1() -> dict:
    """Versioned health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "api_version": "v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# Global exception handler
# ─────────────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all exception handler for unhandled errors.
    Returns a structured JSON error response.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    logger.debug(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
    )


# ─────────────────────────────────────────────────────────────
# Run with uvicorn
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
