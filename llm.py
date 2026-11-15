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

#: How many previous conversation messages to send for follow-up context.
#: Calculations chain message-to-message, so recent context is enough —
#: nobody refers back to something from 10 messages ago.
CONTEXT_MESSAGES = 3

SYSTEM_PROMPT = """You convert a user's message into a single-line mathematical expression.

Rules:
- Reply with ONLY the expression. No words, no explanation, no markdown.
- Use only: digits, + - * / % ** ( ) and the functions sqrt, abs, exp, ln, \
log, log10, sin, cos, tan, asin, acos, atan, factorial, and the constants \
pi, e. Call functions like sqrt(16) and factorial(6) — always with \
parentheses, never postfix notation like 6!.
- If the message is not a math question or calculation, reply with exactly: NOT_MATH
- You may be given previous exchanges for context. An assistant reply there
  looks like "expression = result". If the new message refers back to a
  previous result (e.g. "it", "that", "the answer"), substitute that
  result's actual numeric value into the new expression.

Examples:
"two plus three times four" -> 2+3*4
"square root of 144 plus 6 factorial" -> sqrt(144)+factorial(6)
(after a previous reply of "2+3 = 5") "add 5 to it" -> 5+5
(after a previous reply of "2+3 = 5") "multiply that by 3" -> 5*3
"""


def text_to_expression(text, conversation=None):
    """Ask the LLM to turn `text` into a raw math expression string.

    `conversation` is the full session conversation history (list of
    {"role": ..., "content": ...} dicts); only the last CONTEXT_MESSAGES
    of it are sent, to keep follow-ups like "add 5 to it" working without
    sending the whole session on every call.
    """
    api_key = st.secrets.get("GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise CalculatorError("No API key configured for the LLM.")

    context = (conversation or [])[-CONTEXT_MESSAGES:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *context, {"role": "user", "content": text}]

    client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=15.0)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
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
