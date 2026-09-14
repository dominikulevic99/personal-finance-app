"""Shared visual tokens and a presentation-only dashboard stylesheet."""

from pathlib import Path
import tomllib

import streamlit as st


def fund_card_style(key, fraction):
    """Scope a subtle linear goal indicator to a single native expander header."""
    bar = ""
    if fraction is not None:
        percentage = max(0.0, min(1.0, fraction)) * 100
        bar = f"""
        background-image: linear-gradient(var(--finance-accent), var(--finance-accent)),
                          linear-gradient(var(--finance-border), var(--finance-border));
        background-size: {percentage}% 4px, 100% 4px;
        background-position: left center;
        background-repeat: no-repeat;
        """
    return f"""<style>
    .st-key-{key} [data-testid="stExpander"] {{
        background: var(--finance-surface);
        border: 1px solid var(--finance-border);
        border-radius: 14px;
        overflow: hidden;
    }}
    .st-key-{key} [data-testid="stExpander"] summary {{
        padding: .45rem .85rem;
    }}
    .st-key-{key} summary [data-testid="stMarkdownContainer"] p {{
        white-space: normal;
        overflow-wrap: anywhere;
        line-height: 1.5;
        margin: 0;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: .25rem .75rem;
        color: var(--finance-muted);
        font-size: .85rem;
    }}
    .st-key-{key} summary [data-testid="stMarkdownContainer"] {{ width: 100%; }}
    .st-key-{key} summary p strong {{
        grid-area: 1 / 1;
        color: var(--finance-text);
        font-size: .95rem;
        font-weight: 600;
    }}
    .st-key-{key} summary p em {{
        grid-area: 1 / 2;
        font-style: normal;
        text-align: right;
    }}
    .st-key-{key} summary p br {{ display: none; }}
    .st-key-{key} summary p::after {{
        content: "";
        grid-area: 2 / 1 / 3 / -1;
        height: {"4px" if fraction is not None else "0"};
        border-radius: 4px;
        {bar}
    }}
    </style>"""


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
    max-width: 100%;
    white-space: normal;
    overflow-wrap: anywhere;
}
:is([data-testid="stButton"], [data-testid="stFormSubmitButton"]) button[kind="tertiary"] {
    background: transparent;
    border: 1px solid transparent;
    color: var(--finance-muted);
    padding-inline: .4rem;
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


LAYOUT_CSS = """
<style>
/* Streamlit's semantic info marker excludes warning/error/success alerts. */
[data-testid="stAlertContainer"]:has(> [data-testid="stAlertContentInfo"]) {
    background: var(--finance-surface);
    border: 1px solid var(--finance-control-border);
    border-radius: 14px;
    color: var(--finance-text);
}
/* Keep native status text colors, including within the onboarding shell. */
[data-testid="stAlertContainer"] [data-testid^="stAlertContent"] p {
    color: inherit;
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
    padding-top: .25rem;
    padding-bottom: .65rem;
}
[data-testid="stMain"] h3 {
    color: var(--finance-muted);
    font-size: 1.1rem;
    font-weight: 600;
    padding-bottom: .6rem;
}
[data-testid="stMain"] hr {
    border-color: var(--finance-border);
    margin: 1.5rem 0 1rem;
}
[data-testid="stMain"] :is(h1, h2, h3, p),
[data-testid="stText"], [data-testid="stText"] pre {
    overflow-wrap: anywhere;
}
[data-testid="stText"], [data-testid="stText"] pre { white-space: pre-wrap; }
[data-testid="stMetric"] {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    border-radius: 18px;
    padding: 1.1rem;
    min-height: 116px;
}
[data-testid="stMetricLabel"] {
    color: var(--finance-muted);
    font-size: .85rem;
}
[data-testid="stMetricLabel"] p { white-space: normal; }
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
@media (min-width: 641px) and (max-width: 1050px) {
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) {
        flex-wrap: wrap;
    }
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) > [data-testid="stColumn"] {
        flex: 1 1 calc(33.333% - 1rem);
        min-width: 0;
    }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding: 1.25rem 1rem 2rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 100%;
        width: 100%;
        min-width: 0;
    }
    [data-testid="stMain"] h2 { font-size: 1.5rem; }
}
</style>
"""


DASHBOARD_CSS = """
<style>
[data-testid="stMainBlockContainer"] {
    max-width: 1440px;
    padding-top: 2rem;
    padding-bottom: 3rem;
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
[data-testid="stSidebar"] { border-right: 1px solid var(--finance-border); }
</style>
"""


PICTURE_CSS = """
<style>
.st-key-financial_picture [data-testid="stMetricValue"] {
    font-size: clamp(1.3rem, 2.4vw, 1.85rem);
}
.st-key-financial_picture .st-key-picture_net_worth [data-testid="stMetric"] {
    background: #edf1e7;
    border-color: #c8d2c4;
    border-top: 3px solid var(--finance-accent);
    padding: 1.5rem;
}
.st-key-financial_picture .st-key-picture_net_worth [data-testid="stMetricValue"] {
    font-size: clamp(2.2rem, 6vw, 3.6rem);
}
.st-key-financial_picture h3 {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--finance-text);
    margin-top: .6rem;
}
</style>
"""


SIDEBAR_CSS = """
<style>
/* Only sidebar navigation links; preserve links and controls in the dashboard. */
[data-testid="stSidebar"] a[href^="#"] {
    display: block;
    box-sizing: border-box;
    padding: .45rem .65rem;
    min-height: 40px;
    border-radius: 9px;
    color: var(--finance-text);
    text-decoration: none;
    font-family: inherit;
    font-size: .95rem;
    font-weight: 400;
    line-height: 1.5;
}
[data-testid="stSidebar"] a[href^="#"]:visited {
    color: var(--finance-text);
}
[data-testid="stSidebar"] a[href^="#"]:hover {
    color: var(--finance-accent);
    background: #edf1e7;
    text-decoration: none;
}
[data-testid="stSidebar"] a[href^="#"]:focus-visible {
    outline: 2px solid var(--finance-accent);
    outline-offset: 2px;
    text-decoration: none;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="tertiary"] {
    padding: .45rem .65rem;
    min-height: 40px;
    border: 0;
    border-radius: 9px;
    color: var(--finance-text);
    font-weight: 400;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="tertiary"]:hover {
    background: #edf1e7;
    color: var(--finance-accent);
    filter: none;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="tertiary"],
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="tertiary"] p {
    font-family: inherit;
    font-size: .95rem;
    font-weight: 400;
    line-height: 1.5;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--finance-muted);
}
[data-testid="stSidebar"] a[href="#delete-my-data"],
[data-testid="stSidebar"] a[href="#delete-my-data"]:visited {
    color: #825e56;
    font-size: .85rem;
}
</style>
"""


def apply_dashboard_styles():
    """Called only after onboarding routing has returned to the dashboard."""
    st.html(PALETTE_CSS + BUTTON_CSS + DASHBOARD_CSS + LAYOUT_CSS + FORM_CSS + SIDEBAR_CSS)
