"""Step 3 presentation using the existing debt fields and database functions."""

import streamlit as st

from debts import add_debt, get_debts


# Friendly labels only; keys match the existing dashboard categories.
DEBT_TYPES = {
    "MORTGAGE": "Home loan / mortgage",
    "CAR_LOAN": "Car loan",
    "PERSONAL_LOAN": "Personal loan",
    "CREDIT_CARD": "Credit card balance",
    "OTHER": "Other money I owe",
}


def render_debts_step(user_id):
    """Render inside onboarding_shell(step=3); drafts and navigation are user-scoped."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "debt_form_open"
    form_version_key = prefix + "debt_form_version"

    st.title("Do you currently owe money?")
    st.write(
        "Add loans, credit balances or money you owe that should be included "
        "in your financial picture."
    )
    st.caption(
        "Use a name you recognize and amounts only. Never enter card numbers, "
        "account numbers, PINs, passwords or banking credentials."
    )

    try:
        debts = get_debts(user_id)
    except Exception:
        st.error("We couldn't load your debts. Please try again.")
        if st.button("Retry", key=prefix + "debts_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "debt_saved", False):
        st.success("Debt added to your financial picture.")

    if debts:
        st.subheader("Your debts")
        for debt in debts:
            with st.container(border=True):
                st.text(debt.name)
                st.caption(
                    f"{debt.remaining_balance:,.2f} {debt.currency} remaining · "
                    f"{DEBT_TYPES.get(debt.debt_type, 'Debt')}"
                )

    form_open = st.session_state.get(form_open_key, not debts)
    if form_open:
        draft_prefix = prefix + f"debt_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                "Debt name", placeholder="e.g. Money borrowed from Jonas", key=draft_prefix + "name"
            )
            remaining_balance = st.number_input(
                "Amount you still owe (EUR)",
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder="e.g. 500",
                help="Enter what is left to repay, rather than the original amount borrowed.",
                key=draft_prefix + "balance",
            )
            debt_type = st.selectbox(
                "What kind of debt is it?",
                options=list(DEBT_TYPES),
                index=None,
                placeholder="Choose a kind of debt",
                format_func=DEBT_TYPES.get,
                help="For informal borrowing, such as money owed to a friend, choose Other money I owe.",
                key=draft_prefix + "type",
            )
            with st.expander("Payment and interest"):
                st.caption("Both start at 0. Set them here if you make regular payments or pay interest.")
                monthly_payment = st.number_input(
                    "Monthly payment (EUR)",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    help="The amount you normally repay each month. Leave 0 if there is no regular payment.",
                    key=draft_prefix + "payment",
                )
                interest_rate = st.number_input(
                    "Interest rate (%)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help="Use the percentage shown in your loan or credit agreement, such as 5 for 5%. Leave 0 if no interest is charged.",
                    key=draft_prefix + "interest",
                )
            submitted = st.form_submit_button("Add debt", type="primary")

        if submitted:
            if not name.strip():
                st.error("Please enter a debt name.")
            elif remaining_balance is None:
                st.error("Please enter the amount you still owe. You can enter 0.")
            elif remaining_balance < 0 or monthly_payment < 0 or interest_rate < 0:
                st.error("Amounts and the interest rate must be 0 or more.")
            elif debt_type not in DEBT_TYPES:
                st.error("Please choose what kind of debt this is.")
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
                "We couldn't confirm that the debt was saved. "
                "Check the debt list before trying again."
            )
            if st.button("Refresh debt list", key=prefix + "debts_refresh"):
                st.session_state.pop(prefix + "debt_save_uncertain", None)
                st.rerun()

        if debts and st.button("Cancel", key=prefix + "debt_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif debts:
        if st.button("Continue", type="primary", key=prefix + "debts_continue"):
            st.session_state[prefix + "step"] = "funds"
            st.rerun()
        if st.button("Add another", key=prefix + "debt_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption("Only saved debts will be included. You can add more later.")
        if st.button(
            "I don't have any debt" if not debts else "Skip for now",
            key=prefix + "debts_skip",
        ):
            st.session_state[prefix + "step"] = "funds"
            st.rerun()

    if st.button("Back to Assets", key=prefix + "debts_back"):
        st.session_state[prefix + "step"] = "assets"
        st.rerun()
