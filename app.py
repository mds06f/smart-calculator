"""Streamlit app: type a question or expression, get the answer.

Flow: user text -> llm.text_to_expression() -> calculator.calculate()
The LLM's output is never trusted directly; it goes through the same
validation as anything typed by hand.
"""

import re

import streamlit as st

from calculator import CalculatorError, calculate
from llm import text_to_expression

MAX_HISTORY = 20

st.set_page_config(page_title="Smart Calculator", page_icon="🧮", layout="centered")

st.session_state.setdefault("result", None)
st.session_state.setdefault("error", None)
st.session_state.setdefault("history", [])  # list of (text, result), newest first


def restore(text, result):
    st.session_state["user_input"] = text
    st.session_state["result"] = result
    st.session_state["error"] = None


def clear_history():
    st.session_state["history"] = []


st.title("🧮 Smart Calculator")

with st.form("calculator_form"):
    st.text_input(
        "Ask a question or enter an expression",
        key="user_input",
        placeholder="e.g. two plus three times four",
    )
    submitted = st.form_submit_button("Calculate", type="primary", use_container_width=True)

if submitted:
    text = st.session_state["user_input"].strip()
    if not text:
        st.session_state["result"] = None
        st.session_state["error"] = None
    else:
        try:
            expression = text_to_expression(text)
            result = calculate(expression)
            st.session_state["result"] = result
            st.session_state["error"] = None
            history = st.session_state["history"]
            if not history or history[0] != (text, result):
                history.insert(0, (text, result))
                del history[MAX_HISTORY:]
        except CalculatorError as exc:
            st.session_state["result"] = None
            st.session_state["error"] = str(exc)

if st.session_state["error"]:
    st.error(st.session_state["error"])
else:
    st.text_input("Result", value=st.session_state["result"] or "", disabled=True)

if st.button("Clear", use_container_width=True):
    st.session_state["user_input"] = ""
    st.session_state["result"] = None
    st.session_state["error"] = None
    st.rerun()

with st.sidebar:
    st.header("History")
    history = st.session_state["history"]
    if not history:
        st.caption("No calculations yet.")
    else:
        st.caption(f"Last {MAX_HISTORY} results · click to reuse")
        for index, (text, result) in enumerate(history):
            label = re.sub(r"([\\`*_{}\[\]()#+\-.!])", r"\\\1", f"{text} = {result}")
            if st.button(label, key=f"history_{index}", type="tertiary"):
                restore(text, result)
                st.rerun()
        st.divider()
        if st.button("Clear history", icon=":material/delete:"):
            clear_history()
            st.rerun()
