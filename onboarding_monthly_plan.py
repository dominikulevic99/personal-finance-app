"""Step 5 presentation. Planned amounts never create contribution transactions."""

from datetime import date

import streamlit as st

from assets import get_assets
from calculations import calculate_planned_allocation_summary
from funds import get_funds
from monthly_plan_items import add_plan_item, get_plan_items
from monthly_plans import create_monthly_plan, get_monthly_plan, update_planned_income


ALLOCATION_TYPES = {
    "EXPENSE": "Living costs",
    "FUND": "Saving toward a fund",
    "INVESTMENT": "Investing",
    "DEBT_PAYMENT": "Debt payments",
    "OTHER": "Other",
}


def _render_explanation():
    st.write("Your plan describes what you intend to do with your income.")
    st.caption("Planned allocations are not actual contributions.")
    with st.expander("A simple example"):
        st.caption("An illustration only — these amounts are not added to your plan.")
        st.markdown(
            "| This month's plan | Amount |\n"
            "| :--- | ---: |\n"
            "| Expected income | €2,500 |\n"
            "| Living expenses | €1,400 |\n"
            "| Emergency Fund | €300 |\n"
            "| Investments | €400 |\n"
            "| Travel Fund | €200 |\n"
            "| Unallocated | €200 |"
        )
    with st.expander("What happens at the end of the month?"):
        st.write("At the end of the month, you confirm what you actually contributed to Funds and Investments.")
        st.write(
            "Confirmed Fund and Investment contributions update those balances. "
            "Your bank account balances still need to be updated manually."
        )


def _render_income(user_id, prefix, year, month, plan):
    """Return True while the income form is open, keeping allocation edits separate."""
    edit_key = prefix + "edit_income"
    if plan is not None and not st.session_state.get(edit_key, False):
        return False

    st.subheader("Start with your expected income")
    with st.form(prefix + f"income_form_{plan.id if plan else 'new'}"):
        income = st.number_input(
            "Expected income (EUR)",
            min_value=0.0,
            value=float(plan.planned_income) if plan is not None else None,
            step=100.0,
            placeholder="e.g. 2500",
            help="The money you expect to receive this month. You can update this later.",
            key=prefix + f"income_{plan.id if plan else 'new'}",
        )
        submitted = st.form_submit_button("Save expected income", type="primary")

    if submitted:
        if income is None or income < 0:
            st.error("Please enter expected income of 0 or more.")
        else:
            try:
                if plan is None:
                    # Recheck before creation, so another completed save isn't
                    # silently overwritten by an older, still-open form.
                    existing = get_monthly_plan(user_id, year, month)
                    if existing is None:
                        create_monthly_plan(user_id, year, month, income)
                else:
                    update_planned_income(user_id, plan.id, income)
            except Exception:
                st.session_state[prefix + "income_uncertain"] = True
            else:
                st.session_state[edit_key] = False
                st.session_state.pop(prefix + "income_uncertain", None)
                st.rerun()

    if st.session_state.get(prefix + "income_uncertain", False):
        st.error("We couldn't confirm that the income was saved. Reload your plan before trying again.")
        if st.button("Reload plan", key=prefix + "income_reload"):
            st.session_state.pop(prefix + "income_uncertain", None)
            st.rerun()
    if plan is not None and st.button("Cancel", key=prefix + "income_cancel"):
        st.session_state[edit_key] = False
        st.rerun()
    return True


