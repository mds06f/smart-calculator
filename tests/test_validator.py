"""Unit tests for :mod:`calc.validator`."""

import ast

import pytest

from calc.exceptions import ValidationError
from calc.validator import MAX_LENGTH, normalize, validate


class TestNormalize:
    """Tests for calculator-symbol normalisation."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2 × 3", "2 * 3"),
            ("8 ÷ 2", "8 / 2"),
            ("5 − 1", "5 - 1"),
            ("2^3", "2**3"),
            ("π", "pi"),
            ("√(4)", "sqrt(4)"),
            ("  SIN(PI)  ", "sin(pi)"),
        ],
    )
    def test_symbols_are_converted(self, raw, expected):
        assert normalize(raw) == expected


class TestValidateAccepts:
    """Expressions that must pass validation."""

    @pytest.mark.parametrize(
        "expression",
        [
            "1 + 2",
            "-3 * (4 - 1)",
            "2 ^ 10",
            "10 % 3",
            "3.5 / 0.5",
            "sqrt(16) + abs(-2)",
            "sin(pi / 2) + cos(0)",
            "ln(e) + log10(100)",
            "factorial(5)",
        ],
    )
    def test_valid_expression_returns_ast(self, expression):
        assert isinstance(validate(expression), ast.Expression)


class TestValidateRejects:
    """Expressions that must be rejected."""

    @pytest.mark.parametrize("expression", ["", "   "])
    def test_empty_input(self, expression):
        with pytest.raises(ValidationError, match="enter an expression"):
            validate(expression)

    def test_non_string_input(self):
        with pytest.raises(ValidationError):
            validate(42)  # type: ignore[arg-type]

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate("1+" * MAX_LENGTH + "1")

    def test_too_complex(self):
        with pytest.raises(ValidationError, match="too complex"):
            validate("-" * 150 + "1")

    @pytest.mark.parametrize(
        "expression",
        [
            "__import__('os')",
            "open(\"x\")",
            "1; 2",
            "a = 1",
            "2 & 3",
            "[1, 2]",
        ],
    )
    def test_invalid_characters(self, expression):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate(expression)

    @pytest.mark.parametrize("expression", ["(1 + 2", "2 +", "* 3", "1..2"])
    def test_syntax_errors(self, expression):
        with pytest.raises(ValidationError, match="Invalid syntax"):
            validate(expression)

    @pytest.mark.parametrize(
        "expression",
        [
            "().__class__",
            "pi.real",
            "1 // 2",
            "lambda: 1",
            "1 if 1 else 2",
            "1 < 2",
        ],
    )
    def test_unsupported_syntax(self, expression):
        with pytest.raises(ValidationError):
            validate(expression)

    @pytest.mark.parametrize("expression", ["x + 1", "true", "exec", "eval"])
    def test_unknown_names(self, expression):
        with pytest.raises(ValidationError, match="Unknown name"):
            validate(expression)

    @pytest.mark.parametrize("expression", ["eval(1)", "exec(1)", "foo(2)", "sqrt(4)(2)"])
    def test_unknown_functions(self, expression):
        with pytest.raises(ValidationError, match="function"):
            validate(expression)

    @pytest.mark.parametrize("expression", ["log(8, 2)", "sqrt()", "sin(1, 2)"])
    def test_wrong_argument_count(self, expression):
        with pytest.raises(ValidationError, match="exactly one argument"):
            validate(expression)
