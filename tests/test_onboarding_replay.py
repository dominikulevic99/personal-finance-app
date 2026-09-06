"""Guide replay changes navigation only; no database configuration is loaded."""

import importlib
import sys
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from test_onboarding_accounts import FakeUI, Rerun


with patch.dict(sys.modules, {"database": SimpleNamespace(engine=None)}):
    service = importlib.import_module("onboarding_service")
    onboarding = importlib.import_module("onboarding")


class ReplayUI(FakeUI):
    def __init__(self):
        super().__init__()
        self.session_state = {}
        self.sidebar = self

    def stop(self): raise Rerun()


class GuideReplayTests(unittest.TestCase):
    def setUp(self):
        self.ui = ReplayUI()
        patch.object(onboarding, "render_step_navigation").start()
        self.analytics = patch.object(onboarding, "track_event").start()
        patch.object(onboarding, "st", self.ui).start()
        patch.object(onboarding, "onboarding_shell", side_effect=lambda **kwargs: nullcontext()).start()
        self.has_data = patch.object(service, "has_financial_data", return_value=True).start()
        # Keep this module's service binding explicit when other tests import stubs.
        patch.object(onboarding, "get_entry_route", service.get_entry_route).start()
        self.welcome = patch.object(onboarding, "render_welcome_content").start()
        self.accounts = patch.object(onboarding, "render_accounts_step").start()
        self.picture = patch.object(onboarding, "render_financial_picture").start()
        self.addCleanup(patch.stopall)

    def render(self, user_id=7, **kwargs):
        try:
            onboarding.render_onboarding_entry(user_id, **kwargs)
        except Rerun:
            pass

    def replay(self, user_id=7):
        self.ui.click = "Repeat setup guide"
        try:
            onboarding.render_guide_replay_action(user_id)
        except Rerun:
            pass
        self.ui.click = None

    def test_existing_user_login_still_bypasses_guide(self):
        self.render()
        self.has_data.assert_called_once_with(7)
        self.welcome.assert_not_called()
        self.accounts.assert_not_called()
        self.assertEqual(self.ui.session_state, {})

    def test_new_user_and_tester_routing_are_preserved(self):
        self.has_data.return_value = False
        self.render()
        self.welcome.assert_called_once()
        self.welcome.reset_mock()
        self.has_data.return_value = True
        self.render(force_welcome=True)
        self.welcome.assert_called_once()

    def test_replay_keeps_drafts_period_and_other_users_state(self):
        self.ui.session_state = {
            "onboarding_7_started": True,
            "onboarding_7_dashboard": True,
            "onboarding_7_step": "financial_picture",
            "onboarding_7_account_draft_1_name": "Existing draft",
            "onboarding_7_plan_month": (2026, 9),
            "onboarding_8_dashboard": True,
            "onboarding_8_step": "debts",
        }
        original = dict(self.ui.session_state)
        self.replay()
        expected = original | {
            "onboarding_7_replay_mode": True,
            "onboarding_7_replay_welcome": True,
            "onboarding_7_dashboard": False,
            "onboarding_7_step": "accounts",
        }
        self.assertEqual(self.ui.session_state, expected)
        self.render()
        self.welcome.assert_called_once()
        self.has_data.assert_not_called()

    def test_start_replay_uses_accounts_without_reclassifying_user(self):
        self.replay()
        self.assertNotIn("onboarding_7_started", self.ui.session_state)
        self.ui.click = "Build my financial plan"
        self.render()
        self.ui.click = None
        self.render()
        self.accounts.assert_called_once_with(7)
        self.analytics.assert_any_call(7, "onboarding_started", session_state=self.ui.session_state)
        self.analytics.assert_any_call(7, "onboarding_step_viewed", "accounts", session_state=self.ui.session_state)
        self.assertTrue(self.ui.session_state["onboarding_7_started"])
        self.assertFalse(self.ui.session_state["onboarding_7_replay_welcome"])
        self.has_data.assert_not_called()

    def test_skip_replay_returns_to_dashboard_without_loop(self):
        self.replay()
        self.ui.click = "Skip for now"
        self.render()
        self.welcome.reset_mock()
        self.ui.click = None
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_dashboard"])
        self.assertFalse(self.ui.session_state["onboarding_7_replay_welcome"])
        self.welcome.assert_not_called()
        self.accounts.assert_not_called()

    def test_completion_opens_dashboard_and_can_replay_again(self):
        self.ui.session_state = {"onboarding_7_started": True, "onboarding_7_step": "financial_picture"}
        self.ui.click = "Open my dashboard"
        self.render()
        self.assertTrue(self.ui.session_state["onboarding_7_dashboard"])
        self.replay()
        self.render()
        self.welcome.assert_called_once()

    def test_replay_does_not_change_fresh_session_eligibility(self):
        self.replay()
        self.ui.session_state = {}
        self.assertEqual(service.get_entry_route(7), "dashboard")
        self.has_data.assert_called_with(7)

    def test_info_styles_target_only_semantic_info_marker(self):
        from visual_styles import LAYOUT_CSS
        selector = '[data-testid="stAlertContainer"]:has(> [data-testid="stAlertContentInfo"])'
        self.assertIn(selector, LAYOUT_CSS)
        rule = LAYOUT_CSS.split(selector, 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--finance-surface)", rule)
        self.assertIn("color: var(--finance-text)", rule)
        for kind in ("Warning", "Error", "Success"):
            self.assertNotIn(f':has(> [data-testid="stAlertContent{kind}"])', LAYOUT_CSS)


if __name__ == "__main__":
    unittest.main()
