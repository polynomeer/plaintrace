# Recycle Bin Tests and Code Review

**English** | [한국어](RECYCLE_BIN_TESTS.ko.md)

Validated and manually reviewed on 2026-10-15 on macOS/Python 3.14. All 123 actual Python cases pass without skips with python-evtx 0.8.1: 33 browser, 30 LNK/Prefetch, 32 EVTX and 28 Recycle Bin. This is a self-review and synthetic verification, not an external review or real acquired-file certification. See [the usage and schema contract](RECYCLE_BIN_CLI.md).

## Reproduction and Independent Fixtures

Fixtures encode known little-endian version/size/FILETIME fields and UTF-16 path bytes in temporary directories. Expected UTC includes a known 100 ns remainder; assertions do not derive expected values from the production parser. No acquired evidence or generated exports are committed. Tests run actual adapters, JSON/SQLite exports and CLI subprocesses. Only one new five-source integration needs EVTX; install the optional extra for full discovery. Without it, 115 cases execute and eight integrations explicitly skip, including seven existing EVTX tests. Recycle Bin parsing itself has no extra dependency.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code e0d0145cfb7b649c1713d66776ea140a43f891a3 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| RB-01 | test_version_one_fixed_layout_and_raw_fields | Version 1 fixed field, size, UTC/raw FILETIME and no warnings |
| RB-02 | test_version_two_counted_layout_and_utf16_units | Version 2 counts UTF-16 units, including astral characters and NUL |
| RB-03 | test_literal_unc_extended_relative_and_special_paths | UNC/extended/relative/environment/special paths remain literal |
| RB-04 | test_unsigned_sizes_and_zero_size_preserved | Zero and unsigned 64-bit maximum sizes preserved as decimal text |
| RB-05 | test_zero_and_overflow_deletion_times_are_diagnostic | Zero/overflow FILETIME null with warnings and exact raw ticks |
| RB-06 | test_empty_paths_are_retained_with_warning | Empty path preserved and diagnosed in both layouts |
| RB-07 | test_malformed_utf16_preserves_bytes_and_escapes | Invalid UTF-16 bytes escaped and exact raw field retained |
| RB-08 | test_version_one_nonzero_padding_retained_and_diagnosed | Version 1 nonzero post-NUL field bytes retained and warned |
| RB-09 | test_version_two_early_terminator_and_padding_warn | Version 2 early NUL and extra field padding diagnosed |
| RB-10 | test_trailing_bytes_are_opaque_and_diagnosed | Trailing bytes, including zero bytes, retained as opaque hex |
| RB-11 | test_unknown_versions_and_short_headers_rejected | Unknown versions and incomplete headers fail |
| RB-12 | test_invalid_lengths_counts_and_missing_terminators_rejected | Zero/excessive/out-of-bounds counts and unterminated fields fail |
| RB-13 | test_every_truncated_prefix_of_both_layouts_fails | Every truncated prefix of representative version 1/2 files fails |
| RB-14 | test_path_and_input_limits_cover_direct_parser_and_cli | 32768-unit boundary and 128 KiB input/direct-parser caps |
| RB-15 | test_renamed_and_repeated_sources_have_stable_hash_and_lineage | Renamed/repeated inputs keep distinct source IDs and unchanged hash/bytes |
| RB-16 | test_changed_input_fails_without_publication | Changed file prevents output publication |
| RB-17 | test_json_sqlite_schema_four_and_unsigned_size_roundtrip | JSON/SQLite version 5, unsigned size, Unicode and source FKs |
| RB-18 | test_cli_stdout_strict_and_real_subprocess | Strict warning stdout and actual subprocess success |
| RB-19 | test_cli_all_or_nothing_when_later_input_fails | Later bad input aborts all output and cleans temporary exports |
| RB-20 | test_existing_output_sidecar_and_evidence_collision_preserved | Existing output/sidecars and source collisions never overwrite bytes |
| RB-21 | test_no_payload_sid_owner_or_target_filesystem_inference | Observed file opens only touch the $I source; no owner/$R assertions |
| RB-22 | test_mixed_browser_link_prefetch_and_recycle_sources | Browser/LNK/Prefetch/Recycle Bin source ordering and schema 5 |
| RB-23 | test_mixed_five_source_cli_with_actual_evtx_decoder | Actual EVTX decoder plus all five input kinds in JSON/SQLite |
| RB-24 | test_mutated_inputs_only_raise_contract_errors | 200 seeded mutations raise only contract errors or retain metadata |
| RB-25 | test_review_utf16_terminator_is_aligned_not_byte_substring | NUL search is aligned to UTF-16 units rather than arbitrary bytes |
| RB-26 | test_review_version_one_543_byte_anomaly_is_not_guessed | 543-byte shifted version 1 anomaly rejected without guessing |
| RB-27 | test_review_directory_and_unknown_files_fail_without_report | Directory/missing/$R/INFO2 inputs fail without report |
| RB-28 | test_review_other_artifact_options_do_not_change_recycle_parsing | Browser label/LNK codepage do not affect $I parsing |

