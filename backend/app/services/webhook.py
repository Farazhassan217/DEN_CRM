import hmac
import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from ..core.config import settings
from ..core.redis_client import redis_client

logger = logging.getLogger(__name__)

WEBHOOK_EVENT_TTL = 7 * 24 * 60 * 60  # 7 days deduplication window


class WebhookService:
    """Service for webhook verification, deduplication, and dispatching."""

    @staticmethod
    def is_event_processed(event_id: str) -> bool:
        """Check if a webhook event has already been processed to prevent duplicates."""
        return redis_client.exists(f"webhook:event:{event_id}")

    @staticmethod
    def mark_event_processed(event_id: str) -> bool:
        """Mark event ID as processed with 7-day TTL."""
        return redis_client.set(f"webhook:event:{event_id}", "processed", ex=WEBHOOK_EVENT_TTL)

    @staticmethod
    def verify_stripe_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Verify Stripe signature using HMAC-SHA256.
        Header format: t=timestamp,v1=signature
        """
        if not signature_header or not settings.WEBHOOK_STRIPE_SECRET:
            return False

        try:
            parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
            timestamp = parts.get("t")
            v1_sig = parts.get("v1")
            if not timestamp or not v1_sig:
                return False

            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_sig = hmac.new(
                settings.WEBHOOK_STRIPE_SECRET.encode("utf-8"),
                signed_payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_sig, v1_sig)
        except Exception as e:
            logger.warning("Stripe signature validation failed with error: %s", e)
            return False

    @staticmethod
    def verify_meta_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Verify Meta (Facebook Lead Ads) signature using HMAC-SHA256.
        Header format: sha256=hash
        """
        if not signature_header or not settings.WEBHOOK_META_SECRET:
            return False

        try:
            prefix, _, received_hash = signature_header.partition("=")
            if prefix != "sha256" or not received_hash:
                return False

            expected_hash = hmac.new(
                settings.WEBHOOK_META_SECRET.encode("utf-8"),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_hash, received_hash)
        except Exception as e:
            logger.warning("Meta signature validation failed with error: %s", e)
            return False

    @staticmethod
    def verify_twilio_signature(url: str, params: Dict[str, Any], signature_header: Optional[str]) -> bool:
        """
        Verify Twilio webhook signature using HMAC-SHA1.
        """
        if not signature_header or not settings.WEBHOOK_TWILIO_SECRET:
            return False

        try:
            # Twilio sorts POST parameters alphabetically and concatenates them to the URL
            sorted_keys = sorted(params.keys())
            data_to_sign = url + "".join(f"{k}{params[k]}" for k in sorted_keys)

            import base64
            expected_sig = base64.b64encode(
                hmac.new(
                    settings.WEBHOOK_TWILIO_SECRET.encode("utf-8"),
                    data_to_sign.encode("utf-8"),
                    hashlib.sha1
                ).digest()
            ).decode("utf-8")

            return hmac.compare_digest(expected_sig, signature_header)
        except Exception as e:
            logger.warning("Twilio signature validation failed with error: %s", e)
            return False
