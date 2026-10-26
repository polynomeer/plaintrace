#!/usr/bin/env python3
"""Validate local documentation links, language pairs and traceability IDs."""
from pathlib import Path
import ast
import re
from urllib.parse import unquote, urlsplit
from inspect_sources import ROOT, decode_source
from generate_source_reference import render

def main():
    documents = sorted([ROOT/'README.md', ROOT/'README.ko.md', * (ROOT/'docs').glob('*.md')])
    links = 0
    for path in documents:
        text = path.read_text()
        assert text.count('```') % 2 == 0, f'Unclosed fence: {path}'
        assert not any(ord(c) < 32 and c not in '\n\r\t' for c in text), f'Control character: {path}'
        # A stray row after a blank line is not a Markdown table.
        plain = re.sub(r'```[\s\S]*?```', '', text)
        for block in re.findall(r'(?:^\|[^\n]*\n)+', plain, re.M):
            rows = block.splitlines()
            assert len(rows) >= 2 and re.fullmatch(r'\|[\s:|\-]+', rows[1]), f'Invalid table: {path}: {rows[0]}'
            assert len({row.count('|') for row in rows}) == 1, f'Table column mismatch: {path}'
        for diagram in re.findall(r'```mermaid\n([\s\S]*?)```', text):
            assert diagram.splitlines()[0] in ('flowchart LR', 'flowchart TB', 'flowchart TD', 'sequenceDiagram'), f'Unexpected diagram declaration: {path}'
        for target in re.findall(r'\]\(([^)]+)\)', text):
            url = urlsplit(target.strip('<>'))
            if url.scheme: continue
            resolved = (path.parent/unquote(url.path)).resolve() if url.path else path
            assert resolved.is_file(), f'Missing target: {path}: {target}'
            if re.fullmatch(r'L\d+',url.fragment):
                source = decode_source(resolved.read_bytes()).splitlines()
                line = int(url.fragment[1:])
                assert 1 <= line <= len(source), f'Invalid line: {target}'
            if resolved.suffix == '.md' and resolved.parent == ROOT/'docs' and resolved != path.with_name(path.stem.replace('.ko','') + ('.md' if path.name.endswith('.ko.md') else '.ko.md')):
                assert resolved.name.endswith('.ko.md') == path.name.endswith('.ko.md'), f'Wrong document language: {path}: {target}'
            if url.fragment and not re.fullmatch(r'L\d+', url.fragment):
                raise AssertionError(f'Unvalidated anchor: {target}')
            links += 1
        if not path.name.endswith('.ko.md'):
            korean = path.with_name(path.stem+'.ko.md')
            assert korean in documents, f'Missing Korean pair: {path}'
            ko = korean.read_text()
            assert f'({korean.name})' in text and f'({path.name})' in ko, f'Missing language links: {path}'
            for pattern in (r'^#{1,6} ', r'^\|', r'^```'):
                assert len(re.findall(pattern,text,re.M))==len(re.findall(pattern,ko,re.M)), f'Pair structure mismatch: {path}: {pattern}'
            literals = lambda value: set(re.findall(r'(?<!`)`([^`\n]+)`(?!`)', re.sub(r'```[\s\S]*?```', '', value)))
            assert literals(text) == literals(ko), f'Technical literal mismatch: {path}: {literals(text) ^ literals(ko)}'
            for lang in ('sh','sql'):
                pattern=r'```'+lang+r'\n([\s\S]*?)```'
                assert re.findall(pattern,text)==re.findall(pattern,ko), f'Command/SQL mismatch: {path}'
    for name,content in render().items():
        assert (ROOT/'docs'/name).read_text()==content, f'Stale generated file: {name}'
    english_test_ids = None
    for suffix in ('','.ko'):
        requirements=(ROOT/'docs'/f'REQUIREMENTS{suffix}.md').read_text()
        tests=(ROOT/'docs'/f'TEST_PLAN{suffix}.md').read_text()
        required=set(re.findall(r'\b(?:FR|NFR)-\d+\b',requirements))
        covered=set(re.findall(r'\b(?:FR|NFR)-\d+\b',tests))
        assert required<=covered, f'Unmapped requirements: {required-covered}'
        test_ids=re.findall(r'^\| (T-\d+) \|',tests,re.M)
        assert test_ids == [f'T-{i:02}' for i in range(1, len(test_ids)+1)], f'Invalid test IDs: {suffix}'
        if english_test_ids is None:
            english_test_ids = test_ids
        else:
            assert test_ids == english_test_ids, 'Bilingual test ID mismatch'
        readme=(ROOT/f'README{suffix}.md').read_text()
        assert f'(docs/README{suffix}.md)' in readme, f'Missing documentation index: {suffix}'
    for test_file, plan_name, prefix in (('test_browser_cli.py','PYTHON_TESTS','PY'),
                                          ('test_execution_cli.py','EXECUTION_TESTS','EX'),
                                          ('test_evtx_cli.py','EVTX_TESTS','EV'),
                                          ('test_recycle_bin_cli.py','RECYCLE_BIN_TESTS','RB'),
                                          ('test_usb_registry_cli.py','USB_REGISTRY_TESTS','USB'),
                                          ('test_recent_docs_cli.py','RECENT_DOCS_TESTS','RD'),
                                          ('test_application_mru_cli.py','APPLICATION_MRU_TESTS','APP'),
                                          ('test_jump_lists_cli.py','JUMP_LISTS_TESTS','JL'),
                                          ('test_shellbags_cli.py','SHELLBAGS_TESTS','SB'),
                                          ('test_dialog_mru_cli.py','DIALOG_MRU_TESTS','DM'),
                                          ('test_userassist_cli.py','USERASSIST_TESTS','UA'),
                                          ('test_run_mru_cli.py','RUN_MRU_TESTS','RUN'),
                                          ('test_explorer_history_cli.py','EXPLORER_HISTORY_TESTS','EH'),
                                          ('test_system_info_cli.py','SYSTEM_INFO_TESTS','SYS')):
        python_tests = ROOT/'tests'/test_file
        if not python_tests.exists():
            continue
        tree = ast.parse(python_tests.read_text())
        actual = {node.name for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
        expected = None
        for suffix in ('', '.ko'):
            plan = (ROOT/'docs'/f'{plan_name}{suffix}.md').read_text()
            cases = re.findall(r'^\| ('+prefix+r'-\d+) \| (test_\w+) \|', plan, re.M)
            assert [identity for identity, _ in cases] == [f'{prefix}-{i:02}' for i in range(1, len(cases)+1)], 'Invalid Python test IDs'
            assert len(cases) == len(actual) and {name for _, name in cases} == actual, 'Unmapped Python tests'
            if expected is None:
                expected = cases
            else:
                assert cases == expected, 'Bilingual Python test mismatch'
        print(f'PASS: {len(actual)} executable cases from {test_file} mapped in both languages.')
    print(f'PASS: {len(documents)} documents, {links} local links, bilingual structures, source references and {len(test_ids)} test IDs.')

if __name__=='__main__': main()
