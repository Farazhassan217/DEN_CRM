import hmac
import hashlib
import time
import json
import pytest
from app.core.config import settings

def test_stripe_webhook_invalid_signature(client):
    """Verify that Stripe webhook rejects invalid signatures with 400 Bad Request."""
    response = client.post(
        "/api/v1/webhooks/stripe",
        json={"id": "evt_123", "type": "payment_intent.succeeded"},
        headers={"Stripe-Signature": "t=12345,v1=invalid_signature_hash"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_stripe_webhook_valid_signature_and_deduplication(client):
    """Verify that Stripe webhook accepts valid HMAC signature and deduplicates subsequent calls."""
    payload_dict = {"id": "evt_unique_12345", "type": "payment_intent.succeeded"}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    valid_sig = hmac.new(
        settings.WEBHOOK_STRIPE_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Stripe-Signature": f"t={timestamp},v1={valid_sig}",
        "Content-Type": "application/json"
    }
    
    # 1. First execution
    response1 = client.post("/api/v1/webhooks/stripe", content=payload_bytes, headers=headers)
    assert response1.status_code == 200
    assert response1.json()["processed"] is True
    
    # 2. Duplicate execution with same event id
    response2 = client.post("/api/v1/webhooks/stripe", content=payload_bytes, headers=headers)
    assert response2.status_code == 200
    assert response2.json().get("idempotent") is True


def test_meta_webhook_challenge_verification(client):
    """Verify that Meta webhook returns hub.challenge when token matches."""
    response = client.get(
        f"/api/v1/webhooks/meta-leads?hub.mode=subscribe&hub.verify_token={settings.WEBHOOK_META_VERIFY_TOKEN}&hub.challenge=challenge_token_999"
    )
    assert response.status_code == 200
    assert response.text == "challenge_token_999"
