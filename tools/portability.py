#!/usr/bin/env python3
"""M0 support inventory, strict suite gate and installed-wheel smoke checks.

Development tooling only: generated logs belong outside Git, never take evidence.
Uses the standard library on Python 3.10+; no changes to parser/report contracts.
"""
import argparse
import ast
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'compatibility' / 'support.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_local_result(record, root):
    """Structural consistency check, not authentication of a test claim."""
    env = record.get('environment', {})
    require(all(env.get(k) for k in ('os', 'version', 'machine', 'python', 'sqlite')),
            'Validation requires exact environment')
    counts = record.get('tests', {})
    require(type(counts.get('run')) is int and counts['run'] >= 475,
            'Validation requires complete baseline')
    require(all(type(counts.get(k)) is int and counts[k] == 0
                for k in ('failures', 'errors', 'skips', 'expected_failures', 'unexpected_successes')),
            'Validation cannot pass with failures or skips')
    require(record.get('installed_smoke') == 'passed' and record.get('evidence_qualification') == 'synthetic',
            'M0 qualification requires installed smoke and synthetic-only scope')
    reference = record.get('validation_reference')
    require(isinstance(reference, str) and (root / reference).resolve().is_relative_to(root.resolve())
            and (root / reference).is_file(), 'Missing validation reference')


