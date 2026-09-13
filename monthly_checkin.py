"""Small, read-only monthly return-loop prompts using existing records."""

from datetime import date

import streamlit as st

from monthly_plans import get_monthly_plan
from transactions import get_transactions_for_month


RETURN_COPY = (
    "Near the end of the month, update account balances manually, review the month "
    "and compare your plan with reality. Confirm actual Fund and Investment "
    "contributions, then prepare next month's plan."
)


def render_monthly_checkin(user_id):
    today = date.today()
    with st.container(border=True, key="tour_checkin"):
        st.subheader("This month", anchor="monthly-check-in")
        try:
            plan = get_monthly_plan(user_id, today.year, today.month)
            transactions = [] if plan is None else get_transactions_for_month(user_id, plan.id)
        except Exception:
            st.write("Your monthly check-in couldn't load. Try refreshing the page.")
            return

        if plan is None:
            st.write(f"Start your {today.strftime('%B %Y')} plan.")
            st.write("In Monthly Plan below, choose this month, add your expected income and decide where it should go.")
        else:
            st.write(f"Your {today.strftime('%B %Y')} plan is saved.")
            if any(row.transaction_type in {"FUND_CONTRIBUTION", "INVESTMENT_CONTRIBUTION"}
                   for row in transactions):
                st.caption("You've recorded contributions this month. Review any remaining actual contributions before planning next month.")
        st.write(RETURN_COPY)
        st.caption("No daily check-ins needed. You don't need to record every small purchase.")
