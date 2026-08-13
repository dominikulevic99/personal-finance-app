from sqlalchemy import text

from database import engine


def get_assets(user_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    asset_type,
                    liquidity_class,
                    current_value,
                    currency
                FROM assets
                WHERE user_id = :user_id
                ORDER BY id
            """),
            {"user_id": user_id}
        )

        return result.fetchall()


def add_asset(
    user_id,
    name,
    asset_type,
    liquidity_class,
    current_value
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO assets (
                    user_id,
                    name,
                    asset_type,
                    liquidity_class,
                    current_value
                )
                VALUES (
                    :user_id,
                    :name,
                    :asset_type,
                    :liquidity_class,
                    :current_value
                )
            """),
            {
                "user_id": user_id,
                "name": name,
                "asset_type": asset_type,
                "liquidity_class": liquidity_class,
                "current_value": current_value
            }
        )


def update_asset(
    user_id,
    asset_id,
    name,
    asset_type,
    liquidity_class,
    current_value
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE assets
                SET
                    name = :name,
                    asset_type = :asset_type,
                    liquidity_class = :liquidity_class,
                    current_value = :current_value
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "name": name,
                "asset_type": asset_type,
                "liquidity_class": liquidity_class,
                "current_value": current_value,
                "asset_id": asset_id,
                "user_id": user_id
            }
        )


def delete_asset(user_id, asset_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM assets
                WHERE
                    id = :asset_id
                    AND user_id = :user_id
            """),
            {
                "asset_id": asset_id,
                "user_id": user_id
            }
        )
