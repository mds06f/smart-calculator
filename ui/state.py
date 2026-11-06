"""Session-state management and actions triggered by UI widgets.

Every function here is used as a Streamlit widget callback, which runs
*before* the script re-renders. That is the only point at which it is
allowed to modify the value of a widget such as the expression input.
"""

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from calc import CalculatorError
from calc.engine import calculate
from calc.validator import MAX_LENGTH

#: Session-state key bound to the expression text input.
EXPRESSION_KEY = "expression"

#: Session-state key holding the latest :class:`Outcome`.
OUTCOME_KEY = "outcome"

#: Session-state key holding successful outcomes, newest first.
HISTORY_KEY = "history"

#: Maximum number of history entries kept per session.
MAX_HISTORY = 20


@dataclass(frozen=True)
class Outcome:
    """Result of the most recent calculation attempt.

    Attributes:
        status: ``"ok"`` for a successful calculation, ``"error"`` otherwise.
        expression: The expression that was evaluated.
        message: The formatted result, or the error message.
    """

    status: Literal["ok", "error"]
    expression: str
    message: str


def init_state() -> None:
    """Populate session state with defaults on the first run of a session."""
    st.session_state.setdefault(EXPRESSION_KEY, "")
    st.session_state.setdefault(OUTCOME_KEY, None)
    st.session_state.setdefault(HISTORY_KEY, [])


def insert_text(text: str) -> None:
    """Append ``text`` to the expression, respecting the length limit.

    Args:
        text: Characters to append (e.g. ``"7"``, ``"×"`` or ``"sin("``).
    """
    current = st.session_state[EXPRESSION_KEY]
    if len(current) + len(text) <= MAX_LENGTH:
        st.session_state[EXPRESSION_KEY] = current + text


def backspace() -> None:
    """Delete the last character of the expression."""
    st.session_state[EXPRESSION_KEY] = st.session_state[EXPRESSION_KEY][:-1]


def clear() -> None:
    """Clear the expression and the displayed result."""
    st.session_state[EXPRESSION_KEY] = ""
    st.session_state[OUTCOME_KEY] = None


def compute() -> None:
    """Evaluate the current expression and store the outcome."""
    expression = st.session_state[EXPRESSION_KEY].strip()
    if not expression:
        st.session_state[OUTCOME_KEY] = None
        return
    try:
        outcome = Outcome("ok", expression, calculate(expression))
    except CalculatorError as exc:
        outcome = Outcome("error", expression, str(exc))
    st.session_state[OUTCOME_KEY] = outcome
    if outcome.status == "ok":
        _add_to_history(outcome)


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
    st.session_state[EXPRESSION_KEY] = outcome.expression
    st.session_state[OUTCOME_KEY] = outcome


def clear_history() -> None:
    """Remove all history entries for the current session."""
    st.session_state[HISTORY_KEY] = []
