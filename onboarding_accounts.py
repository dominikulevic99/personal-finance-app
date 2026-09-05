"""Step 1 presentation, using the existing account database functions."""

import streamlit as st

from accounts import add_account, get_accounts


def render_accounts_step(user_id):
    """Render inside onboarding_shell(step=1); keep all draft state user-scoped."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "account_form_open"
    form_version_key = prefix + "account_form_version"

    st.title("Where is your money today?")
    st.write("Add the places where you currently keep money.")
    st.caption("For example: Revolut, Swedbank, Cash or Everyday account.")
    st.info(
        "Only enter a name you recognize and the current balance. Never enter "
        "account numbers, card numbers, PINs, passwords or banking credentials."
    )

    try:
        accounts = get_accounts(user_id)
    except Exception:
        st.error("We couldn't load your accounts. Please try again.")
        if st.button("Retry", key=prefix + "accounts_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "account_saved", False):
        st.success("Account added. One account is enough to continue.")

    if accounts:
        st.subheader("Your accounts")
        for account in accounts:
            with st.container(border=True):
                # st.text keeps names literal, rather than interpreting Markdown/HTML.
                st.text(account.name)
                st.caption(
                    f"{account.balance:,.2f} {account.currency} · "
                    f"{'Cash' if account.account_type == 'CASH' else 'Bank account'}"
                )

    form_open = st.session_state.get(form_open_key, not accounts)
    if form_open:
        # A new key after each successful save clears the next draft without
        # clearing invalid input or modifying an already instantiated widget.
        draft_prefix = prefix + f"account_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                "Account name", placeholder="e.g. Revolut", key=draft_prefix + "name"
            )
            balance = st.number_input(
                "Current balance (EUR)",
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder="e.g. 1250",
                key=draft_prefix + "balance",
            )
            is_cash = st.checkbox(
                "This is cash I keep on hand", key=draft_prefix + "cash"
            )
            submitted = st.form_submit_button("Add account", type="primary")

        if submitted:
            if not name.strip():
                st.error("Please enter an account name.")
            elif balance is None:
                st.error("Please enter the current balance. You can enter 0.")
            elif balance < 0:
                st.error("The balance must be 0 or more.")
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
                "We couldn't confirm that the account was saved. "
                "Check the account list before trying again."
            )
            if st.button("Refresh account list", key=prefix + "accounts_refresh"):
                st.session_state.pop(prefix + "account_save_uncertain", None)
                st.rerun()

        if accounts and st.button("Cancel", key=prefix + "account_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif accounts:
        if st.button("Continue", type="primary", key=prefix + "accounts_continue"):
            st.session_state[prefix + "step"] = "assets"
            st.rerun()
        if st.button("Add another account", key=prefix + "account_another"):
            st.session_state[form_open_key] = True
            st.rerun()
