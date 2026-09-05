"""Shared visual tokens and a presentation-only dashboard stylesheet."""

from pathlib import Path
import tomllib

import streamlit as st


# Read only the public theme file, never Streamlit secrets. This is the single
# source for the main palette used by native widgets and our custom CSS.
with (Path(__file__).parent / ".streamlit" / "config.toml").open("rb") as theme_file:
    _theme = tomllib.load(theme_file)["theme"]

PALETTE_CSS = "<style>:root {" + ";".join(
    f"--finance-{name}: {value}"
    for name, value in {
        "background": _theme["backgroundColor"],
        "surface": _theme["secondaryBackgroundColor"],
        "text": _theme["textColor"],
        "accent": _theme["primaryColor"],
        "muted": "#536158",
        "border": "#e4e6dc",
        "control-border": "#b8c3b7",
    }.items()
) + ";}</style>"


# Limit component selectors to a few named Streamlit elements; avoid generated
# class names, positional selectors, and changes to widget behavior.
BUTTON_CSS = """
<style>
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button {
    border-radius: 12px;
    min-height: 44px;
    padding: .6rem 1.15rem;
    font-weight: 600;
}
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button[kind^="secondary"] {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    color: var(--finance-muted);
}
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button[kind^="primary"] {
    background: var(--finance-accent);
    border: 1px solid var(--finance-accent);
    color: #ffffff;
}
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button p { color: inherit; }
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button:not(:disabled):hover {
    border-color: var(--finance-accent);
    filter: brightness(.96);
}
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button:focus-visible {
    outline: 3px solid #779481;
    outline-offset: 3px;
}
</style>
"""


FORM_CSS = """
<style>
/* Border the control surface, leaving labels, menus and stepper buttons alone. */
:is(
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stNumberInputContainer"],
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child,
    [data-testid="stTextArea"] [data-baseweb="textarea"]
) {
    border: 1px solid var(--finance-control-border);
    border-radius: 10px;
}
:is(
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stNumberInputContainer"],
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child,
    [data-testid="stTextArea"] [data-baseweb="textarea"]
):focus-within {
    border-color: var(--finance-accent);
    box-shadow: 0 0 0 1px var(--finance-accent);
}
[data-testid="stForm"] { padding: 1rem 1.1rem; }
[data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: .65rem; }
</style>
"""


DASHBOARD_CSS = """
<style>
[data-testid="stMainBlockContainer"] {
    max-width: 1440px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}
[data-testid="stMain"] h1 {
    color: var(--finance-text);
    font-weight: 650;
    letter-spacing: -.035em;
    margin-bottom: .25rem;
}
[data-testid="stMain"] h2 {
    font-size: 1.7rem;
    font-weight: 600;
    letter-spacing: -.025em;
    padding-top: .5rem;
    padding-bottom: .8rem;
}
[data-testid="stMain"] h3 {
    color: var(--finance-muted);
    font-size: 1.1rem;
    font-weight: 600;
    padding-bottom: .8rem;
}
[data-testid="stMain"] hr {
    border-color: var(--finance-border);
    margin: 2rem 0 1.25rem;
}
[data-testid="stMetric"] {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    border-radius: 18px;
    padding: 1.1rem;
    min-height: 116px;
}
.st-key-net_worth [data-testid="stMetric"] {
    background: #edf1e7;
    border-top: 3px solid var(--finance-accent);
}
.st-key-net_worth [data-testid="stMetricValue"] {
    font-size: clamp(1.65rem, 2.5vw, 2.4rem);
    font-weight: 650;
}
.st-key-net_worth [data-testid="stMetricLabel"] {
    color: var(--finance-accent);
    font-weight: 600;
}
[data-testid="stMetricLabel"] {
    color: var(--finance-muted);
    font-size: .85rem;
}
[data-testid="stMetricValue"] {
    font-size: clamp(1.2rem, 1.9vw, 1.85rem);
    font-weight: 600;
    letter-spacing: -.035em;
    font-variant-numeric: tabular-nums;
    overflow-wrap: anywhere;
    white-space: normal;
}
[data-testid="stMetricValue"] > div {
    overflow: visible;
    white-space: normal;
    overflow-wrap: anywhere;
}
[data-testid="stForm"], [data-testid="stExpander"] {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    border-radius: 18px;
}
[data-testid="stExpander"] details {
    border: none;
    border-radius: inherit;
}
[data-testid="stExpander"] summary {
    padding: .9rem 1rem;
    font-weight: 500;
}
[data-testid="stSidebar"] {
    border-right: 1px solid var(--finance-border);
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }
}
</style>
"""


def apply_dashboard_styles():
    """Called only after onboarding routing has returned to the dashboard."""
    st.html(PALETTE_CSS + BUTTON_CSS + DASHBOARD_CSS + FORM_CSS)
