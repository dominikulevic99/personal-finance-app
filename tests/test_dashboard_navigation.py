"""Navigation targets stay on the existing dashboard; no data access."""

import ast
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import dashboard_navigation as navigation


class DashboardNavigationTests(unittest.TestCase):
    def test_links_have_explicit_heading_targets(self):
        ui = MagicMock()
        with patch.object(navigation, 'st', ui):
            navigation.render_section_links()
        links = [call.args[0] for call in ui.markdown.call_args_list]
        self.assertEqual(len(links), 7)
        targets = set()
        for filename in ('app.py', 'monthly_checkin.py'):
            tree = ast.parse(Path(filename).read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for keyword in node.keywords:
                        if keyword.arg == 'anchor' and isinstance(keyword.value, ast.Constant):
                            targets.add(keyword.value.value)
        for link in links:
            self.assertIn(link.split('](#')[1][:-1], targets)

    def test_guide_opens_only_on_explicit_click(self):
        ui = MagicMock()
        with patch.object(navigation, 'st', ui), patch.object(navigation, 'start_tour') as guide:
            ui.button.return_value = False
            navigation.render_guide_action(7)
            guide.assert_not_called()
            ui.button.return_value = True
            navigation.render_guide_action(7)
            guide.assert_called_once_with(7)
