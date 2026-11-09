
import streamlit as st

from ui.state import compute

st.title("🧮 Smart Calculator")

# Initialise session state
if "expression" not in st.session_state:
    st.session_state.expression = ""

if "result" not in st.session_state:
    st.session_state.result = None

if "calculation_error" not in st.session_state:
    st.session_state.calculation_error = None

# Text-only expression input
with st.form("calculator_form"):
    st.text_input(
        "Expression",
        key="expression",
        placeholder="e.g. two plus three multiplied by four",
    )

    submitted = st.form_submit_button(
        "Calculate",
        type="primary",
        use_container_width=True,
    )

if submitted:
    compute()

# Display result
if st.session_state.calculation_error:
    st.error(st.session_state.calculation_error)

elif st.session_state.result is not None:
    st.success(f"Result: {st.session_state.result}")
