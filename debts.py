from sqlalchemy import text

from database import engine


def get_debts(user_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    debt_type,
                    remaining_balance,
                    monthly_payment,
                    interest_rate,
                    currency
                FROM debts
                WHERE user_id = :user_id
                ORDER BY id
            """),
            {"user_id": user_id}
        )

        return result.fetchall()


def add_debt(
    user_id,
    name,
    debt_type,
    remaining_balance,
    monthly_payment,
    interest_rate
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO debts (
                    user_id,
                    name,
                    debt_type,
                    remaining_balance,
                    monthly_payment,
                    interest_rate
                )
                VALUES (
                    :user_id,
                    :name,
                    :debt_type,
                    :remaining_balance,
                    :monthly_payment,
                    :interest_rate
                )
            """),
            {
                "user_id": user_id,
                "name": name,
                "debt_type": debt_type,
                "remaining_balance": remaining_balance,
                "monthly_payment": monthly_payment,
                "interest_rate": interest_rate
            }
        )


def update_debt(
    user_id,
    debt_id,
    name,
    debt_type,
    remaining_balance,
    monthly_payment,
    interest_rate
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE debts
                SET
                    name = :name,
                    debt_type = :debt_type,
                    remaining_balance = :remaining_balance,
                    monthly_payment = :monthly_payment,
                    interest_rate = :interest_rate
                WHERE
                    id = :debt_id
                    AND user_id = :user_id
            """),
            {
                "name": name,
                "debt_type": debt_type,
                "remaining_balance": remaining_balance,
                "monthly_payment": monthly_payment,
                "interest_rate": interest_rate,
                "debt_id": debt_id,
                "user_id": user_id
            }
        )


def delete_debt(user_id, debt_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM debts
                WHERE
                    id = :debt_id
                    AND user_id = :user_id
            """),
            {
                "debt_id": debt_id,
                "user_id": user_id
            }
        )
