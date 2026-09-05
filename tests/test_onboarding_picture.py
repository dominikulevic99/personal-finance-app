"""Read-only reveal tests with fixture data and no configured database access."""

import ast
import importlib
import sys
import unittest
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI
from calculations import calculate_financial_summary, calculate_planned_allocation_summary


with patch.dict(sys.modules, {
    "accounts": SimpleNamespace(get_accounts=None),
    "assets": SimpleNamespace(get_assets=None),
    "debts": SimpleNamespace(get_debts=None),
    "funds": SimpleNamespace(get_funds=None),
    "monthly_plans": SimpleNamespace(get_monthly_plan=None),
    "monthly_plan_items": SimpleNamespace(get_plan_items=None),
}):
    picture_ui = importlib.import_module("onboarding_picture")


class PictureUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.session_state.update({"onboarding_7_step": "financial_picture", "onboarding_7_plan_month": (2026, 9)})
        self.metrics = {}
        self.captions = []
        self.messages = []
        self.headlines = []
        self.html_output = []

    def title(self, title): self.headlines.append(title)
    def caption(self, text): self.captions.append(text)
    def info(self, text): self.messages.append(text)
    def html(self, text): self.html_output.append(text)
    def markdown(self, text): self.messages.append(text)
    def expander(self, *args): return nullcontext()
    def columns(self, count): return [nullcontext() for _ in range(count)]
    def metric(self, label, value, **kwargs): self.metrics[label] = value


