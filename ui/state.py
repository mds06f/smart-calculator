
"""Natural-language calculator state and evaluation logic."""

import ast
import operator
import re

import streamlit as st
from word2number import w2n


# Supported mathematical operators
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Supported mathematical functions
FUNCTIONS = {
    "sqrt": __import__("math").sqrt,
    "sin": __import__("math").sin,
    "cos": __import__("math").cos,
    "tan": __import__("math").tan,
    "log": __import__("math").log10,
    "ln": __import__("math").log,
    "factorial": __import__("math").factorial,
    "abs": abs,
}


# Number words recognised by word2number
NUMBER_WORDS = (
    "zero one two three four five six seven eight nine ten "
    "eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen twenty thirty forty fifty sixty seventy "
    "eighty ninety hundred thousand million billion point and"
)

NUMBER_PATTERN = re.compile(
    r"\b(?:" + NUMBER_WORDS.replace(" ", "|") + r")\b(?:[\s-]+\b(?:"
    + NUMBER_WORDS.replace(" ", "|") + r")\b)*",
    re.IGNORECASE,
)


def normalize_expression(expression: str) -> str:
    """Convert natural-language mathematics into a mathematical expression."""

    expression = expression.lower().strip()

    # Mathematical functions
    expression = re.sub(
        r"square root of",
        "sqrt ",
        expression
    )

    expression = re.sub(
        r"square root",
        "sqrt",
        expression
    )

    # Natural-language operators
    replacements = {
        "multiplied by": "*",
        "times": "*",
        "divided by": "/",
        "divided": "/",
        "plus": "+",
        "added to": "+",
        "minus": "-",
        "subtracted by": "-",
        "to the power of": "**",
        "raised to the power of": "**",
        "raised to": "**",
        "power of": "**",
        "modulo": "%",
        "modulus": "%",
    }

    for phrase, symbol in replacements.items():
        expression = expression.replace(phrase, symbol)

    # Convert number words into numeric values
    def convert_number(match):
        phrase = match.group(0).replace("-", " ")
        try:
            return str(w2n.word_to_num(phrase))
        except ValueError:
            return phrase

    expression = NUMBER_PATTERN.sub(convert_number, expression)

    # Convert function expressions such as "sqrt 16" into "sqrt(16)"
    expression = re.sub(
        r"\b(sqrt|sin|cos|tan|ln|log|factorial)\s+"
        r"(-?\d+(?:\.\d+)?)",
        r"\1(\2)",
        expression
    )

    # Remove common filler words
    expression = re.sub(r"\b(what is|calculate|evaluate)\b", "", expression)

    # Replace mathematical symbols
    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("^", "**")
    expression = expression.replace("π", "3.141592653589793")

    return expression.strip()


def safe_evaluate(node):
    """Evaluate only explicitly permitted mathematical AST nodes."""

    if isinstance(node, ast.Expression):
        return safe_evaluate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Invalid value.")

    if isinstance(node, ast.BinOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported operator.")

        left = safe_evaluate(node.left)
        right = safe_evaluate(node.right)

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported operation.")

        return operation(safe_evaluate(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Invalid function.")

        function = FUNCTIONS.get(node.func.id)

        if function is None:
            raise ValueError("Unsupported mathematical function.")

        if node.keywords:
            raise ValueError("Invalid arguments.")

        arguments = [safe_evaluate(arg) for arg in node.args]

        if len(arguments) != 1:
            raise ValueError("This function requires one argument.")

        return function(*arguments)

    raise ValueError("Invalid mathematical expression.")


def calculate(expression: str):
    """Parse and calculate a natural-language expression."""

    normalized = normalize_expression(expression)

    if not normalized:
        raise ValueError("Please enter an expression.")

    try:
        tree = ast.parse(normalized, mode="eval")
        result = safe_evaluate(tree)

        if isinstance(result, complex):
            raise ValueError("Complex results are not supported.")

        if isinstance(result, float) and not __import__("math").isfinite(result):
            raise ValueError("Result is not finite.")

        return result

    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero.")

    except SyntaxError:
        raise ValueError("Could not understand the expression.")

    except (OverflowError, ValueError) as error:
        raise ValueError(str(error))


# Streamlit session-state functions

def compute():
    """Calculate the expression currently stored in Streamlit state."""

    expression = st.session_state.get("expression", "")

    try:
        result = calculate(expression)
        st.session_state["result"] = result
        st.session_state["calculation_error"] = None

    except (ValueError, TypeError, ArithmeticError) as error:
        st.session_state["result"] = None
        st.session_state["calculation_error"] = str(error)


def clear():
    """Clear the expression and result."""

    st.session_state["expression"] = ""
    st.session_state["result"] = None
    st.session_state["calculation_error"] = None


def backspace():
    """Remove the last character."""

    expression = st.session_state.get("expression", "")
    st.session_state["expression"] = expression[:-1]


def insert_text(value: str):
    """Append text to the expression."""

    st.session_state["expression"] = (
        st.session_state.get("expression", "") + value
    )
