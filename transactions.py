from sqlalchemy import text

from database import engine


# =========================================================
# READ TRANSACTIONS
# =========================================================

def get_transactions_for_month(
    user_id,
    monthly_plan_id
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    user_id,
                    monthly_plan_id,
                    monthly_plan_item_id,
                    transaction_type,
                    amount,
                    account_id,
                    fund_id,
                    asset_id,
                    debt_id,
                    description,
                    created_at
                FROM transactions
                WHERE
                    user_id = :user_id
                    AND monthly_plan_id = :monthly_plan_id
                ORDER BY created_at, id
            """),
            {
                "user_id": user_id,
                "monthly_plan_id": monthly_plan_id
            }
        )

        return result.fetchall()


def get_transactions_for_item(
    user_id,
    monthly_plan_item_id
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    transaction_type,
                    amount,
                    account_id,
                    fund_id,
                    asset_id,
                    debt_id,
                    description,
                    created_at
                FROM transactions
                WHERE
                    user_id = :user_id
                    AND monthly_plan_item_id = :monthly_plan_item_id
                ORDER BY created_at, id
            """),
            {
                "user_id": user_id,
                "monthly_plan_item_id": monthly_plan_item_id
            }
        )

        return result.fetchall()


# =========================================================
# ADD FUND CONTRIBUTION
# =========================================================

def add_fund_contribution(
    user_id,
    monthly_plan_id,
    monthly_plan_item_id,
    fund_id,
    amount,
    description=None
):
    with engine.begin() as connection:

        # =================================================
        # VERIFY MONTHLY PLAN OWNERSHIP
        # =================================================

        plan = connection.execute(
            text("""
                SELECT id
                FROM monthly_plans
                WHERE
                    id = :monthly_plan_id
                    AND user_id = :user_id
            """),
            {
                "monthly_plan_id": monthly_plan_id,
                "user_id": user_id
            }
        ).fetchone()

        if plan is None:
            raise ValueError(
                "Monthly plan does not belong to this user."
            )

        # =================================================
        # VERIFY PLAN ITEM OWNERSHIP
        # =================================================

        plan_item = connection.execute(
            text("""
                SELECT mpi.id
                FROM monthly_plan_items mpi

                JOIN monthly_plans mp
                    ON mp.id = mpi.monthly_plan_id

                WHERE
                    mpi.id = :monthly_plan_item_id
                    AND mpi.monthly_plan_id = :monthly_plan_id
                    AND mp.user_id = :user_id
            """),
            {
                "monthly_plan_item_id": monthly_plan_item_id,
                "monthly_plan_id": monthly_plan_id,
                "user_id": user_id
            }
        ).fetchone()

        if plan_item is None:
            raise ValueError(
                "Monthly plan item does not belong to this user."
            )

        # =================================================
        # VERIFY FUND OWNERSHIP
        # =================================================

        fund = connection.execute(
            text("""
                SELECT id
                FROM funds
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "fund_id": fund_id,
                "user_id": user_id
            }
        ).fetchone()

        if fund is None:
            raise ValueError(
                "Fund does not belong to this user."
            )

        # =================================================
        # CREATE TRANSACTION
        # =================================================

        connection.execute(
            text("""
                INSERT INTO transactions (
                    user_id,
                    monthly_plan_id,
                    monthly_plan_item_id,
                    transaction_type,
                    amount,
                    fund_id,
                    description
                )
                VALUES (
                    :user_id,
                    :monthly_plan_id,
                    :monthly_plan_item_id,
                    'FUND_CONTRIBUTION',
                    :amount,
                    :fund_id,
                    :description
                )
            """),
            {
                "user_id": user_id,
                "monthly_plan_id": monthly_plan_id,
                "monthly_plan_item_id": monthly_plan_item_id,
                "amount": amount,
                "fund_id": fund_id,
                "description": description
            }
        )

        # =================================================
        # UPDATE FUND BALANCE
        # =================================================

        connection.execute(
            text("""
                UPDATE funds
                SET current_balance =
                    current_balance + :amount
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "amount": amount,
                "fund_id": fund_id,
                "user_id": user_id
            }
        )

