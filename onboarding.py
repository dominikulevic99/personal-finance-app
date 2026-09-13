"""Welcome and guided setup routing; financial steps live in separate modules."""

import streamlit as st
from analytics import track_event

from onboarding_service import get_entry_route
from onboarding_layout import onboarding_shell, render_welcome_content
from onboarding_accounts import render_accounts_step
from onboarding_assets import render_assets_step
from onboarding_debts import render_debts_step
from onboarding_funds import render_funds_step
from onboarding_monthly_plan import render_monthly_plan_step
from onboarding_picture import render_financial_picture
from onboarding_navigation import render_step_navigation


def render_guide_replay_action(user_id):
    """Voluntary navigation only; financial records and draft inputs stay intact."""
    prefix = f"onboarding_{user_id}_"
    if st.sidebar.button(
        "Repeat setup",
        type="tertiary",
        key=prefix + "replay",
        help="Review your setup again. Your existing data stays intact.",
    ):
        st.session_state[prefix + "replay_welcome"] = True
        st.session_state[prefix + "replay_mode"] = True
        st.session_state[prefix + "dashboard"] = False
        st.session_state[prefix + "step"] = "accounts"
        st.rerun()


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
            replay_requested=st.session_state.get(prefix + "replay_welcome", False),
        )
    except Exception:
        # Database exceptions can contain connection details; do not display them.
        st.error("We couldn't check your setup status. Please try again.")
        if st.button("Retry", key=prefix + "retry"):
            st.rerun()
        st.stop()

    if route == "dashboard":
        return

    step = st.session_state.get(prefix + "step", "accounts")
    shell_step = None if route == "welcome" else {
        "accounts": 1, "assets": 2, "debts": 3, "funds": 4, "monthly_plan": 5,
        "financial_picture": None,
    }.get(step, 1)
    encouragement = (
        "A little clarity starts here." if route == "welcome"
        else "One account is enough to begin." if step == "accounts"
        else "Great start. Three steps left." if step == "assets"
        else "Halfway there." if step == "debts"
        else "Only one step left." if step == "funds"
        else "One last step. Your financial picture is almost ready." if step == "monthly_plan"
        else "A clear starting point for what's next."
    )
    with onboarding_shell(
        step=shell_step, encouragement=encouragement,
        complete=route == "started" and step == "financial_picture",
    ):
        if route == "started":
            render_step_navigation(user_id, unrestricted=force_welcome)
            track_event(user_id, "onboarding_step_viewed", step, session_state=st.session_state)
        if route == "welcome":
            render_welcome_content()
            if st.button("Build my financial picture", type="primary", key=prefix + "start"):
                st.session_state[started_key] = True
                st.session_state[prefix + "replay_welcome"] = False
                st.session_state[prefix + "step"] = "accounts"
                track_event(user_id, "onboarding_started", session_state=st.session_state)
                st.rerun()
            dashboard_label = "Skip for now"
        elif step == "accounts":
            render_accounts_step(user_id)
            dashboard_label = "Skip for now"
        elif step == "assets":
            render_assets_step(user_id)
            dashboard_label = "Open my dashboard"
        elif step == "debts":
            render_debts_step(user_id)
            dashboard_label = "Open my dashboard"
        elif step == "funds":
            render_funds_step(user_id)
            dashboard_label = "Open my dashboard"
        elif step == "monthly_plan":
            render_monthly_plan_step(user_id)
            dashboard_label = "Open my dashboard"
        else:
            render_financial_picture(user_id, track_completion=not force_welcome)
            if st.button("Back to Monthly Plan", type="tertiary", key=prefix + "financial_picture_back"):
                st.session_state[prefix + "step"] = "monthly_plan"
                st.rerun()
            dashboard_label = "Open my dashboard"

        if st.button(
            dashboard_label,
            type="primary" if route == "started" and step == "financial_picture" else "tertiary",
            key=prefix + "open_dashboard",
        ):
            # Keep the started flag so a future saved account cannot end setup.
            st.session_state[dashboard_key] = True
            st.session_state[prefix + "replay_welcome"] = False
            st.rerun()
    st.stop()
