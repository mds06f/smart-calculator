"""End-to-end tests of the Streamlit UI using Streamlit's ``AppTest`` harness."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.display import escape_markdown
from ui.keypad import MAIN_LAYOUT, SCIENTIFIC_LAYOUT
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


def press_key(at: AppTest, key: str) -> None:
    """Click the button with widget key ``key`` and rerun the app."""
    at.button(key=key).click()
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


def test_every_layout_key_is_rendered(app):
    rendered = {b.key for b in app.button}
    for row in SCIENTIFIC_LAYOUT + MAIN_LAYOUT:
        for key in row:
            assert key.widget_key in rendered
    assert "equals" in rendered


def test_keypad_builds_and_evaluates_expression(app):
    keys = ["sci_sqrt", "num_1", "num_6", "num_rparen", "op_mul", "num_2", "sci_pow", "num_3"]
    for key in keys:
        press_key(app, key)
    assert app.text_input(key=EXPRESSION_KEY).value == "√(16)×2^3"
    press_key(app, "equals")
    assert app.metric[0].value == "32"


def test_backspace_and_clear(app):
    for key in ["num_1", "num_2", "op_add"]:
        press_key(app, key)
    press_key(app, "ctrl_backspace")
    assert app.text_input(key=EXPRESSION_KEY).value == "12"
    press_key(app, "equals")
    press_key(app, "ctrl_clear")
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
