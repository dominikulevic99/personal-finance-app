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

from feedback import FEEDBACK_OPTIONS
from feedback import (
    get_user_feedback
)

from calculations import calculate_financial_summary
from users import get_or_create_user

from user_data import delete_all_user_data
from onboarding import render_onboarding_entry, render_guide_replay_action
from analytics import track_event
from monthly_checkin import render_monthly_checkin
from dashboard_navigation import render_section_links, render_guide_action
from dashboard_tour import render_tour
from feedback_ui import open_feedback, render_feedback
from feedback_prompt import render_feedback_prompt
from ui_errors import run_ui_action
from i18n import initialize_language, render_language_switcher, t, month_name, enum_label
from fund_progress import fund_progress_card
from visual_styles import apply_dashboard_styles


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title=t('ui.my_finance_app'),
    page_icon=":material/account_balance_wallet:",
    layout="wide"
)


# =========================================================
# AUTHENTICATION
# =========================================================

if not st.user.is_logged_in:
    initialize_language()
    with st.sidebar:
        render_language_switcher()

    st.title(t('ui.my_finance_app'))

    st.write(
        t('ui.sign_in_to_access_your_private_financial_dashboard')
    )

    if st.button(t('ui.log_in_with_google')):
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
UI_LANGUAGE = initialize_language(CURRENT_USER_ID)
track_event(CURRENT_USER_ID, "login")


# =========================================================
# MAIN APP HEADER
# =========================================================

navigation_slot = st.sidebar.container()
help_slot = st.sidebar.container()
with help_slot:
    st.caption(t('ui.get_more_from_the_app'))
    guide_slot = st.container()
render_guide_replay_action(CURRENT_USER_ID)
feedback_slot = st.sidebar.container()

st.sidebar.divider()
st.sidebar.caption(t('ui.account'))
st.sidebar.caption(t('ui.signed_in_as'))
st.sidebar.text(current_user.email)

if st.sidebar.button(t('ui.log_out'), type="tertiary"):
    st.logout()
with st.sidebar:
    render_language_switcher()
danger_slot = st.sidebar.container()


# Development override: show Welcome for this tester without resetting their data.
render_onboarding_entry(
    CURRENT_USER_ID,
    force_welcome=current_user.email.strip().lower() == "dominic.work310@gmail.com",
)

apply_dashboard_styles()
with navigation_slot:
    render_section_links()
with guide_slot:
    render_guide_action(CURRENT_USER_ID)
with feedback_slot:
    st.button(t('ui.send_feedback'), key=f'feedback_{CURRENT_USER_ID}_sidebar', type='tertiary',
              help=t('feedback.sidebar_help'), on_click=open_feedback, args=(CURRENT_USER_ID, 'sidebar'))
with danger_slot:
    st.divider()
    st.caption(t('ui.delete_my_data_delete_my_data'))
track_event(CURRENT_USER_ID, "dashboard_opened")

st.title(t('ui.your_financial_picture'))
st.caption(t('ui.your_whole_financial_picture_made_clear'))


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
with st.container(key="tour_summary"):
    st.header(t('metrics.financial_summary'), anchor="overview")

    with st.container(key="net_worth"):
        st.metric(
            t('metrics.net_worth'), f"€{net_worth:,.2f}",
            help=t('ui.your_cash_and_assets_minus_what_you_owe'),
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            t('metrics.available_cash'),
            f"€{available_cash:,.2f}",
            help=t('ui.money_currently_available_in_your_accounts_and_cash'),
        )

    with col2:
        st.metric(
            t('metrics.set_aside'),
            f"€{total_reserved_funds:,.2f}",
            help=t('ui.part_of_your_available_cash_assigned_to_specific_goals'),
        )

    with col3:
        st.metric(
            t('metrics.free_cash'),
            f"€{free_cash:,.2f}",
            help=t('ui.cash_not_reserved_for_funds_this_does_not_subtract_monthly'),
        )

    st.caption(t('metrics.cash_explanation'))
    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            t('metrics.liquid_worth'),
            f"€{liquid_worth:,.2f}",
            help=t('ui.cash_plus_assets_that_can_usually_be_converted_to_cash'),
        )

    with col5:
        st.metric(
            t('metrics.total_debt'),
            f"€{total_debt:,.2f}",
            help=t('ui.the_total_amount_you_still_owe_across_your_debts'),
        )

