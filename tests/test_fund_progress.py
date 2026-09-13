import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fund_progress import goal_progress_copy, fund_progress_card


class FundProgressTests(unittest.TestCase):
    def test_card_is_one_expander_with_summary_and_edit_body(self):
        ui = MagicMock()
        fund = SimpleNamespace(id=2, name='Japan Trip', current_balance=800, target_amount=1500)
        with patch('fund_progress.st', ui):
            with fund_progress_card(7, fund):
                ui.text_input('Fund name')
        ui.expander.assert_called_once_with('**Japan Trip** *53.3%*  \n€800.00 saved')
        ui.caption.assert_called_once_with('€700.00 to go')
        ui.container.assert_called_once_with(key='fund_goal_7_2')
        ui.text_input.assert_called_once()

    def test_bar_caps_at_target_and_absent_without_usable_target(self):
        for target in (None, 0, -1, 'NaN', 100):
            ui = MagicMock()
            fund = SimpleNamespace(id=2, name='Goal', current_balance=200, target_amount=target)
            with patch('fund_progress.st', ui):
                with fund_progress_card(7, fund):
                    pass
            css = ui.html.call_args.args[0]
            if target == 100:
                self.assertIn('background-size: 100.0% 4px', css)
                self.assertIn('200.0%', ui.expander.call_args.args[0])
            else:
                self.assertNotIn('background-image:', css)

    def test_partial_goal(self):
        self.assertEqual(goal_progress_copy(800, 1500),
                         ("€800.00 / €1,500.00", "53.3% · €700.00 to go"))

    def test_no_target(self):
        for target in (None, 0):
            self.assertEqual(goal_progress_copy(800, target), ("€800.00", "No target set"))

    def test_reached_and_exceeded(self):
        for balance, percent in ((1500, "100.0%"), (1800, "120.0%")):
            self.assertEqual(goal_progress_copy(balance, 1500)[1], percent + " · Target reached")

    def test_invalid_values_have_no_percentage(self):
        for balance, target in ((-1, 100), (1, -100), (None, 100),
                                ("NaN", 100), (100, "Infinity"), (100, "invalid")):
            detail = goal_progress_copy(balance, target)[1]
            self.assertIn("Progress unavailable", detail)
            self.assertNotIn("%", detail)

    def test_zero_balance(self):
        self.assertEqual(goal_progress_copy(0, 100)[1], "0.0% · €100.00 to go")
