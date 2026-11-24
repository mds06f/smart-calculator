"""Streamlit chat UI. A LangChain agent reads the conversation and decides
which tool to call (calculator, switches, time, system info) — the tools
in tools.py do the actual work, the agent only reasons about when to use
them.
"""

import os

import streamlit as st
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from tools import calculate, change_switch, get_current_time, get_switches, get_system_info

MODEL = "openai/gpt-oss-20b"
CONTEXT_MESSAGES = 5  # only the most recent messages are sent, to cap cost

TOOLS = [calculate, get_switches, change_switch, get_current_time, get_system_info]

SYSTEM_PROMPT = """You are an assistant with these tools: calculate, get_switches,
change_switch, get_current_time, get_system_info. Always use a tool instead of
answering from memory when one applies.

- For arithmetic, break a multi-operation expression (e.g. "9+50-12") into one
  calculate call per operation, following BODMAS/order of operations (^ before
  * and /, before + and -). Never ask the user which operation to do first.
- If the user refers to a previous answer (e.g. "add 5 to it"), use that
  previous result as one of the numbers.
- You never make normal conversation. Do not greet back, chat, answer
  questions about yourself (name, model, who made you, how you are), tell
  jokes, or give opinions. The ONLY two things you ever do are: (1) call a
  tool and report its result, or (2) if the message doesn't call for a
  tool — including greetings, small talk, and questions about yourself —
  reply with exactly: Invalid operation/expression"""


def get_agent():
    api_key = st.secrets.get("GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No API key configured. Set GROQ_API_KEY.")
    model = ChatGroq(model=MODEL, api_key=api_key, temperature=0)
    return create_agent(model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)


st.set_page_config(page_title="Smart Agent", page_icon="🤖", layout="centered")
st.title("🤖 Smart Agent")

st.session_state.setdefault("messages", [])  # full chat, shown and sent to the agent

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask for a calculation, a switch, the time, or system info"):
    with st.chat_message("user"):
        st.write(prompt)

    try:
        agent = get_agent()
        history = st.session_state["messages"][-CONTEXT_MESSAGES:] + [
            {"role": "user", "content": prompt}
        ]
        result = agent.invoke({"messages": history})
        final_reply = result["messages"][-1].content

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
