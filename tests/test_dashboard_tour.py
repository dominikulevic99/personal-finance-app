"""Offline Python integration checks; not a substitute for browser verification."""

import unittest
from unittest.mock import MagicMock, patch

import dashboard_tour as tour


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
        self.assertEqual(set(data), {'steps', 'step'})
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
