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

#: Session-state key bound to the expression text input.
EXPRESSION_KEY = "expression"

#: Session-state key holding the latest :class:`Outcome`.
OUTCOME_KEY = "outcome"


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
