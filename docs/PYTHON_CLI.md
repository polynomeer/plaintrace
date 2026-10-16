# Python Browser CLI

**English** | [한국어](PYTHON_CLI.ko.md)

The current package is 0.12.0 and every output uses schema 12. Earlier version introductions/test results below describe their release context; see [the RunMRU extension](RUN_MRU_CLI.md) for the current contract.

Implemented on 2026-10-14 on branch `codex/python-browser-cli`, based on merged commit `bb476180453c76f7d38e5b6a9f1f025ad2273ce0`. All thirteen EnScript files remain byte-identical to that commit. The original archive tag `archive/pre-improvements-2026-10-13`, manifests and 263 synthetic 2017 commits are preserved. This Python implementation runs independently; it does not interpret EnScript or validate the EnCase host.

## Scope and Requirements

Python 3.10 or later with the standard sqlite3 module is required. Browser parsing has no third-party runtime dependencies and can run directly from the checkout. EVTX requires a separate optional extra; see [EVTX installation](EVTX_CLI.md). Optional package installation uses setuptools as a build dependency and may download it. The test environment was macOS with Python 3.14; Windows/Linux execution and the minimum supported Python version were not exercised in this workspace.

Supported inputs are acquired Chromium-style History databases (Chrome/Opera labels can be selected explicitly) and Firefox places.sqlite. Detection uses tables, not filenames. Auto mode reports the Chromium family rather than guessing Chrome versus Opera. IE index.dat/WebCache, encrypted databases, session files, evidence-image extraction and a GUI are outside the browser adapter. It does not scan live profiles automatically.

## Run and Install

From the repository root, replace the placeholder paths with acquired database files. JSON defaults to stdout; SQLite requires an output path. Repeat the input flag to combine sources. A single explicit browser label applies to every input, so use auto mode for mixed families.

```sh
python3 -m plaintrace --input /path/to/History --browser chrome --output report.json
python3 -m plaintrace --input /path/to/places.sqlite --browser firefox --format sqlite --output report.sqlite
python3 -m plaintrace --input /path/to/History --input /path/to/places.sqlite --strict
```

