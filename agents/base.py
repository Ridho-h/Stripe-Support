"""
Base agent LLM calling infrastructure for Stripe-Support-Agent-Dashboard.
Follows the pattern from Multi-Agent-Coding-Assistant and Multimodal-Food-Agent:
Gemini client with exponential backoff retries, structured JSON schema validation,
and clean error handling.
"""

import json
import logging
import os
import warnings
from typing import Any, Optional, Type

from dotenv import load_dotenv
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError, ServerError
except (ImportError, AttributeError):
    genai = None
    types = None
    ClientError = Exception
    ServerError = Exception
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

# Suppress AFC warnings
warnings.filterwarnings("ignore", message=".*automatic function calling.*", category=UserWarning)

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

_client = None


def get_client() -> Optional[Any]:
    global _client
    if _client is not None:
        return _client
    if genai is None:
        return None
    if API_KEY and API_KEY != "your_gemini_api_key_here":
        try:
            _client = genai.Client(api_key=API_KEY)
            return _client
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
    return None


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, ServerError):
        return True
    return False


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=1.0, min=1, max=5),
    stop=stop_after_attempt(2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_schema: Optional[Type[BaseModel]] = None,
    temperature: float = 0.1,
) -> Any:
    """
    Execute an LLM call via Google GenAI with automatic retries and structured schema support.
    """
    client = get_client()
    if client is None:
        raise RuntimeError("No active Gemini API key configured.")

    config_kwargs: dict = {
        "temperature": temperature,
        "system_instruction": system_prompt,
    }

    if response_schema:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema

    config = types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=config,
    )

    if response_schema:
        try:
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            logger.warning(f"Pydantic parsing failed on LLM response: {e}. Raw: {response.text}")
            # Try parsing json directly
            data = json.loads(response.text)
            return response_schema.model_validate(data)

    return response.text
