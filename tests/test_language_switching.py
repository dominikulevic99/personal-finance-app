"""Server-side draft checks. AppTest does not emulate browser form buffering."""

import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class LanguageSwitchTests(unittest.TestCase):
    def test_representative_values_and_navigation_survive_both_directions(self):
        at = AppTest.from_file(Path(__file__).with_name('language_probe.py')).run()
        self.assertFalse(at.exception)
        at.text_input(key='probe_normal').input('Normal draft')
        at.text_input(key='probe_form_name').input('Unsaved name')
        at.number_input(key='probe_form_balance').set_value(123.45)
        at.selectbox(key='probe_form_type').select('CASH')
        at.text_input(key='account_name_17').input('Edit draft')
        at.number_input(key='account_balance_17').set_value(678.9)
        for language in ('en', 'lt'):
            at.get('button_group')[0].set_value(language).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.text_input(key='probe_normal').value, 'Normal draft')
            self.assertEqual(at.text_input(key='probe_form_name').value, 'Unsaved name')
            self.assertEqual(at.number_input(key='probe_form_balance').value, 123.45)
            self.assertEqual(at.selectbox(key='probe_form_type').value, 'CASH')
            self.assertEqual(at.text_input(key='account_name_17').value, 'Edit draft')
            self.assertEqual(at.number_input(key='account_balance_17').value, 678.9)
            self.assertEqual(at.session_state['onboarding_7_step'], 'accounts')
            self.assertEqual(at.session_state['onboarding_7_highest_step'], 2)
            self.assertEqual(at.session_state['product_tour_7_component_1'], {'step': 2})
            self.assertNotIn('probe_submissions', at.session_state)

    def test_initial_language_and_explicit_preference_survive_rerun(self):
        at = AppTest.from_file(Path(__file__).with_name('language_probe.py')).run()
        self.assertEqual(at.get('button_group')[0].value, 'lt')
        at.get('button_group')[0].set_value('en').run()
        at.run()
        self.assertEqual(at.get('button_group')[0].value, 'en')
        self.assertEqual(at.title[0].value, "Know what you have. Know what it's for.")