Optional installation in a virtual environment creates the plaintrace console command. The first example is for macOS/Linux; the second is for Windows PowerShell.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --version
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --version
```

## Input Preservation and WAL

Acquire a stable DB and its matching WAL together before analysis. The CLI copies the DB and any adjacent WAL to a temporary directory, hashes the original files before/after copying and compares the copies. SQLite opens only the temporary copy in read-only/query-only mode and performs quick_check. Original SHM is untouched; SQLite can create temporary SHM while reading the copied WAL. Nonempty rollback journals, detected changes, corruption and unsupported required schemas produce a fatal error.

Hash stability during copying is not atomic acquisition of a live browser, does not prove the WAL belongs to the DB, and cannot detect every concurrent-change/ABA scenario. A missing WAL cannot be inferred from the DB alone. Do not treat a copied live file as a verified complete acquisition. Source hashes identify the acquired bytes; they do not establish a complete chain of custody.

## Parsing Contracts

| Family / artifact | Interpretation |
| --- | --- |
| Chromium visits | Join visits.url to urls.id and use visit_time; raw transition retained if available |
| Firefox visits | Join moz_historyvisits.place_id to moz_places.id and use visit_date; raw visit_type retained as transition |
| URL summaries | If the event table is absent, use last_visit_time/last_visit_date and mark url_summary with a diagnostic; never invent individual visits |
| Query keywords | Extract all nonempty q/query/search_query parameter values, preserving repeated parameters; split delimiters before UTF-8 decoding; ignore fragments |
| Stored Chromium terms | Read keyword_search_terms separately, marked stored_search_term; URL last-visit time is a summary proxy, not an independently recorded search time |
| Chromium downloads | Require id, start_time and current_path or target_path; prefer nonempty target_path; retain ordered downloads_url_chains and final URL separately from referrer |
| Firefox downloads | Join moz_annos by place_id and annotation names downloads/destinationFileURI and downloads/metaData; never assume attribute IDs or alternating row order |

Firefox downloads are annotation_summary records: one current annotation set per place, not a reconstruction of every historical download. Duplicate annotations select the newest modification/creation time and ID and emit a warning. The start time prefers the latest visit_type 7 event; otherwise annotation dateAdded is an explicitly labeled proxy. Metadata is parsed as JSON, retained verbatim and may contain millisecond endTime or an ISO timestamp with timezone. Destination file URIs are decoded to display paths; raw URIs and browser URLs remain available. Chromium filesystem paths are not URL-decoded.

Query parameters are candidate search terms; arbitrary websites can use these names for other purposes. Query-derived terms and stored terms are separate records and are not deduplicated. Malformed percent escapes are preserved with warnings; invalid UTF-8 recognized query fields are skipped individually with diagnostics, preserving valid neighboring terms and the original visit. Empty query values produce no keyword records. Missing optional tables/columns yield null values or explicit unavailable diagnostics; malformed required tables fail the input. Orphan visit/annotation records are retained and diagnosed.

## Time and Numeric Values

Chromium timestamps use integer microseconds since 1601-01-01 UTC. Firefox visit/annotation times use microseconds since 1970-01-01 UTC; numeric metadata endTime uses milliseconds. ISO end times require an explicit timezone and normalize to UTC. Conversion uses integer arithmetic, retains microseconds and applies no fixed local offset. Raw values and units remain in output. Zero and missing times are null; negative, noninteger or out-of-range times are diagnosed and left null. Numeric size/state fields accept signed 64-bit integers (including browser sentinel values); invalid values become null with diagnostics. Original Firefox metadata remains available.

These choices deliberately differ from the EnScript fixed timezone adjustment, URL-wide decoding and positional/row-order assumptions. They are explicit Python contracts, not claims of byte-for-byte output equivalence with EnCase.

## Output Contract

JSON format_version is 6 and includes tool/tool_version, the five browser collections below plus links, prefetch, events, recycle_bin, usb_registry, recent_doc_keys, recent_docs and counts. SQLite user_version is 6 and contains the five matching browser tables, links, prefetch, events, recycle_bin and usb_registry, recent_doc_keys and recent_docs, plus metadata, whose values are JSON text. Source IDs identify each supplied input; record IDs and source tables preserve row lineage. Transition values are raw and have family-specific meanings.

| Collection / table | Fields |
| --- | --- |
| sources | source_id, path, browser, schema_family, database_sha256, wal_sha256, source_kind, sha256 |
| visits | source_id, browser, record_id, source_table, record_kind, url, title, visited_at, timestamp_raw, timestamp_unit, transition |
| keywords | source_id, browser, record_id, source_table, derivation, visit_record_id, parameter, keyword, url, searched_at, time_basis |
| downloads | source_id, browser, record_id, source_table, record_kind, path, destination_uri, url, url_chain, referrer, state, started_at, ended_at, start_time_raw, end_time_raw, start_time_unit, end_time_unit, start_time_basis, received_bytes, total_bytes, metadata_raw, annotation_ids, start_visit_id |
| diagnostics | source_id, severity, code, message, record_id |

SQLite inserts bind parameters, retain Unicode/quotes/newlines and enforce source foreign keys. The download URL chain is a JSON array in JSON and JSON text in SQLite. Times are UTC ISO strings; unknown fields are null. Stored-term time_basis and download start_time_basis must be checked before interpreting proxy times. The schema is separate from the EnScript Web_* schema; no consumer compatibility is implied.

Output files are built in the destination directory and published with a hard link that refuses an existing file, including a file appearing during analysis. The filesystem must support hard links and the parent must exist/be writable. There is no overwrite flag. Reserved input sidecar paths cannot be used as outputs. A fatal input error aborts the whole command before output publication; partial reports are not published. Stdout redirection is controlled by the shell and does not receive the file-publication guarantees. Results currently reside in memory; very large profiles may require substantial RAM.

## Exit Codes and Diagnostics

| Exit | Meaning |
| --- | --- |
| 0 | Report produced; warnings may be present |
| 1 | Strict mode produced a report with warnings |
| 2 | Invalid arguments, failed input/output, changed/corrupt DB or unsupported required schema |

Warnings are emitted to stderr and included in diagnostics. Inspect them before interpreting an empty collection. Strict mode does not suppress the report. No browser version compatibility guarantee, deleted-record carving, uncommitted transaction recovery or encrypted-DB support is claimed.

## Code Structure

| File | Responsibility |
| --- | --- |
| [evidence.py](../plaintrace/evidence.py) | Isolated DB/WAL snapshot, hash checks, read-only SQLite and integrity checks |
| [browser.py](../plaintrace/browser.py) | Schema detection, visit/keyword/download adapters and annotation correlation |
| [model.py](../plaintrace/model.py) | Report version, exact UTC time conversion, query term extraction and diagnostics |
| [exports.py](../plaintrace/exports.py) | JSON/SQLite serialization, parameterized inserts and exclusive output publication |
| [cli.py](../plaintrace/cli.py) | Arguments, exit codes, stdout/stderr separation |
| [pyproject.toml](../pyproject.toml) | Optional installable console entry point |
| [test_browser_cli.py](../tests/test_browser_cli.py) | Synthetic SQLite fixtures and real Python execution tests |

## Tests and Remaining Validation

The [Python test plan](PYTHON_TESTS.md) records 33 executable synthetic-fixture tests, including committed WAL rows and unchanged original DB/WAL/SHM, real CLI subprocess execution, output transactions and no-overwrite races. The installed console entry point is also smoke-tested in an isolated temporary environment. These are actual Python tests, separate from static EnScript checks.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
```

