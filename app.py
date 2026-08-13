import streamlit as st
from datetime import date

from accounts import (
    get_accounts,
    add_account,
    update_account,
    delete_account
)

from assets import (
    get_assets,
    add_asset,
    update_asset,
    delete_asset
)

from debts import (
    get_debts,
    add_debt,
    update_debt,
    delete_debt
)

from funds import (
    get_funds,
    add_fund,
    update_fund,
    delete_fund
)

from monthly_plans import (
    get_monthly_plan,
    create_monthly_plan,
    update_planned_income
)

from monthly_plan_items import (
    get_plan_items,
    add_plan_item,
    update_plan_item,
    delete_plan_item
)

from transactions import (
    get_transactions_for_item,
    add_fund_contribution,
    update_fund_contribution,
    delete_fund_contribution,
    add_investment_contribution,
    update_investment_contribution,
    delete_investment_contribution
)

from feedback import (
    add_feedback,
    get_user_feedback
)

from calculations import calculate_financial_summary
from users import get_or_create_user

from user_data import delete_all_user_data


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="My Finance App",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# AUTHENTICATION
# =========================================================

if not st.user.is_logged_in:

    st.title("💰 My Finance App")

    st.write(
        "Sign in to access your private financial dashboard."
    )

    if st.button("Log in with Google"):
        st.login()

    st.stop()


# =========================================================
# DATABASE USER
# =========================================================

current_user = get_or_create_user(
    email=st.user.email,
    name=st.user.get("name")
)

CURRENT_USER_ID = current_user.id


# =========================================================
# MAIN APP HEADER
# =========================================================

st.title("💰 My Finance App")
st.write("Personal finance dashboard")

st.sidebar.write(
    f"Signed in as {current_user.email}"
)

if st.sidebar.button("Log out"):
    st.logout()


# =========================================================
# 3. READ ALL EXISTING DATA FIRST
# =========================================================

# -----------------------------
# ACCOUNTS
# -----------------------------

accounts = get_accounts(CURRENT_USER_ID)


# -----------------------------
# ASSETS
# -----------------------------

assets = get_assets(CURRENT_USER_ID)


# -----------------------------
# DEBTS
# -----------------------------

debts = get_debts(CURRENT_USER_ID)

# -----------------------------
# FUNDS
# -----------------------------

funds = get_funds(CURRENT_USER_ID)

# =========================================================
# 4. CALCULATIONS
# =========================================================

available_cash = sum(
    account.balance
    for account in accounts
)

liquid_investments = sum(
    asset.current_value
    for asset in assets
    if asset.liquidity_class == "LIQUID_INVESTMENT"
)

semi_liquid_assets = sum(
    asset.current_value
    for asset in assets
    if asset.liquidity_class == "SEMI_LIQUID"
)

non_liquid_assets = sum(
    asset.current_value
    for asset in assets
    if asset.liquidity_class == "NON_LIQUID"
)

all_assets_value = sum(
    asset.current_value
    for asset in assets
)

total_debt = sum(
    debt.remaining_balance
    for debt in debts
)

total_reserved_funds = sum(
    fund.current_balance
    for fund in funds
)

free_cash = available_cash - total_reserved_funds

liquid_worth = (
    available_cash
    + liquid_investments
)

net_worth = (
    available_cash
    + all_assets_value
    - total_debt
)


# =========================================================
# 5. FINANCIAL SUMMARY
# =========================================================

st.divider()
st.subheader("Financial Summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Available Cash",
        f"€{available_cash:,.2f}"
    )

with col2:
    st.metric(
        "Reserved Funds",
        f"€{total_reserved_funds:,.2f}"
    )

with col3:
    st.metric(
        "Free Cash",
        f"€{free_cash:,.2f}"
    )

with col4:
    st.metric(
        "Liquid Worth",
        f"€{liquid_worth:,.2f}"
    )

with col5:
    st.metric(
        "Total Debt",
        f"€{total_debt:,.2f}"
    )

with col6:
    st.metric(
        "Net Worth",
        f"€{net_worth:,.2f}"
    )


st.caption(
    "Available Cash = bank accounts + cash. "
    "Liquid Worth = available cash + liquid investments. "
    "Virtual funds do not increase net worth."
)


# =========================================================
# 6. ACCOUNTS
# =========================================================

st.divider()
st.header("🏦 Accounts")

st.subheader("Add account")

with st.form("add_account_form"):

    account_name = st.text_input(
        "Account name"
    )

    account_type = st.selectbox(
        "Account type",
        [
            "BANK",
            "CASH"
        ]
    )

    balance = st.number_input(
        "Current balance (€)",
        min_value=0.0,
        step=100.0
    )

    account_submitted = st.form_submit_button(
        "Save account"
    )


if account_submitted:

    if account_name.strip() == "":
        st.error("Please enter an account name.")

    else:
        add_account(
            CURRENT_USER_ID,
            account_name,
            account_type,
            balance
        )

        st.success("Account saved.")
        st.rerun()


st.subheader("Your accounts")

if len(accounts) == 0:

    st.info("No accounts added yet.")

