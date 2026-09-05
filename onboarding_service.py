"""Read-only eligibility checks for guided setup."""

from sqlalchemy import text

from database import engine


def has_financial_data(user_id):
    """Count any financial record, including zero balances and older plans."""
    with engine.connect() as connection:
        return bool(connection.execute(
            text("""
                SELECT
                    EXISTS (SELECT 1 FROM accounts WHERE user_id = :user_id)
                    OR EXISTS (SELECT 1 FROM assets WHERE user_id = :user_id)
                    OR EXISTS (SELECT 1 FROM debts WHERE user_id = :user_id)
                    OR EXISTS (SELECT 1 FROM funds WHERE user_id = :user_id)
                    OR EXISTS (SELECT 1 FROM monthly_plans WHERE user_id = :user_id)
                    OR EXISTS (SELECT 1 FROM transactions WHERE user_id = :user_id)
                    OR EXISTS (
                        SELECT 1 FROM monthly_plan_items mpi
                        JOIN monthly_plans mp ON mp.id = mpi.monthly_plan_id
                        WHERE mp.user_id = :user_id
                    )
            """),
            {"user_id": user_id},
        ).scalar_one())


def get_entry_route(
    user_id, started=False, dashboard_requested=False, force_welcome=False
):
    """Explicit session choices take precedence over data-based routing."""
    if dashboard_requested:
        return "dashboard"
    if started:
        return "started"
    if force_welcome:
        return "welcome"
    return "dashboard" if has_financial_data(user_id) else "welcome"
