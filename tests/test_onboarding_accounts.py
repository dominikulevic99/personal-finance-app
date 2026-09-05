"""Offline UI flow checks. No secrets, real database, or financial writes."""

import importlib
import sys
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch


# Import the UI against a stub accounts module, not the database configuration.
with patch.dict(sys.modules, {"accounts": SimpleNamespace(add_account=None, get_accounts=None)}):
    accounts_ui = importlib.import_module("onboarding_accounts")


class Rerun(BaseException):
    pass


class FakeUI:
    def __init__(self):
        self.session_state = {"onboarding_7_started": True}
        self.name = "Revolut"
        self.balance = 1250.0
        self.cash = False
        self.submit = False
        self.click = None
        self.buttons = []
        self.errors = []

    def title(self, *args): pass
    def write(self, *args): pass
    def caption(self, *args): pass
    def info(self, *args): pass
    def subheader(self, *args): pass
    def text(self, *args): pass
    def success(self, *args): pass
    def error(self, message): self.errors.append(message)
    def container(self, **kwargs): return nullcontext()
    def form(self, key): return nullcontext()
    def text_input(self, *args, **kwargs): return self.name
    def number_input(self, *args, **kwargs): return self.balance
    def checkbox(self, *args, **kwargs): return self.cash
    def form_submit_button(self, *args, **kwargs): return self.submit
    def button(self, label, **kwargs):
        self.buttons.append(label)
        return self.click == label
    def rerun(self): raise Rerun()


class AccountsStepTests(unittest.TestCase):
    def setUp(self):
        self.ui = FakeUI()
        self.records = []
        self.ui_patch = patch.object(accounts_ui, "st", self.ui)
        self.read_patch = patch.object(accounts_ui, "get_accounts", return_value=self.records)
        self.add_patch = patch.object(accounts_ui, "add_account", side_effect=self.save)
        self.ui_patch.start()
        self.read = self.read_patch.start()
        self.add = self.add_patch.start()
        self.addCleanup(patch.stopall)

    def save(self, user_id, name, account_type, balance):
        self.records.append(SimpleNamespace(
            id=len(self.records) + 1, name=name, account_type=account_type,
            balance=balance, currency="EUR",
        ))

    def render(self, user_id=7):
        try:
            accounts_ui.render_accounts_step(user_id)
        except Rerun:
            pass

    def test_first_save_stays_started_and_does_not_duplicate_on_rerun(self):
        self.ui.submit = True
        self.render()
        self.add.assert_called_once_with(7, "Revolut", "BANK", 1250.0)
        self.assertTrue(self.ui.session_state["onboarding_7_started"])
        self.assertNotIn("onboarding_7_dashboard", self.ui.session_state)
        self.ui.submit = False
        self.render()
        self.assertIn("Continue", self.ui.buttons)
        self.assertIn("Add another account", self.ui.buttons)
        self.add.assert_called_once()

    def test_invalid_inputs_do_not_write(self):
        for name, balance in [("  ", 1.0), ("Revolut", None), ("Revolut", -1.0)]:
            with self.subTest(name=name, balance=balance):
                self.ui.name, self.ui.balance, self.ui.submit = name, balance, True
                self.render()
                self.add.assert_not_called()
                self.assertTrue(self.ui.errors)

    def test_zero_balance_cash(self):
        self.ui.name, self.ui.balance, self.ui.cash, self.ui.submit = "Cash", 0.0, True, True
        self.render()
        self.add.assert_called_once_with(7, "Cash", "CASH", 0.0)

    def test_add_another_then_continue_to_assets(self):
        self.ui.submit = True
        self.render()
        self.ui.submit, self.ui.click = False, "Add another account"
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_account_form_open"])
        self.assertEqual(self.ui.session_state["onboarding_7_account_form_version"], 1)
        self.ui.click, self.ui.name, self.ui.submit = None, "Swedbank", True
        self.render()
        self.assertEqual(len(self.records), 2)
        self.ui.submit, self.ui.click = False, "Continue"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "assets")

    def test_empty_user_cannot_continue(self):
        self.render()
        self.assertNotIn("Continue", self.ui.buttons)

    def test_existing_accounts_are_not_overwritten(self):
        self.save(7, "Existing account", "BANK", 100.0)
        self.render()
        self.add.assert_not_called()
        self.assertIn("Continue", self.ui.buttons)

    def test_read_failure_does_not_offer_creation(self):
        self.read.side_effect = RuntimeError("private database detail")
        self.ui.submit = True
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.buttons, ["Retry"])
        self.assertNotIn("private database detail", str(self.ui.errors))

    def test_save_failure_keeps_retry_available_on_later_rerun(self):
        self.add.side_effect = RuntimeError("private database detail")
        self.ui.submit = True
        self.render()
        self.ui.submit = False
        self.render()
        self.assertIn("Refresh account list", self.ui.buttons)
        self.assertNotIn("private database detail", str(self.ui.errors))
        self.assertNotIn("onboarding_7_step", self.ui.session_state)

    def test_second_user_has_separate_draft_and_owner(self):
        self.ui.session_state["onboarding_7_account_form_open"] = False
        self.ui.submit = True
        self.render(user_id=8)
        self.add.assert_called_once_with(8, "Revolut", "BANK", 1250.0)
        self.read.assert_called_with(8)
        self.assertEqual(self.ui.session_state["onboarding_8_account_form_version"], 1)
        self.assertNotIn("onboarding_7_account_form_version", self.ui.session_state)


if __name__ == "__main__":
    unittest.main()