def validate_registry(data, root=ROOT):
    """Reject inconsistent support claims; never promote a host from a CI label."""
    require(type(data.get('registry_version')) is int and data['registry_version'] == 1,
            'Unsupported registry version')
    metadata = (root / 'pyproject.toml').read_text(encoding='utf-8')
    require(data.get('package_version') == re.search(r'^version = "([^"]+)"', metadata, re.M)[1],
            'Package version drift')
    require(data.get('python_requires') == re.search(r'^requires-python = "([^"]+)"', metadata, re.M)[1],
            'Python requirement drift')
    require(data.get('report_schema') == 15, 'M0 must retain report schema 15')
    require(isinstance(data.get('adapters'), list) and data['adapters'], 'Missing adapters')
    seen = set()
    inventoried_tests = set()
    for item in data['adapters']:
        identity = item.get('id')
        require(isinstance(identity, str) and identity and identity not in seen, 'Duplicate/invalid adapter ID')
        seen.add(identity)
        maturity = item.get('implementation_maturity')
        require(maturity in ('planned', 'partial', 'implemented', 'unsupported'), 'Invalid implementation maturity')
        require(item.get('evidence_qualification') in ('unvalidated', 'synthetic', 'acquired', 'independently_compared'),
                'Invalid evidence qualification')
        require(isinstance(item.get('known_gaps'), list) and item['known_gaps'], 'Missing scope exclusions')
        require(isinstance(item.get('format_predicate'), str) and item['format_predicate'], 'Missing format predicate')
        paths = [item.get('contract')]
        if maturity in ('partial', 'implemented'):
            require(item.get('adapter_version') == data['package_version'], 'Adapter version drift')
            require(item.get('tests') and item.get('module'), 'Implemented adapter requires module and tests')
            require(item['evidence_qualification'] != 'unvalidated', 'Missing implementation test evidence')
            paths += [item['module'], *item['tests']]
            inventoried_tests.update(item['tests'])
        else:
            require(not item.get('module') and not item.get('tests') and item.get('adapter_version') is None,
                    'Unimplemented adapter cannot claim code/tests/version')
            require(item['evidence_qualification'] == 'unvalidated', 'Unimplemented adapter cannot claim validation')
        for path in paths:
            require(isinstance(path, str), 'Missing source reference')
            p = (root / path).resolve()
            require(p.is_relative_to(root.resolve()) and p.is_file(), 'Missing/escaping registry reference: '+path)
        if item['evidence_qualification'] in ('acquired', 'independently_compared'):
            require(item.get('validation_reference'), 'Acquired evidence claim requires a validation reference')
    parser_tests = {str(p.relative_to(root)).replace(os.sep, '/') for p in (root / 'tests').glob('test_*_cli.py')}
    require(inventoried_tests == parser_tests, 'Artifact test inventory drift')
    counts = data.get('baseline_artifact_test_counts', {})
    require(set(counts) == inventoried_tests, 'Missing baseline test counts')
    for path, count in counts.items():
        tree = ast.parse((root / path).read_text(encoding='utf-8'))
        actual = sum(isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                     for node in ast.walk(tree))
        require(type(count) is int and actual >= count, 'Artifact baseline test loss: '+path)
    hosts = data.get('host_targets', [])
    hosted = data.get('hosted_validations', [])
    require(len({r.get('id') for r in hosted}) == len(hosted), 'Duplicate hosted validation IDs')
    hosted_by_id = {}
    for record in hosted:
        validate_local_result(record, root)
        require(re.fullmatch(r'[0-9a-f]{40}', record.get('head_sha', '')) is not None,
                'Hosted validation requires an exact commit')
        require(re.fullmatch(r'https://github.com/[^/]+/[^/]+/actions/runs/\d+',
                             record.get('run_url', '')) is not None,
                'Hosted validation requires a run URL')
        hosted_by_id[record['id']] = record
    require(len({h.get('id') for h in hosts}) == len(hosts), 'Duplicate host IDs')
    require({h.get('os_family') for h in hosts} == {'Windows', 'Darwin', 'Linux'}, 'Three host families required')
    for host in hosts:
        require(host.get('host_qualification') in ('unvalidated', 'tested', 'regressed'), 'Invalid host qualification')
        require(host.get('runner_label') and host.get('python_minors') == ['3.10', '3.14'], 'CI lane drift')
        if host['host_qualification'] == 'tested':
            ids = host.get('validation_ids', [])
            require(len(ids) == len(host['python_minors']) and len(set(ids)) == len(ids)
                    and all(identity in hosted_by_id for identity in ids),
                    'Tested host requires exact environment evidence for every CI lane')
            records = [hosted_by_id[identity] for identity in ids]
            require(all(r['environment']['os'] == host['os_family'] and
                        r.get('runner_label') == host['runner_label'] for r in records),
                    'Hosted validation family/runner mismatch')
            minors = ['.'.join(r['environment']['python'].split('.')[:2]) for r in records]
            require(sorted(minors) == sorted(host['python_minors']), 'Incomplete tested interpreter lanes')
    if data.get('milestone_status') == 'M0_named_host_gate_passed':
        require(all(host['host_qualification'] == 'tested' for host in hosts),
                'M0 completion requires every named host')
    records = data.get('local_validations', [])
    require(len({r.get('id') for r in records}) == len(records), 'Duplicate validation IDs')
    for record in records:
        validate_local_result(record, root)
    fixtures = data.get('fixture_policy', {})
    require(fixtures.get('kind') == 'synthetic_in_temporary_directories', 'Unexpected fixture policy')
    require(set(fixtures.get('source_paths', [])) == inventoried_tests |
            {'tests/jump_fixtures.py', 'tools/portability.py'},
            'Fixture-source inventory drift')
    return data


