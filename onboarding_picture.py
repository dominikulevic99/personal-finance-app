"""Read-only completion overview; all totals come from shared calculations."""

from datetime import date

import streamlit as st

from accounts import get_accounts
from assets import get_assets
from debts import get_debts
from funds import get_funds
from monthly_plans import get_monthly_plan
from monthly_plan_items import get_plan_items
from calculations import calculate_financial_summary, calculate_planned_allocation_summary
from visual_styles import PICTURE_CSS


def load_financial_picture(user_id, year, month):
    """Load the user's saved records afresh, without writing or guessing missing data."""
    accounts = get_accounts(user_id)
    assets = get_assets(user_id)
    debts = get_debts(user_id)
    funds = get_funds(user_id)
    summary = calculate_financial_summary(accounts, assets, debts, funds)
    plan = get_monthly_plan(user_id, year, month)
    monthly = None
    if plan is not None:
        items = get_plan_items(user_id, plan.id)
        monthly = calculate_planned_allocation_summary(plan.planned_income, items)
        monthly["income"] = plan.planned_income
    return summary, monthly


def render_financial_picture(user_id):
    prefix = f"onboarding_{user_id}_"
    today = date.today()
    year, month = st.session_state.get(prefix + "plan_month", (today.year, today.month))
    try:
        summary, monthly = load_financial_picture(user_id, year, month)
    except Exception:
        st.error("We couldn't load your financial picture. Please try again.")
        if st.button("Retry", key=prefix + "picture_retry"):
            st.rerun()
        return

    st.html(PICTURE_CSS)
    with st.container(key="financial_picture"):
        st.title("Your financial picture is ready.")
        st.write("Here's where you stand today.")
        st.caption("A snapshot of the information you have saved. You can update it as life changes.")

        with st.container(key="picture_net_worth"):
            st.metric(
                "Net worth", f"€{summary['net_worth']:,.2f}",
                help="Your account balances and asset values, minus what you still owe. Funds are already part of your cash.",
            )
        if summary["net_worth"] > 0:
            st.caption("Based on your saved figures, what you own is worth more than what you owe.")
        elif summary["net_worth"] < 0:
            st.caption("Based on your saved figures, what you owe is greater than what you own. This is a starting snapshot.")
        else:
            st.caption("Your saved cash and asset values balance out your recorded debts.")

        cash_col, debt_col, funds_col = st.columns(3)
        with cash_col:
            st.metric("Available cash", f"€{summary['available_cash']:,.2f}",
                      help="Money recorded in your accounts and cash, including money reserved in funds.")
        with debt_col:
            st.metric("Debt", f"€{summary['total_debt']:,.2f}", help="The total amount you still owe.")
        with funds_col:
            st.metric("Set aside in funds", f"€{summary['reserved_funds']:,.2f}",
                      help="Money reserved within your existing cash. This does not add to net worth.")
        st.caption("Funds reserve existing cash; they are not additional wealth.")

        with st.expander("Your assets, by how readily available they are"):
            liquid_col, semi_col, non_col = st.columns(3)
            with liquid_col:
                st.metric("Liquid investments", f"€{summary['liquid_investments']:,.2f}",
                          help="Assets classified as usually convertible to cash within a few days.")
            with semi_col:
                st.metric("Semi-liquid assets", f"€{summary['semi_liquid_assets']:,.2f}",
                          help="Assets classified as taking more time or effort to access.")
            with non_col:
                st.metric("Non-liquid assets", f"€{summary['non_liquid_assets']:,.2f}",
                          help="Assets classified as usually taking longer to sell, such as property.")
            st.caption("These use the availability classifications saved for your assets. All asset values count toward net worth.")

        st.subheader(f"Your plan for {date(year, month, 1).strftime('%B %Y')}")
        if monthly is None:
            st.info("No monthly plan is saved for this month yet.")
        else:
            income_col, allocation_col, remaining_col = st.columns(3)
            with income_col:
                st.metric("Expected income", f"€{monthly['income']:,.2f}")
            with allocation_col:
                st.metric("Planned allocations", f"€{monthly['allocated']:,.2f}")
            with remaining_col:
                st.metric("Unallocated", f"€{monthly['remaining']:,.2f}")
            if monthly["remaining"] < 0:
                st.caption("Your planned allocations currently exceed your expected income.")
            elif monthly["remaining"] > 0:
                st.caption("Some of your expected income is still unallocated.")
            else:
                st.caption("All of your expected income is allocated in this plan.")
            st.caption("These are intentions, not actual contributions. Planning does not move money or change balances.")

        with st.expander("Your monthly routine"):
            st.markdown(
                "1. Check your bank balances.\n"
                "2. Update account balances manually.\n"
                "3. Review how the month went.\n"
                "4. Compare your plan with reality.\n"
                "5. Confirm actual Fund and Investment contributions.\n"
                "6. Review your financial picture.\n"
                "7. Plan the next month."
            )
            st.write("You don't need to enter every small daily purchase. Your bank's monthly spending summary can help with your review.")
            st.caption("Confirmed contributions update Fund and Investment balances. Account balances still need to be updated manually.")
