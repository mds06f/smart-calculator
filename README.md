# Smart Agent

A chat-style agent built with **Streamlit**, **LangChain**, and **LangGraph**,
talking to Groq's LLMs (OpenAI-compatible). A central orchestrator splits
each request into tasks for three specialist agents, runs independent tasks
in parallel and dependent ones in sequence, then combines their results —
the tools in `tools.py` do the actual work, the LLMs never compute or look
anything up themselves.

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
├── app.py            # Streamlit chat UI, session memory, calls the orchestrator
├── orchestrator.py   # LangGraph StateGraph that routes requests and combines results
├── agent.py          # The three specialist LangChain agents
├── tools.py          # Tools the agents can call (calculate, switches, time, system info)
└── requirements.txt
```

## How it works

1. **tools.py** defines each capability as a small `@tool`-decorated
   function — the only way any agent does math, reads/changes switch
   state, or looks anything up.
2. **agent.py** builds three independent `langchain.agents.create_agent`
   agents, each scoped to one group of tools: a home automation agent
   (switches), a calculator agent, and a system information agent
   (time/system info).
3. **orchestrator.py** is a `langgraph.graph.StateGraph`:
   - A router step asks the model to split the request into stages of
     tasks, each tagged with the specialist agent it belongs to.
   - Tasks within a stage run in parallel (via LangGraph's `Send`); a task
     only lands in a later stage if it depends on an earlier stage's
     result, so dependent work still runs in order.
   - Specialist results are aggregated into one final reply (returned
     directly if there's only one result, or combined by the model if
     there are several). An empty plan means no agent applies, and the
     orchestrator replies `Invalid operation/expression`.
4. **app.py** just wires the Streamlit UI to `orchestrator.run()`. The
   exchange is only saved to `st.session_state` once it succeeds, so a
   failed request never leaves a dangling turn in the conversation sent on
   future calls.