else:

    for account in accounts:

        with st.expander(
            f"{account.name} — €{account.balance:,.2f}"
        ):

            new_account_name = st.text_input(
                "Account name",
                value=account.name,
                key=f"account_name_{account.id}"
            )

            account_type_options = [
                "BANK",
                "CASH"
            ]

            new_account_type = st.selectbox(
                "Account type",
                account_type_options,
                index=account_type_options.index(
                    account.account_type
                ),
                key=f"account_type_{account.id}"
            )

            new_balance = st.number_input(
                "Balance (€)",
                min_value=0.0,
                value=float(account.balance),
                step=100.0,
                key=f"account_balance_{account.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Save changes",
                    key=f"save_account_{account.id}"
                ):

                    update_account(
                        CURRENT_USER_ID,
                        account.id,
                        new_account_name,
                        new_account_type,
                        new_balance
                    )

                    st.success("Account updated.")
                    st.rerun()

            with col2:

                if st.button(
                    "Delete account",
                    key=f"delete_account_{account.id}"
                ):

                    delete_account(
                        CURRENT_USER_ID,
                        account.id
                    )

                    st.success("Account deleted.")
                    st.rerun()


# =========================================================
# 7. ASSETS
# =========================================================

st.divider()
st.header("📈 Assets")

st.subheader("Add asset")

with st.form("add_asset_form"):

    asset_name = st.text_input(
        "Asset name"
    )

    asset_type = st.selectbox(
        "Asset type",
        [
            "INVESTMENT",
            "REAL_ESTATE",
            "CAR",
            "PRIVATE_PROJECT",
            "MONEY_OWED_TO_ME",
            "OTHER"
        ]
    )

    liquidity_class = st.selectbox(
        "Liquidity class",
        [
            "LIQUID_INVESTMENT",
            "SEMI_LIQUID",
            "NON_LIQUID"
        ]
    )

    asset_value = st.number_input(
        "Current value (€)",
        min_value=0.0,
        step=100.0
    )

    asset_submitted = st.form_submit_button(
        "Save asset"
    )


if asset_submitted:

    if asset_name.strip() == "":
        st.error("Please enter an asset name.")

    else:
        add_asset(
            CURRENT_USER_ID,
            asset_name,
            asset_type,
            liquidity_class,
            asset_value
        )

        st.success("Asset saved.")
        st.rerun()


st.subheader("Your assets")

if len(assets) == 0:

    st.info("No assets added yet.")

else:

    for asset in assets:

        with st.expander(
            f"{asset.name} — €{asset.current_value:,.2f}"
        ):

            new_asset_name = st.text_input(
                "Asset name",
                value=asset.name,
                key=f"asset_name_{asset.id}"
            )

            asset_type_options = [
                "INVESTMENT",
                "REAL_ESTATE",
                "CAR",
                "PRIVATE_PROJECT",
                "MONEY_OWED_TO_ME",
                "OTHER"
            ]

            new_asset_type = st.selectbox(
                "Asset type",
                asset_type_options,
                index=asset_type_options.index(
                    asset.asset_type
                ),
                key=f"asset_type_{asset.id}"
            )

            liquidity_options = [
                "LIQUID_INVESTMENT",
                "SEMI_LIQUID",
                "NON_LIQUID"
            ]

            new_liquidity = st.selectbox(
                "Liquidity class",
                liquidity_options,
                index=liquidity_options.index(
                    asset.liquidity_class
                ),
                key=f"asset_liquidity_{asset.id}"
            )

            new_asset_value = st.number_input(
                "Current value (€)",
                min_value=0.0,
                value=float(asset.current_value),
                step=100.0,
                key=f"asset_value_{asset.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Save asset changes",
                    key=f"save_asset_{asset.id}"
                ):

                    update_asset(
                        CURRENT_USER_ID,
                        asset.id,
                        new_asset_name,
                        new_asset_type,
                        new_liquidity,
                        new_asset_value
                    )

                    st.success("Asset updated.")
                    st.rerun()

            with col2:

                if st.button(
                    "Delete asset",
                    key=f"delete_asset_{asset.id}"
                ):

                    delete_asset(
                        CURRENT_USER_ID,
                        asset.id
                    )

                    st.success("Asset deleted.")
                    st.rerun()


# =========================================================
# 8. DEBTS
# =========================================================

st.divider()
st.header("💳 Debts")

st.subheader("Add debt")

with st.form("add_debt_form"):

    debt_name = st.text_input(
        "Debt name"
    )

    debt_type = st.selectbox(
        "Debt type",
        [
            "MORTGAGE",
            "CAR_LOAN",
            "PERSONAL_LOAN",
            "CREDIT_CARD",
            "OTHER"
        ]
    )

    remaining_balance = st.number_input(
        "Remaining balance (€)",
        min_value=0.0,
        step=100.0
    )

    monthly_payment = st.number_input(
        "Monthly payment (€)",
        min_value=0.0,
        step=50.0
    )

    interest_rate = st.number_input(
        "Interest rate (%)",
        min_value=0.0,
        step=0.1
    )

    debt_submitted = st.form_submit_button(
        "Save debt"
    )


