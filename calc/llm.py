"""LLM client: converts free-form text into a mathematical expression.

The LLM's output is untrusted. It is treated exactly like hand-typed input
and must pass through :func:`calc.validator.validate` (via
:func:`calc.engine.calculate`) before the math engine ever sees it.
"""

import os
from typing import Callable, Optional

import streamlit as st
from openai import APIError, APITimeoutError, OpenAI

from calc.exceptions import LLMError

#: xAI's OpenAI-compatible endpoint.
BASE_URL = "https://api.x.ai/v1"

#: Model used for text -> expression conversion.
MODEL = "grok-4-fast"

#: Seconds to wait for a response before giving up.
TIMEOUT = 15.0

#: Number of attempts (including the first) before giving up.
MAX_ATTEMPTS = 2

#: Sentinel the model returns for non-mathematical input.
OUT_OF_SCOPE = "NOT_MATH"

SYSTEM_PROMPT = """You convert a user's message into a single-line mathematical expression.

Rules:
- Reply with ONLY the expression. No words, no explanation, no markdown.
- Use only: digits, + - * / % ** ( ) and the functions sqrt, abs, exp, ln, \
log, log10, sin, cos, tan, asin, acos, atan, factorial, and the constants \
pi, e.
- If the message is not a math question or calculation, reply with exactly: NOT_MATH
"""


def _api_key() -> Optional[str]:
    """Read the xAI API key from Streamlit secrets, falling back to env."""
    try:
        key = st.secrets.get("XAI_API_KEY")
    except Exception:
        key = None
    return key or os.environ.get("XAI_API_KEY")


def _default_client() -> OpenAI:
    """Build the xAI client used outside of tests."""
    api_key = _api_key()
    if not api_key:
        raise LLMError("No API key configured for the LLM.")
    return OpenAI(api_key=api_key, base_url=BASE_URL, timeout=TIMEOUT)


def text_to_expression(
    text: str, client_factory: Callable[[], OpenAI] = _default_client
) -> str:
    """Convert free-form text into a raw mathematical expression.

    The returned string is untrusted and must still be validated by the
    caller (:func:`calc.engine.calculate` does this).

    Args:
        text: The user's raw input.
        client_factory: Factory for the API client. Overridden in tests so
            no real API key or network call is needed.

    Returns:
        A raw expression string, as produced by the LLM.

    Raises:
        LLMError: If the API key is missing, the call fails or times out
            after retries, or the input is out of scope.
    """
    client = client_factory()

    last_error: Optional[Exception] = None
    response = None
    for _ in range(MAX_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0,
            )
            break
        except (APIError, APITimeoutError) as exc:
            last_error = exc

    if response is None:
        raise LLMError("Could not reach the LLM. Please try again.") from last_error

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise LLMError("The LLM returned an empty response.")
    if content == OUT_OF_SCOPE:
        raise LLMError("I can only solve calculations.")
    return content
