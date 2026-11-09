"""Session-state management for the Smart Calculator UI.

Flow: raw user text -> LLM (:func:`calc.llm.text_to_expression`) -> the
expression validator and math engine (:func:`calc.engine.calculate`). The
LLM's output is never trusted directly; it always passes through the same
validator as hand-typed input.
"""

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


def init_state() -> None:
    """Populate session state with defaults on the first run of a session."""
    st.session_state.setdefault(INPUT_KEY, "")
    st.session_state.setdefault(RESULT_KEY, None)
    st.session_state.setdefault(ERROR_KEY, None)


def compute() -> None:
    """Translate the current input to an expression and evaluate it."""
    text = st.session_state[INPUT_KEY].strip()
    if not text:
        st.session_state[RESULT_KEY] = None
        st.session_state[ERROR_KEY] = None
        return

    try:
        expression = text_to_expression(text)
        st.session_state[RESULT_KEY] = calculate(expression)
        st.session_state[ERROR_KEY] = None
    except CalculatorError as exc:
        st.session_state[RESULT_KEY] = None
        st.session_state[ERROR_KEY] = str(exc)


def clear() -> None:
    """Clear the input, result and error."""
    st.session_state[INPUT_KEY] = ""
    st.session_state[RESULT_KEY] = None
    st.session_state[ERROR_KEY] = None
