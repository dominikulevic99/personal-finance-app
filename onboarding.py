"""Welcome and guided setup routing; financial steps live in separate modules."""

import streamlit as st

from onboarding_service import get_entry_route
from onboarding_layout import onboarding_shell, render_welcome_content
from onboarding_accounts import render_accounts_step


def render_onboarding_entry(user_id, force_welcome=False):
    """Stop before the dashboard unless eligibility or an explicit choice allows it."""
    prefix = f"onboarding_{user_id}_"
    started_key = prefix + "started"
    dashboard_key = prefix + "dashboard"

    try:
        route = get_entry_route(
            user_id,
            started=st.session_state.get(started_key, False),
            dashboard_requested=st.session_state.get(dashboard_key, False),
            force_welcome=force_welcome,
        )
    except Exception:
        # Database exceptions can contain connection details; do not display them.
        st.error("We couldn't check your setup status. Please try again.")
        if st.button("Retry", key=prefix + "retry"):
            st.rerun()
        st.stop()

    if route == "dashboard":
        if st.session_state.get(started_key, False):
            if st.sidebar.button("Return to setup", key=prefix + "return"):
                st.session_state[dashboard_key] = False
                st.rerun()
        return

    step = st.session_state.get(prefix + "step", "accounts")
    shell_step = None if route == "welcome" else (1 if step == "accounts" else 2)
    encouragement = (
        "A little clarity starts here." if route == "welcome"
        else "One account is enough to begin." if step == "accounts"
        else "Your accounts are a great start."
    )
    with onboarding_shell(step=shell_step, encouragement=encouragement):
        if route == "welcome":
            render_welcome_content()
            if st.button("Build my financial plan", type="primary", key=prefix + "start"):
                st.session_state[started_key] = True
                st.session_state[prefix + "step"] = "accounts"
                st.rerun()
            dashboard_label = "Skip for now"
        elif step == "accounts":
            render_accounts_step(user_id)
            dashboard_label = "Skip for now"
        else:
            st.title("Next: Assets")
            st.write(
                "Your accounts are saved. The Assets step is not available yet. "
                "You can return to your accounts or open your dashboard."
            )
            if st.button("Back to Accounts", key=prefix + "assets_back"):
                st.session_state[prefix + "step"] = "accounts"
                st.rerun()
            dashboard_label = "Open my dashboard"

        if st.button(
            dashboard_label,
            type="primary" if route == "started" and step == "assets" else "secondary",
            key=prefix + "open_dashboard",
        ):
            # Keep the started flag so a future saved account cannot end setup.
            st.session_state[dashboard_key] = True
            st.rerun()
    st.stop()
