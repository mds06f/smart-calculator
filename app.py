"""Streamlit chat UI. The LLM reads the conversation, decides when a message
needs arithmetic, and calls the `calculate` tool with two numbers and an
operation — Python then does the actual math (calculator.py).
"""

import json
import os

import streamlit as st
from openai import OpenAI

from calculator import calculate

BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a calculator. You only solve calculations — nothing else.

The `calculate` tool takes exactly two numbers and one operation
(+, -, *, /, ^ for power) and never computes anything yourself.

- If the message contains more than one operation (e.g. "9+50-12"), break
  it down following BODMAS/order of operations (^ before * and /, before +
  and -) and call `calculate` once per operation, step by step, using each
  result as an input to the next call. Never ask the user which operation
  to do first — always resolve it yourself using BODMAS.
- If the user refers to a previous answer (e.g. "add 5 to it", "multiply
  that by 3"), use that previous result as one of the numbers.
- If the message is not a calculation (greetings, general questions,
  anything non-mathematical), do not call the tool. Reply with exactly:
  Invalid operation/expression"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a basic arithmetic calculation on two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The first number."},
                    "b": {"type": "number", "description": "The second number."},
                    "operation": {
                        "type": "string",
                        "enum": ["+", "-", "*", "/", "^"],
                        "description": "+, -, *, / or ^ (power).",
                    },
                },
                "required": ["a", "b", "operation"],
            },
        },
    }
]


def get_client():
    api_key = st.secrets.get("GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No API key configured. Set GROQ_API_KEY.")
    return OpenAI(api_key=api_key, base_url=BASE_URL, timeout=15.0)


def ask_llm(client, messages):
    """Send the conversation to the LLM, run any tool calls it asks for,
    and return its final text reply. Returns only the new messages
    (assistant/tool turns) produced while answering.
    """
    new_messages = []
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages + new_messages, tools=TOOLS
        )
    except Exception as exc:
        raise ValueError("Could not reach the LLM. Please try again.") from exc

    reply = response.choices[0].message

    while reply.tool_calls:
        new_messages.append(
            {
                "role": "assistant",
                "content": reply.content,
                "tool_calls": [tc.model_dump() for tc in reply.tool_calls],
            }
        )
        for call in reply.tool_calls:
            try:
                args = json.loads(call.function.arguments)
                result = calculate(args["a"], args["b"], args["operation"])
                content = str(result)
            except (KeyError, ValueError, TypeError) as exc:
                content = f"Error: {exc}"
            new_messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": content}
            )

        try:
            response = client.chat.completions.create(
                model=MODEL, messages=messages + new_messages, tools=TOOLS
            )
        except Exception as exc:
            raise ValueError("Could not reach the LLM. Please try again.") from exc
        reply = response.choices[0].message

    new_messages.append({"role": "assistant", "content": reply.content or ""})
    return new_messages


st.set_page_config(page_title="Smart Calculator", page_icon="🧮", layout="centered")
st.title("🧮 Smart Calculator")

st.session_state.setdefault("messages", [])  # full chat, sent to the LLM for memory

for message in st.session_state["messages"]:
    if message["role"] in ("user", "assistant") and message["content"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if prompt := st.chat_input("Ask a calculation, e.g. what is 12 times 7?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    try:
        client = get_client()
        full_history = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state[
            "messages"
        ]
        new_messages = ask_llm(client, full_history)
        st.session_state["messages"].extend(new_messages)
        final_reply = new_messages[-1]["content"]
        with st.chat_message("assistant"):
            st.write(final_reply)
    except ValueError as exc:
        st.error(str(exc))

if st.button("Clear chat"):
    st.session_state["messages"] = []
    st.rerun()