with st.expander(t('ui.understanding_your_financial_picture')):
    st.write(
        t('ui.net_worth_brings_together_your_cash_and_all_your_assets')
    )
    st.write(
        t('ui.funds_are_money_set_aside_within_your_existing_cash_they')
    )


# =========================================================
# 6. ACCOUNTS
# =========================================================

render_monthly_checkin(CURRENT_USER_ID)

st.divider()
st.header(t('ui.accounts'), anchor="accounts")

st.subheader(t('ui.add_account'))

with st.form("add_account_form"):

    account_name = st.text_input(
        t("accounts.name"),
        placeholder=t('ui.e_g_revolut'),
        key=f"account_create_{CURRENT_USER_ID}_name",
    )

    account_type_col, account_balance_col = st.columns(2)
    with account_type_col:
        account_type = st.selectbox(
            t('ui.account_type'),
            [
                "BANK",
                "CASH"
            ],
            key=f"account_create_{CURRENT_USER_ID}_type",
            format_func=lambda value: t("accounts.cash" if value == "CASH" else "accounts.bank", language=UI_LANGUAGE),
        )

    with account_balance_col:
        balance = st.number_input(
            t("accounts.current_balance"),
            min_value=0.0,
            step=100.0,
            key=f"account_create_{CURRENT_USER_ID}_balance",
        )

    account_submitted = st.form_submit_button(
        t('ui.add_account'), type="primary"
    )


if account_submitted:

    if account_name.strip() == "":
        st.error(t('ui.please_enter_an_account_name'))

    else:
        run_ui_action(add_account,
            CURRENT_USER_ID,
            account_name,
            account_type,
            balance
        )

        st.success(t('ui.account_saved'))
        st.rerun()


st.subheader(t('ui.your_accounts'))

if len(accounts) == 0:

    st.info(t('ui.no_accounts_added_yet'))

else:

    for account in accounts:

        with st.expander(
            f"{account.name} — €{account.balance:,.2f}"
        ):

            new_account_name = st.text_input(
                t("accounts.name"),
                value=account.name,
                key=f"account_name_{account.id}"
            )

            account_type_options = [
                "BANK",
                "CASH"
            ]

            new_account_type = st.selectbox(
                t('ui.account_type'),
                account_type_options,
                index=account_type_options.index(
                    account.account_type
                ),
                key=f"account_type_{account.id}",
                format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
            )

            new_balance = st.number_input(
                t("accounts.current_balance"),
                min_value=0.0,
                value=float(account.balance),
                step=100.0,
                key=f"account_balance_{account.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    t('ui.save_changes'),
                    key=f"save_account_{account.id}"
                ):

                    run_ui_action(update_account,
                        CURRENT_USER_ID,
                        account.id,
                        new_account_name,
                        new_account_type,
                        new_balance
                    )

                    st.success(t('ui.account_updated'))
                    st.rerun()

            with col2:

                if st.button(
                    t('ui.delete_account'),
                    key=f"delete_account_{account.id}"
                ):

                    run_ui_action(delete_account,
                        CURRENT_USER_ID,
                        account.id
                    )

                    st.success(t('ui.account_deleted'))
                    st.rerun()


# =========================================================
# 7. ASSETS
# =========================================================

st.divider()
st.header(t('ui.assets'), anchor="assets")

st.subheader(t('ui.add_asset'))

with st.form("add_asset_form"):

    asset_name = st.text_input(
        t('ui.asset_name'),
        placeholder=t('ui.e_g_my_investment_portfolio'),
        key=f"dashboard_{CURRENT_USER_ID}_asset_name",
    )

    asset_type = st.selectbox(
        t('ui.asset_type'),
        [
            "INVESTMENT",
            "REAL_ESTATE",
            "CAR",
            "PRIVATE_PROJECT",
            "MONEY_OWED_TO_ME",
            "OTHER"
        ],
           key=f"dashboard_{CURRENT_USER_ID}_asset_type", format_func=lambda value: enum_label(value, language=UI_LANGUAGE,
       ),
    )

    liquidity_class = st.selectbox(
        t('ui.liquidity_class'),
        [
            "LIQUID_INVESTMENT",
            "SEMI_LIQUID",
            "NON_LIQUID"
        ],
           key=f"dashboard_{CURRENT_USER_ID}_liquidity_class", format_func=lambda value: enum_label(value, language=UI_LANGUAGE,
       ),
    )

    asset_value = st.number_input(
        t('ui.current_value'),
        min_value=0.0,
        step=100.0,
        key=f"dashboard_{CURRENT_USER_ID}_asset_value",
    )

    asset_submitted = st.form_submit_button(
        t('ui.save_asset'), type="primary"
    )


