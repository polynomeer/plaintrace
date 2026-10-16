# Recycle Bin $I Python CLI

**English** | [한국어](RECYCLE_BIN_CLI.ko.md)

The current package is 0.12.0 and every output uses schema 12. Earlier version introductions/test results below describe their release context; see [the RunMRU extension](RUN_MRU_CLI.md) for the current contract.

Implemented on 2026-10-15 on `codex/python-recycle-bin`, based on merged commit `e0d0145cfb7b649c1713d66776ea140a43f891a3`. All thirteen EnScript files and historical manifests remain byte-identical to the base. The original archive tag and 263 reconstructed 2017 commits are preserved. Package version `0.4.0` is an independent Python extension.

## Run and Install

Python 3.10+ with sqlite3 is declared; validation here uses macOS/Python 3.14. Recycle Bin parsing uses only the standard library. The optional EVTX extra is needed only when analyzing EVTX. Use stable acquired metadata files and repeat `--recycle-bin` for multiple files. The CLI accepts explicit files, including renamed acquisitions; it does not scan a directory or require a particular filename. Quote paths containing a dollar sign so the shell does not expand them.

```sh
python3 -m plaintrace --recycle-bin '/path/to/$IABC123.txt' --output recycle.json
python3 -m plaintrace --recycle-bin '/path/to/$IFIRST' --recycle-bin '/path/to/$ISECOND' --format sqlite --output recycle.sqlite
python3 -m plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --recycle-bin '/path/to/$IABC123.txt' --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --recycle-bin '/path/to/$IABC123.txt'
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --recycle-bin 'C:\acquired\$IABC123.txt' --output recycle.json
```

At least one of `--input`, `--lnk`, `--prefetch`, `--evtx`, `--recycle-bin` is required. Browser/LNK options affect only those input types. JSON defaults to stdout; SQLite requires `--output`. The existing exclusive-publication contract prevents overwriting outputs, source paths and reserved SQLite sidecars. Fatal input errors abort the entire command before publication. Warnings are included in diagnostics and stderr; `--strict` produces the report and returns 1 if warnings exist. See [shared CLI behavior](PYTHON_CLI.md) and [EVTX installation](EVTX_CLI.md).

## Supported Layouts and Bounds

The little-endian header holds an 8-byte format version at offset 0, an unsigned 8-byte original size at offset 8 and an 8-byte deletion FILETIME at offset 16. The parser dispatches by content version, not filename or guessed Windows release.

| Version | Path layout and contract |
| --- | --- |
| 1 | Offset 24: a complete 520-byte UTF-16LE field, corresponding to 260 code units; canonical total size 544 bytes |
| 2 | Offset 24: a 4-byte unsigned code-unit count; offset 28: count × 2 UTF-16LE bytes; count includes the terminating NUL |

Both layouts require a NUL on a two-byte boundary inside the supported path field. Version 2 count must be 1..32768 UTF-16 code units, including the terminator. Supplementary Unicode characters consume two units. Original file size is independent of path length and is never used to allocate data. Each input and direct parser call is capped at 128 KiB. The common reader performs bounded before/read/after hashes; offsets and declared lengths must fit the captured bytes.

Unsupported versions, incomplete headers/fields, excessive counts and unterminated paths are fatal. The rare 543-byte version-1 anomaly with shifted fields, truncated/recovery variants, INFO/INFO2, other recycle formats and directory scanning are unsupported. No shifted-field repair is attempted. Format recognition is not authenticity verification: arbitrary or deliberately edited bytes can resemble a supported header.

## Preserved Values and Diagnostics

The first aligned NUL ends the interpreted path. For version 1, nonzero bytes after that terminator within the fixed field produce a padding warning. For version 2, an early terminator produces a length-mismatch warning, and nonzero subsequent field bytes additionally produce a padding warning. The entire supported path field, including terminator and padding, is retained as `path_utf16_hex`. Bytes beyond the supported layout are retained as `trailing_data_hex` and diagnosed, including zero trailing bytes. Additional/status variants are not interpreted as restored/gone flags.

Valid UTF-16LE becomes `original_path`. Undecodable bytes are escaped with a warning and exact bytes remain in the hex field/source hash. Empty paths are retained with a warning. Stored drive, UNC, extended, relative, environment-variable and mixed-separator text remains literal; paths are not normalized, resolved, expanded or opened. No original-file execution or recovery occurs.

Deletion `deletion_filetime_raw` preserves unsigned 100 ns ticks since 1601-01-01 UTC as decimal text. `deleted_at` is UTC ISO text truncated to microseconds using integer arithmetic. The 100 ns remainder is not lost from the raw field. Zero is unspecified/null with a warning; overflow is null with a warning while raw ticks remain. No fixed local timezone adjustment or acquisition filesystem timestamp is substituted. `original_size` is unsigned decimal text in both JSON and SQLite, preserving the complete range through 18446744073709551615 without SQLite signed-integer overflow or JavaScript integer rounding.

