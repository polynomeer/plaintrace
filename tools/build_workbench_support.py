#!/usr/bin/env python3
"""Build/check the small public UI projection; never includes evidence records."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render():
    registry = json.loads((ROOT/'compatibility/support.json').read_text(encoding='utf-8'))
    data = dict(updated_on=registry['updated_on'], schema=registry['report_schema'],
                adapters=[{key:row[key] for key in ('id','implementation_maturity','format_predicate','known_gaps')}
                          for row in registry['adapters']],
                hosts=[{key:row[key] for key in ('runner_label','os_family','python_minors','host_qualification')}
                       for row in registry['host_targets']])
    return '// UI projection of compatibility/support.json; checked by tests.\nexport default '+json.dumps(data,ensure_ascii=False,indent=2)+';\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    path = ROOT/'plaintrace/web/support.mjs'
    expected = render()
    if args.check:
        if path.read_text(encoding='utf-8') != expected:
            parser.exit(1,'Stale UI support projection; run python tools/build_workbench_support.py\n')
        print('PASS: UI support projection matches registry')
    else:
        path.write_text(expected,encoding='utf-8')
        print('Updated packaged UI support projection')


if __name__=='__main__': main()
