"""M0 gate regressions: a green unittest run alone cannot certify a host."""
from copy import deepcopy
import importlib.metadata
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import portability


class PortabilityTests(unittest.TestCase):
    def registry(self):
        return json.loads(portability.REGISTRY.read_text(encoding='utf-8'))

    def test_current_registry_and_all_artifact_test_inventory(self):
        data = portability.validate_registry(self.registry())
        self.assertEqual(sum(data['baseline_artifact_test_counts'].values()), 475)
        self.assertEqual(len([a for a in data['adapters'] if a['implementation_maturity'] == 'partial']), 17)
        self.assertEqual(len([a for a in data['adapters'] if a['implementation_maturity'] == 'planned']), 4)

    def test_duplicate_missing_and_escaping_references_rejected(self):
        for mutation in ('duplicate', 'missing', 'escape'):
            data = self.registry()
            if mutation == 'duplicate':
                data['adapters'].append(deepcopy(data['adapters'][0]))
            else:
                data['adapters'][0]['contract'] = 'missing.md' if mutation == 'missing' else '../outside.md'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                portability.validate_registry(data)

    def test_unimplemented_adapter_cannot_claim_synthetic_validation(self):
        data = self.registry()
        data['adapters'][-1]['evidence_qualification'] = 'synthetic'
        with self.assertRaisesRegex(ValueError, 'Unimplemented adapter cannot claim validation'):
            portability.validate_registry(data)

    def test_tested_host_cannot_be_inferred_from_runner_label(self):
        data = self.registry()
        data['host_targets'][0]['host_qualification'] = 'tested'
        data['host_targets'][0].pop('validation_ids', None)
        with self.assertRaisesRegex(ValueError, 'Tested host requires exact environment'):
            portability.validate_registry(data)

    def hosted_registry(self):
        # Structural fixtures only, not claims about actual CI execution.
        data = self.registry()
        host = data['host_targets'][0]
        host['host_qualification'] = 'tested'
        host['validation_ids'] = ['synthetic-ci-310', 'synthetic-ci-314']
        data['hosted_validations'] = [dict(id=identity, head_sha='1'*40,
            run_url='https://github.com/example/project/actions/runs/1',
            runner_label=host['runner_label'], environment=dict(os=host['os_family'],
            version='synthetic', machine='synthetic', python=minor+'.0', sqlite='synthetic'),
            tests=dict(run=489, failures=0, errors=0, skips=0, expected_failures=0, unexpected_successes=0),
            installed_smoke='passed', evidence_qualification='synthetic',
            validation_reference='docs/M0_TESTS.md')
            for identity, minor in zip(host['validation_ids'], host['python_minors'])]
        # Other hosts may have real evidence in the repository registry.
        for other in data['host_targets'][1:]:
            other['host_qualification'] = 'unvalidated'
        data['milestone_status'] = 'M0_implemented_named_host_qualification_pending'
        return data

    def test_hosted_qualification_requires_both_interpreters_and_matching_host(self):
        data = self.hosted_registry()
        portability.validate_registry(data)
        for change in ('missing', 'duplicate_minor', 'wrong_family', 'wrong_runner', 'milestone'):
            broken = deepcopy(data)
            records = broken['hosted_validations']
            if change == 'missing':
                records.pop()
            elif change == 'duplicate_minor':
                records[1]['environment']['python'] = '3.10.9'
            elif change == 'wrong_family':
                records[1]['environment']['os'] = 'Other'
            elif change == 'wrong_runner':
                records[1]['runner_label'] = 'other-runner'
            else:
                broken['milestone_status'] = 'M0_named_host_gate_passed'
            with self.subTest(change=change), self.assertRaises(ValueError):
                portability.validate_registry(broken)

    def test_hosted_evidence_requires_unique_ids_exact_commit_and_run_url(self):
        for change in ('duplicate', 'commit', 'url', 'skip'):
            data = self.hosted_registry()
            records = data['hosted_validations']
            if change == 'duplicate':
                records.append(deepcopy(records[0]))
            elif change == 'commit':
                records[0]['head_sha'] = 'branch-name'
            elif change == 'url':
                records[0]['run_url'] = 'not-a-run'
            else:
                records[0]['tests']['skips'] = 1
            with self.subTest(change=change), self.assertRaises(ValueError):
                portability.validate_registry(data)

    def test_passing_result_claim_requires_zero_skips_and_installed_smoke(self):
        # Reuse a real contract path only as a reference-existence fixture.
        record = dict(environment=dict(os='Darwin', version='test', machine='arm64',
                      python='3.14', sqlite='test'), tests=dict(run=488, failures=0,
                      errors=0, skips=0, expected_failures=0, unexpected_successes=0),
                      installed_smoke='passed', evidence_qualification='synthetic',
                      validation_reference='docs/CROSS_PLATFORM_ROADMAP.md')
        portability.validate_local_result(record, portability.ROOT)
        for field in ('failures', 'errors', 'skips', 'expected_failures', 'unexpected_successes'):
            broken = deepcopy(record)
            broken['tests'][field] = 1
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'failures or skips'):
                portability.validate_local_result(broken, portability.ROOT)
        record['installed_smoke'] = 'unvalidated'
        with self.assertRaisesRegex(ValueError, 'installed smoke'):
            portability.validate_local_result(record, portability.ROOT)

    def test_missing_inventory_and_reduced_baseline_rejected(self):
        data = self.registry()
        data['adapters'][0]['tests'] = ['tests/test_execution_cli.py']
        data['adapters'][1]['tests'] = ['tests/test_execution_cli.py']
        with self.assertRaisesRegex(ValueError, 'inventory drift'):
            portability.validate_registry(data)
        data = self.registry()
        data['baseline_artifact_test_counts']['tests/test_browser_cli.py'] = 999
        with self.assertRaisesRegex(ValueError, 'baseline test loss'):
            portability.validate_registry(data)

    def test_package_python_schema_and_lane_drift_rejected(self):
        for field, value in [('package_version', '0.0.0'), ('python_requires', '>=3.14'),
                             ('report_schema', 16), ('registry_version', True)]:
            data = self.registry()
            data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                portability.validate_registry(data)
        data = self.registry()
        data['host_targets'][0]['python_minors'] = ['3.14']
        with self.assertRaisesRegex(ValueError, 'lane drift'):
            portability.validate_registry(data)

    def run_cases(self, *cases):
        return unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(cases))

    def test_skip_expected_failure_and_empty_suite_fail_qualification(self):
        class Skipped(unittest.TestCase):
            def runTest(self):
                self.skipTest('host capability absent')
        class Expected(unittest.TestCase):
            @unittest.expectedFailure
            def runTest(self):
                self.fail('known regression')
        for result in (self.run_cases(Skipped()), self.run_cases(Expected()), self.run_cases()):
            self.assertTrue(result.wasSuccessful())
            self.assertEqual(portability.suite_summary(result)['status'], 'failed')

    def test_passing_suite_qualifies_but_error_and_failure_do_not(self):
        class Pass(unittest.TestCase):
            def runTest(self):
                self.assertEqual(1, 1)
        class Fail(unittest.TestCase):
            def runTest(self):
                self.fail('failed')
        class Error(unittest.TestCase):
            def runTest(self):
                raise ValueError('broken')
        self.assertEqual(portability.suite_summary(self.run_cases(Pass()))['status'], 'passed')
        for result in (self.run_cases(Fail()), self.run_cases(Error())):
            self.assertEqual(portability.suite_summary(result)['status'], 'failed')

    def test_decoder_absent_or_wrong_version_fails_before_discovery(self):
        for installed in (None, '0.8.0'):
            with self.subTest(installed=installed):
                effect = importlib.metadata.PackageNotFoundError('python-evtx') if installed is None else None
                with patch.object(portability.importlib.metadata, 'version', return_value=installed, side_effect=effect):
                    with self.assertRaisesRegex(ValueError, 'python-evtx==0.8.1'):
                        portability.decoder_preflight()

    def test_generated_results_cannot_be_written_into_repository(self):
        with self.assertRaisesRegex(ValueError, 'outside the checkout'):
            portability.main(['suite', '--output', str(portability.ROOT / 'results')])
        self.assertFalse((portability.ROOT / 'results').exists())

    def test_environment_uses_allowlist_not_whole_environment(self):
        with patch.dict('os.environ', {'PLAINTRACE_PRIVATE_TOKEN': 'must-not-export', 'ImageVersion': 'test-image'}):
            data = portability.environment()
        self.assertNotIn('must-not-export', json.dumps(data))
        self.assertEqual(data['runner']['ImageVersion'], 'test-image')
        self.assertTrue(data['python'])
        self.assertTrue(data['sqlite'])


if __name__ == '__main__':
    unittest.main()
