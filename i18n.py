"""Presentation-only localization and user-scoped session preferences."""

import json
from functools import lru_cache
from pathlib import Path
import warnings

import streamlit as st


LANGUAGES = ("lt", "en")


def default_language():
    """Lithuanian validation default; future market selection belongs here."""
    return "lt"


@lru_cache(maxsize=2)
def catalog(language):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    return json.loads((Path(__file__).parent / "locales" / f"{language}.json").read_text(encoding="utf-8"))


def initialize_language(user_id=None):
    scope = "guest" if user_id is None else f"user_{user_id}"
    st.session_state["_i18n_scope"] = scope
    key = f"_i18n_{scope}_language"
    # Consume a deliberate pre-login choice only once; never share user preferences.
    guest = st.session_state.pop("_i18n_guest_explicit", None) if user_id is not None else None
    if guest in LANGUAGES:
        st.session_state[key] = guest
    elif key not in st.session_state:
        st.session_state[key] = default_language()
    return st.session_state[key]


def get_language():
    scope = st.session_state.get("_i18n_scope", "guest")
    value = st.session_state.get(f"_i18n_{scope}_language", default_language())
    return value if value in LANGUAGES else default_language()


def set_language(language):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    scope = st.session_state.get("_i18n_scope", "guest")
    st.session_state[f"_i18n_{scope}_language"] = language
    if scope == "guest":
        st.session_state["_i18n_guest_explicit"] = language


def t(key, *, language=None, **values):
    language = get_language() if language is None else language
    text = catalog(language).get(key)
    if text is None:
        warnings.warn(f"Missing translation: {language}:{key}", RuntimeWarning, stacklevel=2)
        text = catalog("en").get(key, f"[{key}]")
    return text.format(**values)


def render_language_switcher():
    scope = st.session_state.get("_i18n_scope", "guest")
    key = f"_i18n_{scope}_switch"

    def choose():
        selected = st.session_state.get(key)
        if selected in LANGUAGES:
            set_language(selected)
        else:
            st.session_state[key] = get_language()

    st.segmented_control(
        "Kalba / Language", options=LANGUAGES, format_func=str.upper,
        selection_mode="single", default=get_language() if key not in st.session_state else None, key=key,
        on_change=choose, label_visibility="collapsed",
    )


class TranslatedLabels(dict):
    """Internal enum values map to catalog keys; translate only at render time."""

    def __getitem__(self, value):
        return t(super().__getitem__(value))

    def get(self, value, default=None):
        return self[value] if value in self else default

    def items(self):
        return ((value, self[value]) for value in self)

    def formatter(self):
        # Streamlit may call format_func outside this script run. Capture labels.
        labels = dict(self.items())
        return labels.get


def month_name(month, *, language=None):
    return t(f"months.{int(month)}", language=language)


def month_period(year, month):
    return t("months.period", year=year, month=month_name(month))


def enum_label(value, *, language=None):
    """Display supported database values without translating stored identifiers."""
    key = f"enum.{value}"
    language = get_language() if language is None else language
    return t(key if key in catalog(language) else "ui.not_available", language=language)