if asset_submitted:

    if asset_name.strip() == "":
        st.error(t('ui.please_enter_an_asset_name'))

    else:
        run_ui_action(add_asset,
            CURRENT_USER_ID,
            asset_name,
            asset_type,
            liquidity_class,
            asset_value
        )

        st.success(t('ui.asset_saved'))
        st.rerun()


st.subheader(t('ui.your_assets'))

if len(assets) == 0:

    st.info(t('ui.no_assets_added_yet'))

else:

    for asset in assets:

        with st.expander(
            f"{asset.name} — €{asset.current_value:,.2f}"
        ):

            new_asset_name = st.text_input(
                t('ui.asset_name'),
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
                t('ui.asset_type'),
                asset_type_options,
                index=asset_type_options.index(
                    asset.asset_type
                ),
                key=f"asset_type_{asset.id}",
                format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
            )

            liquidity_options = [
                "LIQUID_INVESTMENT",
                "SEMI_LIQUID",
                "NON_LIQUID"
            ]

            new_liquidity = st.selectbox(
                t('ui.liquidity_class'),
                liquidity_options,
                index=liquidity_options.index(
                    asset.liquidity_class
                ),
                key=f"asset_liquidity_{asset.id}",
                format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
            )

            new_asset_value = st.number_input(
                t('ui.current_value'),
                min_value=0.0,
                value=float(asset.current_value),
                step=100.0,
                key=f"asset_value_{asset.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    t('ui.save_asset_changes'),
                    key=f"save_asset_{asset.id}"
                ):

                    run_ui_action(update_asset,
                        CURRENT_USER_ID,
                        asset.id,
                        new_asset_name,
                        new_asset_type,
                        new_liquidity,
                        new_asset_value
                    )

                    st.success(t('ui.asset_updated'))
                    st.rerun()

            with col2:

                if st.button(
                    t('ui.delete_asset'),
                    key=f"delete_asset_{asset.id}"
                ):

                    run_ui_action(delete_asset,
                        CURRENT_USER_ID,
                        asset.id
                    )

                    st.success(t('ui.asset_deleted'))
                    st.rerun()


# =========================================================
# 8. DEBTS
# =========================================================

st.divider()
st.header(t('ui.debts'), anchor="debts")

st.subheader(t('ui.add_debt'))

with st.form("add_debt_form"):

    debt_name = st.text_input(
        t('ui.debt_name'),
        placeholder=t('ui.e_g_money_borrowed_from_jonas'),
        key=f"dashboard_{CURRENT_USER_ID}_debt_name",
    )

    debt_type = st.selectbox(
        t('ui.debt_type'),
        [
            "MORTGAGE",
            "CAR_LOAN",
            "PERSONAL_LOAN",
            "CREDIT_CARD",
            "OTHER"
        ],
           key=f"dashboard_{CURRENT_USER_ID}_debt_type", format_func=lambda value: enum_label(value, language=UI_LANGUAGE,
       ),
    )

    remaining_balance = st.number_input(
        t('ui.remaining_balance'),
        min_value=0.0,
        step=100.0,
        key=f"dashboard_{CURRENT_USER_ID}_remaining_balance",
    )

    monthly_payment = st.number_input(
        t('ui.monthly_payment'),
        min_value=0.0,
        step=50.0,
        key=f"dashboard_{CURRENT_USER_ID}_monthly_payment",
    )

    interest_rate = st.number_input(
        t('ui.interest_rate'),
        min_value=0.0,
        step=0.1,
        key=f"dashboard_{CURRENT_USER_ID}_interest_rate",
    )

    debt_submitted = st.form_submit_button(
        t('ui.save_debt'), type="primary"
    )


if debt_submitted:

    if debt_name.strip() == "":
        st.error(t('ui.please_enter_a_debt_name'))

    else:
        run_ui_action(add_debt,
            CURRENT_USER_ID,
            debt_name,
            debt_type,
            remaining_balance,
            monthly_payment,
            interest_rate
        )

        st.success(t('ui.debt_saved'))
        st.rerun()


st.subheader(t('ui.your_debts'))

if len(debts) == 0:

    st.info(t('ui.no_debts_added_yet'))

