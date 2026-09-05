"""Offline Debts onboarding checks; no real financial records are accessed."""

import ast
import importlib
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI, Rerun


with patch.dict(sys.modules, {"debts": SimpleNamespace(add_debt=None, get_debts=None)}):
    debts_ui = importlib.import_module("onboarding_debts")


class DebtsUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.name = "Money borrowed from Jonas"
        self.debt_type = "OTHER"
        self.balance = 500.0
        self.payment = 0.0
        self.interest = 0.0
        self.session_state["onboarding_7_step"] = "debts"

    def expander(self, *args): return nullcontext()
    def selectbox(self, *args, **kwargs): return self.debt_type
    def number_input(self, *args, **kwargs):
        return getattr(self, kwargs["key"].rsplit("_", 1)[-1])


class DebtsStepTests(unittest.TestCase):
    def setUp(self):
        self.ui = DebtsUI()
        self.records = []
        patch.object(debts_ui, "st", self.ui).start()
        self.read = patch.object(debts_ui, "get_debts", return_value=self.records).start()
        self.add = patch.object(debts_ui, "add_debt", side_effect=self.save).start()
        self.addCleanup(patch.stopall)

    def save(self, user_id, name, debt_type, balance, payment, interest):
        self.records.append(SimpleNamespace(
            id=len(self.records) + 1, name=name, debt_type=debt_type,
            remaining_balance=balance, monthly_payment=payment, interest_rate=interest, currency="EUR",
        ))

    def render(self, user_id=7):
        try:
            debts_ui.render_debts_step(user_id)
        except Rerun:
            pass

    def test_categories_match_dashboard_and_are_passed_unchanged(self):
        tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8-sig"))
        options = next(
            ast.literal_eval(node.value.args[1]) for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
            and any(isinstance(t, ast.Name) and t.id == "debt_type" for t in node.targets)
        )
        self.assertEqual(list(debts_ui.DEBT_TYPES), options)
        for debt_type in options:
            self.ui.session_state["onboarding_7_debt_form_open"] = True
            self.ui.debt_type, self.ui.submit = debt_type, True
            self.render()
            self.add.assert_called_with(7, self.ui.name, debt_type, 500.0, 0.0, 0.0)

    def test_payment_interest_and_zero_balance_pass_through(self):
        self.ui.balance, self.ui.payment, self.ui.interest = 0.0, 50.0, 5.5
        self.ui.submit = True
        self.render()
        self.add.assert_called_once_with(7, self.ui.name, "OTHER", 0.0, 50.0, 5.5)
        self.assertTrue(self.ui.session_state["onboarding_7_started"])
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")
        self.assertNotIn("onboarding_7_dashboard", self.ui.session_state)
        self.ui.submit = False
        self.render()
        self.add.assert_called_once()

    def test_invalid_inputs_do_not_write(self):
        for field, value in [
            ("name", "  "), ("balance", None), ("balance", -1.0),
            ("payment", -1.0), ("interest", -1.0),
            ("debt_type", None), ("debt_type", "NEW_CATEGORY"),
        ]:
            with self.subTest(field=field, value=value):
                previous = getattr(self.ui, field)
                setattr(self.ui, field, value)
                self.ui.submit = True
                self.render()
                self.add.assert_not_called()
                self.assertTrue(self.ui.errors)
                setattr(self.ui, field, previous)

    def test_skip_unsaved_draft_goes_to_funds_without_write(self):
        self.ui.click = "I don't have any debt"
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "funds")

    def test_add_another_and_continue(self):
        self.ui.submit = True
        self.render()
        self.ui.submit, self.ui.click = False, "Add another"
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_debt_form_open"])
        self.assertEqual(self.ui.session_state["onboarding_7_debt_form_version"], 1)
        self.ui.name, self.ui.submit, self.ui.click = "Car loan", True, None
        self.render()
        self.ui.submit, self.ui.click = False, "Continue"
        self.render()
        self.assertEqual(len(self.records), 2)
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "funds")

    def test_existing_debt_survives_skip_and_back(self):
        self.save(7, "Existing", "CAR_LOAN", 1000.0, 50.0, 3.0)
        self.ui.session_state["onboarding_7_debt_form_open"] = True
        self.ui.click = "Skip for now"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "funds")
        self.ui.click = "Back to Assets"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "assets")
        self.add.assert_not_called()
        self.assertEqual(len(self.records), 1)

    def test_read_failure_stops_creation(self):
        self.read.side_effect = RuntimeError("private detail")
        self.ui.submit = True
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.buttons, ["Retry"])
        self.assertNotIn("private detail", str(self.ui.errors))

    def test_save_failure_keeps_refresh_available(self):
        self.add.side_effect = RuntimeError("private detail")
        self.ui.submit = True
        self.render()
        self.ui.submit = False
        self.render()
        self.assertIn("Refresh debt list", self.ui.buttons)
        self.assertNotIn("private detail", str(self.ui.errors))
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")

    def test_user_state_and_write_owner_are_scoped(self):
        self.ui.session_state["onboarding_7_debt_form_open"] = False
        self.ui.submit = True
        self.render(8)
        self.read.assert_called_with(8)
        self.add.assert_called_once_with(8, self.ui.name, "OTHER", 500.0, 0.0, 0.0)
        self.assertEqual(self.ui.session_state["onboarding_8_debt_form_version"], 1)
        self.assertNotIn("onboarding_7_debt_form_version", self.ui.session_state)


if __name__ == "__main__":
    unittest.main()
