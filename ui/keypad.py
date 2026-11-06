"""On-screen calculator keypad component."""

from dataclasses import dataclass
from typing import Callable

import streamlit as st

from ui.state import backspace, clear, compute, insert_text


@dataclass(frozen=True)
class Key:
    """A single keypad button.

    Attributes:
        label: Text shown on the button.
        insert: Text appended to the expression when pressed. Ignored when
            ``action`` is set.
        action: Optional callback run instead of inserting text.
    """

    label: str
    insert: str = ""
    action: Callable[[], None] | None = None


def _digit(label: str) -> Key:
    """Create a key that inserts its own label."""
    return Key(label, insert=label)


def _func(label: str, name: str | None = None) -> Key:
    """Create a key that inserts ``name(`` (defaults to the label)."""
    return Key(label, insert=f"{name or label}(")


#: Keypad layout, one inner list per row.
LAYOUT: list[list[Key]] = [
    [_func("sin"), _func("cos"), _func("tan"), _func("ln"), _func("log", "log10")],
    [_func("√", "√"), Key("xʸ", insert="^"), _digit("π"), _digit("e"), _func("n!", "factorial")],
    [_digit("7"), _digit("8"), _digit("9"), _digit("÷"), Key("C", action=clear)],
    [_digit("4"), _digit("5"), _digit("6"), _digit("×"), Key("⌫", action=backspace)],
    [_digit("1"), _digit("2"), _digit("3"), _digit("−"), _digit("(")],
    [_digit("0"), _digit("."), _digit("%"), _digit("+"), _digit(")")],
]


def render_keypad() -> None:
    """Render the keypad grid followed by a full-width equals button."""
    for row_index, row in enumerate(LAYOUT):
        for col_index, (column, key) in enumerate(zip(st.columns(len(row)), row)):
            with column:
                st.button(
                    key.label,
                    key=f"key_{row_index}_{col_index}",
                    on_click=key.action or insert_text,
                    args=() if key.action else (key.insert,),
                    width="stretch",
                )
    st.button("=", key="key_equals", on_click=compute, type="primary", width="stretch")
