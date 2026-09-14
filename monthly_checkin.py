"""Small, read-only monthly return-loop prompts using existing records."""

from datetime import date

import streamlit as st
from i18n import t, month_period

from monthly_plans import get_monthly_plan
from transactions import get_transactions_for_month


RETURN_COPY = (
    'ui.near_the_end_of_the_month_update_account_balances_manually'
)


def render_monthly_checkin(user_id):
    today = date.today()
    with st.container(border=True, key="tour_checkin"):
        st.subheader(t('ui.this_month'), anchor="monthly-check-in")
        try:
            plan = get_monthly_plan(user_id, today.year, today.month)
            transactions = [] if plan is None else get_transactions_for_month(user_id, plan.id)
        except Exception:
            st.write(t('ui.your_monthly_check_in_couldn_t_load_try_refreshing_the'))
            return

        if plan is None:
            st.write(t("checkin.start", period=month_period(today.year, today.month)))
            st.write(t('ui.in_monthly_plan_below_choose_this_month_add_your_expected'))
        else:
            st.write(t("checkin.saved", period=month_period(today.year, today.month)))
            if any(row.transaction_type in {"FUND_CONTRIBUTION", "INVESTMENT_CONTRIBUTION"}
                   for row in transactions):
                st.caption(t('ui.you_ve_recorded_contributions_this_month_review_any_remaining_actual'))
        st.write(t(RETURN_COPY))
        st.caption(t('ui.no_daily_check_ins_needed_you_don_t_need_to'))
