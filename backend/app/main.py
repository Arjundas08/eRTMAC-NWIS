from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os
import logging

# Ensure package root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings
from backend.app.db.database import Base, engine
from backend.app.api.v1 import wells, similarity, lookahead, ask, backtest, audit, documents, evidence, review, geocore, chronos, sentinel, pulse, nexus

# --- Production Middleware Imports (Phase 09) ---
from backend.app.core.rate_limiter import RateLimitMiddleware
from backend.app.core.security_headers import SecurityHeadersMiddleware
from backend.app.core.request_logging import RequestLoggingMiddleware

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-grade Nearby Wells Intelligence System (NWIS) for Oil India Limited. "
        "Provides stratigraphic depth normalization, multi-criteria explainable offset similarity, "
        "pre-bit look-ahead hazard prediction, and evidence-grounded decision support alongside eRTMAC."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,   # Disable Swagger in production
    redoc_url="/redoc" if settings.DEBUG else None,  # Disable ReDoc in production
    openapi_url="/openapi.json"  # Always expose schema for contract testing
)

# =============================================================================
# MIDDLEWARE STACK (order matters: last added = first executed)
# =============================================================================

# 1. CORS — Environment-aware origin control
if settings.ENVIRONMENT == "production":
    allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
    if not allowed_origins:
        allowed_origins = ["https://nwis.oilindia.in"]  # Production default
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware, environment=settings.ENVIRONMENT)

# 3. Rate Limiting (200 requests/minute per IP in dev, 100 in production)
rate_limit = 200 if settings.ENVIRONMENT != "production" else 100
app.add_middleware(RateLimitMiddleware, max_requests=rate_limit, window_seconds=60)

# 4. Structured Request Logging
app.add_middleware(RequestLoggingMiddleware)

# =============================================================================
# API ROUTERS
# =============================================================================

app.include_router(wells.router, prefix="/api/v1")
app.include_router(similarity.router, prefix="/api/v1")
app.include_router(lookahead.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(geocore.router, prefix="/api/v1")
app.include_router(chronos.router, prefix="/api/v1")
app.include_router(sentinel.router, prefix="/api/v1")
app.include_router(pulse.router, prefix="/api/v1")
app.include_router(nexus.router, prefix="/api/v1")

# =============================================================================
# UI REDIRECTS
# =============================================================================

@app.get("/app/sentinel", tags=["NWIS Sentinel UI"])
def app_sentinel():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/sentinel.html")

@app.get("/app/pulse", tags=["NWIS PULSE UI"])
def app_pulse():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/pulse.html")

@app.get("/app/nexus", tags=["NWIS NEXUS UI"])
def app_nexus():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/nexus.html")

# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/api/v1/status", tags=["Health & Status"])
def api_status():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "organization": "Oil India Limited (Testbed)",
        "status": "OPERATIONAL",
        "evidence_contract": "STRICT_EVIDENCE_OR_SILENCE",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs" if settings.DEBUG else "disabled_in_production"
    }

@app.get("/health", tags=["Health & Status"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database_backend": "SQLite_Local" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL_PostGIS"
    }

# Mount static frontend assets for single-command full-stack execution
frontend_dir = ROOT_DIR / "frontend" / "public"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
