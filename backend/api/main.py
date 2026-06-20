from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from api.core.limiter import limiter
from .routes import jobs, candidates, settings, reports, auth, billing, members, features

import sentry_sdk
import posthog

# ─── Sentry Error Monitoring ────────────────────────────────────
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    def scrub_sensitive_data(event, hint):
        # Strip Authorization headers, cookies, and any 'resume_text',
        # 'raw_text', 'password', 'card' fields from request data if present
        if 'request' in event:
            req = event['request']
            req.pop('cookies', None)
            headers = req.get('headers', {})
            headers.pop('Authorization', None)
            headers.pop('authorization', None)
            headers.pop('Cookie', None)
            headers.pop('cookie', None)
            
            # Scrub request body fields
            data = req.get('data')
            if data:
                if isinstance(data, dict):
                    for k in list(data.keys()):
                        if any(sensitive in k.lower() for sensitive in ('password', 'resume_text', 'raw_text', 'card', 'token', 'secret')):
                            data[k] = '[scrubbed]'
                elif isinstance(data, str):
                    try:
                        parsed = json.loads(data)
                        if isinstance(parsed, dict):
                            for k in list(parsed.keys()):
                                if any(sensitive in k.lower() for sensitive in ('password', 'resume_text', 'raw_text', 'card', 'token', 'secret')):
                                    parsed[k] = '[scrubbed]'
                            req['data'] = json.dumps(parsed)
                    except Exception:
                        pass
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.2,
        profiles_sample_rate=0.2,
        send_default_pii=False,
        before_send=scrub_sensitive_data,
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

# ─── Startup Security Checks ────────────────────────────────────
jwt_secret = os.getenv("JWT_SECRET_KEY")
if not jwt_secret:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")
if len(jwt_secret.strip()) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long.")

app = FastAPI(title="HireIQ API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.on_event("startup")
def on_startup():
    from db.session import engine
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema bootstrapped.")
    
    # Startup check for Resend sandbox domain in non-development environment
    from_email = os.getenv("FROM_EMAIL", "")
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    if not is_dev and "resend.dev" in from_email.lower():
        logger.warning(
            "WARNING: FROM_EMAIL is configured to use Resend's sandbox domain '%s' in a non-development environment! "
            "Emails may fail or land in spam.", from_email
        )

# ─── CORS — restrict to known frontend origins in production ───
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
_allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

# Fail fast if '*' is allowed with allow_credentials=True
if "*" in _allowed_origins:
    raise RuntimeError("CORS configuration error: Cannot allow '*' origin when allow_credentials is True.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").replace(",", " ")
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: https:; "
        f"connect-src 'self' {allowed_origins};"
    )
    return response




app.include_router(auth.router,       prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(jobs.router,       prefix="/api/v1")
app.include_router(settings.router,   prefix="/api/v1")
app.include_router(reports.router,    prefix="/api/v1")
app.include_router(billing.router,    prefix="/api/v1")
app.include_router(members.router,    prefix="/api/v1")
app.include_router(features.router,   prefix="/api/v1")

# ─── Prometheus Monitoring ──────────────────────────────────────
Instrumentator().instrument(app).expose(app)


@app.get("/")
def health_check():
    return {"status": "hireiq api operational", "version": "1.0.0"}


@app.get("/health")
async def health(response: Response):
    import asyncio
    from datetime import datetime
    from db.supabase_client import get_supabase
    
    # 1. Perform database availability check with 2.0s timeout
    db_status = "unreachable"
    error_msg = None
    try:
        async def check_db():
            loop = asyncio.get_running_loop()
            def run_query():
                client = get_supabase()
                client.table("recruiters").select("id").limit(1).execute()
            await loop.run_in_executor(None, run_query)
        
        await asyncio.wait_for(check_db(), timeout=2.0)
        db_status = "connected"
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database health check failed: {e}")

    # 2. Perform optional, non-blocking Redis connection ping (0.1s socket timeout)
    redis_status = "unconfigured"
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            with socket.create_connection((host, port), timeout=0.1):
                redis_status = "connected"
        except Exception:
            redis_status = "disconnected"

    # 3. Determine status and response code
    timestamp = datetime.utcnow().isoformat()
    if db_status == "connected":
        return {
            "status": "healthy",
            "database": "connected",
            "redis": redis_status,
            "timestamp": timestamp
        }
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "database": "unreachable",
            "redis": redis_status,
            "error": error_msg,
            "timestamp": timestamp
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
