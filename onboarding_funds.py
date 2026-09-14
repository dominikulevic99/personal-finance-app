"""Step 4 presentation for funds that reserve existing money."""

import streamlit as st
from i18n import t

from accounts import get_accounts
from calculations import calculate_financial_summary
from funds import add_fund, get_funds
from fund_progress import render_fund_progress


def render_funds_step(user_id):
    """Render inside onboarding_shell(step=4), using existing fund creation rules."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "fund_form_open"
    form_version_key = prefix + "fund_form_version"

    st.title(t('ui.now_give_some_of_your_money_a_purpose'))
    st.write(
        t('ui.your_bank_balance_tells_you_how_much_is_there_funds')
    )
    with st.container(border=True):
        st.caption(t('ui.example_not_your_balances'))
        st.write(t('ui.5_000_available'))
        st.text(t('ui.1_500_emergency_800_japan_900_laptop'))
        st.write(t('ui.1_800_still_free'))
        st.write(
            t('ui.your_bank_still_shows_5_000_but_now_you_know')
        )
    st.write(t('ui.if_it_matters_enough_to_plan_for_it_can_be'))
    with st.expander(t('ui.how_funds_work')):
        st.write(
            t('ui.a_fund_here_is_not_an_investment_fund_it_reserves')
        )
        st.write(
            t('ui.you_can_allocate_part_of_your_monthly_income_toward_a')
        )
        st.write(
            t('ui.at_the_end_of_the_month_you_confirm_how_much'))
        st.write(t('ui.confirmed_contributions_update_the_fund_balance'))
        st.write(
            t('ui.your_bank_account_balances_are_not_synchronized_automatically_so_you')
        )
        st.caption(t('ui.avoid_setting_aside_the_same_money_in_more_than_one'))

    try:
        funds = get_funds(user_id)
        accounts = get_accounts(user_id)
        available_cash = calculate_financial_summary(
            accounts, [], [], funds)["available_cash"]
    except Exception:
        st.error(
            t('ui.we_couldn_t_load_your_funds_and_account_balances_please'))
        if st.button(t('ui.retry'), key=prefix + "funds_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "fund_saved", False):
        st.success(t('ui.fund_created_you_can_build_it_up_over_time'))

    if funds:
        st.subheader(t('buckets.yours'))
        show_all_key = prefix + "show_all_funds"
        show_all = st.session_state.get(show_all_key, False)
        if len(funds) > 3:
            if st.button(
                t('ui.show_fewer_funds') if show_all else t('ui.show_all_funds'),
                type="tertiary", key=prefix + "toggle_funds",
            ):
                st.session_state[show_all_key] = not show_all
                st.rerun()
            st.caption(
                t("buckets.showing", shown=len(funds) if show_all else 3, total=len(funds)))
        for fund in (funds if show_all else funds[:3]):
            with st.container(border=True):
                st.text(fund.name)
                render_fund_progress(fund.current_balance, fund.target_amount)

    form_open = st.session_state.get(form_open_key, not funds)
    if form_open:
        draft_prefix = prefix + \
            f"fund_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                t('buckets.name'), placeholder=t('ui.e_g_emergency_fund'), key=draft_prefix + "name"
            )
            current_balance = st.number_input(
                t('ui.already_set_aside_eur'),
                min_value=0.0,
                value=0.0,
                step=100.0,
                help=t('ui.money_already_in_your_accounts_or_cash_that_you_want'),
                key=draft_prefix + "balance",
            )
            target_amount = st.number_input(
                t('ui.target_amount_eur'),
                min_value=0.0,
                value=0.0,
                step=100.0,
                help=t('ui.how_much_you_would_like_to_set_aside_in_total'),
                key=draft_prefix + "target",
            )
            submitted = st.form_submit_button(t('ui.create_fund'), type="primary")

        if submitted:
            if not name.strip():
                st.error(t('ui.please_enter_a_fund_name'))
            elif current_balance < 0 or target_amount < 0:
                st.error(t('ui.amounts_must_be_0_or_more'))
            elif current_balance > float(available_cash):
                # Preserve the dashboard's existing starting-balance check.
                st.warning(
                    t('ui.the_starting_amount_is_higher_than_the_cash_in_your')
                )
            else:
                try:
                    add_fund(user_id, name, current_balance, target_amount)
                except Exception:
                    st.session_state[prefix + "fund_save_uncertain"] = True
                else:
                    st.session_state[form_open_key] = False
                    st.session_state[form_version_key] = st.session_state.get(
                        form_version_key, 0) + 1
                    st.session_state[prefix + "fund_saved"] = True
                    st.session_state.pop(prefix + "fund_save_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "fund_save_uncertain", False):
            st.error(
                t('ui.we_couldn_t_confirm_that_the_fund_was_saved_check')
            )
            if st.button(t('ui.refresh_fund_list'), key=prefix + "funds_refresh"):
                st.session_state.pop(prefix + "fund_save_uncertain", None)
                st.rerun()

        if funds and st.button(t('ui.cancel'), type="tertiary", key=prefix + "fund_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif funds:
        if st.button(t('actions.continue'), type="primary", key=prefix + "funds_continue"):
            st.session_state[prefix + "step"] = "monthly_plan"
            st.rerun()
        if st.button(t('ui.add_another'), key=prefix + "fund_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption(t('ui.only_saved_funds_will_be_included_you_can_add_a'))
        if st.button(t('ui.skip_for_now'), type="tertiary", key=prefix + "funds_skip"):
            st.session_state[prefix + "step"] = "monthly_plan"
            st.rerun()

    if st.button(t('ui.back_to_debts'), type="tertiary", key=prefix + "funds_back"):
        st.session_state[prefix + "step"] = "debts"
        st.rerun()
