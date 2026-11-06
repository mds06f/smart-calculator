"""Exception hierarchy used across the calculator core.

All errors raised intentionally by the ``calc`` package derive from
:class:`CalculatorError`, so callers (e.g. the UI) can catch a single type
and show its message directly to the user.
"""


class CalculatorError(Exception):
    """Base class for all user-facing calculator errors."""


class ValidationError(CalculatorError):
    """Raised when an expression is malformed or contains disallowed content."""


class EvaluationError(CalculatorError):
    """Raised when a valid expression cannot be evaluated to a real number."""
