"""Session-state management for the Smart Calculator UI.

Flow: raw user text -> LLM (:func:`calc.llm.text_to_expression`) -> the
expression validator and math engine (:func:`calc.engine.calculate`). The
LLM's output is never trusted directly; it always passes through the same
validator as hand-typed input.
"""

from dataclasses import dataclass

import streamlit as st

from calc import CalculatorError
from calc.engine import calculate
from calc.llm import text_to_expression

#: Session-state key bound to the text input.
INPUT_KEY = "user_input"

#: Session-state key holding the latest formatted result, or None.
RESULT_KEY = "result"

#: Session-state key holding the latest error message, or None.
ERROR_KEY = "error"

#: Session-state key holding successful outcomes, newest first.
HISTORY_KEY = "history"

#: Maximum number of history entries kept per session.
MAX_HISTORY = 20


@dataclass(frozen=True)
class Outcome:
    """A successful calculation kept in history.

    Attributes:
        text: The raw text the user entered.
        result: The formatted result.
    """

    text: str
    result: str


def init_state() -> None:
    """Populate session state with defaults on the first run of a session."""
    st.session_state.setdefault(INPUT_KEY, "")
    st.session_state.setdefault(RESULT_KEY, None)
    st.session_state.setdefault(ERROR_KEY, None)
    st.session_state.setdefault(HISTORY_KEY, [])


def compute() -> None:
    """Translate the current input to an expression and evaluate it."""
    text = st.session_state[INPUT_KEY].strip()
    if not text:
        st.session_state[RESULT_KEY] = None
        st.session_state[ERROR_KEY] = None
        return

    try:
        expression = text_to_expression(text)
        result = calculate(expression)
        st.session_state[RESULT_KEY] = result
        st.session_state[ERROR_KEY] = None
        _add_to_history(Outcome(text, result))
    except CalculatorError as exc:
        st.session_state[RESULT_KEY] = None
        st.session_state[ERROR_KEY] = str(exc)


def _add_to_history(outcome: Outcome) -> None:
    """Prepend a successful outcome to the history, skipping repeats.

    Args:
        outcome: A successful calculation outcome.
    """
    history: list[Outcome] = st.session_state[HISTORY_KEY]
    if history and history[0] == outcome:
        return
    history.insert(0, outcome)
    del history[MAX_HISTORY:]


def restore(outcome: Outcome) -> None:
    """Load a history entry back into the input and result display.

    Args:
        outcome: The history entry selected by the user.
    """
    st.session_state[INPUT_KEY] = outcome.text
    st.session_state[RESULT_KEY] = outcome.result
    st.session_state[ERROR_KEY] = None


def clear() -> None:
    """Clear the input, result and error."""
    st.session_state[INPUT_KEY] = ""
    st.session_state[RESULT_KEY] = None
    st.session_state[ERROR_KEY] = None


def clear_history() -> None:
    """Remove all history entries for the current session."""
    st.session_state[HISTORY_KEY] = []