Real acquired profiles across browser versions, Windows/Linux, large profiles, competing live writers, power-loss durability and unsupported schema variants still need validation. EnCase compilation/execution remains unverified; Python test results do not close that limitation.

## Schema Sources

Implementation references include the [Chromium history SQL fixture](https://chromium.googlesource.com/chromium/src/+/77a7f22877f83aca6844991cfb17db3edd6f0947/components/test/data/history/history.30.sql) and [Mozilla download history implementation](https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/downloads/DownloadHistory.sys.mjs). They help establish table/annotation meanings, not universal version support. The original [EnScript analysis](ANALYSIS.md) remains separately documented.

## Follow-up Review Contract

[The review report](PYTHON_REVIEW.md) records nine additional regression cases. Output paths reject final-component symlinks, including dangling ones; SQLite output refuses existing WAL/SHM/journal sidecars both before writing and before publication. This does not atomically reserve all sidecar names against competing writers. JSON serialization fails before stdout emission for unsupported/nonfinite values, although stream transport failures can still leave partial stdout. Native schema names must refer to tables rather than views.

Downloads now include selected Firefox annotation IDs and the start event ID; Chromium has an empty annotation map and null start event ID. The annotation map is JSON text in SQLite. End-before-start values are retained with diagnostics, not corrected. These are additive fields in the first unmerged format-version-1 implementation. ISO normalization overflow and stored-term orphan URLs are also diagnosed.

## Execution Artifact Extension

The 0.2.0 extension supports LNK and Prefetch alongside browser inputs; see [execution artifact usage](EXECUTION_CLI.md) and [tests and review](EXECUTION_TESTS.md). Format version 2 adds links/prefetch collections and tables plus source_kind/sha256 source fields. Version 1 reports are not rewritten or migrated. Consumers must inspect the version before reading the new schema. Database hashes and existing browser fields retain their meanings.

## EVTX Extension and Version 3

The 0.3.0 extension introduced acquired Windows EVTX via an optional decoder, events and explicit report/SQLite version 3. Existing browser fields keep their meanings and old reports are never migrated. See [EVTX contracts and installation](EVTX_CLI.md) and [tests and review](EVTX_TESTS.md). Browser-only reports also received version 3 at introduction; current reports use version 12.

## Recycle Bin Extension and Version 4

The 0.4.0 release adds explicit acquired $I metadata inputs, recycle_bin and schema version 4 for every report. Browser fields keep their existing meanings. See [usage, fields and limits](RECYCLE_BIN_CLI.md) and [tests/review](RECYCLE_BIN_TESTS.md). The earlier version-3 extension above describes its original introduction; current output is version 4.

## USB Registry Extension

The 0.5.0 release introduced schema 5 and usb_registry observations. Previous schema introductions above remain historical context; existing artifact field meanings are unchanged. See [USB registry contracts](USB_REGISTRY_CLI.md) and [tests/review](USB_REGISTRY_TESTS.md).

## RecentDocs Extension

Package 0.6.0 introduced schema 6 and recent_doc_keys/recent_docs. Earlier extension introductions above remain historical context; current consumers must support schema 12. See [RecentDocs contracts](RECENT_DOCS_CLI.md) and [tests/review](RECENT_DOCS_TESTS.md). Existing fields keep their meanings.
