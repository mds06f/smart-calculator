"""Calculation history component, rendered in the sidebar."""

import streamlit as st

from ui.display import escape_markdown
from ui.state import HISTORY_KEY, MAX_HISTORY, Outcome, clear_history, restore


def render_history() -> None:
    """Show recent successful calculations; clicking one restores it."""
    history: list[Outcome] = st.session_state[HISTORY_KEY]
    with st.sidebar:
        st.header("History")
        if not history:
            st.caption("No calculations yet.")
            return

        st.caption(f"Last {MAX_HISTORY} results · click to reuse")
        for index, entry in enumerate(history):
            st.button(
                escape_markdown(f"{entry.expression} = {entry.message}"),
                key=f"history_{index}",
                on_click=restore,
                args=(entry,),
                type="tertiary",
            )
        st.divider()
        st.button("Clear history", on_click=clear_history, icon=":material/delete:")
