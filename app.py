"""Streamlit chat UI. A LangGraph orchestrator reads the conversation,
delegates to the specialist agents in agent.py, and returns the final
reply — this file only wires up the UI and session state.
"""

import os

import streamlit as st

from orchestrator import run

CONTEXT_MESSAGES = 5  # only the most recent messages are sent, to cap cost


def get_api_key() -> str:
    api_key = st.secrets.get("GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No API key configured. Set GROQ_API_KEY.")
    return api_key


st.set_page_config(page_title="Smart Agent", page_icon="🤖", layout="centered")
st.title("🤖 Smart Agent")

st.session_state.setdefault("messages", [])  # full chat, shown and sent to the orchestrator

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask for a calculation, a switch, the time, or system info"):
    with st.chat_message("user"):
        st.write(prompt)

    try:
        api_key = get_api_key()
        history = st.session_state["messages"][-CONTEXT_MESSAGES:]
        final_reply = run(prompt, history, api_key)

        # Only persist the exchange once it succeeds, so a failed call never
        # leaves a user message without a reply in history.
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.session_state["messages"].append({"role": "assistant", "content": final_reply})
        with st.chat_message("assistant"):
            st.write(final_reply)
    except Exception as exc:
        st.error(str(exc))

if st.button("Clear chat"):
    st.session_state["messages"] = []
    st.rerun()
