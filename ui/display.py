"""Result display component and shared display helpers."""

import re

import streamlit as st

from ui.state import OUTCOME_KEY, Outcome

_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|~<>$])")


def escape_markdown(text: str) -> str:
    """Escape Markdown/LaTeX syntax so text is displayed literally.

    Streamlit renders labels (buttons, metrics) as Markdown, so an
    expression such as ``2*3*4`` would otherwise appear in italics.

    Args:
        text: Arbitrary user-visible text.

    Returns:
        ``text`` with every Markdown special character backslash-escaped.
    """
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)


def render_result() -> None:
    """Show the latest calculation result or error message.

    Values are rendered through Streamlit's escaped components, never as
    raw HTML, so user-supplied text cannot inject markup.
    """
    outcome: Outcome | None = st.session_state.get(OUTCOME_KEY)
    if outcome is None:
        st.caption("Type an expression and press **Enter** or **=**.")
    elif outcome.status == "ok":
        st.metric(label=escape_markdown(outcome.expression), value=outcome.message, border=True)
    else:
        st.error(outcome.message, icon=":material/error:")