# =========================================================
# UPDATE FUND CONTRIBUTION
# =========================================================


def update_fund_contribution(
    user_id,
    transaction_id,
    new_fund_id,
    new_amount,
    new_description=None
):
    with engine.begin() as connection:

        old_transaction = connection.execute(
            text("""
                SELECT
                    id,
                    amount,
                    fund_id
                FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
                    AND transaction_type = 'FUND_CONTRIBUTION'
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        ).fetchone()

        if old_transaction is None:
            raise ValueError(
                "Fund contribution was not found."
            )

        new_fund = connection.execute(
            text("""
                SELECT id
                FROM funds
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "fund_id": new_fund_id,
                "user_id": user_id
            }
        ).fetchone()

        if new_fund is None:
            raise ValueError(
                "Fund does not belong to this user."
            )

        old_amount = float(
            old_transaction.amount
        )

        old_fund_id = old_transaction.fund_id

        # Reverse old contribution
        connection.execute(
            text("""
                UPDATE funds
                SET current_balance =
                    current_balance - :amount
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "amount": old_amount,
                "fund_id": old_fund_id,
                "user_id": user_id
            }
        )

        # Apply new contribution
        connection.execute(
            text("""
                UPDATE funds
                SET current_balance =
                    current_balance + :amount
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "amount": new_amount,
                "fund_id": new_fund_id,
                "user_id": user_id
            }
        )

        # Update transaction history
        connection.execute(
            text("""
                UPDATE transactions
                SET
                    fund_id = :fund_id,
                    amount = :amount,
                    description = :description
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
            """),
            {
                "fund_id": new_fund_id,
                "amount": new_amount,
                "description": new_description,
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        )


# =========================================================
# DELETE FUND CONTRIBUTION
# =========================================================

def delete_fund_contribution(
    user_id,
    transaction_id
):
    with engine.begin() as connection:

        transaction = connection.execute(
            text("""
                SELECT
                    id,
                    amount,
                    fund_id
                FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
                    AND transaction_type = 'FUND_CONTRIBUTION'
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        ).fetchone()

        if transaction is None:
            raise ValueError(
                "Fund contribution was not found."
            )

        # Reverse contribution
        connection.execute(
            text("""
                UPDATE funds
                SET current_balance =
                    current_balance - :amount
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "amount": transaction.amount,
                "fund_id": transaction.fund_id,
                "user_id": user_id
            }
        )

        # Delete transaction
        connection.execute(
            text("""
                DELETE FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        )
# =========================================================
# ADD INVESTMENT CONTRIBUTION
# =========================================================


def add_investment_contribution(
    user_id,
    monthly_plan_id,
    monthly_plan_item_id,
    asset_id,
    amount,
    description=None
):
    with engine.begin() as connection:

        # Verify monthly plan belongs to user
        plan = connection.execute(
            text("""
                SELECT id
                FROM monthly_plans
                WHERE
                    id = :monthly_plan_id
                    AND user_id = :user_id
            """),
            {
                "monthly_plan_id": monthly_plan_id,
                "user_id": user_id
            }
        ).fetchone()

        if plan is None:
            raise ValueError(
                "Monthly plan does not belong to this user."
            )

        # Verify plan item belongs to user and plan
        plan_item = connection.execute(
            text("""
                SELECT mpi.id
                FROM monthly_plan_items mpi

                JOIN monthly_plans mp
                    ON mp.id = mpi.monthly_plan_id

                WHERE
                    mpi.id = :monthly_plan_item_id
                    AND mpi.monthly_plan_id = :monthly_plan_id
                    AND mp.user_id = :user_id
            """),
            {
                "monthly_plan_item_id": monthly_plan_item_id,
                "monthly_plan_id": monthly_plan_id,
                "user_id": user_id
            }
        ).fetchone()

        if plan_item is None:
            raise ValueError(
                "Monthly plan item does not belong to this user."
            )

        # Verify asset belongs to user
        asset = connection.execute(
            text("""
                SELECT id
                FROM assets
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "asset_id": asset_id,
                "user_id": user_id
            }
        ).fetchone()

        if asset is None:
            raise ValueError(
                "Investment asset does not belong to this user."
            )

        # Create transaction
        connection.execute(
            text("""
                INSERT INTO transactions (
                    user_id,
                    monthly_plan_id,
                    monthly_plan_item_id,
                    transaction_type,
                    amount,
                    asset_id,
                    description
                )
                VALUES (
                    :user_id,
                    :monthly_plan_id,
                    :monthly_plan_item_id,
                    'INVESTMENT_CONTRIBUTION',
                    :amount,
                    :asset_id,
                    :description
                )
            """),
            {
                "user_id": user_id,
                "monthly_plan_id": monthly_plan_id,
                "monthly_plan_item_id": monthly_plan_item_id,
                "amount": amount,
                "asset_id": asset_id,
                "description": description
            }
        )

        # Increase investment asset value
        connection.execute(
            text("""
                UPDATE assets
                SET current_value =
                    current_value + :amount
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "amount": amount,
                "asset_id": asset_id,
                "user_id": user_id
            }
        )


# =========================================================
# UPDATE INVESTMENT CONTRIBUTION
# =========================================================

def update_investment_contribution(
    user_id,
    transaction_id,
    new_asset_id,
    new_amount,
    new_description=None
):
    with engine.begin() as connection:

        old_transaction = connection.execute(
            text("""
                SELECT
                    amount,
                    asset_id
                FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
                    AND transaction_type =
                        'INVESTMENT_CONTRIBUTION'
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        ).fetchone()

        if old_transaction is None:
            raise ValueError(
                "Investment contribution was not found."
            )

        new_asset = connection.execute(
            text("""
                SELECT id
                FROM assets
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "asset_id": new_asset_id,
                "user_id": user_id
            }
        ).fetchone()

        if new_asset is None:
            raise ValueError(
                "Investment asset does not belong to this user."
            )

        # Reverse old contribution
        connection.execute(
            text("""
                UPDATE assets
                SET current_value =
                    current_value - :amount
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "amount": old_transaction.amount,
                "asset_id": old_transaction.asset_id,
                "user_id": user_id
            }
        )

        # Apply new contribution
        connection.execute(
            text("""
                UPDATE assets
                SET current_value =
                    current_value + :amount
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "amount": new_amount,
                "asset_id": new_asset_id,
                "user_id": user_id
            }
        )

        # Update transaction
        connection.execute(
            text("""
                UPDATE transactions
                SET
                    asset_id = :asset_id,
                    amount = :amount,
                    description = :description
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
            """),
            {
                "asset_id": new_asset_id,
                "amount": new_amount,
                "description": new_description,
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        )


# =========================================================
# DELETE INVESTMENT CONTRIBUTION
# =========================================================

def delete_investment_contribution(
    user_id,
    transaction_id
):
    with engine.begin() as connection:

        transaction = connection.execute(
            text("""
                SELECT
                    amount,
                    asset_id
                FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
                    AND transaction_type =
                        'INVESTMENT_CONTRIBUTION'
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        ).fetchone()

        if transaction is None:
            raise ValueError(
                "Investment contribution was not found."
            )

        # Reverse contribution
        connection.execute(
            text("""
                UPDATE assets
                SET current_value =
                    current_value - :amount
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "amount": transaction.amount,
                "asset_id": transaction.asset_id,
                "user_id": user_id
            }
        )

        # Delete transaction
        connection.execute(
            text("""
                DELETE FROM transactions
                WHERE
                    id = :transaction_id
                    AND user_id = :user_id
            """),
            {
                "transaction_id": transaction_id,
                "user_id": user_id
            }
        )
