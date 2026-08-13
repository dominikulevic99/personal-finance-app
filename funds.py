from sqlalchemy import text

from database import engine


def get_funds(user_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    current_balance,
                    target_amount
                FROM funds
                WHERE user_id = :user_id
                ORDER BY id
            """),
            {"user_id": user_id}
        )

        return result.fetchall()


def add_fund(
    user_id,
    name,
    current_balance,
    target_amount
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO funds (
                    user_id,
                    name,
                    current_balance,
                    target_amount
                )
                VALUES (
                    :user_id,
                    :name,
                    :current_balance,
                    :target_amount
                )
            """),
            {
                "user_id": user_id,
                "name": name,
                "current_balance": current_balance,
                "target_amount": target_amount
            }
        )


def update_fund(
    user_id,
    fund_id,
    name,
    current_balance,
    target_amount
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE funds
                SET
                    name = :name,
                    current_balance = :current_balance,
                    target_amount = :target_amount
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "name": name,
                "current_balance": current_balance,
                "target_amount": target_amount,
                "fund_id": fund_id,
                "user_id": user_id
            }
        )


def delete_fund(user_id, fund_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM funds
                WHERE
                    id = :fund_id
                    AND user_id = :user_id
            """),
            {
                "fund_id": fund_id,
                "user_id": user_id
            }
        )
