from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from scalar_fastapi import get_scalar_api_reference

from .core.config import settings
from .core.supabase_client import init_supabase_clients
from .core.rate_limiter import limiter
from .core.redis_client import redis_client
from .core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    rate_limit_exception_handler,
    generic_exception_handler
)

from .api import (
    auth,
    users,
    organizations,
    clinics,
    leads,
    appointments,
    revenue,
    reports,
    audit,
    ai,
    webhooks
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("Starting up Dental CRM API...")
    init_supabase_clients()
    print("Supabase clients initialized")
    yield
    print("Shutting down Dental CRM API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
## Dental CRM API

A comprehensive CRM platform for dental clinics with role-based access control.

### Features:
- **Multi-Organization Support**: Manage multiple dental clinics
- **Role-Based Access Control**: 6 distinct user roles with granular permissions
- **Lead Management**: Track and convert leads
- **Appointment Scheduling**: Full appointment lifecycle management
- **Revenue Tracking**: Payment processing and financial reporting
- **Audit Logging**: Complete audit trail for compliance
- **AI Features**: OpenAI / Gemini powered automation and summaries
- **Enterprise Security**: Rate limiting, JWT revocation, and Idempotency
- **Webhooks**: Stripe, Twilio, and Meta Lead Ads integrations

### User Roles:
1. **Super Admin**: System-wide access
2. **Org Admin**: Organization management
3. **Clinic Manager**: Clinic operations
4. **Agent**: Lead handling and sales
5. **Reception**: Appointment management
6. **Finance**: Revenue and payment management
    """,
    version="1.0.0",
    lifespan=lifespan,
    servers=[{"url": "http://127.0.0.1:8000", "description": "Local Development Server"}]
)

# SlowAPI Limiter state
app.state.limiter = limiter

# Exception Handlers (Drawback 3 & Drawback 1)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS Middleware (Drawback 8 — Explicit configured origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(organizations.router, prefix=settings.api_prefix)
app.include_router(clinics.router, prefix=settings.api_prefix)
app.include_router(leads.router, prefix=settings.api_prefix)
app.include_router(appointments.router, prefix=settings.api_prefix)
app.include_router(revenue.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(webhooks.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Dental CRM API",
        "version": "1.0.0",
        "docs": "/docs",
        "scalar": "/scalar"
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive system health check monitoring Database, Redis, and AI configurations (Phase 4).
    """
    redis_connected = redis_client.ping()
    redis_status = "connected" if redis_connected else "degraded"

    # Database health check
    db_status = "unknown"
    try:
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    # AI health check
    ai_status = "configured" if settings.GEMINI_API_KEY else "missing_key"

    overall_status = "healthy" if (redis_connected and (db_status == "connected" or "unavailable" not in db_status)) else "degraded"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "components": {
            "database": db_status,
            "redis": redis_status,
            "ai_engine": ai_status
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Scalar API Documentation Endpoint
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
        servers=[{"url": "http://127.0.0.1:8000", "description": "Local Development Server"}],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)