#!/usr/bin/env python3
"""Generate bilingual source and literal SQL references without changing source.

Use --check to detect stale generated documentation. Only static, literal
CREATE TABLE arguments are indexed; dynamic SQL is explicitly outside coverage.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import re
from urllib.parse import quote
from inspect_sources import ROOT, decode_source
from reconstruct_history import mask

STAMP = '2026-10-13'

def header(stem, title, ko):
    nav = f'[English]({stem}.md) | **한국어**' if ko else f'**English** | [한국어]({stem}.ko.md)'
    note = (f'{STAMP} 보존된 소스에서 생성한 사후 참조입니다. 당시 원본 설계 문서가 아닙니다.' if ko else
            f'Generated on {STAMP} from archived source. This is a retrospective reference, not an original design document.')
    return f'# {title}\n\n{nav}\n\n{note}\n\n'

def link(path, line):
    return f'[{path.name}:{line}](../{quote(path.name)}#L{line})'

def index_source():
    files, schemas = [], defaultdict(lambda: defaultdict(list))
    for path in sorted(ROOT.glob('*.EnScript')):
        raw = path.read_bytes()
        text = decode_source(raw)
        clean = mask(text)
        depth, stack, ends = [0] * len(clean), [], {}
        for i, ch in enumerate(clean):
            depth[i] = len(stack)
            if ch == '{': stack.append(i)
            elif ch == '}': ends[stack.pop()] = i
        if stack: raise ValueError(f'Unbalanced source: {path}')
        classes = []
        for match in re.finditer(r'^[ \t]*class[ \t]+(\w+)[^;{}]*\{', clean, re.M):
            opening = match.end()-1
            if depth[opening] != 0: continue
            closing = ends[opening]
            name = match.group(1)
            methods = []
            pattern = (r'^[ \t]*(?:virtual[ \t]+)?(?:void|bool|String|int|uint|ChartClass|MenuReply|ChartClass::ChartTypes)[ \t]+(\w+)[ \t]*\('
                       + r'|^[ \t]*(' + re.escape(name) + r')[ \t]*\(')
            for method in re.finditer(pattern, clean[opening+1:closing], re.M):
                pos = opening+1+method.start()
                token = pos
                while clean[token].isspace(): token += 1
                if depth[token] != 1: continue
                methods.append((method.group(1) or method.group(2), text[:pos].count('\n')+1))
            classes.append((name, text[:match.start()].count('\n')+1, methods))
        files.append((path, len(text.splitlines()), 'UTF-16LE BOM' if raw.startswith(b'\xff\xfe') else 'UTF-8 / ASCII', classes))
        for match in re.finditer(r'ExecuteNonQuery\s*\(\s*"(CREATE\s+TABLE[^"\r\n]*)"', text, re.I):
            if not clean[match.start():match.start()+5].strip(): continue
            sql = match.group(1)
            table = re.match(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(',sql,re.I)
            if not table: continue
            key = re.sub(r'\s+', ' ', sql).strip()
            schemas[table.group(1)][key].append((path, text[:match.start()].count('\n')+1))
    return files, schemas

def render():
    files, schemas = index_source()
    result = {}
    for ko in (False, True):
        suffix = '.ko' if ko else ''
        out = header('CODE_STRUCTURE','코드 구조와 소스 인덱스' if ko else 'Code Structure and Source Index',ko)
        out += ('## 저장소 구성\n\n루트의 13개 EnScript는 보존 구현, `tools/`는 현재 Python 도구, `docs/`는 사후 문서와 JSON 기준입니다. 기존 분석의 모듈 책임은 [분석](ANALYSIS.ko.md), 런타임 관계는 [상세 설계](SYSTEM_DESIGN.ko.md)를 참조하세요.\n\n' if ko else
                '## Repository Layout\n\nThe 13 root EnScript files are the preserved implementation; `tools/` contains present-day Python utilities; `docs/` contains retrospective documents and JSON baselines. Module responsibilities are in [analysis](ANALYSIS.md); runtime relationships are in [detailed design](SYSTEM_DESIGN.md).\n\n')
        out += ('## 도구\n\n' if ko else '## Tools\n\n')
        descriptions = [
            ('inspect_sources.py','Decode source and show classes or numbered lines','소스 디코딩·클래스·행 번호 조회'),
            ('enscript_textconv.py','Decode Git diffs without changing blobs','blob 변경 없는 Git diff 디코딩'),
            ('verify_archive.py','Verify current source, archived README and commit baseline; needs local archive ref','현 소스·과거 README·커밋 기준 검사; 로컬 archive ref 필요'),
            ('reconstruct_history.py','Read-only plan by default; --apply mutates Git history and is not a routine check','기본 읽기 전용 계획; --apply는 기록 변경이므로 일반 검사로 사용하지 않음'),
            ('generate_source_reference.py','Generate/check this index and SQL appendix','이 인덱스·SQL 부록 생성/검사'),
            ('verify_documentation.py','Check local links, language pairs and requirement/test mappings','로컬 링크·언어 쌍·요구사항/테스트 대응 검사')]
        for name,en,kor in descriptions: out += f'- [{name}](../tools/{name}): {kor if ko else en}.\n'
        out += ('\n## 클래스와 메서드\n\n주석·문자열을 제외한 선언 위치입니다. 생성자를 포함하며 forward declaration은 제외합니다. 일부 반환 타입만 정적 추출하므로 EnScript 컴파일러 수준의 심볼 목록은 아닙니다.\n\n' if ko else
                '\n## Classes and Methods\n\nDeclaration locations exclude comments and strings. Constructors are included, forward declarations are omitted. Extraction covers selected return types and is not a compiler-level symbol table.\n\n')
        for path,lines,encoding,classes in files:
            out += f'### {path.name}\n\n{lines} '+('줄' if ko else 'lines')+f'; {encoding}.\n\n'
            out += '| '+('클래스 / 선언' if ko else 'Class / declaration')+' | '+('메서드 / 위치' if ko else 'Methods / locations')+' |\n| --- | --- |\n'
            for name,line,methods in classes:
                listing = ', '.join(f'`{m}` ({link(path,l)})' for m,l in methods) or ('데이터·설정 클래스' if ko else 'Data/configuration class')
                out += f'| `{name}` ({link(path,line)}) | {listing} |\n'
            out += '\n'
        out += '```sh\npython3 tools/generate_source_reference.py --check\n```\n'
        result[f'CODE_STRUCTURE{suffix}.md'] = out
        out = header('SCHEMA_REFERENCE','SQLite 선언 참조' if ko else 'SQLite Declaration Reference',ko)
        out += ('`ExecuteNonQuery`에 직접 전달한 정적 CREATE TABLE 문자열만 추출합니다. 주석·동적 table_name·변수로 전달한 SQL·INSERT/SELECT는 제외합니다. 전체 런타임 스키마가 아니며 SQL을 실행하거나 오류를 수정하지 않습니다. 공백을 정리하고 동일 선언 위치를 합쳤으며 스키마 변형은 별도 보존했습니다. [데이터 모델](DATA_MODEL.ko.md)을 함께 읽으세요.\n\n' if ko else
                'Only static CREATE TABLE string arguments passed directly to `ExecuteNonQuery` are extracted. Comments, dynamic table_name expressions, SQL passed through variables, and INSERT/SELECT statements are excluded. This is not the complete runtime schema. SQL is not executed or repaired. Whitespace is normalized and identical declarations are grouped; variants remain separate. Read with [the data model](DATA_MODEL.md).\n\n')
        out += f'{len(schemas)} '+('개 테이블 이름, ' if ko else 'table names, ')+str(sum(len(v) for v in schemas.values()))+('개 선언 변형.\n\n' if ko else ' declaration variants.\n\n')
        for table,variants in sorted(schemas.items()):
            out += f'## {table}\n\n'
            for n,(sql,locations) in enumerate(variants.items(),1):
                out += ('변형 ' if ko else 'Variant ')+str(n)+': '+', '.join(link(p,l) for p,l in locations)+'.\n\n'
                # Columns contain no nested function commas in the captured declarations.
                pretty = sql.replace(' (',' (',1)
                opening = pretty.find('(')
                closing = pretty.rfind(')')
                if closing>opening:
                    pretty = pretty[:opening+1]+'\n  '+',\n  '.join(x.strip() for x in pretty[opening+1:closing].split(','))+'\n'+pretty[closing:]
                out += f'```sql\n{pretty}\n```\n\n'
        out += '```sh\npython3 tools/generate_source_reference.py --check\n```\n'
        result[f'SCHEMA_REFERENCE{suffix}.md'] = out
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    result = render()
    for name,content in result.items():
        path=ROOT/'docs'/name
        if args.check:
            if not path.is_file() or path.read_text()!=content: raise SystemExit(f'Stale reference: {path}')
        else: path.write_text(content)
    print(f'PASS: {len(result)} source-reference documents '+('match source.' if args.check else 'generated.'))

if __name__=='__main__': main()
