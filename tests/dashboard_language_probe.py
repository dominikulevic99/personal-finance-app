"""Offline full-dashboard fixture. Every database call is replaced with test data."""

from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace as Record
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("database", Record(engine=None))
import streamlit as st
import accounts, assets, debts, funds, monthly_plans, monthly_plan_items, transactions, users, feedback, analytics

account = Record(id=11, name="Original Fund account", account_type="BANK", balance=5000, currency="EUR")
asset = Record(id=12, name="Original investment", asset_type="INVESTMENT", liquidity_class="LIQUID_INVESTMENT", current_value=2000, currency="EUR")
debt = Record(id=13, name="Original debt", debt_type="OTHER", remaining_balance=300, monthly_payment=30, interest_rate=0, currency="EUR")
fund = Record(id=14, name="Original Fund", current_balance=500, target_amount=1500)
plan = Record(id=15, year=2026, month=9, planned_income=2500, actual_income=0, status="DRAFT")
items = [Record(id=i, name=kind, category_type=kind, planned_amount=100, actual_amount=0,
                fund_id=14 if kind == "FUND" else None, asset_id=12 if kind == "INVESTMENT" else None)
         for i, kind in enumerate(("EXPENSE", "FUND", "INVESTMENT", "DEBT_PAYMENT", "OTHER"), 20)]
history = [Record(id=40, amount=50, description="Original description", created_at=datetime(2026, 9, 1), transaction_type="FUND_CONTRIBUTION"),
           Record(id=41, amount=25, description="Investment description", created_at=datetime(2026, 9, 1), transaction_type="INVESTMENT_CONTRIBUTION")]

st.session_state.setdefault("onboarding_7_dashboard", True)
with ExitStack() as stack:
    stack.enter_context(patch.object(st, "user", Record(is_logged_in=True, email="test@example.invalid", get=lambda key: "Test")))
    for module, name, result in (
        (accounts,"get_accounts",[account]), (assets,"get_assets",[asset]), (debts,"get_debts",[debt]),
        (funds,"get_funds",[fund]), (monthly_plans,"get_monthly_plan",plan),
        (monthly_plan_items,"get_plan_items",items), (transactions,"get_transactions_for_item",history),
        (transactions,"get_transactions_for_month",history), (feedback,"get_user_feedback",[]),
        (users,"get_or_create_user",Record(id=7,email="test@example.invalid")), (analytics,"track_event",False),
    ):
        stack.enter_context(patch.object(module,name,return_value=result))
    # Financial writes must never occur merely from rendering or switching language.
    for module in (accounts, assets, debts, funds, monthly_plans, monthly_plan_items, transactions, feedback):
        for name in dir(module):
            if name.startswith(("add_", "update_", "delete_", "create_")):
                stack.enter_context(patch.object(module,name,side_effect=AssertionError("Unexpected financial write")))
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "app.py"), run_name="__main__")
