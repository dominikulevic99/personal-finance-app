"""Optional, user-scoped product tour. No financial data."""

from pathlib import Path

import streamlit as st
from i18n import t, get_language, set_language
from streamlit.components.v2 import component
from feedback_ui import open_feedback, offer_tour_feedback
from feedback_prompt import queue_feedback_prompt


_ASSETS = Path(__file__).parent / "tour_assets"
STEPS = [
    {"target": "tour_summary", "title": 'ui.start_with_the_big_picture',
     "copy": 'ui.this_is_where_you_can_quickly_see_where_you_stand'},
    {"target": "tour_funds", "title": 'ui.give_your_money_a_purpose',
     "copy": 'ui.funds_reserve_existing_cash_for_goals_like_an_emergency_buffer'},
    {"target": "tour_monthly_plan", "title": 'ui.a_plan_is_not_a_contribution',
     "copy": 'ui.planned_allocations_do_not_change_balances_near_month_end_select'},
    {"target": "tour_checkin", "title": 'ui.come_back_when_reality_changes',
     "copy": 'ui.near_month_end_update_account_balances_manually_compare_your_plan'},
]


def start_tour(user_id):
    prefix = f"product_tour_{user_id}_"
    st.session_state[prefix + "run"] = st.session_state.get(prefix + "run", 0) + 1
    st.session_state[prefix + "active"] = True


def render_tour(user_id, *, tester=False):
    prefix = f"product_tour_{user_id}_"
    if not st.session_state.get(prefix + "active", False):
        return
    key = prefix + f"component_{st.session_state[prefix + 'run']}"

    def finish():
        st.session_state[prefix + "active"] = False
        reason = st.session_state.get(key, {}).get("finished")
        if reason == "finish":
            queue_feedback_prompt(user_id, tester=tester, session_state=st.session_state)
        if reason == "feedback":
            open_feedback(user_id, "product_tour")

    def change_language():
        selected = st.session_state.get(key, {}).get("language")
        if selected in ("lt", "en"):
            set_language(selected)
            # Callback runs before sidebar widgets are instantiated on the rerun.
            scope = st.session_state.get("_i18n_scope", f"user_{user_id}")
            st.session_state[f"_i18n_{scope}_switch"] = selected

    # Local assets only. A fresh key starts at step 0; reruns retain component state.
    tour = component(
        "financial_picture_tour_prototype",
        js=(_ASSETS / "spotlight.js").read_text(encoding="utf-8"),
        css=(_ASSETS / "spotlight.css").read_text(encoding="utf-8"),
    )
    previous = st.session_state.get(key, {})
    if key + "_feedback_offer" not in st.session_state:
        st.session_state[key + "_feedback_offer"] = offer_tour_feedback(user_id)
    offer = st.session_state[key + "_feedback_offer"]
    step = previous.get("step", 0)
    if not isinstance(step, int) or not 0 <= step < len(STEPS):
        step = 0
    labels = {name: t(f"tour.{name}") for name in
              ("title", "close", "back", "skip", "next", "finish", "missing", "small")}
    # Count templates retain only non-sensitive positional placeholders for JS.
    labels["count"] = t("tour.count", current="{current}", total="{total}")
    labels["feedback"] = t("feedback.tour_action")
    labels["dashboard"] = t("feedback.tour_dashboard")
    tour(
        key=key, data={"steps": [{"target": item["target"], "title": t(item["title"]),
                                  "copy": t(item["copy"])} for item in STEPS],
                       "step": step, "labels": labels, "language": get_language(), "offer_feedback": offer},
        default={"step": 0}, on_step_change=lambda: None,
        on_finished_change=finish, on_language_change=change_language, height=0,
    )
