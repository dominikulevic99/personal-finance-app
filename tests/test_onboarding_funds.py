"""Offline Funds onboarding checks with mocked account/fund database functions."""

import importlib
import sys
import unittest
from contextlib import nullcontext
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI, Rerun
from calculations import calculate_financial_summary


with patch.dict(sys.modules, {
    "funds": SimpleNamespace(add_fund=None, get_funds=None),
    "accounts": SimpleNamespace(get_accounts=None),
}):
    funds_ui = importlib.import_module("onboarding_funds")


class FundsUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.name = "Emergency fund"
        self.balance = 500.0
        self.target = 3000.0
        self.session_state["onboarding_7_step"] = "funds"

    def expander(self, *args): return nullcontext()
    def warning(self, message): self.errors.append(message)
    def number_input(self, *args, **kwargs):
        return getattr(self, kwargs["key"].rsplit("_", 1)[-1])


class FundsStepTests(unittest.TestCase):
    def setUp(self):
        self.ui = FundsUI()
        self.records = []
        self.accounts = [SimpleNamespace(balance=Decimal("1250.00"))]
        patch.object(funds_ui, "st", self.ui).start()
        self.read = patch.object(funds_ui, "get_funds", return_value=self.records).start()
        self.account_read = patch.object(funds_ui, "get_accounts", return_value=self.accounts).start()
        self.add = patch.object(funds_ui, "add_fund", side_effect=self.save).start()
        self.addCleanup(patch.stopall)

    def save(self, user_id, name, balance, target):
        self.records.append(SimpleNamespace(
            id=len(self.records) + 1, name=name,
            current_balance=Decimal(str(balance)),
            target_amount=None if target is None else Decimal(str(target)),
        ))

    def render(self, user_id=7):
        try:
            funds_ui.render_funds_step(user_id)
        except Rerun:
            pass

    def test_create_reuses_function_and_stays_on_funds(self):
        self.ui.submit = True
        self.render()
        self.add.assert_called_once_with(7, "Emergency fund", 500.0, 3000.0)
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "funds")
        self.assertTrue(self.ui.session_state["onboarding_7_started"])
        self.assertNotIn("onboarding_7_dashboard", self.ui.session_state)
        self.ui.submit = False
        self.render()
        self.add.assert_called_once()
        self.assertIn("Continue", self.ui.buttons)

    def test_existing_calculation_does_not_count_fund_as_extra_wealth(self):
        before = calculate_financial_summary(self.accounts, [], [], [])
        self.ui.submit = True
        self.render()
        after = calculate_financial_summary(self.accounts, [], [], self.records)
        self.assertEqual(before["net_worth"], after["net_worth"])
        self.assertEqual(before["available_cash"], after["available_cash"])
        self.assertEqual(after["free_cash"], Decimal("750.00"))

    def test_invalid_name_and_negative_amounts_do_not_write(self):
        for field, value in [("name", "  "), ("balance", -1.0), ("target", -1.0)]:
            with self.subTest(field=field):
                previous = getattr(self.ui, field)
                setattr(self.ui, field, value)
                self.ui.submit = True
                self.render()
                self.add.assert_not_called()
                self.assertTrue(self.ui.errors)
                setattr(self.ui, field, previous)

    def test_starting_balance_above_cash_is_rejected(self):
        self.ui.balance, self.ui.submit = 1250.01, True
        self.render()
        self.add.assert_not_called()
        self.assertTrue(self.ui.errors)

    def test_starting_balance_equal_to_cash_is_allowed(self):
        self.ui.balance, self.ui.submit = 1250.0, True
        self.render()
        self.add.assert_called_once_with(7, self.ui.name, 1250.0, 3000.0)

    def test_zero_start_and_no_target_work_without_accounts(self):
        self.accounts.clear()
        self.ui.balance, self.ui.target, self.ui.submit = 0.0, 0.0, True
        self.render()
        self.add.assert_called_once_with(7, self.ui.name, 0.0, 0.0)

    def test_add_another_then_continue(self):
        self.ui.submit = True
        self.render()
        self.ui.submit, self.ui.click = False, "Add another"
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_fund_form_open"])
        self.assertEqual(self.ui.session_state["onboarding_7_fund_form_version"], 1)
        self.ui.name, self.ui.click, self.ui.submit = "Travel", None, True
        self.render()
        self.ui.submit, self.ui.click = False, "Continue"
        self.render()
        self.assertEqual(len(self.records), 2)
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "monthly_plan")

    def test_skip_draft_preserves_existing_funds_and_back_navigation(self):
        self.save(7, "Existing", 100.0, None)
        self.ui.session_state["onboarding_7_fund_form_open"] = True
        self.ui.click = "Skip for now"
        self.render()
        self.add.assert_not_called()
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "monthly_plan")
        self.ui.click = "Back to Debts"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")

    def test_empty_user_can_skip_without_creation(self):
        self.ui.click = "Skip for now"
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "monthly_plan")

    def test_read_failures_do_not_assume_zero_cash_or_create_fund(self):
        for reader in (self.read, self.account_read):
            with self.subTest(reader=reader):
                reader.side_effect = RuntimeError("private detail")
                self.ui.submit = True
                self.render()
                self.add.assert_not_called()
                self.assertNotIn("private detail", str(self.ui.errors))
                reader.side_effect = None

    def test_save_failure_keeps_refresh_available(self):
        self.add.side_effect = RuntimeError("private detail")
        self.ui.submit = True
        self.render()
        self.ui.submit = False
        self.render()
        self.assertIn("Refresh fund list", self.ui.buttons)
        self.assertNotIn("private detail", str(self.ui.errors))
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "funds")

    def test_state_and_data_access_are_user_scoped(self):
        self.ui.session_state["onboarding_7_fund_form_open"] = False
        self.ui.submit = True
        self.render(8)
        self.read.assert_called_with(8)
        self.account_read.assert_called_with(8)
        self.add.assert_called_once_with(8, self.ui.name, 500.0, 3000.0)
        self.assertEqual(self.ui.session_state["onboarding_8_fund_form_version"], 1)
        self.assertNotIn("onboarding_7_fund_form_version", self.ui.session_state)


if __name__ == "__main__":
    unittest.main()
