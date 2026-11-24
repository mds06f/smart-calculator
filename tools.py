"""Tools the agent can call. Each function is registered with `@tool` and
does exactly one small, well-defined thing — the agent decides when to
call it and with what arguments, but never computes the result itself.
"""

from langchain_core.tools import tool


@tool
def calculate(a: float, b: float, operation: str) -> float:
    """Perform a basic arithmetic calculation on two numbers.
    operation must be one of: +, -, *, /, ^ (power).
    """
    if operation == "+":
        return a + b
    if operation == "-":
        return a - b
    if operation == "*":
        return a * b
    if operation == "/":
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b
    if operation == "^":
        return a**b
    raise ValueError(f"Unsupported operation '{operation}'.")