## Manual Code Review

| Priority | Risk reviewed | Handling / evidence |
| --- | --- | --- |
| High | Version 2 character count can be mistaken for Python character count or bytes | Count UTF-16 units including NUL; check cap/range before decoding; RB-02/12/14 |
| High | Byte-substring NUL matching can truncate valid UTF-16 | Scan only aligned two-byte units; RB-25 |
| High | Truncated or shifted metadata can produce fabricated size/time/path | Require complete supported fields, reject unknown versions/543-byte anomaly; RB-11/13/26 |
| Medium | Unsigned size exceeds SQLite signed integers/JavaScript exact integers | Decimal text in JSON and SQLite; RB-04/17 |
| Medium | Padding/early NUL/trailing bytes can hide unparsed material | Retain full raw field and trailing bytes, with explicit warnings; RB-08/09/10 |
| Medium | Source directory names or nearby $R files can be mistaken for proven ownership/content | Observe opens restricted to explicit $I source; no SID/payload inference; RB-21 |
| Medium | Adding a collection silently changes consumer expectations | Report/SQLite schema 4 and existing export regression updates; RB-17/22/23 |

Review covered parser, bounded read integration, argument scoping, output publication, schema migration and bilingual documentation. These are reviewed risks and implemented defenses; no external reviewer approval is claimed. The anomalous version-1 layout is deliberately unsupported rather than repaired heuristically.

## Validation and Remaining Limits

The installed 0.4.0 console command is smoke-tested outside the checkout with all five artifact kinds, JSON/SQLite schema 4 and unchanged input hashes. Eleven existing EnScript portable checks, four source references, bilingual documentation/test mappings, whitespace and source/archive comparisons pass separately. Archive verification preserves thirteen archived sources, original README, original tree and 263 synthetic 2017 commits; it does not compile EnScript and requires the original local backup ref.

Actual acquired $I files, Windows/Linux, Python 3.10, independent parser comparison, large collections and acquisition races remain untested. Supported layouts have synthetic coverage only. INFO/INFO2, the 543-byte version-1 anomaly, truncated/corrupt-field repair, directory scanning, $R extraction/recovery/status analysis and account attribution are unsupported. Metadata/CRC-free layout recognition is not authenticity or completeness certification. Existing browser/LNK/Prefetch/EVTX limitations, optional decoder requirements, per-input resource limits and unverified EnCase compilation/execution remain documented.

## USB Registry Regression Run (2026-10-15)

Current full discovery passes 148 cases: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin and 25 USB registry. Without the EVTX extra, 140 execute and eight skip. Current export assertions use schema 5; earlier counts/schema introductions are historical records. See [USB reproduction and review](USB_REGISTRY_TESTS.md).
