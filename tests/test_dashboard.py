"""Exercise real dashboard branches without a running Ollama service."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.audit import PROJECT_ROOT, REVISED_RUN


class DashboardTests(unittest.TestCase):
    def start_app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(PROJECT_ROOT / 'app.py')).run(timeout=30)

    def assert_healthy(self, app):
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(len(app.error), 0, str(app.error))

    def test_saved_runs_demo_views_and_sensitivity(self):
        app = self.start_app()
        self.assert_healthy(app)
        self.assertEqual(app.selectbox[0].value, 'Local-model pilots')
        self.assertTrue(any('Second review pass by the same reviewer' == item.value for item in app.header))
        self.assertTrue(any(item.label == 'Agreement between review passes' and item.value == '75%' for item in app.metric))
        self.assertIn(REVISED_RUN, app.selectbox[1].value.name)
        # Summary table keeps the original labels; sensitivity adds another table.
        self.assertEqual(app.dataframe[0].value.iloc[1]['Failure'], 3)
        app.checkbox[0].check().run(timeout=30)
        self.assert_healthy(app)
        self.assertEqual(app.dataframe[1].value.iloc[1]['Failure'], 2)
        self.assertEqual(app.dataframe[1].value.iloc[1]['Borderline'], 1)
        for option in list(app.selectbox[1].options):
            app.selectbox[1].select(option).run(timeout=30)
            self.assert_healthy(app)
        app.selectbox[0].select('Paired probes').run(timeout=30)
        self.assert_healthy(app)
        for option in list(app.selectbox[1].options):
            app.selectbox[1].select(option).run(timeout=30)
            self.assert_healthy(app)
        for dataset in ('Curated sample data', 'Offline experiment'):
            app.selectbox[0].select(dataset).run(timeout=30)
            self.assert_healthy(app)

    def test_new_unreviewed_run_is_inspectable(self):
        source = PROJECT_ROOT / 'results' / f'local_pilot_{REVISED_RUN}.jsonl'
        with tempfile.TemporaryDirectory() as temp:
            run_id = '20990101T000000Z'
            path = Path(temp) / f'local_pilot_{run_id}.jsonl'
            records = [json.loads(line) for line in source.read_text().splitlines()]
            for row in records:
                row['run_id'] = run_id
            path.write_text(''.join(json.dumps(row) + '\n' for row in records))
            with patch('src.audit.discover_runs', return_value=[path]):
                app = self.start_app()
                self.assert_healthy(app)
                self.assertEqual(app.dataframe[0].value['Unreviewed'].sum(), 12)
                self.assertTrue(any('No attack responses' in item.value for item in app.info))

    def test_corrupt_review_is_reported_without_showing_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.csv'
            path.write_text('test_id,human_label\nwrong,pass\n')
            with patch('src.audit.review_path_for', return_value=path):
                app = self.start_app()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(len(app.error), 1)
                self.assertIn('Review IDs', app.error[0].value)
                self.assertEqual(len(app.dataframe), 0)


if __name__ == '__main__':
    unittest.main()
