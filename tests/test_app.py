"""End-to-end tests of the Streamlit UI using Streamlit's ``AppTest`` harness."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.display import escape_markdown
from ui.state import EXPRESSION_KEY, HISTORY_KEY, MAX_HISTORY

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def app() -> AppTest:
    """Run the app once and return the test harness."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    at.run()
    assert not at.exception
    return at


def press(at: AppTest, label: str) -> None:
    """Click the button whose label is ``label`` and rerun the app."""
    next(b for b in at.button if b.label == label).click()
    at.run()


def enter(at: AppTest, expression: str) -> None:
    """Type ``expression`` into the input box and submit it."""
    at.text_input(key=EXPRESSION_KEY).input(expression)
    at.run()


def test_typed_expression_shows_result(app):
    enter(app, "2 + 3 * 4")
    assert app.metric[0].value == "14"


def test_error_is_shown(app):
    enter(app, "1 / 0")
    assert app.error[0].value == "Result is undefined or infinite."
    assert len(app.metric) == 0


def test_keypad_builds_and_evaluates_expression(app):
    for label in ["√", "1", "6", ")", "×", "2", "xʸ", "3"]:
        press(app, label)
    assert app.text_input(key=EXPRESSION_KEY).value == "√(16)×2^3"
    press(app, "=")
    assert app.metric[0].value == "32"


def test_backspace_and_clear(app):
    for label in ["1", "2", "+"]:
        press(app, label)
    press(app, "⌫")
    assert app.text_input(key=EXPRESSION_KEY).value == "12"
    press(app, "=")
    press(app, "C")
    assert app.text_input(key=EXPRESSION_KEY).value == ""
    assert len(app.metric) == 0


def test_history_records_only_successes(app):
    enter(app, "1 + 1")
    enter(app, "1 / 0")
    enter(app, "2 * 3")
    history = app.session_state[HISTORY_KEY]
    assert [h.expression for h in history] == ["2 * 3", "1 + 1"]


def test_history_is_capped(app):
    for i in range(MAX_HISTORY + 5):
        enter(app, f"{i} + 1")
    assert len(app.session_state[HISTORY_KEY]) == MAX_HISTORY


def test_history_entry_restores_expression(app):
    enter(app, "6 * 7")
    enter(app, "1 + 1")
    press(app, escape_markdown("6 * 7 = 42"))
    assert app.text_input(key=EXPRESSION_KEY).value == "6 * 7"
    assert app.metric[0].value == "42"


def test_clear_history(app):
    enter(app, "1 + 1")
    press(app, "Clear history")
    assert app.session_state[HISTORY_KEY] == []


def test_escape_markdown():
    assert escape_markdown("2*3_4") == r"2\*3\_4"
