from sqlalchemy import text

from database import engine


def get_accounts(user_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    account_type,
                    balance,
                    currency
                FROM accounts
                WHERE user_id = :user_id
                ORDER BY id
            """),
            {"user_id": user_id}
        )

        return result.fetchall()


def add_account(user_id, name, account_type, balance):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO accounts (
                    user_id,
                    name,
                    account_type,
                    balance
                )
                VALUES (
                    :user_id,
                    :name,
                    :account_type,
                    :balance
                )
            """),
            {
                "user_id": user_id,
                "name": name,
                "account_type": account_type,
                "balance": balance
            }
        )


def update_account(
    user_id,
    account_id,
    name,
    account_type,
    balance
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE accounts
                SET
                    name = :name,
                    account_type = :account_type,
                    balance = :balance
                WHERE
                    id = :account_id
                    AND user_id = :user_id
            """),
            {
                "name": name,
                "account_type": account_type,
                "balance": balance,
                "account_id": account_id,
                "user_id": user_id
            }
        )


def delete_account(user_id, account_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM accounts
                WHERE
                    id = :account_id
                    AND user_id = :user_id
            """),
            {
                "account_id": account_id,
                "user_id": user_id
            }
        )
