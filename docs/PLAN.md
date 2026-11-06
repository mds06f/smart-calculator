# Smart Calculator – Development Plan

Based on `docs/architecture/AI Calculator System Architecture Diagram.png`.
Flow: Input → LLM intent classifier → guardrail → expression generator → validator → math engine → UI.

## Phase 1 – Core calculator (no LLM)
Goal: a working, safe calculator with the full UI.
- Project layout: `app.py` (UI), `calc/` package (`validator.py`, `engine.py`), `tests/`
- Streamlit UI: input box, keypad, result display, history (`st.session_state`)
- Expression validator: whitelist of characters/functions, length limit, AST/SymPy-based parse (never `eval`)
- Math engine: SymPy (`parse_expr` with restricted namespace) for +, −, ×, ÷, powers, sqrt, trig, log
- Error handling (div by zero, bad syntax) shown cleanly in the UI
- Unit tests with pytest for validator and engine
- Install later: `sympy`, `pytest`

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
- Code-injection audit of validator/engine: `__import__`, attribute access, huge exponents (`9**9**9`), factorial bombs, very long input (DoS) → add timeouts / size caps
- Secrets: confirm no API key in git history, `.env` and `secrets.toml` in `.gitignore`, key set in Streamlit Cloud secrets
- Rate limiting / per-session call limits to protect API quota
- Input/output sanitisation in the UI (no `unsafe_allow_html`)
- Dependency scan: `pip-audit`, static scan: `bandit`; pin versions in `requirements.txt`
- Fuzz tests for the validator (e.g. `hypothesis`)
- Deploy to Streamlit Cloud, write README + security notes
