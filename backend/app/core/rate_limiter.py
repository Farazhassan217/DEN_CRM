from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from jose import jwt
from .config import settings

def get_clinic_rate_limit_key(request: Request) -> str:
    """
    Extract clinic identity from header, query, or JWT token payload.
    Falls back to remote IP if no clinic context is found.
    """
    # 1. Direct header
    clinic_id = request.headers.get("X-Clinic-ID") or request.headers.get("clinic-id")
    if clinic_id:
        return f"clinic:{clinic_id}"

    # 2. Query parameter
    clinic_param = request.query_params.get("clinic_id")
    if clinic_param:
        return f"clinic:{clinic_param}"

    # 3. Inspect Authorization Bearer token without verifying signature again
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            unverified_claims = jwt.get_unverified_claims(token)
            token_clinic = unverified_claims.get("clinic_id")
            if token_clinic:
                return f"clinic:{token_clinic}"
            assigned = unverified_claims.get("assigned_clinics")
            if assigned and isinstance(assigned, list) and len(assigned) > 0:
                return f"clinic:{assigned[0]}"
            org_id = unverified_claims.get("organization_id")
            if org_id:
                return f"org:{org_id}"
        except Exception:
            pass

    return f"ip:{get_remote_address(request)}"


# Initialize SlowAPI Limiter
# Uses Redis storage_uri if configured, else memory
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["120/minute"]
)
