"""On-screen calculator keypad component.

The keypad is split into two sections, styled like a physical calculator:

* a compact **scientific** row of less-used functions, and
* a large **main** pad of digits, basic operators and controls.

Streamlit has no button-size option, so sizing comes from a static
stylesheet that targets the CSS classes Streamlit derives from widget and
container keys (``st-key-<key>``).
"""

from dataclasses import dataclass
from typing import Callable, Literal

import streamlit as st

from ui.state import backspace, clear, compute, insert_text

KeyKind = Literal["num", "op", "ctrl", "sci"]


@dataclass(frozen=True)
class Key:
    """A single keypad button.

    Attributes:
        label: Text shown on the button (may be empty when ``icon`` is set).
        name: Unique identifier used to build the widget key.
        kind: Styling group: digit, operator, control or scientific.
        insert: Text appended to the expression when pressed. Ignored when
            ``action`` is set.
        action: Optional callback run instead of inserting text.
        icon: Optional Material icon, e.g. ``":material/backspace:"``.
        help: Optional tooltip.
    """

    label: str
    name: str
    kind: KeyKind
    insert: str = ""
    action: Callable[[], None] | None = None
    icon: str | None = None
    help: str | None = None

    @property
    def widget_key(self) -> str:
        """Streamlit widget key, also exposed as CSS class ``st-key-<key>``."""
        return f"{self.kind}_{self.name}"


def _num(label: str, name: str | None = None) -> Key:
    """Create a digit/punctuation key that inserts its own label."""
    return Key(label, name or label, "num", insert=label)


def _op(label: str, name: str) -> Key:
    """Create a basic-operator key that inserts its own label."""
    return Key(label, name, "op", insert=label)


def _sci(label: str, name: str, insert: str) -> Key:
    """Create a compact scientific key."""
    return Key(label, name, "sci", insert=insert)


#: Compact row(s) of less frequently used functions.
SCIENTIFIC_LAYOUT: list[list[Key]] = [
    [
        _sci("sin", "sin", "sin("),
        _sci("cos", "cos", "cos("),
        _sci("tan", "tan", "tan("),
        _sci("ln", "ln", "ln("),
        _sci("log", "log", "log10("),
    ],
    [
        _sci("√", "sqrt", "√("),
        _sci("xʸ", "pow", "^"),
        _sci("π", "pi", "π"),
        _sci("e", "e", "e"),
        _sci("n!", "factorial", "factorial("),
    ],
]

#: Main pad laid out like a physical calculator.
MAIN_LAYOUT: list[list[Key]] = [
    [
        Key("C", "clear", "ctrl", action=clear, help="Clear"),
        Key("", "backspace", "ctrl", action=backspace,
            icon=":material/backspace:", help="Backspace"),
        _op("%", "mod"),
        _op("÷", "div"),
    ],
    [_num("7"), _num("8"), _num("9"), _op("×", "mul")],
    [_num("4"), _num("5"), _num("6"), _op("−", "sub")],
    [_num("1"), _num("2"), _num("3"), _op("+", "add")],
    [_num("(", "lparen"), _num("0"), _num(".", "dot"), _num(")", "rparen")],
]

#: Static stylesheet. Contains no user data, so injecting it is safe.
_STYLES = """
<style>
/* Every key in a row gets an equal share of the width (selector is more
   specific than Streamlit's default `flex: 1 1 fit-content`). */
.st-key-pad_sci .stHorizontalBlock > .stElementContainer,
.st-key-pad_main .stHorizontalBlock > .stElementContainer { flex: 1 1 0; min-width: 0; }

/* Scientific keys: compact. */
.st-key-pad_sci button { min-height: 2rem; padding: 0.1rem 0.4rem; }
.st-key-pad_sci button p { font-size: 0.85rem; }

/* Main pad and equals: large, like a physical calculator. */
.st-key-pad_main button, .st-key-equals button { min-height: 3.75rem; }
.st-key-pad_main button p, .st-key-equals button p { font-size: 1.5rem; }
.st-key-pad_main [data-testid="stIconMaterial"] { font-size: 1.6rem; }

/* Operators and controls get accent tints. */
[class*="st-key-op_"] button {
    background-color: rgba(255, 149, 0, 0.18);
    border-color: rgba(255, 149, 0, 0.55);
}
[class*="st-key-ctrl_"] button {
    background-color: rgba(128, 128, 128, 0.15);
}
</style>
"""


def _render_rows(layout: list[list[Key]]) -> None:
    """Render a grid of keys, one horizontal container per layout row.

    Horizontal containers (unlike ``st.columns``) do not stack vertically
    on narrow screens, so the keypad keeps its shape on mobile.
    """
    for row in layout:
        with st.container(horizontal=True, gap="small", wrap=False):
            for key in row:
                st.button(
                    key.label,
                    key=key.widget_key,
                    on_click=key.action or insert_text,
                    args=() if key.action else (key.insert,),
                    icon=key.icon,
                    help=key.help,
                    width="stretch",
                )


def render_keypad() -> None:
    """Render the scientific row, the main pad and a full-width equals key."""
    st.html(_STYLES)
    with st.container(key="pad_sci"):
        _render_rows(SCIENTIFIC_LAYOUT)
    with st.container(key="pad_main"):
        _render_rows(MAIN_LAYOUT)
    st.button("=", key="equals", on_click=compute, type="primary", width="stretch")
