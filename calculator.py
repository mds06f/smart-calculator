"""Turns a math expression (text) into a safe, exact numeric answer.

Never uses eval()/exec()/sympy.sympify() on user text. Instead:
1. normalize + whitelist the characters
2. parse with Python's `ast` module (parsing only, no execution)
3. walk the parsed tree and reject anything not on our whitelist
4. walk it again to build the equivalent SymPy expression by hand
"""

import ast
import operator
import re

import sympy as sp


class CalculatorError(Exception):
    """Any problem with the expression or its result, shown to the user as-is."""


# Expression + safety limits
MAX_LENGTH = 200
MAX_NODES = 100
MAX_RESULT_DIGITS = 10_000  # blocks huge powers like 9**9**9
MAX_FACTORIAL = 1_000

ALLOWED_CONSTANTS = {"pi": sp.pi, "e": sp.E}

ALLOWED_FUNCTIONS = {
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "exp": sp.exp,
    "ln": sp.log,
    "log": sp.log,
    "log10": lambda x: sp.log(x, 10),
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
}

ALLOWED_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Calculator-style symbols -> Python syntax, applied before parsing.
SYMBOL_REPLACEMENTS = {
    "×": "*",
    "÷": "/",
    "−": "-",
    "π": "pi",
    "√": "sqrt",
    "^": "**",
}

ALLOWED_CHARS = re.compile(r"^[0-9a-z_.+\-*/%()\s,]*$")


def check_node(node):
    """Raise CalculatorError if `node` (or any child) is outside our whitelist."""
    if isinstance(node, ast.Expression):
        check_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError("Only numeric literals are allowed.")
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in ALLOWED_BINARY_OPS:
            raise CalculatorError("Unsupported operator.")
        check_node(node.left)
        check_node(node.right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in ALLOWED_UNARY_OPS:
            raise CalculatorError("Unsupported operator.")
        check_node(node.operand)
    elif isinstance(node, ast.Name):
        if node.id not in ALLOWED_CONSTANTS:
            raise CalculatorError(f"Unknown name '{node.id}'.")
    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name not in ALLOWED_FUNCTIONS and func_name != "factorial":
            raise CalculatorError("Unknown or unsupported function.")
        if node.keywords or len(node.args) != 1:
            raise CalculatorError(f"'{node.func.id}' takes exactly one argument.")
        check_node(node.args[0])
    else:
        raise CalculatorError("Expression contains unsupported syntax.")


def parse_expression(text):
    """Normalize, whitelist-check and parse `text` into an ast.Expression."""
    text = text.strip().lower()
    for symbol, replacement in SYMBOL_REPLACEMENTS.items():
        text = text.replace(symbol, replacement)

    if not text:
        raise CalculatorError("Please enter an expression.")
    if len(text) > MAX_LENGTH:
        raise CalculatorError(f"Expression is too long (max {MAX_LENGTH} characters).")
    if not ALLOWED_CHARS.match(text):
        raise CalculatorError("Expression contains invalid characters.")

    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("Invalid syntax.") from exc

    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise CalculatorError("Expression is too complex.")

    check_node(tree)
    return tree


def safe_pow(base, exponent):
    """base ** exponent, but reject results that would be absurdly large."""
    magnitude = abs(base.evalf(15))
    if magnitude.is_zero or magnitude == 1:
        return base**exponent
    digits = abs(exponent.evalf(15)) * abs(sp.log(magnitude, 10).evalf(15))
    if digits > MAX_RESULT_DIGITS:
        raise CalculatorError("Result is out of range (too large or too small).")
    return base**exponent


def safe_factorial(value):
    if not (value.is_Integer and value >= 0):
        raise CalculatorError("Factorial is only defined for non-negative integers.")
    if value > MAX_FACTORIAL:
        raise CalculatorError(f"Factorial argument too large (max {MAX_FACTORIAL}).")
    return sp.factorial(value)


def to_sympy(node):
    """Recursively turn a whitelisted ast node into the equivalent SymPy expression."""
    if isinstance(node, ast.Expression):
        return to_sympy(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        return sp.Float(repr(node.value))
    if isinstance(node, ast.Name):
        return ALLOWED_CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp):
        return ALLOWED_UNARY_OPS[type(node.op)](to_sympy(node.operand))
    if isinstance(node, ast.BinOp):
        left, right = to_sympy(node.left), to_sympy(node.right)
        op = ALLOWED_BINARY_OPS[type(node.op)]
        return safe_pow(left, right) if op is operator.pow else op(left, right)
    if isinstance(node, ast.Call):
        arg = to_sympy(node.args[0])
        if node.func.id == "factorial":
            return safe_factorial(arg)
        return ALLOWED_FUNCTIONS[node.func.id](arg)
    raise CalculatorError("Unsupported expression.")


def evaluate(tree):
    """Turn a parsed expression tree into a finite, real SymPy number."""
    try:
        value = to_sympy(tree)
    except ZeroDivisionError as exc:
        raise CalculatorError("Division by zero.") from exc

    if value.has(sp.zoo, sp.nan) or value in (sp.oo, -sp.oo):
        raise CalculatorError("Result is undefined or infinite.")

    numeric = value.evalf(12)
    if not numeric.is_number or not numeric.is_finite:
        raise CalculatorError("Result is undefined.")
    if not numeric.is_real:
        raise CalculatorError("Result is not a real number.")
    return value


def format_result(value):
    """Format a SymPy number for display: exact integers, else 12 significant digits."""
    if value.is_Integer and len(str(abs(value))) <= 20:
        return str(value)

    numeric = sp.Float(value.evalf(12), 12)
    if numeric.is_zero:
        return "0"

    text = str(numeric)
    mantissa, sep, exponent = text.partition("e")
    if "." in mantissa:
        mantissa = mantissa.rstrip("0").rstrip(".")
    text = mantissa + sep + exponent
    # Clean up float noise like 0.1 * 10 = 1.00000000000 -> "1"
    return re.sub(r"\.0+$", "", text)


def calculate(expression):
    """Validate, evaluate and format an expression string. Main entry point."""
    tree = parse_expression(expression)
    value = evaluate(tree)
    return format_result(value)
