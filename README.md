# Smart Calculator

A scientific calculator built with **Streamlit** and **SymPy**, designed to grow
into an AI-assisted calculator that understands natural-language questions.
See the [architecture diagram](docs/architecture/) and the
[development plan](docs/PLAN.md).

> **Status:** Phase 1 (core calculator) complete. The LLM layer arrives in Phase 2.

## Features

- Expression input with **Enter** / **=** to evaluate
- Calculator-style keypad: large digit/operator keys, clear and backspace,
  plus a compact scientific row (`sin`, `√`, `xʸ`, `π`, `n!`, …); keeps its
  grid layout on mobile
- Functions: `sqrt`, `abs`, `exp`, `ln`, `log` (natural), `log10`,
  `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `factorial`
- Exact maths with SymPy (`0.1 + 0.2 = 0.3`, `sin(π/2) = 1`)
- Session history in the sidebar; click an entry to reuse it
- Clear error messages for invalid input and undefined results

## Getting started

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
streamlit run app.py
```

Run the test suite:

```bash
pytest
```

## Project structure

```
smart-calculator/
├── app.py               # Streamlit entry point
├── calc/                # Core logic (no UI code)
│   ├── exceptions.py    # CalculatorError / ValidationError / EvaluationError
│   ├── validator.py     # Input normalisation and AST safety whitelist
│   └── engine.py        # AST → SymPy evaluation, limits and formatting
├── ui/                  # Streamlit components
│   ├── state.py         # Session state and widget callbacks
│   ├── display.py       # Result display
│   ├── keypad.py        # On-screen keypad
│   └── history.py       # Sidebar history
├── tests/               # pytest suite (logic + AppTest UI tests)
├── docs/                # Architecture and plan
├── requirements.txt     # Runtime dependencies (pinned)
└── requirements-dev.txt # Runtime + test dependencies
```

## How evaluation stays safe

User input is **never** passed to `eval`, `exec` or `sympy.sympify`.

1. **Validator:** normalises symbols (`×`, `÷`, `π`, `^`), enforces a length
   limit and a character whitelist, parses with `ast` and accepts only numeric
   literals, whitelisted operators, the constants `pi`/`e` and whitelisted
   single-argument functions.
2. **Engine:** walks the validated AST and builds the SymPy expression
   node by node. Power results are capped at 10,000 digits and `factorial` at
   1,000, which blocks DoS inputs such as `9**9**9`.
3. **UI:** labels are Markdown-escaped and user input is never rendered as
   HTML. The only HTML injected is a static keypad stylesheet.

A full security audit is planned for Phase 3.
