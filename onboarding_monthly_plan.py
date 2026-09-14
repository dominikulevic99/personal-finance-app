"""Step 5 presentation. Planned amounts never create contribution transactions."""

from datetime import date

import streamlit as st
from i18n import t, TranslatedLabels, month_period
from analytics import track_event

from assets import get_assets
from calculations import calculate_planned_allocation_summary
from funds import get_funds
from monthly_plan_items import add_plan_item, get_plan_items
from monthly_plans import create_monthly_plan, get_monthly_plan, update_planned_income


ALLOCATION_TYPES = TranslatedLabels({
    "EXPENSE": 'ui.living_costs',
    "FUND": 'ui.saving_toward_a_fund',
    "INVESTMENT": 'ui.investing',
    "DEBT_PAYMENT": 'ui.debt_payments',
    "OTHER": 'ui.other',
})


def _render_explanation():
    st.write(t('ui.your_plan_describes_what_you_intend_to_do_with_your'))
    st.caption(t('ui.planned_allocations_are_not_actual_contributions'))
    with st.expander(t('ui.a_simple_example')):
        st.caption(t('ui.an_illustration_only_these_amounts_are_not_added_to_your'))
        st.markdown(
            t('ui.this_month_s_plan_amount_expected_income_2_500_living')
        )
    with st.expander(t('ui.what_happens_at_the_end_of_the_month')):
        st.write(t('ui.at_the_end_of_the_month_you_confirm_what_you'))
        st.write(
            t('ui.confirmed_fund_and_investment_contributions_update_those_balances_your_bank')
        )


def _render_income(user_id, prefix, year, month, plan):
    """Return True while the income form is open, keeping allocation edits separate."""
    edit_key = prefix + "edit_income"
    if plan is not None and not st.session_state.get(edit_key, False):
        return False

    st.subheader(t('ui.start_with_your_expected_income'))
    with st.form(prefix + f"income_form_{plan.id if plan else 'new'}"):
        income = st.number_input(
            t('ui.expected_income_eur'),
            min_value=0.0,
            value=float(plan.planned_income) if plan is not None else None,
            step=100.0,
            placeholder=t('ui.e_g_2500'),
            help=t('ui.the_money_you_expect_to_receive_this_month_you_can'),
            key=prefix + f"income_{plan.id if plan else 'new'}",
        )
        submitted = st.form_submit_button(t('ui.save_expected_income'), type="primary")

    if submitted:
        if income is None or income < 0:
            st.error(t('ui.please_enter_expected_income_of_0_or_more'))
        else:
            try:
                if plan is None:
                    # Recheck before creation, so another completed save isn't
                    # silently overwritten by an older, still-open form.
                    existing = get_monthly_plan(user_id, year, month)
                    if existing is None:
                        create_monthly_plan(user_id, year, month, income)
                        track_event(user_id, "monthly_plan_created", session_state=st.session_state)
                else:
                    update_planned_income(user_id, plan.id, income)
            except Exception:
                st.session_state[prefix + "income_uncertain"] = True
            else:
                st.session_state[edit_key] = False
                st.session_state.pop(prefix + "income_uncertain", None)
                st.rerun()

    if st.session_state.get(prefix + "income_uncertain", False):
        st.error(t('ui.we_couldn_t_confirm_that_the_income_was_saved_reload'))
        if st.button(t('ui.reload_plan'), key=prefix + "income_reload"):
            st.session_state.pop(prefix + "income_uncertain", None)
            st.rerun()
    if plan is not None and st.button(t('ui.cancel'), type="tertiary", key=prefix + "income_cancel"):
        st.session_state[edit_key] = False
        st.rerun()
    return True


