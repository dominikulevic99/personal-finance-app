"""Step 4 presentation for funds that reserve existing money."""

import streamlit as st

from accounts import get_accounts
from calculations import calculate_financial_summary
from funds import add_fund, get_funds


def render_funds_step(user_id):
    """Render inside onboarding_shell(step=4), using existing fund creation rules."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "fund_form_open"
    form_version_key = prefix + "fund_form_version"

    st.title("What are you saving for?")
    st.write(
        "A Fund is money you mentally set aside for a specific purpose — "
        "for example an emergency fund, travel, a car or a home deposit."
    )
    st.caption("Ideas: Emergency fund · Travel · Car · Home · Other")
    st.info(
        "Funds reserve money already in your accounts or cash. "
        "They do not add extra money or increase your net worth."
    )
    with st.expander("How Funds work"):
        st.write("You can allocate part of your monthly income toward a Fund.")
        st.write("At the end of the month, you confirm how much you actually contributed.")
        st.write("Confirmed contributions update the Fund balance.")
        st.write(
            "Your bank account balances are not synchronized automatically, "
            "so you still update those manually."
        )
        st.caption("Avoid setting aside the same money in more than one fund.")

    try:
        funds = get_funds(user_id)
        accounts = get_accounts(user_id)
        available_cash = calculate_financial_summary(accounts, [], [], funds)["available_cash"]
    except Exception:
        st.error("We couldn't load your funds and account balances. Please try again.")
        if st.button("Retry", key=prefix + "funds_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "fund_saved", False):
        st.success("Fund created. You can build it up over time.")

    if funds:
        st.subheader("Your funds")
        for fund in funds:
            with st.container(border=True):
                st.text(fund.name)
                st.caption(f"{fund.current_balance:,.2f} EUR set aside")
                if fund.target_amount is not None and fund.target_amount > 0:
                    st.caption(f"Target: {fund.target_amount:,.2f} EUR")
                else:
                    st.caption("No target set yet")

    form_open = st.session_state.get(form_open_key, not funds)
    if form_open:
        draft_prefix = prefix + f"fund_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                "Fund name", placeholder="e.g. Emergency fund", key=draft_prefix + "name"
            )
            current_balance = st.number_input(
                "Already set aside (EUR)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Money already in your accounts or cash that you want to reserve for this goal. Leave 0 to start from scratch.",
                key=draft_prefix + "balance",
            )
            target_amount = st.number_input(
                "Target amount (EUR)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="How much you would like to set aside in total, for example 3000. Leave 0 if you have not chosen a target yet.",
                key=draft_prefix + "target",
            )
            submitted = st.form_submit_button("Create fund", type="primary")

        if submitted:
            if not name.strip():
                st.error("Please enter a fund name.")
            elif current_balance < 0 or target_amount < 0:
                st.error("Amounts must be 0 or more.")
            elif current_balance > float(available_cash):
                # Preserve the dashboard's existing starting-balance check.
                st.warning(
                    "The starting amount is higher than the cash in your accounts. "
                    "Check the amount, or start this fund at 0."
                )
            else:
                try:
                    add_fund(user_id, name, current_balance, target_amount)
                except Exception:
                    st.session_state[prefix + "fund_save_uncertain"] = True
                else:
                    st.session_state[form_open_key] = False
                    st.session_state[form_version_key] = st.session_state.get(form_version_key, 0) + 1
                    st.session_state[prefix + "fund_saved"] = True
                    st.session_state.pop(prefix + "fund_save_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "fund_save_uncertain", False):
            st.error(
                "We couldn't confirm that the fund was saved. "
                "Check the fund list before trying again."
            )
            if st.button("Refresh fund list", key=prefix + "funds_refresh"):
                st.session_state.pop(prefix + "fund_save_uncertain", None)
                st.rerun()

        if funds and st.button("Cancel", key=prefix + "fund_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif funds:
        if st.button("Continue", type="primary", key=prefix + "funds_continue"):
            st.session_state[prefix + "step"] = "monthly_plan"
            st.rerun()
        if st.button("Add another", key=prefix + "fund_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption("Only saved funds will be included. You can add a goal later.")
        if st.button("Skip for now", key=prefix + "funds_skip"):
            st.session_state[prefix + "step"] = "monthly_plan"
            st.rerun()

    if st.button("Back to Debts", key=prefix + "funds_back"):
        st.session_state[prefix + "step"] = "debts"
        st.rerun()
