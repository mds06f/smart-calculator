# Smart Calculator – Development Plan

Based on `docs/architecture/SmartCalculator_archimg.png`.
Flow: Input box → LLM → expression validator → math engine → Output box.

## Phase 1 – Core calculator (no LLM) ✅ Done
Goal: a safe expression validator and math engine, usable standalone.
- [x] Project layout: `app.py` (entry point), `calc/` (logic: `validator.py`, `engine.py`, `llm.py`, `exceptions.py`), `ui/` (Streamlit components), `tests/`
- [x] Expression validator: symbol normalisation, character whitelist, length/complexity limits, `ast` parse with operator/name/function whitelist (never `eval`)
- [x] Math engine: builds SymPy expressions directly from the validated AST (no `parse_expr`/`sympify`, which use `eval` internally); caps on power and factorial size against DoS
- [x] Error handling (div by zero, bad syntax, non-real results) shown cleanly in the UI
- [x] pytest suite for validator, engine and UI (Streamlit `AppTest`)
- [x] Pinned `requirements.txt` / `requirements-dev.txt`, `pyproject.toml`, README

## Phase 2 – AI layer ✅ Scaffolded, needs a live key
Goal: natural-language input through a single text box in, text box out.
- [x] Streamlit UI: one text input, one disabled text output, Calculate/Clear
- [x] LLM client (`calc/llm.py`): xAI (Grok) via the OpenAI-compatible API; API key from `st.secrets["XAI_API_KEY"]` / `XAI_API_KEY` env var, never committed
- [x] Text → expression generator; its output ALWAYS goes through the Phase 1 validator (`calc.engine.calculate`) before evaluation
- [x] Out-of-scope guardrail: model returns `NOT_MATH` sentinel → shown as "I can only solve calculations."
- [x] Timeout and single retry on the API call; errors surface in the output box via `LLMError`
- [x] Tests with the LLM mocked (`tests/test_llm.py`, `tests/test_app.py`) — no API key needed to run the suite
- [ ] A real `XAI_API_KEY` set in `st.secrets` / env to exercise the live path
- [ ] Optional short explanation of the result

## Phase 3 – Security audit & hardening, deploy
Goal: make it safe to put on the internet.
- Prompt-injection testing: "ignore previous instructions", role-play, jailbreaks via the text input; confirm LLM output is treated as untrusted (it already goes through the validator, but test deliberately adversarial prompts)
- Code-injection audit of validator/engine: `__import__`, attribute access, huge exponents (`9**9**9`), factorial bombs, very long input (DoS) → verify the Phase 1 size caps, add an evaluation timeout
- Secrets: confirm no API key in git history, `.env` and `secrets.toml` in `.gitignore`, key set in Streamlit Cloud secrets
- Rate limiting / per-session call limits to protect API quota
- Input/output sanitisation in the UI: user input never rendered as HTML
- Dependency scan: `pip-audit`, static scan: `bandit`; keep `requirements.txt` pinned
- Fuzz tests for the validator (e.g. `hypothesis`)
- Deploy to Streamlit Cloud, write README + security notes
