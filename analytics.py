"""Best-effort session analytics. Never accepts financial payloads."""

import streamlit as st
from sqlalchemy import text


EVENT_TYPES = frozenset({
    "login", "onboarding_started", "onboarding_step_viewed",
    "onboarding_completed", "dashboard_opened",
})
ONBOARDING_STEPS = frozenset({
    "accounts", "assets", "debts", "funds", "monthly_plan", "financial_picture",
})


def track_event(user_id, event_type, event_value=None, *, session_state=None):
    """Attempt each user/event/step once per session; failures never block UI.

    Mark before writing: an uncertain commit must not cause rerun duplicates.
    A failed attempt is intentionally not retried until a new session.
    """
    try:
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            return False
        if event_type not in EVENT_TYPES:
            return False
        if event_type == "onboarding_step_viewed":
            if event_value not in ONBOARDING_STEPS:
                return False
        elif event_value is not None:
            return False

        state = st.session_state if session_state is None else session_state
        key = (user_id, event_type, event_value)
        attempted = set(state.get("_analytics_attempted", ()))
        if key in attempted:
            return False
        attempted.add(key)
        state["_analytics_attempted"] = attempted

        # Use the existing engine, but keep import/connection failures contained.
        from database import engine

        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO user_events (user_id, event_type, event_value) "
                "VALUES (:user_id, :event_type, :event_value)"
            ), {"user_id": user_id, "event_type": event_type, "event_value": event_value})
        return True
    except Exception:
        # Database exceptions may contain credentials; don't display or log them.
        return False
