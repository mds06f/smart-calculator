"""End-to-end tests of the Streamlit UI using Streamlit's ``AppTest`` harness.

The LLM call is mocked (``ui.state.text_to_expression`` is monkeypatched)
so these tests need no API key or network access.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.state import INPUT_KEY

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def app(monkeypatch) -> AppTest:
    """Run the app with the LLM mocked as an identity pass-through."""
    monkeypatch.setattr("ui.state.text_to_expression", lambda text: text)
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    at.run()
    assert not at.exception
    return at


def enter(at: AppTest, text: str) -> None:
    """Type ``text`` into the input box and submit the form."""
    at.text_input(key=INPUT_KEY).input(text)
    next(b for b in at.button if b.label == "Calculate").click()
    at.run()


def result_box(at: AppTest) -> str:
    """Return the current value of the read-only result box."""
    return next(t for t in at.text_input if t.label == "Result").value


def test_expression_is_evaluated(app):
    enter(app, "2 + 3 * 4")
    assert result_box(app) == "14"


def test_error_is_shown(app):
    enter(app, "1 / 0")
    assert result_box(app) == "Result is undefined or infinite."


def test_llm_rejection_is_shown_as_error(monkeypatch):
    from calc.exceptions import LLMError

    def refuse(text):
        raise LLMError("I can only solve calculations.")

    monkeypatch.setattr("ui.state.text_to_expression", refuse)
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    at.run()
    enter(at, "tell me a joke")
    assert result_box(at) == "I can only solve calculations."


def test_clear_resets_input_and_result(app):
    enter(app, "1 + 1")
    next(b for b in app.button if b.label == "Clear").click()
    app.run()
    assert app.text_input(key=INPUT_KEY).value == ""
    assert result_box(app) == ""
