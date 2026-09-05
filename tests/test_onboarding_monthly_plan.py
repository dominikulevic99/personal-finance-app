"""Offline monthly setup tests; database operations are replaced with spies."""

import ast
import importlib
import sys
import unittest
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI, Rerun


with patch.dict(sys.modules, {
    "assets": SimpleNamespace(get_assets=None),
    "funds": SimpleNamespace(get_funds=None),
    "monthly_plans": SimpleNamespace(get_monthly_plan=None, create_monthly_plan=None, update_planned_income=None),
    "monthly_plan_items": SimpleNamespace(get_plan_items=None, add_plan_item=None),
}):
    plan_ui = importlib.import_module("onboarding_monthly_plan")


class PlanUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.session_state.update({"onboarding_7_step": "monthly_plan", "onboarding_7_plan_month": (2026, 9)})
        self.income = 2500.0
        self.amount = 1400.0
        self.name = "Living expenses"
        self.category = "EXPENSE"
        self.target = None
        self.submit_label = None
        self.metrics = {}
        self.options = {}
        self.warnings = []

    def expander(self, *args): return nullcontext()
    def markdown(self, *args): pass
    def columns(self, count): return [nullcontext() for _ in range(count)]
    def metric(self, label, value): self.metrics[label] = value
    def warning(self, message): self.warnings.append(message)
    def number_input(self, *args, **kwargs):
        return self.income if "income_" in kwargs["key"] else self.amount
    def selectbox(self, label, **kwargs):
        self.options[label] = kwargs["options"]
        return self.category if kwargs["key"].endswith("category") else self.target
    def form_submit_button(self, label, **kwargs):
        return label == self.submit_label and not kwargs.get("disabled", False)


