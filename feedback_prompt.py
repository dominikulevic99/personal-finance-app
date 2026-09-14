"""Session-only post-setup invitation, gated by a visible dashboard in the browser."""

from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component
from feedback import get_user_feedback
from feedback_ui import open_feedback


def queue_feedback_prompt(user_id, *, tester=False, session_state=None):
    state = st.session_state if session_state is None else session_state
    prefix = f"feedback_{user_id}_"
    # Only explicit completed-guide handoffs call this; never ordinary logins.
    if tester:
        state[prefix + "offered"] = False
        state[prefix + "pending"] = True
        state[prefix + "prompt_run"] = state.get(prefix + "prompt_run", 0) + 1
    elif not state.get(prefix + "offered") and not state.get(prefix + "has_submitted"):
        state[prefix + "pending"] = True


def render_feedback_prompt(user_id, *, tester=False):
    state = st.session_state
    prefix = f"feedback_{user_id}_"
    onboarding = f"onboarding_{user_id}_"
    # A successful reveal followed by an explicit dashboard choice in this session.
    # No login hook, persistent eligibility change, or completion event is involved.
    if state.get(prefix + "picture_seen") and state.get(onboarding + "dashboard"):
        # Consume one successful guide visit, not every dashboard rerun. Replay
        # qualifies too, while normal users still retain submission/session limits.
        state.pop(prefix + "picture_seen", None)
        queue_feedback_prompt(user_id, tester=tester)
    if (not state.get(prefix + "pending") or state.get(prefix + "offered")
            or state.get(prefix + "open") or state.get(f"product_tour_{user_id}_active")):
        return
    if state.get(prefix + "has_submitted") and not tester:
        state[prefix + "pending"] = False
        return

    key = prefix + f"dashboard_visible_{state.get(prefix + 'prompt_run', 0)}"

    def ready():
        if not state.get(prefix + "pending") or state.get(prefix + "offered"):
            return
        # Consume before checking/opening so failures, dismissals and reruns cannot nag.
        state[prefix + "pending"] = False
        state[prefix + "offered"] = True
        if state.get(key, {}).get("ready") != "visible":
            return
        try:
            if get_user_feedback(user_id) and not tester:
                state[prefix + "has_submitted"] = True
                return
        except Exception:
            return
        open_feedback(user_id, "product_tour", automatic=True)

    gate = component(
        "feedback_dashboard_visible",
        js=(Path(__file__).parent / "tour_assets" / "feedback_ready.js").read_text(encoding="utf-8"),
    )
    gate(key=key, data={}, on_ready_change=ready, height=0)
