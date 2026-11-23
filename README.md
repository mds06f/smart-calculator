# Smart Calculator

A chat-style calculator built with **Streamlit** and the **Groq** API
(OpenAI-compatible). The LLM reads your message, extracts two numbers and
an operation, and calls a `calculate` tool — Python does the actual math.
This follows the same pattern as a Semantic Kernel calculator plugin: the
model never computes a result itself, it only calls the tool.

## Features

- Chat interface with conversational memory (`st.session_state`) — ask
  follow-ups like "add 5 to it" or "multiply that by 3"
- LLM extracts two numbers + an operation and calls the `calculate` tool;
  Python performs the arithmetic (`+`, `-`, `*`, `/`, `^`)
- Full tool-calling cycle: tool call -> execute -> tool result ->
  final LLM response
- Handles division by zero, invalid tool arguments and API errors

## Getting started

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Set a Groq API key before running the app:

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY = "..."
# macOS / Linux
export GROQ_API_KEY="..."
```

or add it to `.streamlit/secrets.toml` as `GROQ_API_KEY = "..."` (gitignored).

```bash
streamlit run app.py
```

## Project structure

```
smart-calculator/
├── app.py          # Streamlit chat UI, session memory, tool-calling loop
├── calculator.py   # The `calculate` tool: +, -, *, /, ^ on two numbers
└── requirements.txt
```

## How it works

1. **app.py** sends the chat history plus the `calculate` tool definition
   to the Groq API.
2. If the model wants to do math, it replies with a tool call
   (`a`, `b`, `operation`) instead of text.
3. **app.py** executes `calculator.calculate(a, b, operation)`, appends the
   result (or error) as a tool message, and calls the API again.
4. The model turns that result into a natural-language reply, which is
   shown in the chat and kept in `st.session_state` for future follow-ups.
