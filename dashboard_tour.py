"""Optional, user-scoped product tour. No financial data."""

from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component


_ASSETS = Path(__file__).parent / "tour_assets"
STEPS = [
    {"target": "tour_summary", "title": "Start with the big picture.",
     "copy": "This is where you can quickly see where you stand without digging through transactions."},
    {"target": "tour_funds", "title": "Give your money a purpose.",
     "copy": "Funds reserve existing cash for goals like an emergency buffer, travel or a laptop. They do not add wealth."},
    {"target": "tour_monthly_plan", "title": "A plan is not a contribution.",
     "copy": "Planned allocations do not change balances. Near month-end, select the month and open a Fund or Investment allocation. Enter only what you actually contributed, then choose Confirm contribution. This updates that Fund or Investment balance; update bank account balances manually."},
    {"target": "tour_checkin", "title": "Come back when reality changes.",
     "copy": "Near month-end, update account balances manually, compare your plan with reality, and confirm actual Fund or Investment contributions in Monthly Plan. No daily purchase tracking needed."},
]


def start_tour(user_id):
    prefix = f"product_tour_{user_id}_"
    st.session_state[prefix + "run"] = st.session_state.get(prefix + "run", 0) + 1
    st.session_state[prefix + "active"] = True


def render_tour(user_id):
    prefix = f"product_tour_{user_id}_"
    if not st.session_state.get(prefix + "active", False):
        return
    key = prefix + f"component_{st.session_state[prefix + 'run']}"

    def finish():
        st.session_state[prefix + "active"] = False

    # Local assets only. A fresh key starts at step 0; reruns retain component state.
    tour = component(
        "financial_picture_tour_prototype",
        js=(_ASSETS / "spotlight.js").read_text(encoding="utf-8"),
        css=(_ASSETS / "spotlight.css").read_text(encoding="utf-8"),
    )
    previous = st.session_state.get(key, {})
    step = previous.get("step", 0)
    if not isinstance(step, int) or not 0 <= step < len(STEPS):
        step = 0
    tour(
        key=key, data={"steps": STEPS, "step": step},
        default={"step": 0}, on_step_change=lambda: None,
        on_finished_change=finish, height=0,
    )
