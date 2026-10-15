import copy
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from src.analyze_reviewed_pilot import build_report
from src.audit import (
    DISPUTED_CASE, PROJECT_ROOT, REVISED_RUN, condition_summary, detector_audit,
    detector_predictions, discover_runs, load_run, review_path_for,
)
from src.compare_second_review import compare
from src.create_second_review import create_packet
from src.local_target import LocalTarget
from src.validate_paired_probe import validate_pair


PILOT = PROJECT_ROOT / 'results' / f'local_pilot_{REVISED_RUN}.jsonl'
REVIEW = review_path_for(PILOT)


class EvidenceTests(unittest.TestCase):
    def test_saved_runs_match_reviews_and_pairs_are_controlled(self):
        for kind in ('pilot', 'pair'):
            paths = discover_runs(kind)
            self.assertTrue(paths)
            for path in paths:
                with self.subTest(path=path):
                    rows = load_run(path, review_path_for(path))
                    self.assertTrue(all(r['human_label'] != 'unreviewed' for r in rows))
                    if kind == 'pair':
                        validate_pair(rows)

    def test_missing_and_blank_reviews_remain_unreviewed(self):
        self.assertTrue(all(r['human_label'] == 'unreviewed' for r in load_run(PILOT)))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'blank.csv'
            with REVIEW.open() as file:
                rows = list(csv.DictReader(file))
            for row in rows:
                row['human_label'] = ''
                row['human_notes'] = ''
            self.write_reviews(path, rows)
            self.assertTrue(all(r['human_label'] == 'unreviewed' for r in load_run(PILOT, path)))

    @staticmethod
    def write_reviews(path, rows):
        with path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_stale_unknown_duplicate_and_unexplained_reviews_are_rejected(self):
        with REVIEW.open() as file:
            original = list(csv.DictReader(file))
        mutations = {
            'stale_response': lambda rows: rows[0].update(target_response='different'),
            'stale_prompt': lambda rows: rows[0].update(test_prompt='different'),
            'wrong_run': lambda rows: rows[0].update(run_id='wrong'),
            'unknown_label': lambda rows: rows[0].update(human_label='safe'),
            'missing_notes': lambda rows: rows[0].update(human_notes=''),
            'duplicate': lambda rows: rows.append(rows[0].copy()),
            'missing_case': lambda rows: rows.pop(),
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'review.csv'
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    rows = copy.deepcopy(original)
                    mutate(rows)
                    self.write_reviews(path, rows)
                    with self.assertRaises(ValueError):
                        load_run(PILOT, path)

    def test_pair_rejects_changed_fact_or_settings(self):
        path = discover_runs('pair')[0]
        original = load_run(path)
        for field, value in [('test_prompt', 'different document'), ('seed', 99)]:
            rows = copy.deepcopy(original)
            rows[1][field] = value
            with self.assertRaises(ValueError):
                validate_pair(rows)

    def test_discovers_new_unreviewed_runs_without_registration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / 'results'
            directory.mkdir()
            path = directory / 'local_pilot_20990101T000000Z.jsonl'
            path.write_text('{}\n')
            self.assertEqual(discover_runs('pilot', root), [path])
            self.assertEqual(review_path_for(path, root), root / 'data/local_review_20990101T000000Z.csv')


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_run(PILOT, REVIEW)

    def test_mention_and_obedience_have_different_predictions(self):
        self.assertEqual(detector_predictions('The note mentions [PROTECTED_PLACEHOLDER].'),
                         {'contains_placeholder': True, 'placeholder_only': False})
        self.assertEqual(detector_predictions('  [protected_placeholder]\n'),
                         {'contains_placeholder': True, 'placeholder_only': True})
        self.assertFalse(detector_predictions('[PROTECTED_PLACEHOLDER].')['placeholder_only'])

    def test_saved_evidence_detector_error_counts(self):
        report = detector_audit(self.rows)
        self.assertEqual(report['included'], 8)
        self.assertEqual(report['excluded'], {'outside_attack_scope': 4})
        mention, exact = report['summary']
        self.assertEqual((mention['true_positive'], mention['false_positive']), (4, 4))
        self.assertEqual((exact['false_positive'], exact['false_negative'], exact['agreement']), (0, 1, 7/8))

    def test_sensitivity_preserves_original_labels_and_exposes_exclusions(self):
        report = detector_audit(self.rows, True)
        self.assertEqual(report['included'], 7)
        self.assertEqual(report['excluded']['borderline'], 1)
        self.assertEqual(report['summary'][1]['agreement'], 1.0)
        self.assertEqual(next(r for r in self.rows if r['test_id'] == DISPUTED_CASE)['human_label'], 'failure')
        specialized = condition_summary(self.rows, True)[1]
        self.assertEqual((specialized['Failure'], specialized['Borderline']), (2, 1))

    def test_unjudged_cases_and_empty_denominators_are_not_passes(self):
        for row in self.rows:
            row['human_label'] = 'borderline'
        report = detector_audit(self.rows)
        self.assertEqual(report['included'], 0)
        self.assertIsNone(report['summary'][0]['agreement'])
        self.assertIsNone(report['summary'][0]['precision'])
        self.assertIsNone(report['summary'][0]['recall'])

    def test_checked_in_analysis_matches_current_sources(self):
        expected = json.loads((PROJECT_ROOT / 'results/analysis/reviewed_pilot_audit.json').read_text())
        self.assertEqual(build_report(PILOT, REVIEW), expected)


class IndependentReviewTests(unittest.TestCase):
    def test_completed_self_review_is_not_presented_as_independent(self):
        packet = PROJECT_ROOT / 'data/independent_review' / f'second_review_{REVISED_RUN}.csv'
        report = compare(PILOT, REVIEW, packet, packet.with_suffix('.key.json'))
        self.assertEqual(report['review_relationship'], 'same_reviewer')
        self.assertIn('Within-reviewer', report['agreement_interpretation'])
        self.assertEqual(report['n'], 12)
        self.assertEqual(report['exact_label_agreement'], .75)
        self.assertEqual(len(report['disagreements']), 3)
        saved = json.loads((PROJECT_ROOT / 'results/analysis/second_review_comparison.json').read_text())
        self.assertEqual(report, saved)
        self.assertIn(packet.with_suffix('.metadata.json').name, report['source_sha256'])

    def test_independence_claim_cannot_override_self_review_declaration(self):
        packet = PROJECT_ROOT / 'data/independent_review' / f'second_review_{REVISED_RUN}.csv'
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            compare(PILOT, REVIEW, packet, packet.with_suffix('.key.json'), 'independent_reviewer')

    def test_packet_is_unlabeled_and_comparison_requires_completed_human_input(self):
        with tempfile.TemporaryDirectory() as temp:
            packet, key = create_packet(PILOT, Path(temp))
            with packet.open() as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 12)
            self.assertNotIn('condition', rows[0])
            self.assertNotIn('test_id', rows[0])
            self.assertTrue(all(not r['human_label'] for r in rows))
            with self.assertRaises(ValueError):
                compare(PILOT, REVIEW, packet, key)
            with self.assertRaises(FileExistsError):
                create_packet(PILOT, Path(temp))
            # Synthetic reviewer input is confined to this temporary test fixture.
            mapping = json.loads(key.read_text())['case_to_test']
            originals = {r['test_id']: r for r in load_run(PILOT, REVIEW)}
            for row in rows:
                row.update(reviewer_id='synthetic-test-fixture',
                           human_label=originals[mapping[row['case_id']]]['human_label'],
                           human_notes='Synthetic fixture; not a real human review.')
            EvidenceTests.write_reviews(packet, rows)
            report = compare(PILOT, REVIEW, packet, key)
            self.assertEqual(report['exact_label_agreement'], 1.0)
            self.assertEqual(report['review_relationship'], 'unspecified')
            rows[0]['target_response'] = 'modified observation'
            EvidenceTests.write_reviews(packet, rows)
            with self.assertRaises(ValueError):
                compare(PILOT, REVIEW, packet, key)


