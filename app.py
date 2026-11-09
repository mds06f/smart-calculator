"""Streamlit entry point for the Smart Calculator.

Run locally with::

    streamlit run app.py
"""

import streamlit as st

from ui.state import ERROR_KEY, INPUT_KEY, RESULT_KEY, clear, compute, init_state


def main() -> None:
    """Build and render the calculator page."""
    st.set_page_config(page_title="Smart Calculator", page_icon="🧮", layout="centered")
    init_state()

    st.title("🧮 Smart Calculator")

    with st.form("calculator_form"):
        st.text_input(
            "Ask a question or enter an expression",
            key=INPUT_KEY,
            placeholder="e.g. two plus three times four",
        )
        submitted = st.form_submit_button(
            "Calculate", type="primary", use_container_width=True
        )

    if submitted:
        compute()

    output = st.session_state[ERROR_KEY] or st.session_state[RESULT_KEY] or ""
    st.text_input("Result", value=output, disabled=True)

    st.button("Clear", on_click=clear, use_container_width=True)


if __name__ == "__main__":
    main()