if debt_submitted:

    if debt_name.strip() == "":
        st.error("Please enter a debt name.")

    else:
        add_debt(
            CURRENT_USER_ID,
            debt_name,
            debt_type,
            remaining_balance,
            monthly_payment,
            interest_rate
        )

        st.success("Debt saved.")
        st.rerun()


st.subheader("Your debts")

if len(debts) == 0:

    st.info("No debts added yet.")

else:

    for debt in debts:

        with st.expander(
            f"{debt.name} — €{debt.remaining_balance:,.2f}"
        ):

            new_debt_name = st.text_input(
                "Debt name",
                value=debt.name,
                key=f"debt_name_{debt.id}"
            )

            debt_type_options = [
                "MORTGAGE",
                "CAR_LOAN",
                "PERSONAL_LOAN",
                "CREDIT_CARD",
                "OTHER"
            ]

            new_debt_type = st.selectbox(
                "Debt type",
                debt_type_options,
                index=debt_type_options.index(
                    debt.debt_type
                ),
                key=f"debt_type_{debt.id}"
            )

            new_remaining_balance = st.number_input(
                "Remaining balance (€)",
                min_value=0.0,
                value=float(debt.remaining_balance),
                step=100.0,
                key=f"debt_balance_{debt.id}"
            )

            new_monthly_payment = st.number_input(
                "Monthly payment (€)",
                min_value=0.0,
                value=float(debt.monthly_payment),
                step=50.0,
                key=f"debt_payment_{debt.id}"
            )

            new_interest_rate = st.number_input(
                "Interest rate (%)",
                min_value=0.0,
                value=float(debt.interest_rate),
                step=0.1,
                key=f"debt_interest_{debt.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Save debt changes",
                    key=f"save_debt_{debt.id}"
                ):

                    update_debt(
                        CURRENT_USER_ID,
                        debt.id,
                        new_debt_name,
                        new_debt_type,
                        new_remaining_balance,
                        new_monthly_payment,
                        new_interest_rate
                    )

                    st.success("Debt updated.")
                    st.rerun()

            with col2:

                if st.button(
                    "Delete debt",
                    key=f"delete_debt_{debt.id}"
                ):

                    delete_debt(
                        CURRENT_USER_ID,
                        debt.id
                    )

                    st.success("Debt deleted.")
                    st.rerun()


# =========================================================
# 9. VIRTUAL FUNDS
# =========================================================

st.divider()
st.header("🎯 Virtual Funds")

st.write(
    "Funds are allocations of money that already exists in your bank "
    "accounts or cash. They do not increase your net worth."
)


# -----------------------------
# ADD NEW FUND
# -----------------------------

with st.form("add_fund_form"):

    fund_name = st.text_input(
        "Fund name"
    )

    fund_balance = st.number_input(
        "Current reserved amount (€)",
        min_value=0.0,
        step=100.0
    )

    fund_target = st.number_input(
        "Target amount (€)",
        min_value=0.0,
        step=100.0
    )

    fund_submitted = st.form_submit_button(
        "Save fund"
    )


# -----------------------------
# SAVE NEW FUND
# -----------------------------

if fund_submitted:

    if fund_name.strip() == "":
        st.error("Please enter a fund name.")

    elif fund_balance > float(available_cash):
        st.warning(
            "Reserved amount is higher than your available cash. "
            "Please check the amount."
        )

    else:

        add_fund(
            CURRENT_USER_ID,
            fund_name,
            fund_balance,
            fund_target
        )

        st.success("Fund saved.")
        st.rerun()


# -----------------------------
# SHOW EXISTING FUNDS
# -----------------------------

st.subheader("Your funds")

if len(funds) == 0:

    st.info("No virtual funds added yet.")

else:

    for fund in funds:

        balance = float(fund.current_balance)

        target = (
            float(fund.target_amount)
            if fund.target_amount is not None
            else 0.0
        )

        with st.expander(
            f"{fund.name} — €{balance:,.2f}"
        ):

            # -----------------------------
            # EDIT FUND NAME
            # -----------------------------

            new_fund_name = st.text_input(
                "Fund name",
                value=fund.name,
                key=f"fund_name_{fund.id}"
            )

            # -----------------------------
            # EDIT FUND BALANCE
            # -----------------------------

            new_fund_balance = st.number_input(
                "Reserved amount (€)",
                min_value=0.0,
                value=balance,
                step=100.0,
                key=f"fund_balance_{fund.id}"
            )

            # -----------------------------
            # EDIT FUND TARGET
            # -----------------------------

            new_fund_target = st.number_input(
                "Target amount (€)",
                min_value=0.0,
                value=target,
                step=100.0,
                key=f"fund_target_{fund.id}"
            )

            # -----------------------------
            # FUND PROGRESS
            # -----------------------------

            if target > 0:

                raw_progress = balance / target

                display_progress = min(
                    raw_progress,
                    1.0
                )

                st.progress(display_progress)

                st.write(
                    f"{raw_progress * 100:.1f}% of target"
                )

            # -----------------------------
            # SAVE / DELETE BUTTONS
            # -----------------------------

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Save fund changes",
                    key=f"save_fund_{fund.id}"
                ):

                    update_fund(
                        CURRENT_USER_ID,
                        fund.id,
                        new_fund_name,
                        new_fund_balance,
                        new_fund_target
                    )

                    st.success("Fund updated.")
                    st.rerun()

            with col2:

                if st.button(
                    "Delete fund",
                    key=f"delete_fund_{fund.id}"
                ):

                    delete_fund(
                        CURRENT_USER_ID,
                        fund.id
                    )

                    st.success("Fund deleted.")
                    st.rerun()


