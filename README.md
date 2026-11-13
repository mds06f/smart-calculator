# Smart Calculator

An AI-assisted calculator built with **Streamlit**, **SymPy** and an LLM
(Groq). Type a question or expression in plain English; the LLM turns it
into a mathematical expression, which is validated and evaluated exactly.

## Features

- Single text box in, single text box out — type natural language or a
  direct expression, get the result or a plain-language error
- LLM converts text to an expression; its output is always re-validated
  before evaluation, never trusted directly
- Functions: `sqrt`, `abs`, `exp`, `ln`, `log` (natural), `log10`,
  `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `factorial`
- Exact maths with SymPy (`0.1 + 0.2 = 0.3`, `sin(π/2) = 1`)
- Session history in the sidebar; click an entry to reuse it
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
├── app.py          # Streamlit UI, session state, history sidebar
├── llm.py          # Text -> expression via the Groq API
├── calculator.py   # Expression validation, safe evaluation, formatting
└── requirements.txt
```

## How evaluation stays safe

User input — typed directly or produced by the LLM — is **never** passed to
`eval`, `exec` or `sympy.sympify`.

1. **llm.py:** converts free-form text into a raw expression string. This
   output is treated as untrusted input, exactly like anything a user types.
2. **calculator.py:** normalises symbols (`×`, `÷`, `π`, `^`), enforces a
   length limit and a character whitelist, parses with Python's `ast` module
   (parsing only, never executing), and only accepts numeric literals,
   whitelisted operators, the constants `pi`/`e` and whitelisted
   single-argument functions. The whitelisted tree is then walked to build
   the equivalent SymPy expression by hand. Power results are capped at
   10,000 digits and `factorial` at 1,000, which blocks DoS inputs such as
   `9**9**9`.
3. **app.py:** the result box is read-only and never renders HTML.
