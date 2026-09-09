import json
import logging
from typing import Optional, Any, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from .redis_client import redis_client

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60  # 24 hours
IN_PROGRESS_TTL_SECONDS = 60  # 60 seconds lock


def check_idempotency(key: str) -> Optional[dict]:
    """Retrieve stored idempotency record from Redis."""
    raw = redis_client.get(f"idempotency:{key}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception as e:
        logger.warning("Failed to deserialize idempotency record for %s: %s", key, e)
        return None


def lock_idempotency_key(key: str) -> bool:
    """Lock key with 'processing' status to prevent race conditions."""
    redis_key = f"idempotency:{key}"
    existing = redis_client.get(redis_key)
    if existing:
        return False
    payload = json.dumps({"status": "processing"})
    return redis_client.set(redis_key, payload, ex=IN_PROGRESS_TTL_SECONDS)


def save_idempotent_response(key: str, status_code: int, data: Any, ttl: int = IDEMPOTENCY_TTL_SECONDS) -> bool:
    """Store finalized response in Redis with 24-hour TTL."""
    redis_key = f"idempotency:{key}"
    payload = json.dumps({
        "status": "completed",
        "status_code": status_code,
        "data": data
    })
    return redis_client.set(redis_key, payload, ex=ttl)


def release_idempotency_lock(key: str) -> bool:
    """Release in-progress lock if operation failed."""
    redis_key = f"idempotency:{key}"
    existing = check_idempotency(key)
    if existing and existing.get("status") == "processing":
        return redis_client.delete(redis_key)
    return False


async def execute_idempotent(
    request: Request,
    idempotency_key: Optional[str],
    action: Callable[[], Any]
) -> Any:
    """
    Executes an action with idempotency enforcement if key is provided.
    If no key is provided, executes the action normally.
    """
    if not idempotency_key:
        return await action()

    clean_key = idempotency_key.strip()
    if len(clean_key) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is too long (maximum 128 characters)."
        )

    # 1. Check existing record
    cached = check_idempotency(clean_key)
    if cached:
        if cached.get("status") == "completed":
            logger.info("Idempotency match found for key %s; replaying response", clean_key)
            return JSONResponse(
                status_code=cached.get("status_code", 200),
                content=cached.get("data"),
                headers={"X-Idempotent-Replay": "true"}
            )
        elif cached.get("status") == "processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request with this Idempotency-Key is currently being processed. Please retry shortly."
            )

    # 2. Lock key
    if not lock_idempotency_key(clean_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is currently being processed. Please retry shortly."
        )

    try:
        result = await action()
        # Extract serializable data
        status_code = status.HTTP_200_OK
        if hasattr(result, "status_code"):
            status_code = result.status_code

        serializable = result
        if hasattr(result, "model_dump"):
            serializable = result.model_dump(mode="json")
        elif hasattr(result, "dict"):
            serializable = result.dict()

        save_idempotent_response(clean_key, status_code, serializable)
        return result
    except Exception as exc:
        release_idempotency_lock(clean_key)
        raise exc
