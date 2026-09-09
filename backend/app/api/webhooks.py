import json
import logging
from fastapi import APIRouter, Request, HTTPException, status, Query, Header
from fastapi.responses import PlainTextResponse
from typing import Optional
from ..core.config import settings
from ..services.webhook import WebhookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """
    Inbound Stripe webhook for payment status updates (e.g. payment_intent.succeeded).
    Validates HMAC signature and guarantees idempotent processing.
    """
    payload_bytes = await request.body()
    if not WebhookService.verify_stripe_signature(payload_bytes, stripe_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature"
        )

    try:
        event = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = event.get("id")
    if event_id:
        if WebhookService.is_event_processed(event_id):
            logger.info("Stripe event %s already processed; acknowledging safely", event_id)
            return {"status": "success", "message": "Event already processed", "idempotent": True}
        WebhookService.mark_event_processed(event_id)

    event_type = event.get("type", "unknown")
    logger.info("Processing verified Stripe event: %s", event_type)
    return {"status": "success", "event": event_type, "processed": True}


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None, alias="X-Twilio-Signature")
):
    """
    Inbound Twilio SMS/WhatsApp webhook for appointment confirmations ('YES' to confirm).
    """
    form_data = await request.form()
    params = dict(form_data)
    url = str(request.url)

    if not WebhookService.verify_twilio_signature(url, params, x_twilio_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature"
        )

    message_sid = params.get("MessageSid")
    if message_sid:
        if WebhookService.is_event_processed(message_sid):
            logger.info("Twilio message %s already processed", message_sid)
            return {"status": "success", "message": "Duplicate ignored", "idempotent": True}
        WebhookService.mark_event_processed(message_sid)

    from_number = params.get("From")
    body = params.get("Body", "").strip()
    logger.info("Twilio inbound message received from %s: '%s'", from_number, body)

    return {"status": "success", "action": "acknowledged"}


@router.get("/meta-leads")
async def meta_lead_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Meta (Facebook Lead Ads) webhook verification endpoint.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_META_VERIFY_TOKEN:
        logger.info("Meta webhook verification challenge succeeded")
        return PlainTextResponse(content=hub_challenge or "")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.post("/meta-leads")
async def meta_lead_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """
    Inbound Meta Lead Ads webhook.
    """
    payload_bytes = await request.body()
    if not WebhookService.verify_meta_signature(payload_bytes, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Meta webhook signature"
        )

    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    entry = data.get("entry", [])
    for item in entry:
        lead_id = item.get("id")
        if lead_id and WebhookService.is_event_processed(lead_id):
            continue
        if lead_id:
            WebhookService.mark_event_processed(lead_id)

    return {"status": "success", "processed": True}
