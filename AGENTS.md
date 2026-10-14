# Plaintrace / Plain View of Multi Artifacts

Legacy Windows forensic artifact plugin written in EnCase EnScript, originally developed during the 2017 BoB digital forensics project.

- Read `docs/ANALYSIS.md` and `docs/HISTORY.md` before changing archived code or history.
- Preserve original `.EnScript` bytes, BOM, mixed UTF-8/UTF-16LE encodings and CRLF. Never apply a repository-wide formatter or encoding conversion.
- Use `python3 tools/inspect_sources.py` to read decoded source and inspect classes. Plain `rg` will miss UTF-16 files.
- Use `python3 tools/verify_archive.py` to verify the archived snapshot. This is integrity validation, not compilation or behavioral testing.
- Runtime validation requires Windows, EnCase and its EnScript APIs; no SDK, case fixture or portable compiler is bundled. Do not claim runtime tests passed on macOS.
- Keep generated exports, evidence, caches and backup bundles out of Git.
- History dated July–November 2017 is a retrospective reconstruction from a final snapshot. Its dates and task order are synthetic, not evidence of actual historical work.
- Modern agent tooling and analysis must use actual creation dates, outside the reconstructed historical chain.

## Improvement branch

- The user authorized source improvements on `codex/prioritized-code-fixes`; preserve the baseline at tag `archive/pre-improvements-2026-10-13` and never rewrite master or the 2017 history.
- Read `docs/IMPROVEMENTS.md` for the branch's behavior and remaining host-validation requirements. Keep file encodings, BOMs and CRLF when editing.
- Use `python3 tools/verify_archive.py --archive-only` to validate historical blobs on an improvement branch. Default verification intentionally requires unchanged working source.
- Run `python3 tools/test_improvements.py` and regenerate source references after source changes. Portable tests do not establish EnCase compilation or execution.

## Python port branch

- Python changes belong on `codex/python-browser-cli`; preserve all thirteen EnScript files byte-for-byte against merged commit `bb476180453c76f7d38e5b6a9f1f025ad2273ce0` and preserve all archive refs/manifests/history.
- Read `docs/PYTHON_CLI.md` and `docs/PYTHON_TESTS.md`. Run `python3 -m unittest discover -s tests -v` for actual Python behavior; these results do not certify EnCase.
- Analyze acquired stable DB/WAL snapshots only. Keep real evidence and exports out of Git; synthetic test databases are created in temporary directories.
