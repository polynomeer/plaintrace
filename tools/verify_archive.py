#!/usr/bin/env python3
"""Verify source bytes and synthetic archival commit metadata, not runtime behavior."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-only', action='store_true', help='Validate historical blobs without requiring current improved sources to match')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'docs/source-manifest.json').read_text())
    records = json.loads((ROOT/'docs/history-map.json').read_text())
    tip = records[-1]['commit']
    for name, expected in manifest.items():
        # README is maintained today; its manifest describes the archive snapshot.
        data = git('show', f'{tip}:{name}') if name == 'README.md' or args.archive_only else (ROOT/name).read_bytes()
        assert len(data) == expected['bytes'], name
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
    for i, record in enumerate(records):
        commit = record['commit']
        fields = git('show', '-s', '--format=%aI%n%cI%n%s%n%P%n%B', commit).decode().splitlines()
        assert fields[0] == fields[1] == record['date'], commit
        assert fields[2] == record['subject'], commit
        assert fields[3] == (records[i-1]['commit'] if i else ''), commit
        assert 'Synthetic date and order' in '\n'.join(fields[4:]), commit
        changed = git('diff-tree', '--root', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines()
        assert changed == [record['file']], (commit, changed)
    assert git('rev-parse', tip+'^{tree}') == git('rev-parse', 'refs/archive/pre-reconstruction^{tree}')
    assert git('merge-base', '--is-ancestor', tip, 'HEAD') == b''
    scope = 'archived' if args.archive_only else 'current'
    print(f'PASS: {len(manifest)-1} {scope} sources and archived README preserved; '
          f'{len(records)} synthetic commits verified; original tree matches.')

if __name__ == '__main__': main()
