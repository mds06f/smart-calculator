"""Unit tests for :mod:`calc.engine`."""

import pytest

from calc.engine import MAX_FACTORIAL, calculate
from calc.exceptions import EvaluationError, ValidationError


class TestArithmetic:
    """Basic operations and operator precedence."""

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("1 + 2", "3"),
            ("2 + 3 * 4", "14"),
            ("(2 + 3) * 4", "20"),
            ("10 / 4", "2.5"),
            ("7 - 10", "-3"),
            ("-(-5)", "5"),
            ("2 ^ 10", "1024"),
            ("2 ** -1", "0.5"),
            ("10 % 3", "1"),
            ("-7 % 3", "2"),
            ("2.5e3", "2500"),
        ],
    )
    def test_results(self, expression, expected):
        assert calculate(expression) == expected

    def test_calculator_symbols(self):
        assert calculate("6 × 7 ÷ 2 − 1") == "20"


class TestFormatting:
    """Display formatting of results."""

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("0.1 + 0.2", "0.3"),
            ("0.1 * 10", "1"),
            ("1 / 3", "0.333333333333"),
            ("0 * 1.5", "0"),
            ("1e-20", "1e-20"),
            ("factorial(20)", "2432902008176640000"),
            ("2 ** 100", "1.26765060023e+30"),
        ],
    )
    def test_formatting(self, expression, expected):
        assert calculate(expression) == expected


class TestFunctions:
    """Whitelisted functions and constants."""

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("sqrt(16)", "4"),
            ("sqrt(2)", "1.41421356237"),
            ("abs(-3)", "3"),
            ("sin(pi / 2)", "1"),
            ("cos(0)", "1"),
            ("tan(0)", "0"),
            ("asin(1) * 2", "3.14159265359"),
            ("ln(e)", "1"),
            ("log(e ** 2)", "2"),
            ("log10(1000)", "3"),
            ("exp(0)", "1"),
            ("factorial(5)", "120"),
            ("π", "3.14159265359"),
        ],
    )
    def test_functions(self, expression, expected):
        assert calculate(expression) == expected


class TestMathErrors:
    """Mathematically invalid expressions produce friendly errors."""

    @pytest.mark.parametrize("expression", ["1 / 0", "5 % 0", "log(0)", "tan(pi / 2)", "0 ** -1"])
    def test_undefined(self, expression):
        with pytest.raises(EvaluationError):
            calculate(expression)

    @pytest.mark.parametrize("expression", ["sqrt(-1)", "asin(2)", "ln(-1)"])
    def test_not_real(self, expression):
        with pytest.raises(EvaluationError, match="not a real number"):
            calculate(expression)

    @pytest.mark.parametrize("expression", ["factorial(-1)", "factorial(2.5)"])
    def test_factorial_domain(self, expression):
        with pytest.raises(EvaluationError, match="non-negative integers"):
            calculate(expression)


class TestResourceLimits:
    """Inputs that would exhaust CPU/memory are rejected quickly."""

    @pytest.mark.parametrize(
        "expression",
        ["9 ** 9 ** 9", "2 ** 40000", "2 ** -40000", "10 ** (10 ** 5)", "0.5 ** 100000"],
    )
    def test_huge_powers(self, expression):
        with pytest.raises(EvaluationError, match="out of range"):
            calculate(expression)

    def test_large_but_allowed_power(self):
        assert calculate("2 ** 10000").startswith("1.99506311688e+3010")

    def test_factorial_limit(self):
        calculate(f"factorial({MAX_FACTORIAL})")
        with pytest.raises(EvaluationError, match="too large"):
            calculate(f"factorial({MAX_FACTORIAL + 1})")

    def test_nested_factorial(self):
        with pytest.raises(EvaluationError):
            calculate("factorial(factorial(10))")


def test_validation_errors_propagate():
    """``calculate`` surfaces validator errors unchanged."""
    with pytest.raises(ValidationError):
        calculate("__import__('os').system('dir')")