# =========================================================
# 10. MONTHLY PLAN
# =========================================================

st.divider()
st.header("📅 Monthly Plan")

today = date.today()


# =========================================================
# SELECT MONTH
# =========================================================

month_col1, month_col2 = st.columns(2)

with month_col1:

    selected_year = st.number_input(
        "Year",
        min_value=2020,
        max_value=2100,
        value=today.year,
        step=1
    )

with month_col2:

    selected_month = st.selectbox(
        "Month",
        options=list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda month: date(
            2000,
            month,
            1
        ).strftime("%B")
    )


# =========================================================
# GET MONTHLY PLAN
# =========================================================

monthly_plan = get_monthly_plan(
    CURRENT_USER_ID,
    selected_year,
    selected_month
)


# =========================================================
# CREATE MONTHLY PLAN
# =========================================================

if monthly_plan is None:

    st.info(
        "No monthly plan exists for this month yet."
    )

    with st.form("create_monthly_plan_form"):

        planned_income = st.number_input(
            "Planned monthly income (€)",
            min_value=0.0,
            step=100.0
        )

        create_plan_submitted = (
            st.form_submit_button(
                "Create monthly plan"
            )
        )

    if create_plan_submitted:

        create_monthly_plan(
            CURRENT_USER_ID,
            selected_year,
            selected_month,
            planned_income
        )

        st.success(
            "Monthly plan created."
        )

        st.rerun()


# =========================================================
# MONTHLY PLAN EXISTS
# =========================================================