else:

    for debt in debts:

        with st.expander(
            f"{debt.name} — €{debt.remaining_balance:,.2f}"
        ):

            new_debt_name = st.text_input(
                t('ui.debt_name'),
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
                t('ui.debt_type'),
                debt_type_options,
                index=debt_type_options.index(
                    debt.debt_type
                ),
                key=f"debt_type_{debt.id}",
                format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
            )

            new_remaining_balance = st.number_input(
                t('ui.remaining_balance'),
                min_value=0.0,
                value=float(debt.remaining_balance),
                step=100.0,
                key=f"debt_balance_{debt.id}"
            )

            new_monthly_payment = st.number_input(
                t('ui.monthly_payment'),
                min_value=0.0,
                value=float(debt.monthly_payment),
                step=50.0,
                key=f"debt_payment_{debt.id}"
            )

            new_interest_rate = st.number_input(
                t('ui.interest_rate'),
                min_value=0.0,
                value=float(debt.interest_rate),
                step=0.1,
                key=f"debt_interest_{debt.id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    t('ui.save_debt_changes'),
                    key=f"save_debt_{debt.id}"
                ):

                    run_ui_action(update_debt,
                        CURRENT_USER_ID,
                        debt.id,
                        new_debt_name,
                        new_debt_type,
                        new_remaining_balance,
                        new_monthly_payment,
                        new_interest_rate
                    )

                    st.success(t('ui.debt_updated'))
                    st.rerun()

            with col2:

                if st.button(
                    t('ui.delete_debt'),
                    key=f"delete_debt_{debt.id}"
                ):

                    run_ui_action(delete_debt,
                        CURRENT_USER_ID,
                        debt.id
                    )

                    st.success(t('ui.debt_deleted'))
                    st.rerun()


# =========================================================
# 9. VIRTUAL FUNDS
# =========================================================

st.divider()
with st.container(key="tour_funds"):
    st.header(t('buckets.plural'), anchor="funds")

    st.caption(t('ui.money_you_ve_set_aside_for_specific_goals'))


# -----------------------------
# ADD NEW FUND
# -----------------------------

with st.form("add_fund_form"):

    fund_name = st.text_input(
        t('buckets.name'),
        placeholder=t('ui.e_g_emergency_fund'),
        key=f"dashboard_{CURRENT_USER_ID}_fund_name",
    )

    fund_balance = st.number_input(
        t('ui.current_reserved_amount'),
        min_value=0.0,
        step=100.0,
        key=f"dashboard_{CURRENT_USER_ID}_fund_balance",
    )

    fund_target = st.number_input(
        t('ui.target_amount'),
        min_value=0.0,
        step=100.0,
        key=f"dashboard_{CURRENT_USER_ID}_fund_target",
    )

    fund_submitted = st.form_submit_button(
        t('ui.save_fund'), type="primary"
    )


# -----------------------------
# SAVE NEW FUND
# -----------------------------

if fund_submitted:

    if fund_name.strip() == "":
        st.error(t('ui.please_enter_a_fund_name'))

    elif fund_balance > float(available_cash):
        st.warning(
            t('ui.reserved_amount_is_higher_than_your_available_cash_please_check')
        )

    else:

        run_ui_action(add_fund,
            CURRENT_USER_ID,
            fund_name,
            fund_balance,
            fund_target
        )

        st.success(t('ui.fund_saved'))
        st.rerun()


# -----------------------------
# SHOW EXISTING FUNDS
# -----------------------------

st.subheader(t('buckets.yours'))
st.caption(t('buckets.support'))

if len(funds) == 0:

    st.info(t('ui.no_virtual_funds_added_yet'))

else:

    for fund in funds:

        balance = float(fund.current_balance)

        target = (
            float(fund.target_amount)
            if fund.target_amount is not None
            else 0.0
        )

        with fund_progress_card(CURRENT_USER_ID, fund):

            # -----------------------------
            # EDIT FUND NAME
            # -----------------------------

            new_fund_name = st.text_input(
                t('buckets.name'),
                value=fund.name,
                key=f"fund_name_{fund.id}"
            )

            # -----------------------------
            # EDIT FUND BALANCE
            # -----------------------------

            new_fund_balance = st.number_input(
                t('ui.reserved_amount'),
                min_value=0.0,
                value=balance,
                step=100.0,
                key=f"fund_balance_{fund.id}"
            )

            # -----------------------------
            # EDIT FUND TARGET
            # -----------------------------

            new_fund_target = st.number_input(
                t('ui.target_amount'),
                min_value=0.0,
                value=target,
                step=100.0,
                key=f"fund_target_{fund.id}"
            )

            # -----------------------------
            # SAVE / DELETE BUTTONS
            # -----------------------------

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    t('ui.save_fund_changes'),
                    key=f"save_fund_{fund.id}"
                ):

                    run_ui_action(update_fund,
                        CURRENT_USER_ID,
                        fund.id,
                        new_fund_name,
                        new_fund_balance,
                        new_fund_target
                    )

                    st.success(t('ui.fund_updated'))
                    st.rerun()

            with col2:

                if st.button(
                    t('ui.delete_fund'),
                    key=f"delete_fund_{fund.id}"
                ):

                    run_ui_action(delete_fund,
                        CURRENT_USER_ID,
                        fund.id
                    )

                    st.success(t('ui.fund_deleted'))
                    st.rerun()


