"""Real Streamlit dialog interactions against the offline dashboard fixture."""
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from streamlit.testing.v1 import AppTest
import feedback_ui


class FeedbackDialogTests(unittest.TestCase):
    def test_auto_prompt_has_not_now_and_dismissal_does_not_reopen(self):
        for language in ('lt', 'en'):
            with self.subTest(language=language), patch.object(feedback_ui, 'add_feedback') as save:
                at = AppTest.from_file(str(Path(__file__).with_name('dashboard_language_probe.py')), default_timeout=20).run()
                at.segmented_control[0].set_value(language).run()
                with patch.object(feedback_ui, 'st', SimpleNamespace(session_state=at.session_state)):
                    feedback_ui.open_feedback(7, 'product_tour', automatic=True)
                at.run()
                self.assertFalse(at.exception)
                self.assertEqual(at.button(key='feedback_7_not_now').label, 'Ne dabar' if language=='lt' else 'Not now')
                at.button(key='feedback_7_not_now').click().run()
                at.run()
                self.assertFalse(at.session_state['feedback_7_open'])
                self.assertTrue(at.session_state['feedback_7_offered'])
                save.assert_not_called()
                at.button(key='feedback_7_sidebar').click().run()
                self.assertTrue(at.session_state['feedback_7_open'])

    def test_product_tour_opener_uses_same_dialog_and_source_in_both_languages(self):
        for language in ('lt', 'en'):
            with self.subTest(language=language), patch.object(feedback_ui, 'add_feedback') as save:
                at = AppTest.from_file(str(Path(__file__).with_name('dashboard_language_probe.py')), default_timeout=20).run()
                at.segmented_control[0].set_value(language).run()
                with patch.object(feedback_ui, 'st', SimpleNamespace(session_state=at.session_state)):
                    feedback_ui.open_feedback(7, 'product_tour')
                at.run()
                self.assertFalse(at.exception)
                at.checkbox(key='feedback_7_option_nothing_missing').check().run()
                at.button(key='feedback_7_submit').click().run()
                self.assertFalse(at.exception)
                save.assert_called_once_with(7, '', ['nothing_missing'], 'product_tour')

    def test_sidebar_draft_language_exclusivity_submit_and_reruns(self):
        with patch.object(feedback_ui, 'add_feedback') as save:
            at = AppTest.from_file(str(Path(__file__).with_name('dashboard_language_probe.py')), default_timeout=20).run()
            at.button(key='feedback_7_sidebar').click().run()
            self.assertFalse(at.exception)
            at.checkbox(key='feedback_7_option_bank_connection').check().run()
            at.checkbox(key='feedback_7_option_other').check().run()
            self.assertTrue(at.checkbox(key='feedback_7_option_bank_connection').value)
            at.checkbox(key='feedback_7_option_nothing_missing').check().run()
            self.assertFalse(at.checkbox(key='feedback_7_option_bank_connection').value)
            self.assertFalse(at.checkbox(key='feedback_7_option_other').value)
            at.checkbox(key='feedback_7_option_other').check().run()
            self.assertFalse(at.checkbox(key='feedback_7_option_nothing_missing').value)
            at.text_area(key='feedback_7_comment').set_value('Unchanged draft')
            at.segmented_control(key='feedback_7_language').set_value('en').run()
            self.assertFalse(at.exception)
            self.assertEqual(at.text_area(key='feedback_7_comment').value, 'Unchanged draft')
            self.assertTrue(at.checkbox(key='feedback_7_option_other').value)
            self.assertEqual(at.button(key='feedback_7_submit').label, 'Send feedback')
            at.button(key='feedback_7_submit').click().run()
            self.assertFalse(at.exception)
            save.assert_called_once_with(7, 'Unchanged draft', ['other'], 'sidebar')
            at.run()
            save.assert_called_once()
            at.button(key='feedback_7_return').click().run()
            self.assertFalse(at.session_state['feedback_7_open'])
            at.button(key='feedback_7_sidebar').click().run()
            self.assertEqual(at.text_area(key='feedback_7_comment').value, '')
            self.assertFalse(at.checkbox(key='feedback_7_option_other').value)

    def test_empty_structured_only_comment_only_and_nonfatal_failure(self):
        for language in ('lt','en'):
            with self.subTest(language=language), patch.object(feedback_ui,'add_feedback') as save:
                at = AppTest.from_file(str(Path(__file__).with_name('dashboard_language_probe.py')), default_timeout=20).run()
                at.segmented_control[0].set_value(language).run()
                at.button(key='feedback_7_sidebar').click().run()
                at.button(key='feedback_7_submit').click().run()
                save.assert_not_called()
                self.assertFalse(at.exception)
                at.checkbox(key='feedback_7_option_other').check().run()
                at.button(key='feedback_7_submit').click().run()
                save.assert_called_once_with(7, '', ['other'], 'sidebar')
                at.button(key='feedback_7_return').click().run()
                at.button(key='feedback_7_sidebar').click().run()
                at.text_area(key='feedback_7_comment').set_value('Comment only')
                save.side_effect = RuntimeError('private database details')
                at.button(key='feedback_7_submit').click().run()
                self.assertFalse(at.exception)
                self.assertTrue(at.error)
                self.assertNotIn('private database details', at.error[0].value)
                self.assertEqual(at.text_area(key='feedback_7_comment').value, 'Comment only')
                save.side_effect = None
                at.button(key='feedback_7_submit').click().run()
                self.assertFalse(at.exception)
                save.assert_called_with(7, 'Comment only', [], 'sidebar')
