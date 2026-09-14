"""Translate validation failures at the UI boundary, without changing domain rules."""

import streamlit as st
from i18n import t


_MESSAGES = {
    "User does not exist.": "errors.user_unavailable",
    "Monthly plan does not belong to this user.": "errors.plan_unavailable",
    "Fund does not belong to this user.": "errors.bucket_unavailable",
    "Asset does not belong to this user.": "errors.asset_unavailable",
    "Plan item does not belong to this user.": "errors.allocation_unavailable",
    "Monthly plan item does not belong to this user.": "errors.allocation_unavailable",
    "Investment asset does not belong to this user.": "errors.investment_unavailable",
    "Fund contribution was not found.": "errors.bucket_contribution_unavailable",
    "Investment contribution was not found.": "errors.investment_contribution_unavailable",
}


def run_ui_action(action, *args, **kwargs):
    """Pass arguments unchanged; a rejected action must never show a success state."""
    try:
        return action(*args, **kwargs)
    except ValueError as error:
        key = _MESSAGES.get(str(error))
        if key is None:
            raise  # Unexpected programming errors retain their diagnostic behavior.
        st.error(t(key))
        st.stop()