def environment():
    packages = {}
    for name in ('plaintrace', 'python-evtx', 'hexdump', 'pip', 'setuptools', 'wheel', 'build', 'packaging', 'pyproject_hooks'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    distribution = None
    if platform.system() == 'Linux':
        try:
            distribution = {key: value for key, value in platform.freedesktop_os_release().items()
                            if key in ('ID', 'VERSION_ID', 'PRETTY_NAME')}
        except OSError:
            pass
    return dict(os=platform.system(), release=platform.release(), version=platform.version(),
                macos_version=platform.mac_ver()[0] or None, machine=platform.machine(),
                linux_distribution=distribution,
                python=platform.python_version(), implementation=platform.python_implementation(),
                sqlite=sqlite3.sqlite_version, byteorder=sys.byteorder, packages=packages,
                runner={key: os.environ.get(key) for key in
                        ('RUNNER_OS', 'RUNNER_ARCH', 'ImageOS', 'ImageVersion', 'GITHUB_SHA', 'GITHUB_RUN_ID',
                         'PLAINTRACE_CONTAINER_IMAGE')})


def suite_summary(result):
    def ids(items):
        return [case.id() for case, _ in items]
    # unittest treats skips and expected failures as successful. Qualification does not.
    passed = (result.wasSuccessful() and result.testsRun > 0 and not result.skipped
              and not result.expectedFailures and not result.unexpectedSuccesses)
    return dict(status='passed' if passed else 'failed', tests_run=result.testsRun,
                failures=ids(result.failures), errors=ids(result.errors),
                skipped=[dict(test=case.id(), reason=reason) for case, reason in result.skipped],
                expected_failures=ids(result.expectedFailures),
                unexpected_successes=[case.id() for case in result.unexpectedSuccesses])


def decoder_preflight():
    try:
        installed = importlib.metadata.version('python-evtx')
    except importlib.metadata.PackageNotFoundError as error:
        raise ValueError('Full validation requires .[evtx]: python-evtx==0.8.1') from error
    require(installed == '0.8.1', 'Full validation requires python-evtx==0.8.1, found '+installed)


def suite_check(output):
    decoder_preflight()
    validate_registry(json.loads(REGISTRY.read_text(encoding='utf-8')))
    # Discovery modifies sys.path for tests' existing cross-module fixture imports.
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    require(suite.countTestCases() >= 475, 'Incomplete discovery: original baseline has 475 tests')
    with (output / 'unittest.log').open('w', encoding='utf-8') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    summary = suite_summary(result)
    summary['command'] = 'python -m unittest discover -s tests -v (strict result gate)'
    summary['source_sha256'] = {str(p.relative_to(ROOT)).replace(os.sep, '/'): digest(p)
                               for folder in ('plaintrace', 'tests', 'tools')
                               for p in sorted((ROOT / folder).glob('*.py'))}
    summary['registry_sha256'] = digest(REGISTRY)
    summary['configuration_sha256'] = {name: digest(ROOT / name) for name in
                                       ('pyproject.toml', '.github/workflows/portability.yml')}
    return summary


def run_command(args, cwd, env):
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding='utf-8', errors='strict', timeout=60)
    require(result.returncode == 0, 'Command failed: '+str(args[0])+'\n'+result.stderr)
    return result.stdout


