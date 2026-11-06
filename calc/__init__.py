"""Core calculator package: expression validation and evaluation.

This package contains no UI code so it can be tested in isolation and
reused by the Phase 2 LLM pipeline.
"""

from calc.exceptions import CalculatorError, EvaluationError, ValidationError

__all__ = ["CalculatorError", "EvaluationError", "ValidationError"]
