"""Converts a free-form question into a math expression, using the Groq API.

The returned expression is untrusted text, just like anything the user types
by hand — calculator.calculate() re-validates it before any math happens.
"""

import os

import streamlit as st
from openai import OpenAI

from calculator import CalculatorError

BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-20b"
OUT_OF_SCOPE = "NOT_MATH"

SYSTEM_PROMPT = """You convert a user's message into a single-line mathematical expression.

Rules:
- Reply with ONLY the expression. No words, no explanation, no markdown.
- Use only: digits, + - * / % ** ( ) and the functions sqrt, abs, exp, ln, \
log, log10, sin, cos, tan, asin, acos, atan, factorial, and the constants \
pi, e. Call functions like sqrt(16) and factorial(6) — always with \
parentheses, never postfix notation like 6!.
- If the message is not a math question or calculation, reply with exactly: NOT_MATH

Examples:
"two plus three times four" -> 2+3*4
"square root of 144 plus 6 factorial" -> sqrt(144)+factorial(6)
"""


def text_to_expression(text):
    """Ask the LLM to turn `text` into a raw math expression string."""
    api_key = st.secrets.get("GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise CalculatorError("No API key configured for the LLM.")

    client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=15.0)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
        )
    except Exception as exc:
        raise CalculatorError("Could not reach the LLM. Please try again.") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise CalculatorError("The LLM returned an empty response.")
    if content == OUT_OF_SCOPE:
        raise CalculatorError("Invalid mathematical expression.")
    return content
