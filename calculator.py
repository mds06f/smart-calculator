"""The only thing allowed to do math. The LLM never computes a result
itself — it extracts two numbers and an operation, and calls `calculate`.
"""


class CalculatorError(Exception):
    """Raised for an unsupported operation or an invalid calculation."""


def calculate(a, b, operation):
    """Apply `operation` (+, -, *, /, ^) to numbers a and b."""
    if operation == "+":
        return a + b
    if operation == "-":
        return a - b
    if operation == "*":
        return a * b
    if operation == "/":
        if b == 0:
            raise CalculatorError("Cannot divide by zero.")
        return a / b
    if operation == "^":
        return a**b
    raise CalculatorError(f"Unsupported operation '{operation}'.")
