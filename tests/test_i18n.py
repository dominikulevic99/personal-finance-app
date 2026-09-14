import unittest
from unittest.mock import patch
from types import SimpleNamespace

import i18n


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.state = {}
        stub = patch.object(i18n, 'st', SimpleNamespace(session_state=self.state))
        stub.start()
        self.addCleanup(stub.stop)

    def test_default_and_explicit_choice(self):
        self.assertEqual(i18n.initialize_language(7), 'lt')
        i18n.set_language('en')
        self.assertEqual(i18n.initialize_language(7), 'en')

    def test_users_are_independent_and_guest_choice_is_consumed_once(self):
        i18n.initialize_language()
        i18n.set_language('en')
        self.assertEqual(i18n.initialize_language(7), 'en')
        self.assertEqual(i18n.initialize_language(8), 'lt')
        self.assertEqual(i18n.initialize_language(7), 'en')

    def test_approved_terminology(self):
        self.assertEqual(i18n.t('product.promise', language='lt'), 'Žinok, kiek turi. Žinok, kam skirti tavo pinigai.')
        for key, lt, en in [('buckets.plural', 'Tikslai', 'Buckets'),
                            ('metrics.set_aside', 'Atidėta tikslams', 'Set Aside'),
                            ('metrics.free_cash', 'Laisvi pinigai', 'Free Cash')]:
            self.assertEqual(i18n.t(key, language='lt'), lt)
            self.assertEqual(i18n.t(key, language='en'), en)

    def test_catalog_parity_and_missing_key_detection(self):
        self.assertEqual(set(i18n.catalog('lt')), set(i18n.catalog('en')))
        with self.assertWarns(RuntimeWarning):
            self.assertEqual(i18n.t('unknown', language='lt'), '[unknown]')

    def test_switch_only_changes_language_preference(self):
        self.state.update({'onboarding_7_step': 'funds', 'product_tour_7_component_1': {'step': 2},
                           'fund_id': 23, 'draft_balance': '123.45',
                           '_analytics_attempted': {(7, 'contribution_confirmed', 'fund')}})
        original = dict(self.state)
        i18n.initialize_language(7)
        i18n.set_language('en')
        i18n.set_language('lt')
        for key, value in original.items():
            self.assertEqual(self.state[key], value)