class MonthlyPlanStepTests(unittest.TestCase):
    def setUp(self):
        self.ui = PlanUI()
        self.prefix = "onboarding_7_plan_2026_9_"
        self.plan = None
        self.items = []
        self.funds = [SimpleNamespace(id=10, name="Emergency fund", current_balance=Decimal("300"))]
        self.assets = [
            SimpleNamespace(id=20, name="Investments", asset_type="INVESTMENT", current_value=Decimal("1000")),
            SimpleNamespace(id=21, name="Home", asset_type="REAL_ESTATE", current_value=Decimal("100000")),
        ]
        patch.object(plan_ui, "st", self.ui).start()
        self.read = patch.object(plan_ui, "get_monthly_plan", side_effect=lambda *a: self.plan).start()
        self.create = patch.object(plan_ui, "create_monthly_plan", side_effect=self.create_plan).start()
        self.update = patch.object(plan_ui, "update_planned_income", side_effect=self.update_income).start()
        self.read_items = patch.object(plan_ui, "get_plan_items", return_value=self.items).start()
        self.read_funds = patch.object(plan_ui, "get_funds", return_value=self.funds).start()
        self.read_assets = patch.object(plan_ui, "get_assets", return_value=self.assets).start()
        self.add = patch.object(plan_ui, "add_plan_item", side_effect=self.add_item).start()
        self.addCleanup(patch.stopall)

    def create_plan(self, uid=7, year=2026, month=9, income=2500.0):
        self.plan = SimpleNamespace(id=70, user_id=uid, year=year, month=month,
                                    planned_income=Decimal(str(income)), actual_income=Decimal("900"), status="OPEN")

    def update_income(self, uid, plan_id, income):
        self.plan.planned_income = Decimal(str(income))

    def add_item(self, uid, plan_id, name, category, amount, fund_id=None, asset_id=None):
        self.items.append(SimpleNamespace(
            id=len(self.items) + 1, name=name, category_type=category,
            planned_amount=Decimal(str(amount)), actual_amount=Decimal("0"), fund_id=fund_id, asset_id=asset_id,
        ))

    def render(self, uid=7):
        try:
            plan_ui.render_monthly_plan_step(uid)
        except Rerun:
            pass

    def test_example_and_initial_view_do_not_write(self):
        self.render()
        self.create.assert_not_called()
        self.add.assert_not_called()
        self.update.assert_not_called()
        self.assertNotIn("See my financial picture", self.ui.buttons)

    def test_create_income_reuses_current_pinned_month(self):
        self.ui.submit_label = "Save expected income"
        self.render()
        self.create.assert_called_once_with(7, 2026, 9, 2500.0)
        self.ui.submit_label = None
        self.render()
        self.create.assert_called_once()
        self.assertEqual(self.ui.metrics["Expected income"], "€2,500.00")

    def test_existing_plan_is_only_updated_by_explicit_income_save(self):
        self.create_plan()
        self.add_item(7, 70, "Existing", "EXPENSE", 100)
        self.items[0].actual_amount = Decimal("50")
        self.render()
        self.create.assert_not_called()
        self.update.assert_not_called()
        self.ui.session_state[self.prefix + "edit_income"] = True
        self.ui.income, self.ui.submit_label = 3000.0, "Save expected income"
        self.render()
        self.update.assert_called_once_with(7, 70, 3000.0)
        self.assertEqual(self.plan.actual_income, Decimal("900"))
        self.assertEqual(self.items[0].actual_amount, Decimal("50"))

    def test_plan_appearing_before_create_is_not_overwritten(self):
        external = SimpleNamespace(id=99, planned_income=Decimal("1800"))
        self.read.side_effect = [None, external]
        self.ui.submit_label = "Save expected income"
        self.render()
        self.create.assert_not_called()
        self.update.assert_not_called()

    def test_invalid_income_rejected_and_zero_allowed(self):
        self.ui.submit_label = "Save expected income"
        for value in (None, -1.0):
            self.ui.income = value
            self.render()
            self.create.assert_not_called()
        self.ui.income = 0.0
        self.render()
        self.create.assert_called_once_with(7, 2026, 9, 0.0)

    def test_categories_match_dashboard(self):
        tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8-sig"))
        options = next(ast.literal_eval(n.value.args[1]) for n in ast.walk(tree)
                       if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                       and any(isinstance(t, ast.Name) and t.id == "plan_item_type" for t in n.targets))
        self.assertEqual(list(plan_ui.ALLOCATION_TYPES), options)

    def test_allocations_pass_exact_categories_links_and_owner(self):
        self.create_plan()
        for category in plan_ui.ALLOCATION_TYPES:
            with self.subTest(category=category):
                self.ui.session_state[self.prefix + "allocation_open"] = True
                self.ui.category = category
                self.ui.target = 10 if category == "FUND" else 20 if category == "INVESTMENT" else None
                self.ui.submit_label = "Add allocation"
                self.render()
                self.add.assert_called_with(7, 70, self.ui.name, category, 1400.0,
                                            fund_id=10 if category == "FUND" else None,
                                            asset_id=20 if category == "INVESTMENT" else None)
        self.assertEqual(self.funds[0].current_balance, Decimal("300"))
        self.assertEqual(self.assets[0].current_value, Decimal("1000"))
        self.assertEqual(self.ui.options["Which investment?"], [20])
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "monthly_plan")

    def test_missing_or_wrong_targets_do_not_write(self):
        self.create_plan()
        self.ui.category, self.ui.submit_label = "INVESTMENT", "Add allocation"
        for target in (None, 21, 999):
            self.ui.target = target
            self.render()
            self.add.assert_not_called()
        self.assets.clear()
        self.render()
        self.assertIn("Back to Assets", self.ui.buttons)
        self.ui.category = "FUND"
        self.funds.clear()
        self.render()
        self.assertIn("Back to Funds", self.ui.buttons)
        self.add.assert_not_called()

    def test_invalid_allocation_drafts_do_not_write(self):
        self.create_plan()
        self.ui.submit_label = "Add allocation"
        for name, amount in [("  ", 10.0), ("Living costs", None), ("Living costs", -1.0)]:
            self.ui.name, self.ui.amount = name, amount
            self.render()
            self.add.assert_not_called()

    def test_totals_overallocation_and_income_update(self):
        self.create_plan()
        self.add_item(7, 70, "Living costs", "EXPENSE", 1400)
        self.add_item(7, 70, "Saving", "FUND", 300, fund_id=10)
        self.add_item(7, 70, "Investing", "INVESTMENT", 400, asset_id=20)
        self.add_item(7, 70, "Travel", "FUND", 200, fund_id=10)
        self.render()
        self.assertEqual(self.ui.metrics["Planned allocations"], "€2,300.00")
        self.assertEqual(self.ui.metrics["Unallocated"], "€200.00")
        self.plan.planned_income = Decimal("2000")
        self.render()
        self.assertEqual(self.ui.metrics["Unallocated"], "€-300.00")
        self.assertTrue(self.ui.warnings)

    def test_fresh_draft_and_finish_go_to_reveal_not_dashboard(self):
        self.create_plan()
        self.ui.submit_label = "Add allocation"
        self.render()
        self.assertEqual(self.ui.session_state[self.prefix + "allocation_version"], 1)
        self.ui.submit_label, self.ui.click = None, "Add another allocation"
        self.render()
        self.assertTrue(self.ui.session_state[self.prefix + "allocation_open"])
        self.ui.click = "Cancel"
        self.render()
        self.ui.click = "See my financial picture"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "financial_picture")
        self.assertNotIn("onboarding_7_dashboard", self.ui.session_state)

    def test_income_only_plan_can_finish_without_creating_allocations(self):
        self.create_plan(income=0)
        self.ui.click = "Plan allocations later"
        self.render()
        self.ui.click = "See my financial picture"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "financial_picture")
        self.add.assert_not_called()

    def test_read_failures_never_create_or_update(self):
        self.create_plan()
        for reader in (self.read, self.read_items, self.read_funds, self.read_assets):
            previous = reader.side_effect
            reader.side_effect = RuntimeError("private detail")
            self.ui.submit_label = "Add allocation"
            self.render()
            self.create.assert_not_called()
            self.update.assert_not_called()
            self.add.assert_not_called()
            reader.side_effect = previous
        self.assertNotIn("private detail", str(self.ui.errors))

    def test_write_failure_offers_reload_on_next_rerun(self):
        self.create_plan()
        self.add.side_effect = RuntimeError("private detail")
        self.ui.submit_label = "Add allocation"
        self.render()
        self.ui.submit_label = None
        self.render()
        self.assertIn("Reload allocations", self.ui.buttons)
        self.assertNotIn("private detail", str(self.ui.errors))

    def test_module_does_not_import_transactions_or_balance_writers(self):
        tree = ast.parse(Path(plan_ui.__file__).read_text(encoding="utf-8-sig"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("transactions", imports)
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & {"add_fund_contribution", "add_investment_contribution", "update_fund", "update_asset", "update_account"})

    def test_period_drafts_reads_and_writes_are_user_scoped(self):
        self.ui.session_state["onboarding_8_plan_month"] = (2026, 8)
        self.ui.session_state[self.prefix + "allocation_open"] = False
        self.create_plan(uid=8, month=8)
        self.ui.submit_label = "Add allocation"
        self.render(8)
        self.read.assert_called_with(8, 2026, 8)
        self.read_items.assert_called_with(8, 70)
        self.read_funds.assert_called_with(8)
        self.read_assets.assert_called_with(8)
        self.add.assert_called_once_with(8, 70, self.ui.name, "EXPENSE", 1400.0, fund_id=None, asset_id=None)
        self.assertEqual(self.ui.session_state["onboarding_8_plan_2026_8_allocation_version"], 1)
        self.assertNotIn(self.prefix + "allocation_version", self.ui.session_state)


if __name__ == "__main__":
    unittest.main()
