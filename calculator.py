"""The only thing allowed to do math. The LLM never computes a result
itself — it extracts two numbers and an operation, and calls `calculate`.
"""


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
            raise ValueError("Cannot divide by zero.")
        return a / b
    if operation == "^":
        return a**b
    raise ValueError(f"Unsupported operation '{operation}'.")
