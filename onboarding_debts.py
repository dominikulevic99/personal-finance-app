"""Step 3 presentation using the existing debt fields and database functions."""

import streamlit as st
from i18n import t, TranslatedLabels, month_period

from debts import add_debt, get_debts


# Friendly labels only; keys match the existing dashboard categories.
DEBT_TYPES = TranslatedLabels({
    "MORTGAGE": 'ui.home_loan_mortgage',
    "CAR_LOAN": 'ui.car_loan',
    "PERSONAL_LOAN": 'ui.personal_loan',
    "CREDIT_CARD": 'ui.credit_card_balance',
    "OTHER": 'ui.other_money_i_owe',
})


def render_debts_step(user_id):
    """Render inside onboarding_shell(step=3); drafts and navigation are user-scoped."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "debt_form_open"
    form_version_key = prefix + "debt_form_version"

    st.title(t('ui.what_you_own_is_only_half_the_picture'))
    st.write(
        t('ui.add_what_you_owe_to_see_your_net_worth_what')
    )
    st.caption(
        t('ui.use_a_name_you_recognize_and_amounts_only_never_enter')
    )

    try:
        debts = get_debts(user_id)
    except Exception:
        st.error(t('ui.we_couldn_t_load_your_debts_please_try_again'))
        if st.button(t('ui.retry'), key=prefix + "debts_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "debt_saved", False):
        st.success(t('ui.debt_added_to_your_financial_picture'))

    if debts:
        st.subheader(t('ui.your_debts'))
        for debt in debts:
            with st.container(border=True):
                st.text(debt.name)
                st.caption(
                    t("debts.remaining", amount=f"{debt.remaining_balance:,.2f}", currency=debt.currency,
                      kind=DEBT_TYPES.get(debt.debt_type, t('ui.debt')))
                )

    form_open = st.session_state.get(form_open_key, not debts)
    if form_open:
        draft_prefix = prefix + f"debt_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                t('ui.debt_name'), placeholder=t('ui.e_g_money_borrowed_from_jonas'), key=draft_prefix + "name"
            )
            remaining_balance = st.number_input(
                t('ui.amount_you_still_owe_eur'),
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder=t('ui.e_g_500'),
                help=t('ui.enter_what_is_left_to_repay_rather_than_the_original'),
                key=draft_prefix + "balance",
            )
            debt_type = st.selectbox(
                t('ui.what_kind_of_debt_is_it'),
                options=list(DEBT_TYPES),
                index=None,
                placeholder=t('ui.choose_a_kind_of_debt'),
                format_func=DEBT_TYPES.formatter(),
                help=t('ui.for_informal_borrowing_such_as_money_owed_to_a_friend'),
                key=draft_prefix + "type",
            )
            with st.expander(t('ui.payment_and_interest')):
                st.caption(t('ui.both_start_at_0_set_them_here_if_you_make'))
                monthly_payment = st.number_input(
                    t('ui.monthly_payment_eur'),
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    help=t('ui.the_amount_you_normally_repay_each_month_leave_0_if'),
                    key=draft_prefix + "payment",
                )
                interest_rate = st.number_input(
                    t('ui.interest_rate'),
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help=t('ui.use_the_percentage_shown_in_your_loan_or_credit_agreement'),
                    key=draft_prefix + "interest",
                )
            submitted = st.form_submit_button(t('ui.add_debt'), type="primary")

        if submitted:
            if not name.strip():
                st.error(t('ui.please_enter_a_debt_name'))
            elif remaining_balance is None:
                st.error(t('ui.please_enter_the_amount_you_still_owe_you_can_enter'))
            elif remaining_balance < 0 or monthly_payment < 0 or interest_rate < 0:
                st.error(t('ui.amounts_and_the_interest_rate_must_be_0_or_more'))
            elif debt_type not in DEBT_TYPES:
                st.error(t('ui.please_choose_what_kind_of_debt_this_is'))
            else:
                try:
                    add_debt(user_id, name, debt_type, remaining_balance, monthly_payment, interest_rate)
                except Exception:
                    st.session_state[prefix + "debt_save_uncertain"] = True
                else:
                    st.session_state[form_open_key] = False
                    st.session_state[form_version_key] = st.session_state.get(form_version_key, 0) + 1
                    st.session_state[prefix + "debt_saved"] = True
                    st.session_state.pop(prefix + "debt_save_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "debt_save_uncertain", False):
            st.error(
                t('ui.we_couldn_t_confirm_that_the_debt_was_saved_check')
            )
            if st.button(t('ui.refresh_debt_list'), key=prefix + "debts_refresh"):
                st.session_state.pop(prefix + "debt_save_uncertain", None)
                st.rerun()

        if debts and st.button(t('ui.cancel'), type="tertiary", key=prefix + "debt_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif debts:
        if st.button(t('actions.continue'), type="primary", key=prefix + "debts_continue"):
            st.session_state[prefix + "step"] = "funds"
            st.rerun()
        if st.button(t('ui.add_another'), key=prefix + "debt_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption(t('ui.only_saved_debts_will_be_included_you_can_add_more'))
        if st.button(
            t('ui.i_don_t_have_any_debt') if not debts else t('ui.skip_for_now'),
            type="tertiary",
            key=prefix + "debts_skip",
        ):
            st.session_state[prefix + "step"] = "funds"
            st.rerun()

    if st.button(t('ui.back_to_assets'), type="tertiary", key=prefix + "debts_back"):
        st.session_state[prefix + "step"] = "assets"
        st.rerun()
