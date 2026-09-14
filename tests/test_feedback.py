"""Structured feedback storage and session-state checks, with no live database."""
import unittest
from unittest.mock import MagicMock, patch
import feedback
import feedback_ui


class FeedbackStorageTests(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()
        self.connection = self.engine.begin.return_value.__enter__.return_value
        self.connection.execute.return_value.fetchone.return_value = (7,)
        patcher = patch.object(feedback, 'engine', self.engine)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_parameterized_structured_only_and_comment_only(self):
        for message, options, source in [('', ['bank_connection','other'], 'product_tour'),
                                         (' My comment ', [], 'sidebar')]:
            feedback.add_feedback(7, message, options, source)
            sql, params = self.connection.execute.call_args.args
            self.assertIn(':selected_options', str(sql))
            self.assertIn(':source', str(sql))
            self.assertEqual(params, dict(user_id=7, message=message.strip(), selected_options=options, source=source))
        self.assertEqual(self.connection.execute.call_args_list[0].args[1], {'user_id': 7})

    def test_invalid_options_sources_conflicts_and_empty_never_write(self):
        for message, options, source in [('', [], 'sidebar'), (' ', [], 'sidebar'),
            ('', ['nothing_missing','other'], 'sidebar'), ('', ['Translated label'], 'sidebar'),
            ('Comment', [], None), ('Comment', [], 'unknown')]:
            with self.assertRaises(ValueError):
                feedback.add_feedback(7, message, options, source)
        self.engine.begin.assert_not_called()

    def test_user_must_exist_and_reads_remain_scoped(self):
        self.connection.execute.return_value.fetchone.return_value = None
        with self.assertRaises(ValueError):
            feedback.add_feedback(99, 'Comment', [], 'sidebar')
        self.assertEqual(self.connection.execute.call_count, 1)
        feedback.get_user_feedback(7)
        sql, params = self.engine.connect.return_value.__enter__.return_value.execute.call_args.args
        self.assertIn('WHERE user_id = :user_id', str(sql))
        self.assertIn('selected_options', str(sql))
        self.assertEqual(params, {'user_id': 7})


class FeedbackStateTests(unittest.TestCase):
    def setUp(self):
        self.ui = MagicMock()
        self.ui.session_state = {}
        patcher = patch.object(feedback_ui, 'st', self.ui)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_mutual_exclusivity_and_user_isolation(self):
        state = self.ui.session_state
        state.update(feedback_7_option_other=True, feedback_7_option_bank_connection=True,
                     feedback_7_option_nothing_missing=True, feedback_8_option_other=True)
        feedback_ui.select_option(7, 'nothing_missing')
        self.assertFalse(state['feedback_7_option_other'])
        self.assertFalse(state['feedback_7_option_bank_connection'])
        self.assertTrue(state['feedback_8_option_other'])
        state['feedback_7_option_other'] = True
        feedback_ui.select_option(7, 'other')
        self.assertFalse(state['feedback_7_option_nothing_missing'])
        state['feedback_7_option_bank_connection'] = True
        feedback_ui.select_option(7, 'bank_connection')
        self.assertTrue(state['feedback_7_option_other'])

    def test_shared_open_retains_draft_and_records_source(self):
        self.ui.session_state['feedback_7_comment'] = 'Draft'
        for source in ('sidebar','product_tour'):
            feedback_ui.open_feedback(7, source)
            self.assertEqual(self.ui.session_state['feedback_7_source'], source)
            self.assertEqual(self.ui.session_state['feedback_7_comment'], 'Draft')
            self.assertTrue(self.ui.session_state['feedback_7_open'])
            self.assertNotIn('feedback_8_open', self.ui.session_state)

    def test_invitation_once_per_session_and_not_after_existing_feedback(self):
        with patch.object(feedback_ui, 'get_user_feedback', return_value=[]) as read:
            self.assertTrue(feedback_ui.offer_tour_feedback(7))
            self.assertTrue(feedback_ui.offer_tour_feedback(7))
            read.assert_called_once_with(7)
            self.ui.session_state['feedback_7_offered'] = True
            self.assertFalse(feedback_ui.offer_tour_feedback(7))
        with patch.object(feedback_ui, 'get_user_feedback', return_value=[object()]):
            self.assertFalse(feedback_ui.offer_tour_feedback(8))
        with patch.object(feedback_ui, 'get_user_feedback', side_effect=RuntimeError('private details')):
            self.assertFalse(feedback_ui.offer_tour_feedback(9))