## Scope and Original EnScript Differences

Each input yields one metadata record; `record_id` is the string 0, the header offset scoped by `source_id`. Repeated inputs remain separate sources, even with identical filenames/content. Source `sha256` hashes the acquired metadata bytes, not the original deleted file or companion payload. Acquisition paths and hashes remain in sources. Copy stability does not certify atomic acquisition, complete evidence or chain of custody. Reports remain in memory; the per-input limit is not an aggregate report-memory limit.

The parser does not read, locate, hash, extract or restore a `$R` companion. It does not infer whether a payload exists, was restored or was permanently deleted. SID/owner/account attribution is not present in the supported `$I` header and is not guessed from acquisition directory names. The original EnScript collected case-file metadata/MD5 and SID path context; this port covers only `$I` metadata. It explicitly distinguishes versions instead of assuming a path immediately after offset 24, and replaces fixed timezone display with UTC/raw ticks. No EnCase output parity is claimed. Metadata records alone do not establish user intent, payload identity or a complete deletion history.

## Current Schema and Architecture

Every JSON `format_version` and SQLite `user_version` is 10, even when no Recycle Bin input is supplied. Version 4 adds `recycle_bin` and its count while preserving existing browser, LNK, Prefetch and EVTX field meanings. Existing version-1/2/3 reports are not rewritten or migrated; consumers must recognize version 10 explicitly. SQLite inserts bind values and enforce source foreign keys. Sources use `source_kind` and `schema_family` recycle_bin, full input `sha256`, and null browser/database/WAL fields.

| Collection/table recycle_bin field | Meaning |
| --- | --- |
| source_id, record_id | Source ID and source-local header offset 0 |
| version | Stored format version 1 or 2; not an OS version assertion |
| original_size | Unsigned 64-bit original size in bytes, stored as decimal text |
| deleted_at, deletion_filetime_raw | UTC microsecond display and exact raw FILETIME text |
| original_path | Literal decoded path or escaped invalid text; empty remains empty |
| path_length_units | Declared UTF-16 unit count for version 2; null for version 1 |
| path_utf16_hex | Entire fixed/counted path field bytes, including terminator/padding |
| trailing_data_hex | Uninterpreted bytes after the supported layout; empty string when absent |

[recycle_bin.py](../plaintrace/recycle_bin.py) validates layouts and interprets metadata. [execution.py](../plaintrace/execution.py) combines input sources, [model.py](../plaintrace/model.py) defines version 10/counts, [exports.py](../plaintrace/exports.py) adds the table, and [cli.py](../plaintrace/cli.py) adds the repeatable flag. Existing LNK/Prefetch 8 MiB and EVTX 64 MiB limits remain unchanged.

## Tests, Review and Remaining Validation

[Tests and manual review](RECYCLE_BIN_TESTS.md) map 28 new cases, including both layouts, astral Unicode, literal paths, unsigned sizes, exact ticks, every truncated prefix, limits, warnings, source preservation, JSON/SQLite and actual subprocess CLI execution. With the optional EVTX extra, all 123 cases pass without skips: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin. Without it, 115 cases run and eight integrations explicitly skip, including one new five-source EVTX integration. All Recycle Bin-only tests still execute. Synthetic files are temporary; no acquired evidence is committed.

Actual acquired `$I` files from different Windows releases, Windows/Linux and Python 3.10 execution, independent forensic-tool comparisons, large collections, acquisition races and EnCase compilation/execution remain unvalidated. Existing browser/LNK/Prefetch/EVTX limitations and opaque structures remain documented. No real-file certification, corruption recovery, companion-content analysis, user attribution or forensic completeness is claimed.

## Format References

Structure interpretation uses the [libyal Recycle.Bin working specification](https://github.com/libyal/dtformats/blob/main/documentation/Windows%20Recycle.Bin%20file%20formats.asciidoc) and [rifiuti2 reference implementation](https://github.com/abelcheung/rifiuti2/blob/master/src/rifiuti-vista.c). These guide layout and anomaly handling; no dependency source is vendored and no independent runtime parity has been established. See the preserved [EnScript analysis](ANALYSIS.md).

## USB Registry Extension

The 0.5.0 release introduced schema 5 and usb_registry observations. Previous schema introductions above remain historical context; existing artifact field meanings are unchanged. See [USB registry contracts](USB_REGISTRY_CLI.md) and [tests/review](USB_REGISTRY_TESTS.md).

## RecentDocs Extension

Package 0.6.0 introduced schema 6 and recent_doc_keys/recent_docs. Earlier extension introductions above remain historical context; current consumers must support schema 12. See [RecentDocs contracts](RECENT_DOCS_CLI.md) and [tests/review](RECENT_DOCS_TESTS.md). Existing fields keep their meanings.
