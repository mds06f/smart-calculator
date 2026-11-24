"""Tools the agent can call. Each function is registered with `@tool` and
does exactly one small, well-defined thing — the agent decides when to
call it and with what arguments, but never computes the result itself.
"""

from langchain_core.tools import tool

# A few fake switches, like the C# sample's SwitchesPlugin. In-memory only
# — state resets whenever the app restarts.
_switches = [
    {"name": "Living Room Light", "state": "off"},
    {"name": "Bedroom Light", "state": "on"},
    {"name": "Kitchen Fan", "state": "off"},
]


@tool
def get_switches() -> list:
    """List every switch and its current state (on/off)."""
    return _switches


@tool
def change_switch(switch_name: str, state: str) -> str:
    """Turn a switch on or off. state must be 'on' or 'off'."""
    for switch in _switches:
        if switch["name"].lower() == switch_name.lower():
            switch["state"] = state
            return f"{switch['name']} is now {state}."
    raise ValueError(f"No switch named '{switch_name}'.")


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
