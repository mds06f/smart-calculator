"""Result display component."""

import streamlit as st

from ui.state import OUTCOME_KEY, Outcome


def render_result() -> None:
    """Show the latest calculation result or error message.

    Values are rendered through Streamlit's escaped components, never as
    raw HTML, so user-supplied text cannot inject markup.
    """
    outcome: Outcome | None = st.session_state.get(OUTCOME_KEY)
    if outcome is None:
        st.caption("Type an expression and press **Enter** or **=**.")
    elif outcome.status == "ok":
        st.metric(label=outcome.expression, value=outcome.message, border=True)
    else:
        st.error(outcome.message, icon=":material/error:")