def _render_allocation_form(user_id, prefix, plan, items, funds_by_id, investments_by_id):
    version = st.session_state.get(prefix + "allocation_version", 0)
    draft_prefix = prefix + f"allocation_{version}_"
    with st.container(border=True):
        st.subheader(t('ui.give_an_amount_a_purpose'))
        # This selector is outside the form so target choices update immediately.
        category = st.selectbox(
            t('ui.where_should_this_money_go'),
            options=list(ALLOCATION_TYPES),
            format_func=ALLOCATION_TYPES.formatter(),
            key=draft_prefix + "category",
        )
        targets = funds_by_id if category == "FUND" else investments_by_id
        needs_target = category in ("FUND", "INVESTMENT")
        missing_target = needs_target and not targets
        if missing_target:
            is_fund = category == "FUND"
            st.info(t('ui.create_a_fund_first_to_plan_saving_toward_it') if is_fund else
                    t('ui.add_an_investment_asset_first_to_plan_investing_toward_it'))
            if st.button(t('ui.back_to_funds') if is_fund else t('ui.back_to_assets'), type="tertiary", key=draft_prefix + "create_target"):
                st.session_state[f"onboarding_{user_id}_step"] = "funds" if is_fund else "assets"
                st.rerun()

        with st.form(draft_prefix + category + "_form"):
            name = st.text_input(
                t('ui.allocation_name'), placeholder=t('ui.e_g_living_expenses'), key=draft_prefix + "name"
            )
            amount = st.number_input(
                t('ui.planned_amount_eur'), min_value=0.0, value=None, step=50.0,
                placeholder=t('ui.e_g_1400'), key=draft_prefix + "amount",
            )
            target_id = None
            if needs_target and targets:
                target_id = st.selectbox(
                    t('ui.which_fund') if category == "FUND" else t('ui.which_investment'),
                    options=list(targets), index=None,
                    placeholder=t('ui.choose_a_fund') if category == "FUND" else t('ui.choose_an_investment'),
                    format_func=targets.get, key=draft_prefix + category + "_target",
                )
            submitted = st.form_submit_button(t('ui.add_allocation_detail'), type="primary", disabled=missing_target)

        if submitted:
            if not name.strip():
                st.error(t('ui.please_enter_an_allocation_name'))
            elif amount is None or amount < 0:
                st.error(t('ui.please_enter_a_planned_amount_of_0_or_more'))
            elif category not in ALLOCATION_TYPES:
                st.error(t('ui.please_choose_where_this_money_should_go'))
            elif needs_target and target_id not in targets:
                st.error(t('ui.please_choose_a_saved_fund_or_investment_for_this_allocation'))
            else:
                try:
                    add_plan_item(
                        user_id, plan.id, name, category, amount,
                        fund_id=target_id if category == "FUND" else None,
                        asset_id=target_id if category == "INVESTMENT" else None,
                    )
                except Exception:
                    st.session_state[prefix + "allocation_uncertain"] = True
                else:
                    st.session_state[prefix + "allocation_open"] = False
                    st.session_state[prefix + "allocation_version"] = version + 1
                    st.session_state[prefix + "allocation_saved"] = True
                    st.session_state.pop(prefix + "allocation_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "allocation_uncertain", False):
            st.error(t('ui.we_couldn_t_confirm_that_the_allocation_was_saved_check'))
            if st.button(t('ui.reload_allocations'), key=prefix + "allocation_reload"):
                st.session_state.pop(prefix + "allocation_uncertain", None)
                st.rerun()
        if st.button(t('ui.cancel') if items else t('ui.plan_allocations_later'), type="tertiary", key=prefix + "allocation_cancel"):
            st.session_state[prefix + "allocation_open"] = False
            st.rerun()


def render_monthly_plan_step(user_id):
    user_prefix = f"onboarding_{user_id}_"
    today = date.today()
    # Keep the chosen month stable if setup crosses a month boundary.
    year, month = st.session_state.setdefault(user_prefix + "plan_month", (today.year, today.month))
    prefix = user_prefix + f"plan_{year}_{month}_"

    st.title(t('ui.decide_what_this_month_s_money_should_do'))
    st.write(t('ui.give_your_expected_income_direction_before_everyday_spending_takes_over'))
    st.caption(t("plan.period", period=month_period(year, month)))
    _render_explanation()

    try:
        plan = get_monthly_plan(user_id, year, month)
        items = get_plan_items(user_id, plan.id) if plan is not None else []
        funds = get_funds(user_id) if plan is not None else []
        assets = get_assets(user_id) if plan is not None else []
    except Exception:
        st.error(t('ui.we_couldn_t_load_your_monthly_plan_please_try_again'))
        if st.button(t('ui.retry'), key=prefix + "retry"):
            st.rerun()
        return

    editing_income = _render_income(user_id, prefix, year, month, plan)
    if plan is not None and not editing_income:
        funds_by_id = {fund.id: fund.name for fund in funds}
        investments_by_id = {asset.id: asset.name for asset in assets if asset.asset_type == "INVESTMENT"}
        totals = calculate_planned_allocation_summary(plan.planned_income, items)
        allocated = totals["allocated"]
        remaining = totals["remaining"]
        income_col, allocated_col, remaining_col = st.columns(3)
        with income_col:
            st.metric(t('plan.expected_income'), f"€{plan.planned_income:,.2f}")
        with allocated_col:
            st.metric(t('ui.planned_allocations'), f"€{allocated:,.2f}")
        with remaining_col:
            st.metric(t('ui.unallocated'), f"€{remaining:,.2f}")
        if remaining < 0:
            st.warning(t("plan.over_income", amount=f"{abs(remaining):,.2f}"))
        elif remaining > 0:
            st.caption(t('ui.you_can_leave_some_income_unallocated_and_decide_later'))
        else:
            st.caption(t('ui.every_euro_of_your_expected_income_has_a_purpose'))

        if st.session_state.pop(prefix + "allocation_saved", False):
            st.success(t('ui.allocation_saved_to_your_plan_no_contribution_has_been_recorded'))
        if items:
            st.subheader(t('ui.your_allocations'))
            for item in items:
                with st.container(border=True):
                    st.text(item.name)
                    st.caption(t("plan.allocation_summary", amount=f"{item.planned_amount:,.2f}", kind=ALLOCATION_TYPES.get(item.category_type, t('ui.allocation'))))
                    if item.category_type == "FUND":
                        st.text(t("buckets.linked", name=funds_by_id.get(item.fund_id, t('ui.not_available'))))
                    elif item.category_type == "INVESTMENT":
                        st.text(t("investments.linked", name=investments_by_id.get(item.asset_id, t('ui.not_available'))))

        if st.session_state.get(prefix + "allocation_open", not items):
            _render_allocation_form(user_id, prefix, plan, items, funds_by_id, investments_by_id)
        else:
            if st.button(t('ui.see_my_financial_picture'), type="primary", key=prefix + "finish"):
                st.session_state[user_prefix + "step"] = "financial_picture"
                st.rerun()
            if st.button(t('ui.add_another_allocation') if items else t('ui.add_allocation_detail'), key=prefix + "another"):
                st.session_state[prefix + "allocation_open"] = True
                st.rerun()
        if st.button(t('ui.change_expected_income'), key=prefix + "edit_income_button"):
            st.session_state[prefix + "edit_income"] = True
            st.rerun()

    if st.button(t('ui.back_to_funds'), type="tertiary", key=prefix + "back"):
        st.session_state[user_prefix + "step"] = "funds"
        st.rerun()
