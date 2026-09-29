import pytest
from unittest.mock import AsyncMock
from fastapi import Request
from app.core.idempotency import execute_idempotent

@pytest.mark.asyncio
async def test_idempotency_execution_and_replay():
    """Verify that idempotent execution caches and replays responses without duplicate side effects."""
    mock_request = AsyncMock(spec=Request)
    key = "test-idempotency-key-12345"
    
    call_counter = 0
    
    async def sample_payment_action():
        nonlocal call_counter
        call_counter += 1
        return {"payment_id": "pay_999", "status": "succeeded", "amount": 150.0}

    # First call: executes action
    res1 = await execute_idempotent(mock_request, key, sample_payment_action)
    assert call_counter == 1
    assert res1["payment_id"] == "pay_999"
    
    # Second call with same key: must NOT call action again!
    res2 = await execute_idempotent(mock_request, key, sample_payment_action)
    assert call_counter == 1  # Still 1, not incremented!
    assert res2.status_code == 200
    assert res2.headers.get("X-Idempotent-Replay") == "true"


@pytest.mark.asyncio
async def test_idempotency_without_key():
    """Requests without Idempotency-Key execute normally every time."""
    mock_request = AsyncMock(spec=Request)
    call_counter = 0

    async def normal_action():
        nonlocal call_counter
        call_counter += 1
        return {"count": call_counter}

    await execute_idempotent(mock_request, None, normal_action)
    await execute_idempotent(mock_request, None, normal_action)
    assert call_counter == 2
