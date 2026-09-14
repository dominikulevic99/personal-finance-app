"""Run regression checks without loading database configuration or secrets.

Usage: python tests/run_offline.py
"""

from pathlib import Path
import ast
import logging
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
sys.modules['database'] = SimpleNamespace(engine=None)
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').disabled = True

# Import production UI against the stub before individual tests mock imports.
import onboarding


def main():
    for path in list(ROOT.glob('*.py')) + list((ROOT / 'tests').glob('*.py')):
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    loader = unittest.TestLoader()
    with patch('fund_progress.st'):
        result = unittest.TextTestRunner().run(loader.discover(str(ROOT / 'tests')))
        # Run existing UI/domain regression cases in EN as well as default LT.
        english = unittest.TestSuite()
        for path in sorted((ROOT / 'tests').glob('test_*.py')):
            if path.stem not in {'test_i18n', 'test_language_switching', 'test_localization_coverage', 'test_feedback_dialog'}:
                english.addTests(loader.loadTestsFromName(path.stem))
        with patch('i18n.get_language', return_value='en'):
            en_result = unittest.TextTestRunner().run(english)
    return 0 if result.wasSuccessful() and en_result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
