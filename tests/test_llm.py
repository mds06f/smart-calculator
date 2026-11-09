"""Unit tests for :mod:`calc.llm`, with the API client mocked.

No real API key or network access is required: ``text_to_expression``
accepts a ``client_factory`` override, and these tests supply a fake
client that returns canned responses.
"""

from types import SimpleNamespace

import pytest
from openai import APITimeoutError

from calc.exceptions import LLMError
from calc.llm import MAX_ATTEMPTS, text_to_expression


def _response(content: str) -> SimpleNamespace:
    """Build a fake chat-completion response with the given content."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


class _FakeClient:
    """Stands in for the ``openai`` client's ``chat.completions.create``."""

    def __init__(self, replies):
        self._replies = iter(replies)
        self.calls = []

        class _Completions:
            def create(inner_self, **kwargs):
                self.calls.append(kwargs)
                reply = next(self._replies)
                if isinstance(reply, Exception):
                    raise reply
                return _response(reply)

        self.chat = SimpleNamespace(completions=_Completions())


def test_returns_expression_from_model():
    client = _FakeClient(["2 + 3 * 4"])
    assert text_to_expression("two plus three times four", lambda: client) == "2 + 3 * 4"


def test_strips_surrounding_whitespace():
    client = _FakeClient(["  sqrt(16)  \n"])
    assert text_to_expression("square root of 16", lambda: client) == "sqrt(16)"


def test_out_of_scope_raises_llm_error():
    client = _FakeClient(["NOT_MATH"])
    with pytest.raises(LLMError, match="only solve calculations"):
        text_to_expression("tell me a joke", lambda: client)


def test_empty_response_raises_llm_error():
    client = _FakeClient([""])
    with pytest.raises(LLMError, match="empty response"):
        text_to_expression("2 + 2", lambda: client)


def test_retries_once_then_succeeds():
    client = _FakeClient([APITimeoutError(request=None), "4"])
    assert text_to_expression("2 + 2", lambda: client) == "4"
    assert len(client.calls) == 2


def test_gives_up_after_max_attempts():
    client = _FakeClient([APITimeoutError(request=None)] * MAX_ATTEMPTS)
    with pytest.raises(LLMError, match="Could not reach the LLM"):
        text_to_expression("2 + 2", lambda: client)
    assert len(client.calls) == MAX_ATTEMPTS


def test_missing_api_key_raises_llm_error(monkeypatch):
    from calc import llm

    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setattr(llm.st, "secrets", {})
    with pytest.raises(LLMError, match="No API key"):
        text_to_expression("2 + 2")
