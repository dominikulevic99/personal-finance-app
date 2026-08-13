from sqlalchemy import text

from database import engine


# =========================================================
# GET PLAN ITEMS
# =========================================================

def get_plan_items(
    user_id,
    monthly_plan_id
):
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    mpi.id,
                    mpi.monthly_plan_id,
                    mpi.name,
                    mpi.category_type,
                    mpi.planned_amount,
                    mpi.actual_amount,
                    mpi.fund_id,
                    mpi.asset_id
                FROM monthly_plan_items mpi

                JOIN monthly_plans mp
                    ON mp.id = mpi.monthly_plan_id

                WHERE
                    mpi.monthly_plan_id = :monthly_plan_id
                    AND mp.user_id = :user_id

                ORDER BY mpi.id
            """),
            {
                "monthly_plan_id": monthly_plan_id,
                "user_id": user_id
            }
        )

        return result.fetchall()


# =========================================================
# ADD PLAN ITEM
# =========================================================

def add_plan_item(
    user_id,
    monthly_plan_id,
    name,
    category_type,
    planned_amount,
    fund_id=None,
    asset_id=None
):
    with engine.begin() as connection:

        # ---------------------------------------------
        # VERIFY MONTHLY PLAN OWNERSHIP
        # ---------------------------------------------

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

        # ---------------------------------------------
        # VERIFY FUND OWNERSHIP
        # ---------------------------------------------

        if fund_id is not None:

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

        # ---------------------------------------------
        # VERIFY ASSET OWNERSHIP
        # ---------------------------------------------

        if asset_id is not None:

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
                    "Asset does not belong to this user."
                )

        # ---------------------------------------------
        # INSERT PLAN ITEM
        # ---------------------------------------------

        connection.execute(
            text("""
                INSERT INTO monthly_plan_items (
                    monthly_plan_id,
                    name,
                    category_type,
                    planned_amount,
                    actual_amount,
                    fund_id,
                    asset_id
                )
                VALUES (
                    :monthly_plan_id,
                    :name,
                    :category_type,
                    :planned_amount,
                    0,
                    :fund_id,
                    :asset_id
                )
            """),
            {
                "monthly_plan_id": monthly_plan_id,
                "name": name,
                "category_type": category_type,
                "planned_amount": planned_amount,
                "fund_id": fund_id,
                "asset_id": asset_id
            }
        )


# =========================================================
# UPDATE PLAN ITEM
# =========================================================

def update_plan_item(
    user_id,
    item_id,
    name,
    category_type,
    planned_amount,
    actual_amount,
    fund_id=None,
    asset_id=None
):
    with engine.begin() as connection:

        # ---------------------------------------------
        # VERIFY ITEM OWNERSHIP
        # ---------------------------------------------

        item = connection.execute(
            text("""
                SELECT
                    mpi.id,
                    mpi.category_type,
                    mpi.fund_id,
                    mpi.asset_id
                FROM monthly_plan_items mpi

                JOIN monthly_plans mp
                    ON mp.id = mpi.monthly_plan_id

                WHERE
                    mpi.id = :item_id
                    AND mp.user_id = :user_id
            """),
            {
                "item_id": item_id,
                "user_id": user_id
            }
        ).fetchone()

        if item is None:
            raise ValueError(
                "Plan item does not belong to this user."
            )

        # ---------------------------------------------
        # VERIFY FUND OWNERSHIP
        # ---------------------------------------------

        if fund_id is not None:

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

        # ---------------------------------------------
        # VERIFY ASSET OWNERSHIP
        # ---------------------------------------------

        if asset_id is not None:

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
                    "Asset does not belong to this user."
                )

        # ---------------------------------------------
        # UPDATE PLAN ITEM
        # ---------------------------------------------

        connection.execute(
            text("""
                UPDATE monthly_plan_items
                SET
                    name = :name,
                    category_type = :category_type,
                    planned_amount = :planned_amount,
                    actual_amount = :actual_amount,
                    fund_id = :fund_id,
                    asset_id = :asset_id
                WHERE id = :item_id
            """),
            {
                "item_id": item_id,
                "name": name,
                "category_type": category_type,
                "planned_amount": planned_amount,
                "actual_amount": actual_amount,
                "fund_id": fund_id,
                "asset_id": asset_id
            }
        )


# =========================================================
# DELETE PLAN ITEM
# =========================================================

def delete_plan_item(
    user_id,
    item_id
):
    with engine.begin() as connection:

        # ---------------------------------------------
        # VERIFY ITEM OWNERSHIP
        # ---------------------------------------------

        item = connection.execute(
            text("""
                SELECT
                    mpi.id,
                    mpi.category_type,
                    mpi.monthly_plan_id
                FROM monthly_plan_items mpi

                JOIN monthly_plans mp
                    ON mp.id = mpi.monthly_plan_id

                WHERE
                    mpi.id = :item_id
                    AND mp.user_id = :user_id
            """),
            {
                "item_id": item_id,
                "user_id": user_id
            }
        ).fetchone()

        if item is None:
            raise ValueError(
                "Plan item does not belong to this user."
            )

        # =================================================
        # GET ALL TRANSACTIONS CONNECTED TO ITEM
        # =================================================

        transactions = connection.execute(
            text("""
                SELECT
                    id,
                    transaction_type,
                    amount,
                    fund_id,
                    asset_id
                FROM transactions
                WHERE
                    user_id = :user_id
                    AND monthly_plan_item_id = :item_id
            """),
            {
                "user_id": user_id,
                "item_id": item_id
            }
        ).fetchall()

        # =================================================
        # REVERSE TRANSACTION EFFECTS
        # =================================================

        for transaction in transactions:

            # ---------------------------------------------
            # REVERSE FUND CONTRIBUTION
            # ---------------------------------------------

            if (
                transaction.transaction_type
                == "FUND_CONTRIBUTION"
                and transaction.fund_id is not None
            ):

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

            # ---------------------------------------------
            # REVERSE INVESTMENT CONTRIBUTION
            # ---------------------------------------------

            elif (
                transaction.transaction_type
                == "INVESTMENT_CONTRIBUTION"
                and transaction.asset_id is not None
            ):

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

        # =================================================
        # DELETE TRANSACTIONS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM transactions
                WHERE
                    user_id = :user_id
                    AND monthly_plan_item_id = :item_id
            """),
            {
                "user_id": user_id,
                "item_id": item_id
            }
        )

        # =================================================
        # DELETE PLAN ITEM
        # =================================================

        connection.execute(
            text("""
                DELETE FROM monthly_plan_items
                WHERE id = :item_id
            """),
            {
                "item_id": item_id
            }
        )
