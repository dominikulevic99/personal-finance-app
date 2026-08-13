from sqlalchemy import text

from database import engine


def get_or_create_user(email, name=None):
    with engine.begin() as connection:

        user = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    email,
                    currency
                FROM users
                WHERE email = :email
            """),
            {
                "email": email
            }
        ).fetchone()

        if user is not None:
            return user

        result = connection.execute(
            text("""
                INSERT INTO users (
                    name,
                    email,
                    currency
                )
                VALUES (
                    :name,
                    :email,
                    'EUR'
                )
                RETURNING
                    id,
                    name,
                    email,
                    currency
            """),
            {
                "name": name or email,
                "email": email
            }
        )

        return result.fetchone()