def installed_smoke(wheel):
    """Read a synthetic SQLite file through the *installed* CLI, outside checkout."""
    import plaintrace
    module_path = Path(plaintrace.__file__).resolve()
    require(not module_path.is_relative_to(ROOT), 'Smoke imported checkout instead of installed package')
    require(importlib.metadata.version('plaintrace') == plaintrace.__version__ == '0.15.0',
            'Installed package version mismatch')
    with ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.startswith('plaintrace/') and name.endswith('.py')]
        require(names, 'Wheel has no package modules')
        for name in names:
            require((module_path.parent.parent / name).read_bytes() == archive.read(name),
                    'Installed module differs from supplied wheel: '+name)
    decoder_preflight()
    console = Path(sysconfig.get_path('scripts')) / ('plaintrace.exe' if os.name == 'nt' else 'plaintrace')
    require(console.is_file(), 'Installed console entry point missing')
    clean_env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    clean_env['PYTHONIOENCODING'] = 'utf-8'
    with tempfile.TemporaryDirectory(prefix='plaintrace-installed-') as folder:
        cwd = Path(folder)
        source = cwd / "획득 O'Brien.sqlite"
        with closing(sqlite3.connect(source)) as db, db:
            db.executescript('CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT,last_visit_time INTEGER);'
                             'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER,visit_time INTEGER);')
            db.execute('INSERT INTO urls VALUES (1,?,?,?)',
                       ('https://example.org/?q=%ED%95%9C%EA%B8%80', "O'Brien,한글\nline", 13222310400123456))
            db.execute('INSERT INTO visits VALUES (41,1,13222310400123456)')
        before = digest(source)
        version = run_command([console, '--version'], cwd, clean_env).strip()
        require(version == 'plaintrace 0.15.0', 'Console version drift')
        module_version = run_command([sys.executable, '-I', '-m', 'plaintrace', '--version'], cwd, clean_env).strip()
        require(module_version == version, 'Module/console mismatch')
        report = json.loads(run_command([console, '--input', source], cwd, clean_env))
        require(report['format_version'] == 15 and report['counts']['visits'] == 1, 'Installed JSON/schema mismatch')
        visit = report['visits'][0]
        require(visit['title'] == "O'Brien,한글\nline" and visit['visited_at'] == '2020-01-01T00:00:00.123456Z',
                'Installed Unicode/time interpretation mismatch')
        require(report['sources'][0]['database_sha256'] == before, 'Installed source digest mismatch')
        dest = cwd / 'report.sqlite'
        run_command([console, '--input', source, '--format', 'sqlite', '--output', dest], cwd, clean_env)
        with closing(sqlite3.connect(dest)) as db:
            require(db.execute('PRAGMA user_version').fetchone()[0] == 15, 'Installed SQLite schema mismatch')
            require(db.execute('SELECT title,visited_at FROM visits').fetchone() ==
                    (visit['title'], visit['visited_at']), 'JSON/SQLite observation mismatch')
            require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'Installed foreign-key mismatch')
        previous = digest(dest)
        refused = subprocess.run([str(console), '--input', str(source), '--output', str(dest)],
                                 cwd=cwd, env=clean_env, capture_output=True, timeout=60)
        require(refused.returncode == 2 and digest(dest) == previous, 'Existing output was not protected')
        require(digest(source) == before, 'Installed analysis mutated synthetic input')
    return dict(status='passed', console_version=version, import_location='outside_checkout',
                wheel_sha256=digest(wheel), checks=['console_and_isolated_module', 'unicode_and_exact_time',
                'source_hash_and_preservation', 'json_sqlite_schema_15_parity', 'foreign_keys', 'no_overwrite'],
                fixture_kind='synthetic_temporary_sqlite', evtx_integration='covered_by_full_suite_not_this_smoke')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=('validate', 'suite', 'smoke'))
    parser.add_argument('--output', type=Path, help='New generated-result directory outside the checkout')
    parser.add_argument('--wheel', type=Path, help='Wheel installed into this interpreter (smoke)')
    args = parser.parse_args(argv)
    if args.check == 'validate':
        data = validate_registry(json.loads(REGISTRY.read_text(encoding='utf-8')))
        print(f"PASS: {len(data['adapters'])} adapter entries; 3 host families; schema 15")
        return 0
    require(args.output is not None, '--output is required')
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), 'Generated results must stay outside the checkout')
    if args.check == 'smoke':
        require(args.wheel is not None and args.wheel.is_file(), '--wheel must identify an installed wheel')
    output.mkdir(parents=True, exist_ok=False)
    record = dict(result_version=1, recorded_at=datetime.now(timezone.utc).isoformat(), check=args.check,
                  environment=environment(), status='failed')
    try:
        record['result'] = suite_check(output) if args.check == 'suite' else installed_smoke(args.wheel)
        record['status'] = record['result']['status']
    except Exception as error:
        record['error'] = str(error)
    (output / 'result.json').write_text(json.dumps(record, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"{record['status'].upper()}: {args.check}; record: {output / 'result.json'}")
    if 'error' in record:
        print(record['error'], file=sys.stderr)
    return 0 if record['status'] == 'passed' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
