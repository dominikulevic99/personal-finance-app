"""Step 1 presentation, using the existing account database functions."""

import streamlit as st
from i18n import t

from accounts import add_account, get_accounts


def render_accounts_step(user_id):
    """Render inside onboarding_shell(step=1); keep all draft state user-scoped."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "account_form_open"
    form_version_key = prefix + "account_form_version"

    st.title(t('ui.start_with_the_money_you_can_access_today'))
    st.write(t('ui.add_where_your_available_cash_sits_using_a_familiar_name'))
    st.caption(t('ui.for_example_revolut_swedbank_cash_or_everyday_account'))
    st.info(
        t('ui.only_enter_a_name_you_recognize_and_the_current_balance')
    )

    try:
        accounts = get_accounts(user_id)
    except Exception:
        st.error(t('ui.we_couldn_t_load_your_accounts_please_try_again'))
        if st.button(t('ui.retry'), key=prefix + "accounts_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "account_saved", False):
        st.success(t('ui.account_added_one_account_is_enough_to_continue'))

    if accounts:
        st.subheader(t('ui.your_accounts'))
        for account in accounts:
            with st.container(border=True):
                # st.text keeps names literal, rather than interpreting Markdown/HTML.
                st.text(account.name)
                st.caption(
                    f"{account.balance:,.2f} {account.currency} · "
                    f"{t('accounts.cash') if account.account_type == 'CASH' else t('accounts.bank')}"
                )

    form_open = st.session_state.get(form_open_key, not accounts)
    if form_open:
        # A new key after each successful save clears the next draft without
        # clearing invalid input or modifying an already instantiated widget.
        draft_prefix = prefix + f"account_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                t("accounts.name"), placeholder=t('ui.e_g_revolut'), key=draft_prefix + "name"
            )
            balance = st.number_input(
                t("accounts.current_balance"),
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder=t('ui.e_g_1250'),
                key=draft_prefix + "balance",
            )
            is_cash = st.checkbox(
                t('ui.this_is_cash_i_keep_on_hand'), key=draft_prefix + "cash"
            )
            submitted = st.form_submit_button(t('ui.add_account'), type="primary")

        if submitted:
            if not name.strip():
                st.error(t('ui.please_enter_an_account_name'))
            elif balance is None:
                st.error(t('ui.please_enter_the_current_balance_you_can_enter_0'))
            elif balance < 0:
                st.error(t('ui.the_balance_must_be_0_or_more'))
            else:
                try:
                    add_account(user_id, name, "CASH" if is_cash else "BANK", balance)
                except Exception:
                    st.session_state[prefix + "account_save_uncertain"] = True
                else:
                    st.session_state[form_open_key] = False
                    st.session_state[form_version_key] = st.session_state.get(form_version_key, 0) + 1
                    st.session_state[prefix + "account_saved"] = True
                    st.session_state.pop(prefix + "account_save_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "account_save_uncertain", False):
            st.error(
                t('ui.we_couldn_t_confirm_that_the_account_was_saved_check')
            )
            if st.button(t('ui.refresh_account_list'), key=prefix + "accounts_refresh"):
                st.session_state.pop(prefix + "account_save_uncertain", None)
                st.rerun()

        if accounts and st.button(t('ui.cancel'), type="tertiary", key=prefix + "account_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif accounts:
        if st.button(t('actions.continue'), type="primary", key=prefix + "accounts_continue"):
            st.session_state[prefix + "step"] = "assets"
            st.rerun()
        if st.button(t('ui.add_another_account'), key=prefix + "account_another"):
            st.session_state[form_open_key] = True
            st.rerun()
