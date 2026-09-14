"""Read-only completion overview; all totals come from shared calculations."""

from datetime import date

import streamlit as st
from i18n import t, month_period
from analytics import track_event
from monthly_checkin import RETURN_COPY

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


def render_financial_picture(user_id, *, track_completion=True):
    prefix = f"onboarding_{user_id}_"
    today = date.today()
    year, month = st.session_state.get(prefix + "plan_month", (today.year, today.month))
    try:
        summary, monthly = load_financial_picture(user_id, year, month)
    except Exception:
        st.error(t('ui.we_couldn_t_load_your_financial_picture_please_try_again'))
        if st.button(t('ui.retry'), key=prefix + "picture_retry"):
            st.rerun()
        return

    if track_completion and not st.session_state.get(prefix + "replay_mode", False):
        track_event(user_id, "onboarding_completed", session_state=st.session_state)
    st.html(PICTURE_CSS)
    st.session_state[f"feedback_{user_id}_picture_seen"] = True
    with st.container(key="financial_picture"):
        st.title(t('ui.your_financial_picture_is_ready'))
        st.write(t('ui.what_you_have_what_s_reserved_and_what_s_free'))
        st.caption(t('ui.a_snapshot_of_the_information_you_have_saved_you_can'))

        with st.container(key="picture_net_worth"):
            st.metric(
                t('metrics.net_worth'), f"€{summary['net_worth']:,.2f}",
                help=t('ui.your_cash_and_assets_minus_what_you_owe'),
            )
        if summary["net_worth"] > 0:
            st.caption(t('ui.based_on_your_saved_figures_what_you_own_is_worth'))
        elif summary["net_worth"] < 0:
            st.caption(t('ui.based_on_your_saved_figures_what_you_owe_is_greater'))
        else:
            st.caption(t('ui.your_saved_cash_and_asset_values_balance_out_your_recorded'))

        cash_col, funds_col, free_col = st.columns(3)
        with cash_col:
            st.metric(t('metrics.available_cash'), f"€{summary['available_cash']:,.2f}",
                      help=t('ui.money_currently_available_in_your_accounts_and_cash'))
        with funds_col:
            st.metric(t('metrics.set_aside'), f"€{summary['reserved_funds']:,.2f}",
                      help=t('ui.part_of_your_available_cash_assigned_to_specific_goals'))
        with free_col:
            st.metric(t('metrics.free_cash'), f"€{summary['free_cash']:,.2f}",
                      help=t('ui.cash_not_reserved_for_funds_this_does_not_subtract_monthly'))
        st.caption(t('metrics.cash_explanation'))

        with st.expander(t('ui.your_assets_and_debts')):
            st.metric(t('ui.debt'), f"€{summary['total_debt']:,.2f}", help=t('ui.the_total_amount_you_still_owe'))
            liquid_col, semi_col, non_col = st.columns(3)
            with liquid_col:
                st.metric(t('ui.liquid_investments_detail'), f"€{summary['liquid_investments']:,.2f}",
                          help=t('ui.assets_classified_as_usually_convertible_to_cash_within_a_few'))
            with semi_col:
                st.metric(t('ui.semi_liquid_assets_detail'), f"€{summary['semi_liquid_assets']:,.2f}",
                          help=t('ui.assets_classified_as_taking_more_time_or_effort_to_access'))
            with non_col:
                st.metric(t('ui.non_liquid_assets_detail'), f"€{summary['non_liquid_assets']:,.2f}",
                          help=t('ui.assets_classified_as_usually_taking_longer_to_sell_such_as'))
            st.caption(t('ui.these_use_the_availability_classifications_saved_for_your_assets_all'))

        st.subheader(t("plan.your_period", period=month_period(year, month)))
        if monthly is None:
            st.info(t('ui.no_monthly_plan_is_saved_for_this_month_yet'))
        else:
            income_col, allocation_col, remaining_col = st.columns(3)
            with income_col:
                st.metric(t('plan.expected_income'), f"€{monthly['income']:,.2f}")
            with allocation_col:
                st.metric(t('ui.planned_allocations'), f"€{monthly['allocated']:,.2f}")
            with remaining_col:
                st.metric(t('ui.unallocated'), f"€{monthly['remaining']:,.2f}")
            if monthly["remaining"] < 0:
                st.caption(t('ui.your_planned_allocations_currently_exceed_your_expected_income'))
            elif monthly["remaining"] > 0:
                st.caption(t('ui.some_of_your_expected_income_is_still_unallocated'))
            else:
                st.caption(t('ui.all_of_your_expected_income_is_allocated_in_this_plan'))
            st.caption(t('ui.these_are_intentions_not_actual_contributions_planning_does_not_move'))

        with st.container(border=True):
            if monthly is not None and (year, month) == (today.year, today.month):
                st.subheader(t('ui.you_re_set_for_this_month'))
                st.caption(t('ui.your_plan_is_saved_you_can_adjust_it_whenever_you'))
            else:
                st.subheader(t('ui.make_room_for_a_monthly_check_in'))
                st.caption(t('ui.prepare_this_month_s_plan_in_the_dashboard_when_you'))
            st.write(t('ui.you_don_t_need_to_check_this_app_every_day'))
            st.write(t(RETURN_COPY))

        with st.expander(t('ui.your_monthly_routine')):
            st.markdown(
                t('ui.1_check_your_bank_balances_2_update_account_balances_manually')
            )
            st.write(t('ui.you_don_t_need_to_enter_every_small_daily_purchase'))
            st.caption(t('ui.confirmed_contributions_update_fund_and_investment_balances_account_balances_still'))
