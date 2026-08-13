from sqlalchemy import text

from database import engine


def get_monthly_plan(
    user_id,
    year,
    month
):
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    id,
                    user_id,
                    year,
                    month,
                    planned_income,
                    actual_income,
                    status
                FROM monthly_plans
                WHERE
                    user_id = :user_id
                    AND year = :year
                    AND month = :month
            """),
            {
                "user_id": user_id,
                "year": year,
                "month": month
            }
        )

        return result.fetchone()


def create_monthly_plan(
    user_id,
    year,
    month,
    planned_income
):
    with engine.begin() as connection:

        connection.execute(
            text("""
                INSERT INTO monthly_plans (
                    user_id,
                    year,
                    month,
                    planned_income
                )
                VALUES (
                    :user_id,
                    :year,
                    :month,
                    :planned_income
                )
            """),
            {
                "user_id": user_id,
                "year": year,
                "month": month,
                "planned_income": planned_income
            }
        )


def update_planned_income(
    user_id,
    plan_id,
    planned_income
):
    with engine.begin() as connection:

        connection.execute(
            text("""
                UPDATE monthly_plans
                SET planned_income = :planned_income
                WHERE
                    id = :plan_id
                    AND user_id = :user_id
            """),
            {
                "planned_income": planned_income,
                "plan_id": plan_id,
                "user_id": user_id
            }
        )
