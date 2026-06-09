from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routes import jobs, candidates, settings, reports, auth

app = FastAPI(title="HireIQ API", version="1.0.0")

# ─── CORS — restrict to known frontend origins in production ───
_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:6901,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global rate limiting (simple in-memory) ────────────────────
from collections import defaultdict
import time

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


@app.get("/")
def health_check():
    return {"status": "hireiq api operational", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
