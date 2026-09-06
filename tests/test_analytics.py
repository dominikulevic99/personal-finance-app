"""Offline analytics tests: no credentials or real database connections."""

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from analytics import ONBOARDING_STEPS, track_event


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.state = {}
        self.engine = MagicMock()
        self.connection = self.engine.begin.return_value.__enter__.return_value
        stub = patch.dict(sys.modules, {"database": SimpleNamespace(engine=self.engine)})
        stub.start()
        self.addCleanup(stub.stop)

    def track(self, event="login", value=None, user=7):
        return track_event(user, event, value, session_state=self.state)

    def test_parameterized_insert_uses_only_allowed_fields(self):
        self.assertTrue(self.track())
        sql, params = self.connection.execute.call_args.args
        self.assertEqual(str(sql), "INSERT INTO user_events (user_id, event_type, event_value) "
                         "VALUES (:user_id, :event_type, :event_value)")
        self.assertEqual(params, {"user_id": 7, "event_type": "login", "event_value": None})

    def test_each_event_and_step_is_attempted_once_per_session(self):
        events = [(name, None) for name in (
            "login", "onboarding_started", "onboarding_completed", "dashboard_opened",
            "monthly_plan_created")]
        events += [("contribution_confirmed", kind) for kind in ("fund", "investment")]
        events += [("onboarding_step_viewed", step) for step in ONBOARDING_STEPS]
        for event, value in events:
            self.assertTrue(self.track(event, value))
            self.assertFalse(self.track(event, value))
        self.assertEqual(self.connection.execute.call_count, 13)

    def test_users_and_new_sessions_are_independent(self):
        self.assertTrue(self.track(user=7))
        self.assertTrue(self.track(user=8))
        self.assertFalse(self.track(user=7))
        self.state = {}
        self.assertTrue(self.track(user=7))

    def test_connection_execute_and_commit_failures_do_not_escape_or_retry(self):
        for failing in (self.engine.begin, self.connection.execute,
                        self.engine.begin.return_value.__exit__):
            with self.subTest(failing=failing):
                self.state = {}
                self.engine.reset_mock()
                failing.side_effect = RuntimeError("private database details")
                self.assertFalse(self.track())
                self.assertFalse(self.track())
                self.engine.begin.assert_called_once()
                failing.side_effect = None

    def test_financial_payloads_and_unknown_events_are_rejected(self):
        for event, value in (("balance", None), ("login", "1250"),
                             ("onboarding_step_viewed", "1250"),
                             ("onboarding_step_viewed", None),
                             ("contribution_confirmed", "1250"),
                             ("contribution_confirmed", None),
                             ("monthly_plan_created", "2500")):
            self.assertFalse(self.track(event, value))
        self.engine.begin.assert_not_called()
        self.assertEqual(self.state, {})

    def test_missing_or_invalid_user_is_rejected(self):
        for user in (None, 0, -1, True, "7"):
            self.assertFalse(self.track(user=user))
        self.engine.begin.assert_not_called()

    def test_session_state_failure_does_not_escape(self):
        state = MagicMock()
        state.get.side_effect = RuntimeError("state unavailable")
        self.assertFalse(track_event(7, "login", session_state=state))
        self.engine.begin.assert_not_called()


if __name__ == "__main__":
    unittest.main()