def _render_allocation_form(user_id, prefix, plan, items, funds_by_id, investments_by_id):
    version = st.session_state.get(prefix + "allocation_version", 0)
    draft_prefix = prefix + f"allocation_{version}_"
    with st.container(border=True):
        st.subheader("Give an amount a purpose")
        # This selector is outside the form so target choices update immediately.
        category = st.selectbox(
            "Where should this money go?",
            options=list(ALLOCATION_TYPES),
            format_func=ALLOCATION_TYPES.get,
            key=draft_prefix + "category",
        )
        targets = funds_by_id if category == "FUND" else investments_by_id
        needs_target = category in ("FUND", "INVESTMENT")
        missing_target = needs_target and not targets
        if missing_target:
            is_fund = category == "FUND"
            st.info("Create a fund first to plan saving toward it." if is_fund else
                    "Add an investment asset first to plan investing toward it.")
            if st.button("Back to Funds" if is_fund else "Back to Assets", key=draft_prefix + "create_target"):
                st.session_state[f"onboarding_{user_id}_step"] = "funds" if is_fund else "assets"
                st.rerun()

        with st.form(draft_prefix + category + "_form"):
            name = st.text_input(
                "Allocation name", placeholder="e.g. Living expenses", key=draft_prefix + "name"
            )
            amount = st.number_input(
                "Planned amount (EUR)", min_value=0.0, value=None, step=50.0,
                placeholder="e.g. 1400", key=draft_prefix + "amount",
            )
            target_id = None
            if needs_target and targets:
                target_id = st.selectbox(
                    "Which fund?" if category == "FUND" else "Which investment?",
                    options=list(targets), index=None,
                    placeholder="Choose a fund" if category == "FUND" else "Choose an investment",
                    format_func=targets.get, key=draft_prefix + category + "_target",
                )
            submitted = st.form_submit_button("Add allocation", type="primary", disabled=missing_target)

        if submitted:
            if not name.strip():
                st.error("Please enter an allocation name.")
            elif amount is None or amount < 0:
                st.error("Please enter a planned amount of 0 or more.")
            elif category not in ALLOCATION_TYPES:
                st.error("Please choose where this money should go.")
            elif needs_target and target_id not in targets:
                st.error("Please choose a saved fund or investment for this allocation.")
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
            st.error("We couldn't confirm that the allocation was saved. Check the list before trying again.")
            if st.button("Reload allocations", key=prefix + "allocation_reload"):
                st.session_state.pop(prefix + "allocation_uncertain", None)
                st.rerun()
        if st.button("Cancel" if items else "Plan allocations later", key=prefix + "allocation_cancel"):
            st.session_state[prefix + "allocation_open"] = False
            st.rerun()


def render_monthly_plan_step(user_id):
    user_prefix = f"onboarding_{user_id}_"
    today = date.today()
    # Keep the chosen month stable if setup crosses a month boundary.
    year, month = st.session_state.setdefault(user_prefix + "plan_month", (today.year, today.month))
    prefix = user_prefix + f"plan_{year}_{month}_"

    st.title("Give this month's money a job.")
    st.write("Start with your expected income, then decide how much you want to keep for living costs, saving and investing.")
    st.caption(f"Plan for {date(year, month, 1).strftime('%B %Y')}")
    _render_explanation()

    try:
        plan = get_monthly_plan(user_id, year, month)
        items = get_plan_items(user_id, plan.id) if plan is not None else []
        funds = get_funds(user_id) if plan is not None else []
        assets = get_assets(user_id) if plan is not None else []
    except Exception:
        st.error("We couldn't load your monthly plan. Please try again.")
        if st.button("Retry", key=prefix + "retry"):
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
            st.metric("Expected income", f"€{plan.planned_income:,.2f}")
        with allocated_col:
            st.metric("Planned allocations", f"€{allocated:,.2f}")
        with remaining_col:
            st.metric("Unallocated", f"€{remaining:,.2f}")
        if remaining < 0:
            st.warning(f"You have planned €{abs(remaining):,.2f} more than your expected income.")
        elif remaining > 0:
            st.caption("You can leave some income unallocated and decide later.")
        else:
            st.caption("Every euro of your expected income has a purpose.")

        if st.session_state.pop(prefix + "allocation_saved", False):
            st.success("Allocation saved to your plan. No contribution has been recorded.")
        if items:
            st.subheader("Your allocations")
            for item in items:
                with st.container(border=True):
                    st.text(item.name)
                    st.caption(f"{item.planned_amount:,.2f} EUR planned · {ALLOCATION_TYPES.get(item.category_type, 'Allocation')}")
                    if item.category_type == "FUND":
                        st.text(f"Fund: {funds_by_id.get(item.fund_id, 'Not available')}")
                    elif item.category_type == "INVESTMENT":
                        st.text(f"Investment: {investments_by_id.get(item.asset_id, 'Not available')}")

        if st.session_state.get(prefix + "allocation_open", not items):
            _render_allocation_form(user_id, prefix, plan, items, funds_by_id, investments_by_id)
        else:
            if st.button("See my financial picture", type="primary", key=prefix + "finish"):
                st.session_state[user_prefix + "step"] = "financial_picture"
                st.rerun()
            if st.button("Add another allocation" if items else "Add allocation", key=prefix + "another"):
                st.session_state[prefix + "allocation_open"] = True
                st.rerun()
        if st.button("Change expected income", key=prefix + "edit_income_button"):
            st.session_state[prefix + "edit_income"] = True
            st.rerun()

    if st.button("Back to Funds", key=prefix + "back"):
        st.session_state[user_prefix + "step"] = "funds"
        st.rerun()