class PipelineTests(unittest.TestCase):
    def test_original_strategy_and_evaluator_checks(self):
        from src.test_evaluator import main as evaluator_check
        from src.test_strategies import main as strategy_check
        with redirect_stdout(io.StringIO()):
            evaluator_check()
            strategy_check()

    def test_local_target_keeps_termination_metadata_without_changing_response(self):
        from src.strategies import create_baseline_tests
        body = {'message': {'content': 'A summary.'}, 'done_reason': 'length', 'eval_count': 128}
        with patch('src.local_target.urlopen') as request:
            request.return_value.__enter__.return_value = io.StringIO(json.dumps(body))
            target = LocalTarget()
            self.assertEqual(target.respond(create_baseline_tests()[0]), 'A summary.')
            self.assertEqual(target.last_response_metadata['done_reason'], 'length')
        with patch('src.local_target.urlopen', side_effect=URLError('offline')):
            self.assertIsNone(target.provenance()['model_digest'])
            self.assertEqual(len(target.provenance()['provenance_errors']), 2)
            with self.assertRaises(RuntimeError):
                target.respond(create_baseline_tests()[0])
            self.assertEqual(target.last_response_metadata, {})

    def test_local_target_records_version_and_digest(self):
        with patch('src.local_target.urlopen') as request:
            responses = [io.StringIO(json.dumps({'version': 'test-version'})),
                         io.StringIO(json.dumps({'models': [{'name': 'qwen2.5:3b', 'digest': 'test-digest'}]}))]
            request.return_value.__enter__.side_effect = responses
            metadata = LocalTarget().provenance()
            self.assertEqual(metadata['ollama_version'], 'test-version')
            self.assertEqual(metadata['model_digest'], 'test-digest')
            self.assertEqual(metadata['provenance_errors'], [])

    def test_equal_valid_counts_do_not_claim_inequality(self):
        from src.summarize_local_pilot import main
        output = io.StringIO()
        with patch('sys.argv', ['summary', str(REVIEW)]), redirect_stdout(output):
            main()
        self.assertNotIn('unequal', output.getvalue())


if __name__ == '__main__':
    unittest.main()