else:

    st.success(
        f"Monthly plan status: {monthly_plan.status}"
    )

    # =====================================================
    # INCOME
    # =====================================================

    st.subheader("Income Plan")

    planned_income_value = float(
        monthly_plan.planned_income
    )

    new_planned_income = st.number_input(
        "Planned monthly income (€)",
        min_value=0.0,
        value=planned_income_value,
        step=100.0,
        key="planned_income_value"
    )

    if st.button(
        "Save planned income",
        key="save_planned_income"
    ):

        update_planned_income(
            CURRENT_USER_ID,
            monthly_plan.id,
            new_planned_income
        )

        st.success(
            "Planned income updated."
        )

        st.rerun()

    # =====================================================
    # GET ALLOCATIONS
    # =====================================================

    st.divider()
    st.subheader("Monthly Allocation")

    plan_items = get_plan_items(
        CURRENT_USER_ID,
        monthly_plan.id
    )

    # =====================================================
    # GET TRANSACTIONS
    # =====================================================

    transactions_by_item = {}

    for item in plan_items:

        transactions_by_item[item.id] = (
            get_transactions_for_item(
                CURRENT_USER_ID,
                item.id
            )
        )

    # =====================================================
    # MONTH TOTALS
    # =====================================================

    total_planned_allocation = sum(
        float(item.planned_amount)
        for item in plan_items
    )

    remaining_to_allocate = (
        planned_income_value
        - total_planned_allocation
    )

    total_actual_allocation = 0.0

    for item in plan_items:

        item_transactions = (
            transactions_by_item[item.id]
        )

        if item.category_type == "FUND":

            actual_value = sum(
                float(transaction.amount)
                for transaction in item_transactions
                if transaction.transaction_type
                == "FUND_CONTRIBUTION"
            )

        elif item.category_type == "INVESTMENT":

            actual_value = sum(
                float(transaction.amount)
                for transaction in item_transactions
                if transaction.transaction_type
                == "INVESTMENT_CONTRIBUTION"
            )

        else:

            actual_value = float(
                item.actual_amount
            )

        total_actual_allocation += actual_value

    # =====================================================
    # SUMMARY
    # =====================================================

    summary_col1, summary_col2, summary_col3, summary_col4 = (
        st.columns(4)
    )

    with summary_col1:

        st.metric(
            "Planned Income",
            f"€{planned_income_value:,.2f}"
        )

    with summary_col2:

        st.metric(
            "Planned Allocation",
            f"€{total_planned_allocation:,.2f}"
        )

    with summary_col3:

        st.metric(
            "Remaining",
            f"€{remaining_to_allocate:,.2f}"
        )

    with summary_col4:

        st.metric(
            "Actual So Far",
            f"€{total_actual_allocation:,.2f}"
        )

    if remaining_to_allocate < 0:

        st.warning(
            f"You planned €{abs(remaining_to_allocate):,.2f} "
            "more than your planned income."
        )

    elif remaining_to_allocate == 0:

        st.success(
            "Your planned income is fully allocated."
        )

    else:

        st.info(
            f"You still have €{remaining_to_allocate:,.2f} "
            "left to allocate."
        )

    # =====================================================
    # ADD ALLOCATION
    # =====================================================

    st.divider()
    st.subheader("Add Allocation")

    plan_item_name = st.text_input(
        "Allocation name",
        key="new_plan_item_name"
    )

    plan_item_type = st.selectbox(
        "Allocation type",
        [
            "EXPENSE",
            "FUND",
            "INVESTMENT",
            "DEBT_PAYMENT",
            "OTHER"
        ],
        key="new_plan_item_type"
    )

    # -----------------------------------------------------
    # LINK FUND
    # -----------------------------------------------------

    linked_fund_id = None

    if plan_item_type == "FUND":

        if len(funds) == 0:

            st.warning(
                "Create a virtual fund first."
            )

        else:

            linked_fund_id = st.selectbox(
                "Linked virtual fund",
                options=[
                    fund.id
                    for fund in funds
                ],
                format_func=lambda fund_id: next(
                    fund.name
                    for fund in funds
                    if fund.id == fund_id
                ),
                key="new_linked_fund"
            )

    # -----------------------------------------------------
    # LINK INVESTMENT ASSET
    # -----------------------------------------------------

    linked_asset_id = None

    if plan_item_type == "INVESTMENT":

        investment_assets = [
            asset
            for asset in assets
            if asset.asset_type == "INVESTMENT"
        ]

        if len(investment_assets) == 0:

            st.warning(
                "Create an investment asset first."
            )

        else:

            linked_asset_id = st.selectbox(
                "Linked investment",
                options=[
                    asset.id
                    for asset in investment_assets
                ],
                format_func=lambda asset_id: next(
                    asset.name
                    for asset in investment_assets
                    if asset.id == asset_id
                ),
                key="new_linked_asset"
            )

    plan_item_amount = st.number_input(
        "Planned amount (€)",
        min_value=0.0,
        step=50.0,
        key="new_plan_item_amount"
    )

    if st.button(
        "Add allocation",
        key="add_new_allocation"
    ):

        if plan_item_name.strip() == "":

            st.error(
                "Please enter an allocation name."
            )

        elif (
            plan_item_type == "FUND"
            and linked_fund_id is None
        ):

            st.error(
                "Please select a virtual fund."
            )

        elif (
            plan_item_type == "INVESTMENT"
            and linked_asset_id is None
        ):

            st.error(
                "Please select an investment asset."
            )

        else:

            add_plan_item(
                CURRENT_USER_ID,
                monthly_plan.id,
                plan_item_name,
                plan_item_type,
                plan_item_amount,
                linked_fund_id,
                linked_asset_id
            )

            st.success(
                "Allocation added."
            )

            st.rerun()

    # =====================================================
    # EXISTING ALLOCATIONS
    # =====================================================

    st.divider()
    st.subheader("Your Allocation Plan")

    if len(plan_items) == 0:

        st.info(
            "No allocations added yet."
        )

    else:

        for item in plan_items:

            item_planned = float(
                item.planned_amount
            )

            stored_actual = float(
                item.actual_amount
            )

            item_transactions = (
                transactions_by_item[item.id]
            )

            # -------------------------------------------------
            # PERCENTAGE
            # -------------------------------------------------

            percentage = 0.0

            if planned_income_value > 0:

                percentage = (
                    item_planned
                    / planned_income_value
                    * 100
                )

            # -------------------------------------------------
            # FUND TRANSACTIONS
            # -------------------------------------------------

            fund_transactions = [
                transaction
                for transaction in item_transactions
                if transaction.transaction_type
                == "FUND_CONTRIBUTION"
            ]

            actual_fund_contributed = sum(
                float(transaction.amount)
                for transaction in fund_transactions
            )

            # -------------------------------------------------
            # INVESTMENT TRANSACTIONS
            # -------------------------------------------------

            investment_transactions = [
                transaction
                for transaction in item_transactions
                if transaction.transaction_type
                == "INVESTMENT_CONTRIBUTION"
            ]

            actual_invested = sum(
                float(transaction.amount)
                for transaction
                in investment_transactions
            )

            # -------------------------------------------------
            # ACTUAL VALUE
            # -------------------------------------------------

            if item.category_type == "FUND":

                item_actual = (
                    actual_fund_contributed
                )

            elif item.category_type == "INVESTMENT":

                item_actual = (
                    actual_invested
                )

            else:

                item_actual = stored_actual

            # =================================================
            # ALLOCATION EXPANDER
            # =================================================

            with st.expander(
                f"{item.name} — "
                f"€{item_planned:,.2f} "
                f"({percentage:.1f}%)"
            ):

                # -------------------------------------------------
                # EDIT NAME
                # -------------------------------------------------

                new_item_name = st.text_input(
                    "Name",
                    value=item.name,
                    key=f"plan_item_name_{item.id}"
                )

                # -------------------------------------------------
                # EDIT TYPE
                # -------------------------------------------------

                item_type_options = [
                    "EXPENSE",
                    "FUND",
                    "INVESTMENT",
                    "DEBT_PAYMENT",
                    "OTHER"
                ]

                new_item_type = st.selectbox(
                    "Type",
                    item_type_options,
                    index=item_type_options.index(
                        item.category_type
                    ),
                    key=f"plan_item_type_{item.id}"
                )

                # -------------------------------------------------
                # EDIT LINKED FUND
                # -------------------------------------------------

                new_linked_fund_id = item.fund_id

                if new_item_type == "FUND":

                    if len(funds) == 0:

                        st.warning(
                            "Create a virtual fund first."
                        )

                    else:

                        fund_ids = [
                            fund.id
                            for fund in funds
                        ]

                        default_fund_index = 0

                        if item.fund_id in fund_ids:

                            default_fund_index = (
                                fund_ids.index(
                                    item.fund_id
                                )
                            )

                        new_linked_fund_id = st.selectbox(
                            "Linked virtual fund",
                            options=fund_ids,
                            index=default_fund_index,
                            format_func=lambda fund_id: next(
                                fund.name
                                for fund in funds
                                if fund.id == fund_id
                            ),
                            key=f"linked_fund_{item.id}"
                        )

                else:

                    new_linked_fund_id = None

                # -------------------------------------------------
                # EDIT LINKED INVESTMENT
                # -------------------------------------------------

                new_linked_asset_id = item.asset_id

                if new_item_type == "INVESTMENT":

                    investment_assets = [
                        asset
                        for asset in assets
                        if asset.asset_type == "INVESTMENT"
                    ]

                    if len(investment_assets) == 0:

                        st.warning(
                            "Create an investment asset first."
                        )

                    else:

                        investment_asset_ids = [
                            asset.id
                            for asset in investment_assets
                        ]

                        default_asset_index = 0

                        if (
                            item.asset_id
                            in investment_asset_ids
                        ):

                            default_asset_index = (
                                investment_asset_ids.index(
                                    item.asset_id
                                )
                            )

                        new_linked_asset_id = st.selectbox(
                            "Linked investment",
                            options=investment_asset_ids,
                            index=default_asset_index,
                            format_func=lambda asset_id: next(
                                asset.name
                                for asset in investment_assets
                                if asset.id == asset_id
                            ),
                            key=f"linked_asset_{item.id}"
                        )

                else:

                    new_linked_asset_id = None

                # -------------------------------------------------
                # PLANNED AMOUNT
                # -------------------------------------------------

                new_planned_amount = st.number_input(
                    "Planned amount (€)",
                    min_value=0.0,
                    value=item_planned,
                    step=50.0,
                    key=f"plan_item_planned_{item.id}"
                )

                # -------------------------------------------------
                # ACTUAL AMOUNT
                # -------------------------------------------------

                if item.category_type in [
                    "FUND",
                    "INVESTMENT"
                ]:

                    st.metric(
                        "Actual amount",
                        f"€{item_actual:,.2f}"
                    )

                    st.caption(
                        "Actual amount is calculated "
                        "from recorded transactions."
                    )

                else:

                    new_actual_amount = st.number_input(
                        "Actual amount (€)",
                        min_value=0.0,
                        value=stored_actual,
                        step=50.0,
                        key=f"plan_item_actual_{item.id}"
                    )

                # -------------------------------------------------
                # VARIANCE
                # -------------------------------------------------

                variance = (
                    item_actual
                    - new_planned_amount
                )

                if variance > 0:

                    st.warning(
                        f"€{variance:,.2f} above plan"
                    )

                elif variance < 0:

                    st.info(
                        f"€{abs(variance):,.2f} below plan"
                    )

                else:

                    st.success(
                        "Actual amount matches the plan."
                    )

                # =================================================
                # SAVE / DELETE ALLOCATION
                # =================================================

                allocation_col1, allocation_col2 = (
                    st.columns(2)
                )

                with allocation_col1:

                    if st.button(
                        "Save allocation",
                        key=f"save_plan_item_{item.id}"
                    ):

                        if (
                            new_item_type == "FUND"
                            and new_linked_fund_id is None
                        ):

                            st.error(
                                "Select a virtual fund."
                            )

                        elif (
                            new_item_type == "INVESTMENT"
                            and new_linked_asset_id is None
                        ):

                            st.error(
                                "Select an investment asset."
                            )

                        else:

                            if item.category_type in [
                                "FUND",
                                "INVESTMENT"
                            ]:

                                actual_value_to_save = (
                                    stored_actual
                                )

                            else:

                                actual_value_to_save = (
                                    new_actual_amount
                                )

                            update_plan_item(
                                CURRENT_USER_ID,
                                item.id,
                                new_item_name,
                                new_item_type,
                                new_planned_amount,
                                actual_value_to_save,
                                new_linked_fund_id,
                                new_linked_asset_id
                            )

                            st.success(
                                "Allocation updated."
                            )

                            st.rerun()

                with allocation_col2:

                    if st.button(
                        "Delete allocation",
                        key=f"delete_plan_item_{item.id}"
                    ):

                        delete_plan_item(
                            CURRENT_USER_ID,
                            item.id
                        )

                        st.success(
                            "Allocation deleted."
                        )

                        st.rerun()

                # =================================================
                # FUND CONTRIBUTION
                # =================================================

                if item.category_type == "FUND":

                    st.divider()

                    st.subheader(
                        "Actual Fund Contribution"
                    )

                    if item.fund_id is None:

                        st.warning(
                            "This allocation is not linked "
                            "to a virtual fund."
                        )

                    else:

                        linked_fund = next(
                            (
                                fund
                                for fund in funds
                                if fund.id == item.fund_id
                            ),
                            None
                        )

                        if linked_fund is None:

                            st.error(
                                "Linked virtual fund "
                                "was not found."
                            )

                        else:

                            st.info(
                                f"🎯 {linked_fund.name}"
                            )

                            fund_col1, fund_col2 = (
                                st.columns(2)
                            )

                            with fund_col1:

                                st.metric(
                                    "Planned",
                                    f"€{item_planned:,.2f}"
                                )

                            with fund_col2:

                                st.metric(
                                    "Actual",
                                    f"€{actual_fund_contributed:,.2f}"
                                )

                            with st.form(
                                f"fund_contribution_form_{item.id}"
                            ):

                                contribution_amount = (
                                    st.number_input(
                                        "Actual contribution (€)",
                                        min_value=0.01,
                                        step=50.0,
                                        key=(
                                            "fund_contribution_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                contribution_description = (
                                    st.text_input(
                                        "Description",
                                        key=(
                                            "fund_description_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                contribution_submitted = (
                                    st.form_submit_button(
                                        "Record contribution"
                                    )
                                )

                            if contribution_submitted:

                                add_fund_contribution(
                                    CURRENT_USER_ID,
                                    monthly_plan.id,
                                    item.id,
                                    item.fund_id,
                                    contribution_amount,
                                    contribution_description
                                )

                                st.success(
                                    "Fund contribution recorded."
                                )

                                st.rerun()

                            # -----------------------------------------
                            # FUND HISTORY
                            # -----------------------------------------

                            if len(fund_transactions) > 0:

                                st.write(
                                    "#### Contribution History"
                                )

                            for transaction in fund_transactions:

                                transaction_amount = float(
                                    transaction.amount
                                )

                                transaction_date = (
                                    transaction.created_at.strftime(
                                        "%Y-%m-%d"
                                    )
                                )

                                with st.expander(
                                    f"€{transaction_amount:,.2f} "
                                    f"— {transaction_date}"
                                ):

                                    edited_amount = (
                                        st.number_input(
                                            "Amount (€)",
                                            min_value=0.01,
                                            value=transaction_amount,
                                            step=50.0,
                                            key=(
                                                "fund_edit_amount_"
                                                f"{transaction.id}"
                                            )
                                        )
                                    )

                                    edited_description = (
                                        st.text_input(
                                            "Description",
                                            value=(
                                                transaction.description
                                                or ""
                                            ),
                                            key=(
                                                "fund_edit_description_"
                                                f"{transaction.id}"
                                            )
                                        )
                                    )

                                    edit_col, delete_col = (
                                        st.columns(2)
                                    )

                                    with edit_col:

                                        if st.button(
                                            "Save contribution",
                                            key=(
                                                "fund_save_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            update_fund_contribution(
                                                CURRENT_USER_ID,
                                                transaction.id,
                                                item.fund_id,
                                                edited_amount,
                                                edited_description
                                            )

                                            st.rerun()

                                    with delete_col:

                                        if st.button(
                                            "Delete contribution",
                                            key=(
                                                "fund_delete_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            delete_fund_contribution(
                                                CURRENT_USER_ID,
                                                transaction.id
                                            )

                                            st.rerun()

                # =================================================
                # INVESTMENT CONTRIBUTION
                # =================================================

                if item.category_type == "INVESTMENT":

                    st.divider()

                    st.subheader(
                        "Actual Investment Contribution"
                    )

                    if item.asset_id is None:

                        st.warning(
                            "This allocation is not linked "
                            "to an investment asset."
                        )

                    else:

                        linked_asset = next(
                            (
                                asset
                                for asset in assets
                                if asset.id == item.asset_id
                            ),
                            None
                        )

                        if linked_asset is None:

                            st.error(
                                "Linked investment asset "
                                "was not found."
                            )

                        else:

                            st.info(
                                f"📈 {linked_asset.name}"
                            )

                            investment_col1, investment_col2 = (
                                st.columns(2)
                            )

                            with investment_col1:

                                st.metric(
                                    "Planned",
                                    f"€{item_planned:,.2f}"
                                )

                            with investment_col2:

                                st.metric(
                                    "Actual",
                                    f"€{actual_invested:,.2f}"
                                )

                            # -----------------------------------------
                            # ADD INVESTMENT
                            # -----------------------------------------

                            with st.form(
                                f"investment_form_{item.id}"
                            ):

                                investment_amount = (
                                    st.number_input(
                                        "Actual investment (€)",
                                        min_value=0.01,
                                        step=50.0,
                                        key=(
                                            "investment_amount_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                investment_description = (
                                    st.text_input(
                                        "Description",
                                        key=(
                                            "investment_description_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                investment_submitted = (
                                    st.form_submit_button(
                                        "Record investment"
                                    )
                                )

                            if investment_submitted:

                                add_investment_contribution(
                                    CURRENT_USER_ID,
                                    monthly_plan.id,
                                    item.id,
                                    item.asset_id,
                                    investment_amount,
                                    investment_description
                                )

                                st.success(
                                    f"€{investment_amount:,.2f} "
                                    f"added to "
                                    f"{linked_asset.name}."
                                )

                                st.rerun()

                            # -----------------------------------------
                            # INVESTMENT HISTORY
                            # -----------------------------------------

                            if len(
                                investment_transactions
                            ) > 0:

                                st.write(
                                    "#### Investment History"
                                )

                            for transaction in investment_transactions:

                                transaction_amount = float(
                                    transaction.amount
                                )

                                transaction_date = (
                                    transaction.created_at.strftime(
                                        "%Y-%m-%d"
                                    )
                                )

                                with st.expander(
                                    f"€{transaction_amount:,.2f} "
                                    f"— {transaction_date}"
                                ):

                                    edited_investment_amount = (
                                        st.number_input(
                                            "Amount (€)",
                                            min_value=0.01,
                                            value=transaction_amount,
                                            step=50.0,
                                            key=(
                                                "investment_edit_amount_"
                                                f"{transaction.id}"
                                            )
                                        )
                                    )

                                    edited_investment_description = (
                                        st.text_input(
                                            "Description",
                                            value=(
                                                transaction.description
                                                or ""
                                            ),
                                            key=(
                                                "investment_edit_description_"
                                                f"{transaction.id}"
                                            )
                                        )
                                    )

                                    investment_edit_col, investment_delete_col = (
                                        st.columns(2)
                                    )

                                    with investment_edit_col:

                                        if st.button(
                                            "Save investment",
                                            key=(
                                                "investment_save_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            update_investment_contribution(
                                                CURRENT_USER_ID,
                                                transaction.id,
                                                item.asset_id,
                                                edited_investment_amount,
                                                edited_investment_description
                                            )

                                            st.rerun()

                                    with investment_delete_col:

                                        if st.button(
                                            "Delete investment",
                                            key=(
                                                "investment_delete_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            delete_investment_contribution(
                                                CURRENT_USER_ID,
                                                transaction.id
                                            )

                                            st.rerun()
# =========================================================
# 11. LIQUIDITY BREAKDOWN
# =========================================================

st.divider()
st.header("💧 Liquidity Breakdown")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Cash & Bank",
        f"€{available_cash:,.2f}"
    )

with col2:
    st.metric(
        "Liquid Investments",
        f"€{liquid_investments:,.2f}"
    )

with col3:
    st.metric(
        "Semi-liquid Assets",
        f"€{semi_liquid_assets:,.2f}"
    )

with col4:
    st.metric(
        "Non-liquid Assets",
        f"€{non_liquid_assets:,.2f}"
    )

# =========================================================
# FEEDBACK
# =========================================================

st.divider()
st.header("💬 Feedback")

st.write(
    "This app is currently in beta. "
    "Tell me what was useful, confusing, or missing."
)

with st.form("feedback_form"):

    feedback_message = st.text_area(
        "Your feedback",
        placeholder=(
            "What worked well? "
            "What was confusing? "
            "What would you change?"
        )
    )

    feedback_submitted = (
        st.form_submit_button(
            "Send feedback"
        )
    )

if feedback_submitted:

    if feedback_message.strip() == "":

        st.error(
            "Please write something before submitting."
        )

    else:

        add_feedback(
            CURRENT_USER_ID,
            feedback_message.strip()
        )

        st.success(
            "Thank you — feedback saved."
        )

        st.rerun()


# =========================================================
# OPTIONAL: SHOW OWN PREVIOUS FEEDBACK
# =========================================================

previous_feedback = get_user_feedback(
    CURRENT_USER_ID
)

if len(previous_feedback) > 0:

    with st.expander(
        "Your previous feedback"
    ):

        for feedback_item in previous_feedback:

            feedback_date = (
                feedback_item.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
            )

            st.write(
                f"**{feedback_date}**"
            )

            st.write(
                feedback_item.message
            )

            st.divider()

# =========================================================
# DANGER ZONE
# =========================================================

st.divider()

with st.expander("⚠️ Danger Zone | Delete data "):

    st.warning(
        "Deleting your data will permanently remove "
        "your accounts, assets, debts, funds, monthly plans "
        "and feedback."
    )

    st.write(
        "Your login account will remain active, "
        "but your financial data cannot be recovered."
    )

    confirm_delete = st.checkbox(
        "I understand that this action is permanent.",
        key="confirm_delete_all_data"
    )

    delete_confirmation = st.text_input(
        'Type "DELETE" to confirm:',
        key="delete_confirmation_text"
    )

    if st.button(
        "Delete all my data",
        type="primary",
        key="delete_all_user_data_button"
    ):

        if not confirm_delete:

            st.error(
                "Please confirm that you understand "
                "this action is permanent."
            )

        elif delete_confirmation != "DELETE":

            st.error(
                'Please type "DELETE" exactly to confirm.'
            )

        else:

            delete_all_user_data(
                CURRENT_USER_ID
            )

            st.success(
                "All your financial data has been deleted."
            )

            st.rerun()
