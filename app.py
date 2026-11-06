"""Streamlit entry point for the Smart Calculator.

Run locally with::

    streamlit run app.py
"""

import streamlit as st

from calc.validator import MAX_LENGTH
from ui.display import render_result
from ui.state import EXPRESSION_KEY, compute, init_state


def main() -> None:
    """Build and render the calculator page."""
    st.set_page_config(page_title="Smart Calculator", page_icon="🧮", layout="centered")
    init_state()

    st.title("🧮 Smart Calculator")

    input_col, equals_col = st.columns([5, 1], vertical_alignment="bottom")
    with input_col:
        st.text_input(
            "Expression",
            key=EXPRESSION_KEY,
            on_change=compute,
            max_chars=MAX_LENGTH,
            placeholder="e.g. 2 + 3 × √(16)",
        )
    with equals_col:
        st.button("=", on_click=compute, type="primary", width="stretch")

    render_result()


if __name__ == "__main__":
    main()
