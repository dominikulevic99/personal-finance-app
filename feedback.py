from sqlalchemy import text

from database import engine


# =========================================================
# ADD FEEDBACK
# =========================================================

def add_feedback(
    user_id,
    message
):
    with engine.begin() as connection:

        # Verify user exists
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

        connection.execute(
            text("""
                INSERT INTO feedback (
                    user_id,
                    message
                )
                VALUES (
                    :user_id,
                    :message
                )
            """),
            {
                "user_id": user_id,
                "message": message
            }
        )


# =========================================================
# GET USER FEEDBACK
# =========================================================

def get_user_feedback(
    user_id
):
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    id,
                    message,
                    created_at
                FROM feedback
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {
                "user_id": user_id
            }
        )

        return result.fetchall()
