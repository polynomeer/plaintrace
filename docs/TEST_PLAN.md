# Verification and Test Plan

**English** | [한국어](TEST_PLAN.ko.md)

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Status and Strategy

Archive integrity and document link checks are available on macOS. EnCase compilation, parser correctness, end-to-end UI behavior and performance have not been validated. The cases below are a proposed execution plan, not passed historical test records. Use synthetic or authorized test evidence with independently known expected values.

## Levels and Oracles

| Level | Method | Oracle |
| --- | --- | --- |
| Archive | Source hashes, final reconstructed tree, commit metadata | Original manifest and local backup ref |
| Static | Decoded class/method and SQL inspection | Source lines and documented variants |
| Host integration | Compile/load complete entry and includes in recorded EnCase version | Host diagnostics and UI availability |
| Artifact parsing | Controlled fixture per format | Independently decoded original record values |
| Export | Parse output, compare cells and rows | Unfiltered source results plus original records |
| End to end | Build DB and correlate families | Selected fixture inventory and expected events |
| Presentation | Restore missing HTML/JS first | Agreed schema, timestamp and range contract |

## Test Matrix

| ID | Requirement | Fixture / action | Expected observation to assess |
| --- | --- | --- | --- |
| T-01 | FR-01 | Empty case, non-Windows volume, two Windows volumes | Defined rejection/no-match behavior and first-volume entry scope |
| T-02 | FR-02 | SAM with known RID, F/V times and account flags | Correct identity, counts, state and strings; missing values distinguished |
| T-03 | FR-03 | Common/hidden/deleted files and known $I records | Correct classification, size, original path and deletion time |
| T-04 | FR-04 | Known Prefetch/LNK layouts and malformed/truncated variants | Expected parsed fields; unsupported formats do not silently yield trusted data |
| T-05 | FR-04 | Office/HWP/Adobe recent entries with matching/nonmatching LNK | Correlation and exclusions agree with source rules |
| T-06 | FR-05 | Events 4624/4634/4647/12/13 and unrelated IDs | Relevant events only; correct user, logon ID and time |
| T-07 | FR-05 | USB registry records and connect/disconnect event fixtures | Device fields and event transitions correspond to original records |
| T-08 | FR-06 | Browser databases with known visits, queries and downloads | Per-browser epoch, URL decoding, keyword and size fields match |
| T-09 | FR-07 | Apostrophes, commas, quotes, newlines and Korean text in fields | CSV/SQL parsing preserves values; current implementation may fail |
| T-10 | FR-07 | Search → filter → clear filter; logon/power rows | Row count and every copied field preserved; detects known argument issues |
| T-11 | FR-08 / NFR-02 | Known multi-family selected case | Total DB schemas, row counts, timestamp values and source coverage match fixture |
| T-12 | FR-08 / NFR-03 | Run twice, pre-existing tables, locked/unwritable output | No unreported overwrite/duplicate/partial result; document current failures |
| T-13 | NFR-03 | Empty selection, multiple devices, long collection, early close | Scope, progress, cleanup and busy-state behavior recorded |
| T-14 | FR-09 | Missing HTML/browser, then restored agreed assets | Missing dependency is diagnosed; actual visualization remains blocked until restored |
| T-15 | NFR-01 | Run archive verifier in original workspace | Hashes, all 263 commit records and baseline tree match |
| T-16 | NFR-04 | Load entry script and all includes in the recorded Windows/EnCase environment | Host compiles/loads and opens expected controls; exact versions recorded |

## Execution Record Template

For each case record: test ID, source commit, Windows/EnCase versions, fixture hash, independent expected values, selected scope, output hashes and table counts, actual values, diagnostics, and result (pass/fail/blocked/not run). Add failure reproduction steps. Do not mark an item passed solely because the progress indicator finished.

## Exit Criteria for a Future Release

Host compilation and every supported artifact fixture must pass; export round trips must preserve values; timestamps must have documented interpretation; scope and repeated-run behavior must be explicit; known failures need fixes or clearly stated exclusions. HTML-dependent cases stay blocked until assets and contracts are restored. Performance runs should record evidence size, item counts, duration, output sizes and resource use; no historical target exists to claim compliance against.

See [requirements](REQUIREMENTS.md), [analysis](ANALYSIS.md), and [operations](USER_GUIDE.md).

## Additional Regression Cases

| ID | Requirement | Fixture / action | Expected observation to assess |
| --- | --- | --- | --- |
| T-17 | FR-02 / FR-07 | System selection chart, Prefetch/web SQLite charts; empty and small inputs | Compare system chart with selected items and other charts with independent database aggregates |
| T-18 | FR-03 / FR-04 / FR-07 | Extract checked rows with duplicate names across volumes; paired $I/$R fixtures | Row keys identify intended evidence; exported bytes match original content; metadata parsing is distinguished from content recovery |

For T-02, compare computer-name queries and record the unfinished shutdown-time result. For T-08, check whether keyword processing receives an exhausted reader. For T-09, validate USB event header names, field order and quoting. For T-10, check whether the power keyword filter actually filters rows. For T-11, inspect absent Web_Visit/Web_Host creation and malformed IE inserts before interpreting browser coverage. Also exercise the Recent view's unhandled SQLite menu item in T-09.
