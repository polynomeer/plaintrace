#!/usr/bin/env python3
"""Plan or create explicitly synthetic archival history using a private Git index.

Default is read-only. --apply builds an independent chain and atomically updates
master only after exact tree verification; existing history is bundled and kept
under refs/archive/pre-reconstruction. No working source is rewritten.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from inspect_sources import decode_source

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['Win_SystemInfo', 'Win_FileMetaData', 'Win_UserAccount', 'Win_RecycleBin',
         'Win_PowerLogOnOff', 'Win_USBInfo', 'Win_PrefetchFile', 'Win_LinkFile',
         'Win_RecentDocuments', 'Win_WebDownloads', 'Win_WebVisitKeyword',
         'Win_TimeLine', 'Plain View of Multi Artifacts']

def git(*args, data=None, env=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, input=data, env=env)

def mask(text):
    # Keep offsets/newlines; ignore braces in comments, string and char literals.
    pattern = r'//[^\r\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"|\x27(?:\\[\s\S]|[^\x27\\])*\x27'
    return re.sub(pattern, lambda m: re.sub(r'[^\r\n]', ' ', m[0]), text)

def stages(name, data):
    text = decode_source(data)
    clean = mask(text)
    depth = [0] * (len(clean) + 1)
    stack, closes = [], {}
    for i, ch in enumerate(clean):
        depth[i] = len(stack)
        if ch == '{': stack.append(i)
        elif ch == '}':
            if not stack: raise ValueError(f'Unmatched closing brace in {name}')
            closes[stack.pop()] = i
    if stack: raise ValueError(f'Unmatched opening brace in {name}')
    encode = lambda s: s.encode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8')
    result = []
    classes = list(re.finditer(r'^\s*class\s+(\w+)[^;{}]*\{', clean, re.M))
    for ci, match in enumerate(classes):
        opening = match.end() - 1
        if depth[opening] != 0: continue
        closing = closes[opening]
        methods = []
        for method in re.finditer(r'^\s*(?:virtual\s+)?(?:void|bool|String|int|uint|ChartClass|MenuReply|ChartClass::ChartTypes)\s+(\w+)\s*\(', clean[opening+1:closing], re.M):
            start = opening + 1 + method.start()
            token = start
            while clean[token].isspace(): token += 1
            if depth[token] != 1: continue
            body = clean.find('{', token, closing)
            if body < 0 or depth[body] != 1: continue
            methods.append((start, closes[body]+1, method.group(1)))
        end = classes[ci+1].start() if ci+1 < len(classes) else len(text)
        if methods:
            result.append((f'{match.group(1)} fields and constructor', encode(text[:methods[0][0]] + '\r\n}\r\n')))
            for mi, (_, stop, method_name) in enumerate(methods):
                fragment = text[:end] if mi == len(methods)-1 else text[:stop] + '\r\n}\r\n'
                result.append((f'{match.group(1)}.{method_name}', encode(fragment)))
        else:
            result.append((match.group(1), encode(text[:end])))
    if not result or result[-1][1] != data:
        raise ValueError(f'Final byte preservation failed for {name}')
    # Avoid empty/duplicate stages.
    return [stage for i, stage in enumerate(result) if i == 0 or stage[1] != result[i-1][1]]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    original = git('rev-parse', 'HEAD').decode().strip()
    plan = [('README.md', 'preserve project description', git('show', f'{original}:README.md'))]
    for stem in ORDER:
        name = stem + '.EnScript'
        data = git('show', f'{original}:{name}')
        for label, fragment in stages(name, data): plan.append((name, label, fragment))
    start = datetime(2017, 7, 1, 10, tzinfo=timezone(timedelta(hours=9)))
    finish = datetime(2017, 11, 30, 18, tzinfo=start.tzinfo)
    records = []
    for i, (name, label, _) in enumerate(plan):
        date = start + (finish-start) * i / (len(plan)-1)
        date = date.replace(microsecond=0)
        records.append({'sequence': i+1, 'date': date.isoformat(), 'file': name,
                        'subject': f'archive: add {Path(name).stem} / {label}'})
    if not args.apply:
        print(json.dumps(records, ensure_ascii=False, indent=2)); return
    if git('symbolic-ref', '--short', 'HEAD').decode().strip() != 'master':
        raise RuntimeError('Expected master; refusing to update another branch')
    if git('diff', '--name-only') or git('diff', '--cached', '--name-only'):
        raise RuntimeError('Tracked changes exist; preserve them before applying')
    backup = ROOT / '.history-backup'
    backup.mkdir(exist_ok=True)
    bundle = backup / f'original-{original[:12]}.bundle'
    if not bundle.exists(): git('bundle', 'create', str(bundle), '--all')
    git('bundle', 'verify', str(bundle))
    archive_ref = 'refs/archive/pre-reconstruction'
    if git('for-each-ref', '--format=%(objectname)', archive_ref).strip():
        raise RuntimeError('Archive ref exists; reconstruction already applied')
    git('update-ref', archive_ref, original)
    manifest = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                        'bytes': p.stat().st_size} for p in ROOT.glob('*.EnScript')}
    manifest['README.md'] = {'sha256': hashlib.sha256((ROOT/'README.md').read_bytes()).hexdigest(), 'bytes': (ROOT/'README.md').stat().st_size}
    with tempfile.TemporaryDirectory(prefix='plaintrace-index-') as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp)/'index'))
        git('read-tree', '--empty', env=env)
        parent = None
        for (name, _, fragment), record in zip(plan, records):
            blob = git('hash-object', '-w', '--stdin', data=fragment).decode().strip()
            git('update-index', '--add', '--cacheinfo', f'100644,{blob},{name}', env=env)
            tree = git('write-tree', env=env).decode().strip()
            commit_env = dict(env, GIT_AUTHOR_DATE=record['date'], GIT_COMMITTER_DATE=record['date'])
            message = record['subject'] + '\n\nRetrospective reconstruction from the preserved final snapshot.\nSynthetic date and order; not an original 2017 development commit.\n'
            params = ['commit-tree', tree] + (['-p', parent] if parent else [])
            parent = git(*params, data=message.encode(), env=commit_env).decode().strip()
            record['commit'] = parent
        if git('rev-parse', f'{parent}^{{tree}}') != git('rev-parse', f'{original}^{{tree}}'):
            raise RuntimeError('Tree mismatch; master has not been changed')
        git('update-ref', 'refs/heads/master', parent, original)
        git('read-tree', parent)
    (ROOT/'docs/source-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (ROOT/'docs/history-map.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n')
    print(f'Created {len(plan)} historical commits. Archive tip: {parent}. Backup: {bundle}')

if __name__ == '__main__': main()
