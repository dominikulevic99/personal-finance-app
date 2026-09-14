from sqlalchemy import text

from database import engine

FEEDBACK_OPTIONS = (
    "easier_data_entry", "bank_connection", "investment_tracking", "spending_analysis",
    "progress_over_time", "better_monthly_planning", "navigation_clarity", "nothing_missing", "other",
)


# =========================================================
# ADD FEEDBACK
# =========================================================

def add_feedback(
    user_id,
    message,
    selected_options=(),
    source="sidebar",
):
    options = list(dict.fromkeys(selected_options))
    if any(option not in FEEDBACK_OPTIONS for option in options):
        raise ValueError("Invalid feedback option.")
    if "nothing_missing" in options and len(options) > 1:
        raise ValueError("Conflicting feedback options.")
    if source not in ("product_tour", "sidebar"):
        raise ValueError("Invalid feedback source.")
    message = message.strip()
    if not options and not message:
        raise ValueError("Feedback is empty.")
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
                    message,
                    selected_options,
                    source
                )
                VALUES (
                    :user_id,
                    :message,
                    :selected_options,
                    :source
                )
            """),
            {
                "user_id": user_id,
                "message": message,
                "selected_options": options,
                "source": source,
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
                    created_at,
                    selected_options,
                    source
                FROM feedback
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {
                "user_id": user_id
            }
        )

        return result.fetchall()
