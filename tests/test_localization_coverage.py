"""Catalog, tooltip and real dashboard checks; no database connection."""

import ast
from pathlib import Path
from string import Formatter
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import i18n
import ui_errors
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
UI_FILES = ['app.py', 'onboarding.py', 'onboarding_layout.py', 'onboarding_navigation.py',
            'onboarding_accounts.py', 'onboarding_assets.py', 'onboarding_debts.py', 'onboarding_funds.py',
            'onboarding_monthly_plan.py', 'onboarding_picture.py', 'dashboard_navigation.py',
            'dashboard_tour.py', 'monthly_checkin.py', 'fund_progress.py']


class LocalizationCoverageTests(unittest.TestCase):
    def test_known_validation_failure_is_translated_and_stops_success_path(self):
        for language in ('lt', 'en'):
            with patch('i18n.get_language', return_value=language), patch.object(ui_errors, 'st') as ui:
                ui.stop.side_effect = RuntimeError('stopped')
                action = unittest.mock.Mock(side_effect=ValueError('Fund does not belong to this user.'))
                with self.assertRaisesRegex(RuntimeError, 'stopped'):
                    ui_errors.run_ui_action(action, 7, 14)
                action.assert_called_once_with(7, 14)
                ui.error.assert_called_once_with(i18n.t('errors.bucket_unavailable'))

    def test_localized_action_keeps_arguments_and_success_result(self):
        action = unittest.mock.Mock(return_value=14)
        self.assertEqual(ui_errors.run_ui_action(action, 7, amount=20), 14)
        action.assert_called_once_with(7, amount=20)

    def test_placeholders_and_catalog_keys_match(self):
        en, lt = i18n.catalog('en'), i18n.catalog('lt')
        self.assertEqual(en.keys(), lt.keys())
        fields = lambda value: {field for _, field, _, _ in Formatter().parse(value) if field}
        for key in en:
            with self.subTest(key=key):
                self.assertTrue(en[key].strip() and lt[key].strip())
                self.assertEqual(fields(en[key]), fields(lt[key]))
        for file in UI_FILES:
            for node in ast.walk(ast.parse((ROOT / file).read_text(encoding='utf-8-sig'))):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 't' and node.args and isinstance(node.args[0], ast.Constant):
                    self.assertIn(node.args[0].value, en, file)

    def test_no_literal_ui_labels_help_or_messages(self):
        methods = {'title','header','subheader','caption','text','write','info','warning','error','success',
                   'metric','text_input','text_area','number_input','selectbox','checkbox','button','form_submit_button','expander'}
        for file in UI_FILES:
            for node in ast.walk(ast.parse((ROOT / file).read_text(encoding='utf-8-sig'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in methods:
                    for value in node.args[:1] + [kw.value for kw in node.keywords if kw.arg in ('help','placeholder')]:
                        self.assertFalse(isinstance(value,ast.Constant) and isinstance(value.value,str), f'{file}:{node.lineno}')

    def test_months_and_internal_enum_labels(self):
        for language in ('lt', 'en'):
            with patch('i18n.get_language', return_value=language):
                self.assertIn('2025', i18n.month_period(2025, 1))
                self.assertIn(i18n.month_name(1), i18n.month_period(2025, 1))
                self.assertEqual(i18n.enum_label('FUND'), 'Tikslas' if language=='lt' else 'Bucket')

    def test_dashboard_drafts_tooltips_and_internal_options_survive_language_switch(self):
        at = AppTest.from_file(str(ROOT / 'tests' / 'dashboard_language_probe.py'), default_timeout=20).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value, 'Tavo finansinis vaizdas')
        self.assertIn('Pinigai tavo sąskaitose', at.metric[1].proto.help)
        at.text_input(key='account_name_11').set_value('Draft unchanged')
        at.text_input(key='dashboard_7_asset_name').set_value('Unsaved asset')
        at.selectbox(key='dashboard_7_asset_type').set_value('CAR')
        at.number_input(key='fund_edit_amount_40').set_value(77)
        at.segmented_control[0].set_value('en').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input(key='account_name_11').value, 'Draft unchanged')
        self.assertEqual(at.text_input(key='dashboard_7_asset_name').value, 'Unsaved asset')
        self.assertEqual(at.selectbox(key='dashboard_7_asset_type').value, 'CAR')
        self.assertEqual(at.number_input(key='fund_edit_amount_40').value, 77)
        self.assertIn('Money currently available', at.metric[1].proto.help)
        self.assertEqual(at.selectbox(key='plan_item_type_21').value, 'FUND')
        at.segmented_control[0].set_value('lt').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input(key='account_name_11').value, 'Draft unchanged')
        self.assertEqual(at.text_input(key='dashboard_7_asset_name').value, 'Unsaved asset')
        self.assertEqual(at.number_input(key='fund_edit_amount_40').value, 77)
        self.assertEqual(at.session_state['onboarding_7_dashboard'], True)