class FinancialPictureTests(unittest.TestCase):
    def setUp(self):
        self.ui = PictureUI()
        self.accounts = [SimpleNamespace(balance=Decimal("2500"))]
        self.assets = [
            SimpleNamespace(current_value=Decimal("4000"), liquidity_class="LIQUID_INVESTMENT"),
            SimpleNamespace(current_value=Decimal("1000"), liquidity_class="SEMI_LIQUID"),
            SimpleNamespace(current_value=Decimal("100000"), liquidity_class="NON_LIQUID"),
        ]
        self.debts = [SimpleNamespace(remaining_balance=Decimal("20000"))]
        self.funds = [SimpleNamespace(current_balance=Decimal("300")), SimpleNamespace(current_balance=Decimal("200"))]
        self.plan = SimpleNamespace(id=70, planned_income=Decimal("2500"))
        self.items = [SimpleNamespace(planned_amount=Decimal(str(n))) for n in (1400, 300, 400, 200)]
        patch.object(picture_ui, "st", self.ui).start()
        self.readers = {}
        for name, result in {
            "get_accounts": self.accounts, "get_assets": self.assets,
            "get_debts": self.debts, "get_funds": self.funds,
            "get_monthly_plan": self.plan, "get_plan_items": self.items,
        }.items():
            self.readers[name] = patch.object(picture_ui, name, return_value=result).start()
        self.summary = patch.object(picture_ui, "calculate_financial_summary", wraps=calculate_financial_summary).start()
        self.addCleanup(patch.stopall)

    def test_displayed_metrics_match_shared_calculations(self):
        picture_ui.render_financial_picture(7)
        self.summary.assert_called_once_with(self.accounts, self.assets, self.debts, self.funds)
        self.assertEqual(self.ui.metrics, {
            "Net worth": "€87,500.00", "Available cash": "€2,500.00",
            "Debt": "€20,000.00", "Set aside in funds": "€500.00",
            "Liquid investments": "€4,000.00", "Semi-liquid assets": "€1,000.00",
            "Non-liquid assets": "€100,000.00", "Expected income": "€2,500.00",
            "Planned allocations": "€2,300.00", "Unallocated": "€200.00",
        })

    def test_all_reads_use_user_and_selected_month(self):
        picture_ui.load_financial_picture(8, 2026, 8)
        for name in ("get_accounts", "get_assets", "get_debts", "get_funds"):
            self.readers[name].assert_called_with(8)
        self.readers["get_monthly_plan"].assert_called_with(8, 2026, 8)
        self.readers["get_plan_items"].assert_called_with(8, 70)

    def test_render_does_not_change_state_or_records(self):
        state = dict(self.ui.session_state)
        before = repr((self.accounts, self.assets, self.debts, self.funds, self.plan, self.items))
        picture_ui.render_financial_picture(7)
        picture_ui.render_financial_picture(7)
        self.assertEqual(state, self.ui.session_state)
        self.assertEqual(before, repr((self.accounts, self.assets, self.debts, self.funds, self.plan, self.items)))

    def test_missing_plan_is_not_shown_as_zero_income(self):
        self.readers["get_monthly_plan"].return_value = None
        picture_ui.render_financial_picture(7)
        self.assertNotIn("Expected income", self.ui.metrics)
        self.assertIn("No monthly plan is saved for this month yet.", self.ui.messages)
        self.readers["get_plan_items"].assert_not_called()

    def test_zero_income_plan_is_distinct_from_missing_plan(self):
        self.plan.planned_income = Decimal("0")
        self.items.clear()
        picture_ui.render_financial_picture(7)
        self.assertEqual(self.ui.metrics["Expected income"], "€0.00")
        self.assertEqual(self.ui.metrics["Unallocated"], "€0.00")

    def test_empty_optional_data_renders_without_errors(self):
        self.accounts.clear()
        self.assets.clear()
        self.debts.clear()
        self.funds.clear()
        picture_ui.render_financial_picture(7)
        self.assertEqual(self.ui.metrics["Net worth"], "€0.00")
        self.assertEqual(self.ui.metrics["Set aside in funds"], "€0.00")
        self.assertFalse(self.ui.errors)

    def test_negative_values_are_not_hidden_or_judged(self):
        self.debts[0].remaining_balance = Decimal("200000")
        self.plan.planned_income = Decimal("2000")
        picture_ui.render_financial_picture(7)
        self.assertEqual(self.ui.metrics["Net worth"], "€-92,500.00")
        self.assertEqual(self.ui.metrics["Unallocated"], "€-300.00")
        self.assertIn("Your planned allocations currently exceed your expected income.", self.ui.captions)

    def test_any_read_failure_shows_retry_without_partial_metrics(self):
        for reader in self.readers.values():
            with self.subTest(reader=reader):
                reader.side_effect = RuntimeError("private database detail")
                picture_ui.render_financial_picture(7)
                self.assertFalse(self.ui.metrics)
                self.assertNotIn("Your financial picture is ready.", self.ui.headlines)
                self.assertIn("Retry", self.ui.buttons)
                self.assertNotIn("private database detail", str(self.ui.errors))
                reader.side_effect = None

    def test_reveal_only_imports_readers_from_database_modules(self):
        tree = ast.parse(Path(picture_ui.__file__).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotEqual(node.module, "transactions")
                if node.module in ("accounts", "assets", "debts", "funds", "monthly_plans", "monthly_plan_items"):
                    self.assertTrue(all(alias.name.startswith("get_") for alias in node.names))

    def test_monthly_helper_retains_previous_float_formulas(self):
        for income in (Decimal("0"), Decimal("2500.01")):
            for items in ([], self.items):
                allocated = sum(float(item.planned_amount) for item in items)
                self.assertEqual(calculate_planned_allocation_summary(income, items),
                                 {"allocated": allocated, "remaining": float(income) - allocated})

    def test_completed_shell_and_existing_step_progress(self):
        import onboarding_layout
        with patch.object(onboarding_layout, "st", self.ui):
            with onboarding_layout.onboarding_shell(complete=True): pass
            self.assertIn("Setup complete", self.ui.html_output[-1])
            self.assertIn('aria-valuenow="5"', self.ui.html_output[-1])
            with onboarding_layout.onboarding_shell(step=2): pass
            self.assertIn("Step 2 of 5", self.ui.html_output[-1])
            self.assertIn('aria-valuenow="1"', self.ui.html_output[-1])


if __name__ == "__main__":
    unittest.main()
