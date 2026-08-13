def calculate_financial_summary(
    accounts,
    assets,
    debts,
    funds
):

    available_cash = sum(
        account.balance
        for account in accounts
    )

    liquid_investments = sum(
        asset.current_value
        for asset in assets
        if asset.liquidity_class == "LIQUID_INVESTMENT"
    )

    semi_liquid_assets = sum(
        asset.current_value
        for asset in assets
        if asset.liquidity_class == "SEMI_LIQUID"
    )

    non_liquid_assets = sum(
        asset.current_value
        for asset in assets
        if asset.liquidity_class == "NON_LIQUID"
    )

    all_assets_value = sum(
        asset.current_value
        for asset in assets
    )

    total_debt = sum(
        debt.remaining_balance
        for debt in debts
    )

    total_reserved_funds = sum(
        fund.current_balance
        for fund in funds
    )

    free_cash = (
        available_cash
        - total_reserved_funds
    )

    liquid_worth = (
        available_cash
        + liquid_investments
    )

    net_worth = (
        available_cash
        + all_assets_value
        - total_debt
    )

    return {
        "available_cash": available_cash,
        "reserved_funds": total_reserved_funds,
        "free_cash": free_cash,
        "liquid_worth": liquid_worth,
        "total_debt": total_debt,
        "net_worth": net_worth,
        "liquid_investments": liquid_investments,
        "semi_liquid_assets": semi_liquid_assets,
        "non_liquid_assets": non_liquid_assets
    }
