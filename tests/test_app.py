"""End-to-end tests of the Streamlit UI using Streamlit's ``AppTest`` harness.

The LLM call is mocked (``ui.state.text_to_expression`` is monkeypatched)
so these tests need no API key or network access.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.history import escape_markdown
from ui.state import HISTORY_KEY, INPUT_KEY, MAX_HISTORY

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


def test_history_records_only_successes(app):
    enter(app, "1 + 1")
    enter(app, "1 / 0")
    enter(app, "2 * 3")
    history = app.session_state[HISTORY_KEY]
    assert [h.text for h in history] == ["2 * 3", "1 + 1"]


def test_history_is_capped(app):
    for i in range(MAX_HISTORY + 5):
        enter(app, f"{i} + 1")
    assert len(app.session_state[HISTORY_KEY]) == MAX_HISTORY


def test_history_entry_restores_input_and_result(app):
    enter(app, "6 * 7")
    enter(app, "1 + 1")
    app.sidebar.button(key="history_1").click()
    app.run()
    assert app.text_input(key=INPUT_KEY).value == "6 * 7"
    assert result_box(app) == "42"


def test_clear_history_button(app):
    enter(app, "1 + 1")
    next(b for b in app.sidebar.button if b.label == "Clear history").click()
    app.run()
    assert app.session_state[HISTORY_KEY] == []


def test_escape_markdown():
    assert escape_markdown("2*3_4") == r"2\*3\_4"
