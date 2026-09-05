"""Offline Assets onboarding checks; all reads and writes are mocked."""

import ast
import importlib
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI, Rerun


with patch.dict(sys.modules, {"assets": SimpleNamespace(add_asset=None, get_assets=None)}):
    assets_ui = importlib.import_module("onboarding_assets")


class AssetsUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.name = "My investments"
        self.asset_type = "INVESTMENT"
        self.liquidity_class = "LIQUID_INVESTMENT"
        self.session_state["onboarding_7_step"] = "assets"

    def expander(self, *args): return nullcontext()

    def selectbox(self, label, **kwargs):
        self.assertions = kwargs
        return self.asset_type if kwargs["key"].endswith("type") else self.liquidity_class


class AssetsStepTests(unittest.TestCase):
    def setUp(self):
        self.ui = AssetsUI()
        self.records = []
        patch.object(assets_ui, "st", self.ui).start()
        self.read = patch.object(assets_ui, "get_assets", return_value=self.records).start()
        self.add = patch.object(assets_ui, "add_asset", side_effect=self.save).start()
        self.addCleanup(patch.stopall)

    def save(self, user_id, name, asset_type, liquidity_class, value):
        self.records.append(SimpleNamespace(
            id=len(self.records) + 1, name=name, asset_type=asset_type,
            liquidity_class=liquidity_class, current_value=value, currency="EUR",
        ))

    def render(self, user_id=7):
        try:
            assets_ui.render_assets_step(user_id)
        except Rerun:
            pass

    def test_categories_exactly_match_existing_dashboard(self):
        tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if any(isinstance(t, ast.Name) and t.id == "asset_type" for t in node.targets):
                    self.assertEqual(list(assets_ui.ASSET_TYPES), ast.literal_eval(node.value.args[1]))
                if any(isinstance(t, ast.Name) and t.id == "liquidity_class" for t in node.targets):
                    self.assertEqual(list(assets_ui.LIQUIDITY_CLASSES), ast.literal_eval(node.value.args[1]))

    def test_type_and_liquidity_are_passed_independently(self):
        for asset_type in assets_ui.ASSET_TYPES:
            for liquidity in assets_ui.LIQUIDITY_CLASSES:
                with self.subTest(asset_type=asset_type, liquidity=liquidity):
                    self.ui.session_state["onboarding_7_asset_form_open"] = True
                    self.ui.asset_type, self.ui.liquidity_class = asset_type, liquidity
                    self.ui.submit = True
                    self.render()
                    self.add.assert_called_with(7, "My investments", asset_type, liquidity, 1250.0)
                    self.assertEqual(self.ui.session_state["onboarding_7_step"], "assets")
                    self.assertNotIn("onboarding_7_dashboard", self.ui.session_state)

    def test_invalid_draft_does_not_write(self):
        for field, value in [
            ("name", "  "), ("balance", None), ("balance", -1.0),
            ("asset_type", None), ("liquidity_class", None),
            ("asset_type", "NEW_CATEGORY"), ("liquidity_class", "LIQUID"),
        ]:
            with self.subTest(field=field, value=value):
                previous = getattr(self.ui, field)
                setattr(self.ui, field, value)
                self.ui.submit = True
                self.render()
                self.add.assert_not_called()
                self.assertTrue(self.ui.errors)
                setattr(self.ui, field, previous)

    def test_zero_value_is_valid_and_rerun_does_not_duplicate(self):
        self.ui.balance, self.ui.submit = 0.0, True
        self.render()
        self.ui.submit = False
        self.render()
        self.add.assert_called_once_with(7, "My investments", "INVESTMENT", "LIQUID_INVESTMENT", 0.0)
        self.assertIn("Continue", self.ui.buttons)

    def test_skip_empty_or_unsaved_draft_advances_without_write(self):
        self.ui.click = "I don't have any yet"
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")

    def test_add_another_and_continue(self):
        self.ui.submit = True
        self.render()
        self.ui.submit, self.ui.click = False, "Add another"
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_asset_form_open"])
        self.assertEqual(self.ui.session_state["onboarding_7_asset_form_version"], 1)
        self.ui.name, self.ui.click, self.ui.submit = "My home", None, True
        self.ui.asset_type, self.ui.liquidity_class = "REAL_ESTATE", "NON_LIQUID"
        self.render()
        self.ui.submit, self.ui.click = False, "Continue"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")
        self.assertEqual(len(self.records), 2)

    def test_skip_additional_draft_preserves_existing_asset(self):
        self.save(7, "Existing", "CAR", "SEMI_LIQUID", 1000.0)
        self.ui.session_state["onboarding_7_asset_form_open"] = True
        self.ui.click = "Skip for now"
        self.render()
        self.add.assert_not_called()
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "debts")

    def test_back_returns_to_accounts_without_writing(self):
        self.ui.click = "Back to Accounts"
        self.render()
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "accounts")
        self.add.assert_not_called()

    def test_read_failure_is_safe(self):
        self.read.side_effect = RuntimeError("private detail")
        self.ui.submit = True
        self.render()
        self.add.assert_not_called()
        self.assertEqual(self.ui.buttons, ["Retry"])
        self.assertNotIn("private detail", str(self.ui.errors))

    def test_save_failure_keeps_draft_and_refresh_option(self):
        self.add.side_effect = RuntimeError("private detail")
        self.ui.submit = True
        self.render()
        self.ui.submit = False
        self.render()
        self.assertIn("Refresh asset list", self.ui.buttons)
        self.assertNotIn("private detail", str(self.ui.errors))
        self.assertEqual(self.ui.session_state["onboarding_7_step"], "assets")

    def test_state_and_write_owner_are_user_scoped(self):
        self.ui.session_state["onboarding_7_asset_form_open"] = False
        self.ui.submit = True
        self.render(8)
        self.read.assert_called_with(8)
        self.add.assert_called_once_with(8, "My investments", "INVESTMENT", "LIQUID_INVESTMENT", 1250.0)
        self.assertEqual(self.ui.session_state["onboarding_8_asset_form_version"], 1)
        self.assertNotIn("onboarding_7_asset_form_version", self.ui.session_state)


if __name__ == "__main__":
    unittest.main()
