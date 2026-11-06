"""Mathematical engine: turns a validated AST into a numeric result.

The engine never calls ``eval`` or ``sympy.sympify`` (which uses ``eval``
internally). Instead it walks the AST produced by
:func:`calc.validator.validate` and builds the equivalent SymPy expression
node by node, so only whitelisted operations can ever be executed.
"""

import ast
import operator
import re
from typing import Callable

import sympy as sp

from calc.exceptions import EvaluationError
from calc.validator import validate

#: Significant digits shown for non-integer results.
DISPLAY_PRECISION = 12

#: Integers with more digits than this are shown in scientific notation.
MAX_PLAIN_INTEGER_DIGITS = 20

_CONSTANTS: dict[str, sp.Expr] = {"pi": sp.pi, "e": sp.E}

_FUNCTIONS: dict[str, Callable[[sp.Expr], sp.Expr]] = {
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
    "factorial": sp.factorial,
}

_BINARY_OPS: dict[type, Callable[[sp.Expr, sp.Expr], sp.Expr]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_UNARY_OPS: dict[type, Callable[[sp.Expr], sp.Expr]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _to_sympy(node: ast.AST) -> sp.Expr:
    """Recursively convert a validated AST node into a SymPy expression.

    Args:
        node: A node from a tree that has already passed validation.

    Returns:
        The equivalent SymPy expression.

    Raises:
        EvaluationError: If an unexpected node type is encountered (this
            indicates the validator and engine are out of sync).
    """
    if isinstance(node, ast.Expression):
        return _to_sympy(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        return sp.Float(repr(node.value))
    if isinstance(node, ast.Name):
        return _CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp):
        return _UNARY_OPS[type(node.op)](_to_sympy(node.operand))
    if isinstance(node, ast.BinOp):
        left, right = _to_sympy(node.left), _to_sympy(node.right)
        return _BINARY_OPS[type(node.op)](left, right)
    if isinstance(node, ast.Call):
        return _FUNCTIONS[node.func.id](_to_sympy(node.args[0]))
    raise EvaluationError("Unsupported expression.")


def evaluate(tree: ast.Expression) -> sp.Expr:
    """Evaluate a validated expression tree.

    Args:
        tree: AST returned by :func:`calc.validator.validate`.

    Returns:
        A finite, real SymPy number. Exact results (e.g. ``Integer(4)`` or
        ``sqrt(2)``) are kept exact; formatting happens separately.

    Raises:
        EvaluationError: On division by zero, undefined results or results
            that are not real numbers.
    """
    try:
        value = _to_sympy(tree)
    except ZeroDivisionError as exc:
        raise EvaluationError("Division by zero.") from exc

    if value.has(sp.zoo, sp.nan) or value in (sp.oo, -sp.oo):
        raise EvaluationError("Result is undefined or infinite.")

    numeric = value.evalf(DISPLAY_PRECISION)
    if not numeric.is_number or not numeric.is_finite:
        raise EvaluationError("Result is undefined.")
    if not numeric.is_real:
        raise EvaluationError("Result is not a real number.")
    return value


def _strip_trailing_zeros(text: str) -> str:
    """Remove redundant zeros from a decimal mantissa (``2.500e+3`` → ``2.5e+3``)."""
    mantissa, sep, exponent = text.partition("e")
    if "." in mantissa:
        mantissa = mantissa.rstrip("0").rstrip(".")
    return mantissa + sep + exponent


def format_result(value: sp.Expr) -> str:
    """Format an evaluated result for display.

    Integers are shown exactly (unless very large); everything else is shown
    as a decimal rounded to :data:`DISPLAY_PRECISION` significant digits.

    Args:
        value: A finite, real SymPy number returned by :func:`evaluate`.

    Returns:
        Human-readable string representation of ``value``.
    """
    if value.is_Integer and len(str(abs(value))) <= MAX_PLAIN_INTEGER_DIGITS:
        return str(value)

    numeric = sp.Float(value.evalf(DISPLAY_PRECISION), DISPLAY_PRECISION)
    if numeric.is_zero:
        return "0"
    text = _strip_trailing_zeros(str(numeric))
    # Present float-noise results like 0.1 * 10 = 1.00000000000 as "1".
    return re.sub(r"\.0+$", "", text)


def calculate(expression: str) -> str:
    """Validate, evaluate and format an expression in one step.

    This is the main entry point used by the UI.

    Args:
        expression: Raw expression as entered by the user.

    Returns:
        The formatted result.

    Raises:
        CalculatorError: A :class:`ValidationError` or
            :class:`EvaluationError` with a user-friendly message.
    """
    return format_result(evaluate(validate(expression)))
