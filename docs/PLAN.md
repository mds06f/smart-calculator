# Smart Calculator – Development Plan

Based on `docs/architecture/AI Calculator System Architecture Diagram.png`.
Flow: Input → LLM intent classifier → guardrail → expression generator → validator → math engine → UI.

## Phase 1 – Core calculator (no LLM) ✅ Done
Goal: a working, safe calculator with the full UI.
- [x] Project layout: `app.py` (entry point), `calc/` (logic: `validator.py`, `engine.py`, `exceptions.py`), `ui/` (Streamlit components), `tests/`
- [x] Streamlit UI: input box, calculator-style keypad (large main keys, compact scientific row, mobile-friendly), result display, sidebar history (`st.session_state`)
- [x] Expression validator: symbol normalisation, character whitelist, length/complexity limits, `ast` parse with operator/name/function whitelist (never `eval`)
- [x] Math engine: builds SymPy expressions directly from the validated AST (no `parse_expr`/`sympify`, which use `eval` internally); caps on power and factorial size against DoS
- [x] Error handling (div by zero, bad syntax, non-real results) shown cleanly in the UI
- [x] pytest suite for validator, engine and UI (Streamlit `AppTest`)
- [x] Pinned `requirements.txt` / `requirements-dev.txt`, `pyproject.toml`, README

## Phase 2 – AI layer (Grok)
Goal: natural-language input and guardrails.
- Grok API client (`calc/llm.py`); API key via `st.secrets` / env var, never committed
- Intent classifier: `expression` | `text_problem` | `out_of_scope`
- Guardrail: out-of-scope → "I can only solve calculations."
- Text → expression generator; its output ALWAYS goes through the Phase 1 validator
- Timeouts, retries, graceful fallback when the API is down
- Optional short explanation of the result
- Tests with the LLM mocked
- Install later: `openai` (xAI API is OpenAI-compatible) or `requests`, `python-dotenv`

## Phase 3 – Security audit & hardening, deploy
Goal: make it safe to put on the internet.
- Prompt-injection testing: "ignore previous instructions", role-play, jailbreaks via the text input; confirm LLM output is treated as untrusted
- Code-injection audit of validator/engine: `__import__`, attribute access, huge exponents (`9**9**9`), factorial bombs, very long input (DoS) → verify the Phase 1 size caps, add an evaluation timeout
- Secrets: confirm no API key in git history, `.env` and `secrets.toml` in `.gitignore`, key set in Streamlit Cloud secrets
- Rate limiting / per-session call limits to protect API quota
- Input/output sanitisation in the UI: user input never rendered as HTML; review the static keypad stylesheet (`st.html`)
- Dependency scan: `pip-audit`, static scan: `bandit`; keep `requirements.txt` pinned
- Fuzz tests for the validator (e.g. `hypothesis`)
- Deploy to Streamlit Cloud, write README + security notes
