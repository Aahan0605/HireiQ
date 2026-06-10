from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
import time
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from .routes import jobs, candidates, settings, reports, auth, billing

import sentry_sdk
import posthog

# ─── Sentry Error Monitoring ────────────────────────────────────
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# ─── PostHog Analytics ──────────────────────────────────────────
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
if POSTHOG_API_KEY:
    posthog.project_api_key = POSTHOG_API_KEY
    posthog.host = POSTHOG_HOST
else:
    posthog.disabled = True

# ─── Structured JSON Logging ────────────────────────────────────
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    # Setup root logger with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="HireIQ API", version="1.0.0")

@app.on_event("startup")
def seed_default_user():
    import uuid
    from db.session import SessionLocal, engine
    from db.models import User, Base
    from api.core.security import get_password_hash

    # Ensure all tables are created (including new models)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        email = "REDACTED_EMAIL@example.com"
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password=get_password_hash("REDACTED_PASSWORD"),
                role="Admin"
            )
            db.add(new_user)
            db.commit()
            logger.info("Auto-seeded default user: REDACTED_EMAIL@example.com")
    except Exception as e:
        logger.error(f"Failed to seed default user: {e}")
    finally:
        db.close()

# ─── CORS — restrict to known frontend origins in production ───
_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:6901,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Strict Security Headers Middleware ─────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://localhost:8000 ws://localhost:8000 http://localhost:6901 ws://localhost:6901;"
    )
    return response

# ─── Global rate limiting (simple in-memory) ────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
_UPLOAD_RATE_LIMIT = 10  # uploads per minute per IP

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Determine limit — uploads get a stricter limit
    is_upload = "upload" in request.url.path
    limit = _UPLOAD_RATE_LIMIT if is_upload else _RATE_LIMIT

    # Clean old entries (older than 60 seconds)
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if now - t < 60]

    if len(_rate_store[client_ip]) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    _rate_store[client_ip].append(now)
    response = await call_next(request)
    return response


app.include_router(auth.router,       prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(jobs.router,       prefix="/api/v1")
app.include_router(settings.router,   prefix="/api/v1")
app.include_router(reports.router,    prefix="/api/v1")
app.include_router(billing.router,    prefix="/api/v1")

# ─── Prometheus Monitoring ──────────────────────────────────────
Instrumentator().instrument(app).expose(app)


@app.get("/")
def health_check():
    return {"status": "hireiq api operational", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
