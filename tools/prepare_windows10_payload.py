#!/usr/bin/env python3
"""Build an external, source-only test payload directory for a Windows VM CD."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--python-installer', required=True, type=Path)
    parser.add_argument('--node-archive', required=True, type=Path)
    parser.add_argument('--node-shasums', required=True, type=Path)
    args = parser.parse_args()
    dest = args.directory.expanduser().resolve()
    if dest.is_relative_to(ROOT) or dest == Path(dest.anchor):
        parser.error('Payload must stay in a dedicated directory outside the repository')
    if dest.exists():
        parser.error('Existing payload directories will not be replaced')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    node = args.node_archive.resolve(strict=True)
    expected = next(line.split()[0] for line in args.node_shasums.read_text().splitlines()
                    if line.split()[-1] == node.name)
    if sha(node).lower() != expected.lower():
        parser.error('Node archive does not match official published SHA-256')
    python = args.python_installer.resolve(strict=True)
    if python.name != 'python-3.14.8-amd64.exe' or node.name != 'node-v22.23.4-win-x64.zip':
        parser.error('Unexpected runtime filename')
    dest.mkdir(parents=True)
    for file in [python, node, ROOT / 'tools/windows10_guest_bootstrap.ps1']:
        shutil.copyfile(file, dest / file.name)
    with (dest / 'plaintrace.zip').open('xb') as stream:
        subprocess.run(['git', 'archive', '--format=zip', 'HEAD'], cwd=ROOT, stdout=stream, check=True)
    record = {'created_at': datetime.now(timezone.utc).isoformat(), 'source_commit': source_commit,
              'guest_execution': 'not_run', 'windows_license_acceptance': 'user_required',
              'files': [{'name': p.name, 'sha256': sha(p)} for p in sorted(dest.iterdir())]}
    (dest / 'payload.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
