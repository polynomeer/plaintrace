#!/usr/bin/env python3
"""Read archived EnScript without modifying encodings or line endings."""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def decode_source(data):
    return data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8-sig')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', nargs='?', help='filename to display as decoded text')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int)
    args = parser.parse_args()
    if args.file:
        lines = decode_source((ROOT / args.file).read_bytes()).splitlines()
        for i in range(args.start - 1, min(args.end or len(lines), len(lines))):
            print(f'{i + 1:5}: {lines[i]}')
    else:
        for path in sorted(ROOT.glob('*.EnScript')):
            data = path.read_bytes()
            text = decode_source(data)
            print(f'{path.name}: {len(text.splitlines())} lines, {len(data)} bytes, '
                  f'{"UTF-16LE BOM" if data.startswith(bytes.fromhex("fffe")) else "UTF-8/ASCII"}')
            for match in re.finditer(r'^\s*class\s+(\w+)[^;\r\n]*\{', text, re.M):
                print(f'  {match.group(1)}')

if __name__ == '__main__':
    main()
