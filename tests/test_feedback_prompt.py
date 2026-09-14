"""Automatic invitations require an explicit handoff and a client visibility signal."""
import unittest
from unittest.mock import MagicMock, patch
import feedback_prompt as prompt


class FeedbackPromptTests(unittest.TestCase):
    def setUp(self):
        self.ui = MagicMock()
        self.ui.session_state = {}
        self.widget = MagicMock()
        self.ui_patch = patch.object(prompt, 'st', self.ui)
        self.factory_patch = patch.object(prompt, 'component', return_value=self.widget)
        self.read_patch = patch.object(prompt, 'get_user_feedback', return_value=[])
        self.open_patch = patch.object(prompt, 'open_feedback')
        self.ui_patch.start()
        self.factory = self.factory_patch.start()
        self.read = self.read_patch.start()
        self.opened = self.open_patch.start()
        self.addCleanup(patch.stopall)

    def visible(self, reason='visible'):
        key = self.widget.call_args.kwargs['key']
        self.ui.session_state[key] = {'ready': reason}
        self.widget.call_args.kwargs['on_ready_change']()

    def test_normal_logins_and_new_sessions_do_not_arm_prompt(self):
        for state in ({}, {'onboarding_7_dashboard': True}, {'onboarding_7_started': True}):
            self.ui.session_state = dict(state)
            prompt.render_feedback_prompt(7)
        self.factory.assert_not_called()
        self.opened.assert_not_called()

    def test_successful_reveal_and_dashboard_handoff_wait_for_visibility(self):
        self.ui.session_state.update(feedback_7_picture_seen=True)
        prompt.render_feedback_prompt(7)
        self.factory.assert_not_called()
        self.ui.session_state['onboarding_7_dashboard'] = True
        prompt.render_feedback_prompt(7)
        self.opened.assert_not_called()
        self.assertEqual(self.widget.call_args.kwargs['data'], {})
        self.visible()
        self.opened.assert_called_once_with(7, 'product_tour', automatic=True)
        self.assertTrue(self.ui.session_state['feedback_7_offered'])
        self.visible()
        prompt.render_feedback_prompt(7)
        self.opened.assert_called_once()

    def test_prior_feedback_or_failed_lookup_suppresses_prompt(self):
        for result in ([object()], RuntimeError('private details')):
            self.ui.session_state = {'feedback_7_pending': True}
            self.read.side_effect = result if isinstance(result, Exception) else None
            self.read.return_value = result
            prompt.render_feedback_prompt(7)
            self.visible()
            self.opened.assert_not_called()
            self.assertTrue(self.ui.session_state['feedback_7_offered'])

    def test_other_user_and_active_tour_do_not_prompt(self):
        self.ui.session_state.update(feedback_7_picture_seen=True, onboarding_7_dashboard=True,
                                     onboarding_7_replay_mode=True)
        prompt.queue_feedback_prompt(7, session_state=self.ui.session_state)
        prompt.render_feedback_prompt(8)
        self.ui.session_state['product_tour_7_active'] = True
        prompt.render_feedback_prompt(7)
        self.factory.assert_not_called()

    def test_replay_qualifies_but_existing_feedback_still_suppresses(self):
        self.ui.session_state.update(feedback_7_picture_seen=True, onboarding_7_dashboard=True,
                                     onboarding_7_replay_mode=True)
        self.read.return_value = [object()]
        prompt.render_feedback_prompt(7)
        self.visible()
        self.opened.assert_not_called()
        self.assertNotIn('feedback_7_picture_seen', self.ui.session_state)

    def test_tester_can_repeat_completed_guide_despite_prior_feedback(self):
        self.read.return_value = [object()]
        self.ui.session_state.update(feedback_7_has_submitted=True, feedback_7_offered=True,
                                     onboarding_7_dashboard=True, onboarding_7_replay_mode=True)
        prompt.render_feedback_prompt(7, tester=True)
        self.factory.assert_not_called()  # Login/dashboard alone still never prompts.
        keys = []
        for count in (1, 2):
            self.ui.session_state['feedback_7_picture_seen'] = True
            prompt.render_feedback_prompt(7, tester=True)
            keys.append(self.widget.call_args.kwargs['key'])
            self.visible()
            self.assertEqual(self.opened.call_count, count)
            prompt.render_feedback_prompt(7, tester=True)
            self.assertEqual(self.opened.call_count, count)
        self.assertNotEqual(keys[0], keys[1])

    def test_replay_without_previous_feedback_can_prompt_once(self):
        self.ui.session_state.update(feedback_7_picture_seen=True, onboarding_7_dashboard=True,
                                     onboarding_7_replay_mode=True)
        prompt.render_feedback_prompt(7)
        self.visible()
        self.opened.assert_called_once_with(7, 'product_tour', automatic=True)
        self.ui.session_state['feedback_7_picture_seen'] = True
        prompt.render_feedback_prompt(7)
        self.opened.assert_called_once()

    def test_interaction_or_missing_target_cancels_without_opening(self):
        prompt.queue_feedback_prompt(7, session_state=self.ui.session_state)
        prompt.render_feedback_prompt(7)
        self.visible('cancelled')
        self.assertTrue(self.ui.session_state['feedback_7_offered'])
        self.assertFalse(self.ui.session_state['feedback_7_pending'])
        self.opened.assert_not_called()

    def test_manual_feedback_and_previous_submission_prevent_pending_prompt(self):
        for state in ({'feedback_7_offered': True}, {'feedback_7_has_submitted': True}):
            self.ui.session_state = state
            prompt.queue_feedback_prompt(7, session_state=state)
            prompt.render_feedback_prompt(7)
        self.factory.assert_not_called()
