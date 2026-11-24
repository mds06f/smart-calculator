# Smart Agent

A chat-style agent built with **Streamlit** and **LangChain**, talking to
Groq's LLMs (OpenAI-compatible). The agent reasons about which tool a
request needs and calls it — the tools in `tools.py` do the actual work,
the LLM never computes or looks anything up itself. This follows the same
pattern as a Semantic Kernel sample project: small, single-purpose plugin
functions the model can call, instead of one model that does everything.

## Features

- Chat interface with conversational memory (`st.session_state`) — ask
  follow-ups like "add 5 to it"
- Tools the agent can call:
  - `calculate` — basic arithmetic (`+`, `-`, `*`, `/`, `^`), resolved in
    BODMAS order for multi-operation requests like `9+50-12`
  - `get_switches` / `change_switch` — list and toggle a few fake switches
  - `get_current_time` — current date and time
  - `get_system_info` — basic OS/Python info
- Requests that don't match any tool get exactly: `Invalid operation/expression`
- Only the last 5 messages are sent per request, to keep token/cost growth
  bounded as a conversation gets longer
- Handles bad tool arguments and API errors without corrupting chat history

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
├── app.py          # Streamlit chat UI, session memory, builds the agent
├── tools.py        # Tools the agent can call (calculate, switches, time, system info)
└── requirements.txt
```

## How it works

1. **tools.py** defines each capability as a small `@tool`-decorated
   function — the agent's only way to do math, read/change switch state,
   or look anything up.
2. **app.py** builds a `langchain.agents.create_agent` agent out of the
   Groq chat model and those tools, with a system prompt describing when
   to use which tool (and to reply `Invalid operation/expression` when
   none fits).
3. On each message, the agent decides whether to call a tool, runs it,
   and keeps going until it has a final text reply — all handled by
   LangChain's agent loop, not hand-written code.
4. The exchange is only saved to `st.session_state` once it succeeds, so a
   failed request never leaves a dangling turn in the conversation sent on
   future calls.
