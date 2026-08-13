from sqlalchemy import text

from database import engine


# =========================================================
# DELETE ALL USER DATA
# =========================================================

def delete_all_user_data(user_id):

    with engine.begin() as connection:

        # =================================================
        # VERIFY USER
        # =================================================

        user = connection.execute(
            text("""
                SELECT id
                FROM users
                WHERE id = :user_id
            """),
            {
                "user_id": user_id
            }
        ).fetchone()

        if user is None:
            raise ValueError(
                "User does not exist."
            )

        # =================================================
        # DELETE TRANSACTIONS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM transactions
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE MONTHLY PLAN ITEMS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM monthly_plan_items
                WHERE monthly_plan_id IN (
                    SELECT id
                    FROM monthly_plans
                    WHERE user_id = :user_id
                )
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE MONTHLY PLANS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM monthly_plans
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE FUNDS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM funds
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE ASSETS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM assets
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE DEBTS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM debts
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE ACCOUNTS
        # =================================================

        connection.execute(
            text("""
                DELETE FROM accounts
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )

        # =================================================
        # DELETE FEEDBACK
        # =================================================

        connection.execute(
            text("""
                DELETE FROM feedback
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        )
