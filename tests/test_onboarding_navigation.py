import unittest
from i18n import t
from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import onboarding_navigation as nav


class NavigationTests(unittest.TestCase):
    def render(self, state, click=None, unrestricted=False):
        ui = MagicMock()
        ui.session_state = state
        ui.columns.side_effect = lambda count: [nullcontext() for _ in range(count)]
        ui.button.side_effect = lambda label, **kw: kw['key'] == click
        with patch.object(nav, 'st', ui):
            nav.render_step_navigation(7, unrestricted=unrestricted)
        return ui

    def test_first_time_cannot_jump_ahead(self):
        state = {'onboarding_7_step': 'accounts'}
        ui = self.render(state, 'onboarding_7_nav_funds')
        self.assertEqual(state['onboarding_7_step'], 'accounts')
        self.assertTrue(ui.button.call_args_list[3].kwargs['disabled'])
        ui.rerun.assert_not_called()

    def test_tester_can_jump_with_navigation_collapsed_by_default(self):
        state = {'onboarding_7_step': 'accounts'}
        ui = self.render(state, 'onboarding_7_nav_monthly_plan', unrestricted=True)
        self.assertEqual(state['onboarding_7_step'], 'monthly_plan')
        self.assertNotIn('onboarding_7_highest_step', state)
        ui.expander.assert_called_once_with(t('ui.navigate_setup'), expanded=False)

    def test_reached_steps_remain_accessible_after_going_back(self):
        state = {'onboarding_7_step': 'funds'}
        self.render(state, 'onboarding_7_nav_accounts')
        self.assertEqual(state['onboarding_7_highest_step'], 3)
        self.render(state, 'onboarding_7_nav_funds')
        self.assertEqual(state['onboarding_7_step'], 'funds')

    def test_current_step_does_not_rerun(self):
        ui = self.render({'onboarding_7_step': 'accounts'}, 'onboarding_7_nav_accounts')
        ui.rerun.assert_not_called()

    def test_replay_unlocks_every_step_without_advancing_first_time_progress(self):
        state = {'onboarding_7_step': 'accounts', 'onboarding_7_replay_mode': True,
                 'onboarding_8_step': 'debts'}
        ui = self.render(state, 'onboarding_7_nav_financial_picture')
        self.assertEqual(state['onboarding_7_step'], 'financial_picture')
        self.assertNotIn('onboarding_7_highest_step', state)
        self.assertEqual(state['onboarding_8_step'], 'debts')
        self.assertFalse(ui.button.call_args_list[-1].kwargs['disabled'])