# =========================================================
# 10. MONTHLY PLAN
# =========================================================

st.divider()
with st.container(key="tour_monthly_plan"):
    st.header(t('plan.title'), anchor="monthly-plan")
    st.caption(t('ui.decide_where_you_want_this_month_s_income_to_go'))

today = date.today()


# =========================================================
# SELECT MONTH
# =========================================================

month_col1, month_col2 = st.columns(2)

with month_col1:

    selected_year = st.number_input(
        t('ui.year'),
        min_value=2020,
        max_value=2100,
        value=today.year,
        step=1,
        key=f"dashboard_{CURRENT_USER_ID}_selected_year",
    )

with month_col2:

    selected_month = st.selectbox(
        t('ui.month'),
        options=list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda month: month_name(month, language=UI_LANGUAGE),
        key=f"dashboard_{CURRENT_USER_ID}_selected_month",
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
        t('ui.no_monthly_plan_exists_for_this_month_yet')
    )

    with st.form("create_monthly_plan_form"):

        planned_income = st.number_input(
            t('ui.planned_monthly_income'),
            min_value=0.0,
            step=100.0,
            key=f"dashboard_{CURRENT_USER_ID}_planned_income",
        )

        create_plan_submitted = (
            st.form_submit_button(
                t('ui.create_monthly_plan'), type="primary"
            )
        )

    if create_plan_submitted:

        run_ui_action(create_monthly_plan,
            CURRENT_USER_ID,
            selected_year,
            selected_month,
            planned_income
        )

        track_event(CURRENT_USER_ID, "monthly_plan_created")
        st.success(
            t('ui.monthly_plan_created')
        )

        st.rerun()


# =========================================================
# MONTHLY PLAN EXISTS
# =========================================================

