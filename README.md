# Smart Calculator

An AI-assisted calculator built with **Streamlit**, **SymPy** and an LLM
(Groq). Type a question or expression in plain English; the LLM turns it
into a mathematical expression, which is validated and evaluated exactly.
See the [architecture diagram](docs/architecture/) and the
[development plan](docs/PLAN.md).

> **Status:** Core pipeline (validator + engine + LLM client) built and
> tested, with the LLM mocked in tests. A live `GROQ_API_KEY` is needed to
> run the app end-to-end.

## Features

- Single text box in, single text box out — type natural language or a
  direct expression, get the result or a plain-language error
- LLM converts text to an expression; its output is always re-validated
  before evaluation, never trusted directly
- Functions: `sqrt`, `abs`, `exp`, `ln`, `log` (natural), `log10`,
  `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `factorial`
- Exact maths with SymPy (`0.1 + 0.2 = 0.3`, `sin(π/2) = 1`)
- Clear error messages for invalid input, out-of-scope questions and
  undefined results

## Getting started

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
```

Set a Groq API key before running the app (not needed for the test suite):

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

Run the test suite (the LLM is mocked, so no key is required):

```bash
pytest
```

## Project structure

```
smart-calculator/
├── app.py               # Streamlit entry point
├── calc/                # Core logic (no UI code)
│   ├── exceptions.py    # CalculatorError / ValidationError / EvaluationError / LLMError
│   ├── llm.py           # Text -> expression via the Groq API
│   ├── validator.py     # Input normalisation and AST safety whitelist
│   └── engine.py        # AST → SymPy evaluation, limits and formatting
├── ui/                   # Streamlit components
│   └── state.py          # Session state: input -> LLM -> validator/engine -> result
├── tests/                # pytest suite (logic + mocked LLM + AppTest UI tests)
├── docs/                 # Architecture and plan
├── requirements.txt      # Runtime dependencies (pinned)
└── requirements-dev.txt  # Runtime + test dependencies
```

## How evaluation stays safe

User input — typed directly or produced by the LLM — is **never** passed to
`eval`, `exec` or `sympy.sympify`.

1. **LLM:** converts free-form text into a raw expression string. This
   output is treated as untrusted input, exactly like anything a user types.
2. **Validator:** normalises symbols (`×`, `÷`, `π`, `^`), enforces a length
   limit and a character whitelist, parses with `ast` and accepts only numeric
   literals, whitelisted operators, the constants `pi`/`e` and whitelisted
   single-argument functions.
3. **Engine:** walks the validated AST and builds the SymPy expression
   node by node. Power results are capped at 10,000 digits and `factorial` at
   1,000, which blocks DoS inputs such as `9**9**9`.
4. **UI:** the result/output box is read-only and never renders HTML.

A full security audit (including prompt-injection testing on the LLM step)
is planned for Phase 3.
