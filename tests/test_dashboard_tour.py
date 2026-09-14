"""Offline Python integration checks; not a substitute for browser verification."""

import unittest
from unittest.mock import MagicMock, patch

import dashboard_tour as tour
import i18n


class DashboardTourTests(unittest.TestCase):
    def setUp(self):
        self.ui = MagicMock()
        self.ui.session_state = {}
        self.widget = MagicMock()
        self.ui_patch = patch.object(tour, 'st', self.ui)
        self.component_patch = patch.object(tour, 'component', return_value=self.widget)
        self.ui_patch.start()
        self.register = self.component_patch.start()
        self.addCleanup(self.ui_patch.stop)
        self.addCleanup(self.component_patch.stop)

    def test_no_automatic_tour(self):
        tour.render_tour(7)
        self.register.assert_not_called()

    def test_start_and_finish_are_user_scoped(self):
        tour.start_tour(7)
        tour.render_tour(8)
        self.register.assert_not_called()
        tour.render_tour(7)
        self.widget.call_args.kwargs['on_finished_change']()
        self.assertFalse(self.ui.session_state['product_tour_7_active'])
        self.assertNotIn('product_tour_8_active', self.ui.session_state)

    def test_payload_has_only_static_targets_and_step(self):
        tour.start_tour(7)
        tour.render_tour(7)
        data = self.widget.call_args.kwargs['data']
        self.assertEqual(set(data), {'steps', 'step', 'labels', 'language', 'offer_feedback'})
        self.assertIn(data['language'], ('lt', 'en'))
        self.assertEqual(set(data['labels']), {'title', 'close', 'back', 'skip', 'next', 'finish', 'missing', 'small', 'count', 'feedback', 'dashboard'})
        self.assertEqual([step['target'] for step in data['steps']],
                         ['tour_summary', 'tour_funds', 'tour_monthly_plan', 'tour_checkin'])
        self.assertTrue(all(set(step) == {'target', 'title', 'copy'} for step in data['steps']))

    def test_rerun_retains_step_and_replay_gets_new_key(self):
        tour.start_tour(7)
        tour.render_tour(7)
        key = self.widget.call_args.kwargs['key']
        self.ui.session_state[key] = {'step': 2}
        tour.render_tour(7)
        self.assertEqual(self.widget.call_args.kwargs['data']['step'], 2)
        tour.start_tour(7)
        tour.render_tour(7)
        self.assertNotEqual(self.widget.call_args.kwargs['key'], key)
        self.assertEqual(self.widget.call_args.kwargs['data']['step'], 0)

    def test_language_change_keeps_current_step_and_session(self):
        with patch.object(i18n, 'st', self.ui):
            i18n.initialize_language(7)
            tour.start_tour(7)
            tour.render_tour(7)
            key = self.widget.call_args.kwargs['key']
            self.ui.session_state[key] = {'step': 2, 'language': 'en'}
            self.widget.call_args.kwargs['on_language_change']()
            tour.render_tour(7)
            data = self.widget.call_args.kwargs['data']
            self.assertEqual(data['step'], 2)
            self.assertEqual(data['language'], 'en')
            self.assertEqual(self.widget.call_args.kwargs['key'], key)
            self.assertEqual(data['labels']['close'], 'Close')
            self.assertEqual(self.ui.session_state['_i18n_user_7_switch'], 'en')
            self.assertTrue(self.ui.session_state['product_tour_7_active'])

    def test_only_feedback_choice_opens_dialog_after_tour_cleanup(self):
        for reason in ('close', 'skip', 'escape', 'finish', 'feedback'):
            with patch.object(tour, 'open_feedback') as opened:
                tour.start_tour(7)
                tour.render_tour(7)
                key = self.widget.call_args.kwargs['key']
                self.ui.session_state[key] = {'step': 3, 'finished': reason}
                self.widget.call_args.kwargs['on_finished_change']()
                self.assertFalse(self.ui.session_state['product_tour_7_active'])
                if reason == 'feedback':
                    opened.assert_called_once_with(7, 'product_tour')
                else:
                    opened.assert_not_called()

    def test_dashboard_choice_only_queues_prompt_without_opening_it(self):
        with patch.object(tour, 'open_feedback') as opened:
            tour.start_tour(7)
            tour.render_tour(7)
            key = self.widget.call_args.kwargs['key']
            self.ui.session_state[key] = {'step': 3, 'finished': 'finish'}
            self.widget.call_args.kwargs['on_finished_change']()
            self.assertTrue(self.ui.session_state['feedback_7_pending'])
            self.assertFalse(self.ui.session_state.get('feedback_7_offered', False))
            self.assertFalse(self.ui.session_state['product_tour_7_active'])
            opened.assert_not_called()

    def test_tester_completed_tours_rearm_despite_previous_feedback(self):
        self.ui.session_state.update(feedback_7_has_submitted=True, feedback_7_offered=True)
        for run in (1, 2):
            tour.start_tour(7)
            tour.render_tour(7, tester=True)
            key = self.widget.call_args.kwargs['key']
            self.ui.session_state[key] = {'finished': 'finish'}
            self.widget.call_args.kwargs['on_finished_change']()
            self.assertTrue(self.ui.session_state['feedback_7_pending'])
            self.assertFalse(self.ui.session_state['feedback_7_offered'])
            self.assertEqual(self.ui.session_state['feedback_7_prompt_run'], run)
            self.ui.session_state['feedback_7_offered'] = True
            tour.render_tour(7, tester=True)
            self.assertTrue(self.ui.session_state['feedback_7_offered'])

    def test_ordinary_completed_tour_preserves_submission_suppression(self):
        self.ui.session_state['feedback_7_has_submitted'] = True
        tour.start_tour(7)
        tour.render_tour(7)
        key = self.widget.call_args.kwargs['key']
        self.ui.session_state[key] = {'finished': 'finish'}
        self.widget.call_args.kwargs['on_finished_change']()
        self.assertFalse(self.ui.session_state.get('feedback_7_pending', False))
