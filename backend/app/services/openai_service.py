import logging
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize AsyncOpenAI client pointing to Gemini's OpenAI-compatible endpoint
client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=float(settings.AI_TIMEOUT_SECONDS)
)


@retry(
    reraise=True,
    stop=stop_after_attempt(settings.AI_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError))
)
async def _call_model_with_retry(model_name: str, messages: list[dict]) -> str:
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages
    )
    return response.choices[0].message.content


class OpenAIService:
    @staticmethod
    async def generate_lead_summary(lead_notes: str) -> str:
        """
        Generate lead summary asynchronously with automatic exponential backoff
        and seamless fallback to secondary model on persistent failures.
        """
        messages = [
            {"role": "system", "content": "You are an AI dental CRM assistant. Summarize lead notes concisely."},
            {"role": "user", "content": lead_notes}
        ]

        # 1. Attempt Primary Model
        try:
            return await _call_model_with_retry(settings.AI_PRIMARY_MODEL, messages)
        except Exception as primary_error:
            logger.warning(
                "Primary AI model '%s' failed (%s); attempting fallback to '%s'",
                settings.AI_PRIMARY_MODEL,
                primary_error,
                settings.AI_FALLBACK_MODEL
            )

        # 2. Attempt Fallback Model
        try:
            return await _call_model_with_retry(settings.AI_FALLBACK_MODEL, messages)
        except Exception as fallback_error:
            logger.error("Fallback AI model '%s' also failed: %s", settings.AI_FALLBACK_MODEL, fallback_error)
            raise fallback_error