else:

    st.success(
        t("plan.status", status=enum_label(monthly_plan.status))
    )

    # =====================================================
    # INCOME
    # =====================================================

    st.subheader(t('ui.income_plan'))

    planned_income_value = float(
        monthly_plan.planned_income
    )

    new_planned_income = st.number_input(
        t('ui.planned_monthly_income'),
        min_value=0.0,
        value=planned_income_value,
        step=100.0,
        key="planned_income_value"
    )

    if st.button(
        t('ui.save_planned_income'),
        key="save_planned_income"
    ):

        run_ui_action(update_planned_income,
            CURRENT_USER_ID,
            monthly_plan.id,
            new_planned_income
        )

        st.success(
            t('ui.planned_income_updated')
        )

        st.rerun()

    # =====================================================
    # GET ALLOCATIONS
    # =====================================================

    st.divider()
    st.subheader(t('ui.monthly_allocation'))

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
            t('ui.planned_income'),
            f"€{planned_income_value:,.2f}"
        )

    with summary_col2:

        st.metric(
            t('ui.planned_allocation'),
            f"€{total_planned_allocation:,.2f}"
        )

    with summary_col3:

        st.metric(
            t('ui.remaining'),
            f"€{remaining_to_allocate:,.2f}"
        )

    with summary_col4:

        st.metric(
            t('ui.actual_so_far'),
            f"€{total_actual_allocation:,.2f}"
        )

    if remaining_to_allocate < 0:

        st.warning(
            t("plan.over_income", amount=f"{abs(remaining_to_allocate):,.2f}")
        )

    elif remaining_to_allocate == 0:

        st.success(
            t('ui.your_planned_income_is_fully_allocated')
        )

    else:

        st.info(
            t("plan.unallocated_amount", amount=f"{remaining_to_allocate:,.2f}")
        )

    # =====================================================
    # ADD ALLOCATION
    # =====================================================

    st.divider()
    st.subheader(t('ui.add_allocation'))

    plan_item_name = st.text_input(
        t('ui.allocation_name'),
        placeholder=t('ui.e_g_groceries'),
        key="new_plan_item_name"
    )

    plan_item_type = st.selectbox(
        t('ui.allocation_type'),
        [
            "EXPENSE",
            "FUND",
            "INVESTMENT",
            "DEBT_PAYMENT",
            "OTHER"
        ],
        key="new_plan_item_type",
        format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
    )

    # -----------------------------------------------------
    # LINK FUND
    # -----------------------------------------------------

    linked_fund_id = None

    if plan_item_type == "FUND":

        if len(funds) == 0:

            st.warning(
                t('ui.create_a_virtual_fund_first')
            )

        else:

            linked_fund_id = st.selectbox(
                t('ui.linked_virtual_fund'),
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
                t('ui.create_an_investment_asset_first')
            )

        else:

            linked_asset_id = st.selectbox(
                t('ui.linked_investment'),
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
        t('ui.planned_amount'),
        min_value=0.0,
        step=50.0,
        key="new_plan_item_amount"
    )

    if st.button(
        t('ui.add_allocation_detail'),
        type="primary",
        key="add_new_allocation"
    ):

        if plan_item_name.strip() == "":

            st.error(
                t('ui.please_enter_an_allocation_name')
            )

        elif (
            plan_item_type == "FUND"
            and linked_fund_id is None
        ):

            st.error(
                t('ui.please_select_a_virtual_fund')
            )

        elif (
            plan_item_type == "INVESTMENT"
            and linked_asset_id is None
        ):

            st.error(
                t('ui.please_select_an_investment_asset')
            )

        else:

            run_ui_action(add_plan_item,
                CURRENT_USER_ID,
                monthly_plan.id,
                plan_item_name,
                plan_item_type,
                plan_item_amount,
                linked_fund_id,
                linked_asset_id
            )

            st.success(
                t('ui.allocation_added')
            )

            st.rerun()

    # =====================================================
    # EXISTING ALLOCATIONS
    # =====================================================

    st.divider()
    st.subheader(t('ui.your_allocation_plan'))

    if len(plan_items) == 0:

        st.info(
            t('ui.no_allocations_added_yet')
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
                    t('ui.name'),
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
                    t('ui.type'),
                    item_type_options,
                    index=item_type_options.index(
                        item.category_type
                    ),
                    key=f"plan_item_type_{item.id}",
                    format_func=lambda value: enum_label(value, language=UI_LANGUAGE),
                )

                # -------------------------------------------------
                # EDIT LINKED FUND
                # -------------------------------------------------

                new_linked_fund_id = item.fund_id

                if new_item_type == "FUND":

                    if len(funds) == 0:

                        st.warning(
                            t('ui.create_a_virtual_fund_first')
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
                            t('ui.linked_virtual_fund'),
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
                            t('ui.create_an_investment_asset_first')
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
                            t('ui.linked_investment'),
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
                    t('ui.planned_amount'),
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
                        t('ui.actual_amount'),
                        f"€{item_actual:,.2f}"
                    )

                    st.caption(
                        t('ui.actual_contributions_are_shown_here_use_confirm_contribution_below_to')
                    )

                else:

                    new_actual_amount = st.number_input(
                        t('ui.actually_spent_this_month') if item.category_type == "EXPENSE" else t('ui.actual_amount_this_month'),
                        min_value=0.0,
                        value=stored_actual,
                        step=50.0,
                        key=f"plan_item_actual_{item.id}"
                    )
                    st.caption(
                        t('ui.enter_the_total_for_this_allocation_for_the_month_not')
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
                        t("plan.above", amount=f"{variance:,.2f}")
                    )

                elif variance < 0:

                    st.info(
                        t("plan.below", amount=f"{abs(variance):,.2f}")
                    )

                else:

                    st.success(
                        t('ui.recorded_actual_amount_matches_the_plan')
                    )

                # =================================================
                # SAVE / DELETE ALLOCATION
                # =================================================

                allocation_col1, allocation_col2 = (
                    st.columns(2)
                )

                with allocation_col1:

                    if st.button(
                        t('ui.save_plan_changes') if item.category_type in ("FUND", "INVESTMENT") else (
                            t('ui.record_actual_spending') if item.category_type == "EXPENSE" else t('ui.record_actual_amount')
                        ),
                        type="primary",
                        key=f"save_plan_item_{item.id}"
                    ):

                        if (
                            new_item_type == "FUND"
                            and new_linked_fund_id is None
                        ):

                            st.error(
                                t('ui.select_a_virtual_fund')
                            )

                        elif (
                            new_item_type == "INVESTMENT"
                            and new_linked_asset_id is None
                        ):

                            st.error(
                                t('ui.select_an_investment_asset')
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

                            run_ui_action(update_plan_item,
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
                                t('ui.plan_changes_saved') if item.category_type in ("FUND", "INVESTMENT")
                                else t('ui.actual_amount_and_allocation_changes_saved_account_balances_are_unchanged')
                            )

                            st.rerun()

                with allocation_col2:

                    if st.button(
                        t('ui.delete_allocation'),
                        key=f"delete_plan_item_{item.id}"
                    ):

                        run_ui_action(delete_plan_item,
                            CURRENT_USER_ID,
                            item.id
                        )

                        st.success(
                            t('ui.allocation_deleted')
                        )

                        st.rerun()

                # =================================================
                # FUND CONTRIBUTION
                # =================================================

                if item.category_type == "FUND":

                    st.divider()

                    st.subheader(
                        t('ui.actual_fund_contribution')
                    )
                    st.caption(
                        t('ui.confirm_only_a_new_contribution_you_actually_made_this_adds')
                    )

                    if item.fund_id is None:

                        st.warning(
                            t('ui.this_allocation_is_not_linked_to_a_virtual_fund')
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
                                t('ui.linked_virtual_fund_was_not_found')
                            )

                        else:

                            st.info(
                                t("buckets.linked", name=linked_fund.name)
                            )

                            fund_col1, fund_col2 = (
                                st.columns(2)
                            )

                            with fund_col1:

                                st.metric(
                                    t('ui.planned'),
                                    f"€{item_planned:,.2f}"
                                )

                            with fund_col2:

                                st.metric(
                                    t('ui.actual'),
                                    f"€{actual_fund_contributed:,.2f}"
                                )

                            with st.form(
                                f"fund_contribution_form_{item.id}"
                            ):

                                contribution_amount = (
                                    st.number_input(
                                        t('ui.actual_contribution'),
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
                                        t('ui.description'),
                                        key=(
                                            "fund_description_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                contribution_submitted = (
                                    st.form_submit_button(
                                        t('ui.confirm_contribution'), type="primary"
                                    )
                                )

                            if contribution_submitted:

                                run_ui_action(add_fund_contribution,
                                    CURRENT_USER_ID,
                                    monthly_plan.id,
                                    item.id,
                                    item.fund_id,
                                    contribution_amount,
                                    contribution_description
                                )

                                track_event(CURRENT_USER_ID, "contribution_confirmed", "fund")
                                st.success(
                                    t('ui.fund_contribution_recorded')
                                )

                                st.rerun()

                            # -----------------------------------------
                            # FUND HISTORY
                            # -----------------------------------------

                            if len(fund_transactions) > 0:

                                st.write(
                                    t('ui.contribution_history')
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
                                            t('ui.amount'),
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
                                            t('ui.description'),
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
                                            t('ui.save_contribution'),
                                            key=(
                                                "fund_save_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            run_ui_action(update_fund_contribution,
                                                CURRENT_USER_ID,
                                                transaction.id,
                                                item.fund_id,
                                                edited_amount,
                                                edited_description
                                            )

                                            st.rerun()

                                    with delete_col:

                                        if st.button(
                                            t('ui.delete_contribution'),
                                            key=(
                                                "fund_delete_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            run_ui_action(delete_fund_contribution,
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
                        t('ui.actual_investment_contribution')
                    )
                    st.caption(
                        t('ui.confirm_only_a_new_contribution_you_actually_made_this_adds_detail')
                    )

                    if item.asset_id is None:

                        st.warning(
                            t('ui.this_allocation_is_not_linked_to_an_investment_asset')
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
                                t('ui.linked_investment_asset_was_not_found')
                            )

                        else:

                            st.info(
                                t("investments.linked", name=linked_asset.name)
                            )

                            investment_col1, investment_col2 = (
                                st.columns(2)
                            )

                            with investment_col1:

                                st.metric(
                                    t('ui.planned'),
                                    f"€{item_planned:,.2f}"
                                )

                            with investment_col2:

                                st.metric(
                                    t('ui.actual'),
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
                                        t('ui.actual_investment'),
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
                                        t('ui.description'),
                                        key=(
                                            "investment_description_"
                                            f"{item.id}"
                                        )
                                    )
                                )

                                investment_submitted = (
                                    st.form_submit_button(
                                        t('ui.confirm_contribution'), type="primary"
                                    )
                                )

                            if investment_submitted:

                                run_ui_action(add_investment_contribution,
                                    CURRENT_USER_ID,
                                    monthly_plan.id,
                                    item.id,
                                    item.asset_id,
                                    investment_amount,
                                    investment_description
                                )

                                track_event(CURRENT_USER_ID, "contribution_confirmed", "investment")
                                st.success(
                                    t("contribution.added", amount=f"{investment_amount:,.2f}", name=linked_asset.name)
                                )

                                st.rerun()

                            # -----------------------------------------
                            # INVESTMENT HISTORY
                            # -----------------------------------------

                            if len(
                                investment_transactions
                            ) > 0:

                                st.write(
                                    t('ui.investment_history')
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
                                            t('ui.amount'),
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
                                            t('ui.description'),
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
                                            t('ui.save_investment'),
                                            key=(
                                                "investment_save_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            run_ui_action(update_investment_contribution,
                                                CURRENT_USER_ID,
                                                transaction.id,
                                                item.asset_id,
                                                edited_investment_amount,
                                                edited_investment_description
                                            )

                                            st.rerun()

                                    with investment_delete_col:

                                        if st.button(
                                            t('ui.delete_investment'),
                                            key=(
                                                "investment_delete_"
                                                f"{transaction.id}"
                                            )
                                        ):

                                            run_ui_action(delete_investment_contribution,
                                                CURRENT_USER_ID,
                                                transaction.id
                                            )

                                            st.rerun()
# =========================================================
# 11. LIQUIDITY BREAKDOWN
# =========================================================

st.divider()
st.header(t('ui.liquidity_breakdown'))

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        t('ui.cash_bank'),
        f"€{available_cash:,.2f}"
    )

with col2:
    st.metric(
        t('ui.liquid_investments'),
        f"€{liquid_investments:,.2f}"
    )

with col3:
    st.metric(
        t('ui.semi_liquid_assets'),
        f"€{semi_liquid_assets:,.2f}"
    )

with col4:
    st.metric(
        t('ui.non_liquid_assets'),
        f"€{non_liquid_assets:,.2f}"
    )

# =========================================================
# FEEDBACK
# =========================================================

# =========================================================
# OPTIONAL: SHOW OWN PREVIOUS FEEDBACK
# =========================================================

try:
    previous_feedback = get_user_feedback(CURRENT_USER_ID)
except Exception:
    previous_feedback = []

if len(previous_feedback) > 0:
    st.divider()
    st.header(t('ui.feedback'), anchor="feedback")

    with st.expander(
        t('ui.your_previous_feedback')
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

            for option in getattr(feedback_item, "selected_options", []):
                if option in FEEDBACK_OPTIONS:
                    st.write(t(f"feedback.option.{option}"))
            st.text(feedback_item.message)

            st.divider()

# =========================================================
# DANGER ZONE
# =========================================================

st.divider()

st.html('<div id="delete-my-data"></div>')
with st.expander(t('ui.delete_your_data')):

    st.warning(
        t('ui.deleting_your_data_will_permanently_remove_your_accounts_assets_debts')
    )

    st.write(
        t('ui.your_login_account_will_remain_active_but_your_financial_data')
    )

    confirm_delete = st.checkbox(
        t('ui.i_understand_that_this_action_is_permanent'),
        key="confirm_delete_all_data"
    )

    delete_confirmation = st.text_input(
        t('ui.type_delete_to_confirm'),
        key="delete_confirmation_text"
    )

    if st.button(
        t('ui.delete_all_my_data'),
        type="primary",
        key="delete_all_user_data_button"
    ):

        if not confirm_delete:

            st.error(
                t('ui.please_confirm_that_you_understand_this_action_is_permanent')
            )

        elif delete_confirmation != "DELETE":

            st.error(
                t('ui.please_type_delete_exactly_to_confirm')
            )

        else:

            run_ui_action(delete_all_user_data,
                CURRENT_USER_ID
            )

            st.success(
                t('ui.all_your_financial_data_has_been_deleted')
            )

            st.rerun()


# Mount only after dashboard targets exist; no onboarding or financial side effects.
render_tour(
    CURRENT_USER_ID,
    tester=current_user.email.strip().lower() == "dominic.work310@gmail.com",
)
render_feedback_prompt(
    CURRENT_USER_ID,
    tester=current_user.email.strip().lower() == "dominic.work310@gmail.com",
)
render_feedback(CURRENT_USER_ID)
