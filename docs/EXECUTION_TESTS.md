# Execution Artifact Tests and Code Review

**English** | [한국어](EXECUTION_TESTS.ko.md)

Validated and manually reviewed on 2026-10-14 on macOS/Python 3.14. All 63 actual Python cases pass: 33 browser regressions and 30 execution cases. This is not an external review or real acquired-file certification. EnScript and archive preservation are checked separately.

## Reproduction and Fixtures

Run unittest discovery from the repository root. Fixtures are generated in temporary directories from independently specified field values. The XPRESS fixture encoder emits complete fixed-code tables and known literals/matches; no production evidence or library source is committed. Expected FILETIME ticks retain a known 100 ns remainder and UTC value.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d1830099999cb1669f8f868506d5c323acdb8ca5 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Expected behavior |
| --- | --- | --- |
| EX-01 | test_lnk_unicode_strings_and_correct_time_order | UTF-16 strings and correct target creation/access/write order |
| EX-02 | test_lnk_ansi_codepage | Explicit cp949 and rejection of non-ANSI-compatible encoding |
| EX-03 | test_lnk_local_volume_no_duplicate_suffix | Volume fields and no duplicated target basename |
| EX-04 | test_lnk_unicode_link_info_preferred | Unicode paths override ANSI LinkInfo paths |
| EX-05 | test_lnk_network_path | UNC share and common suffix candidate |
| EX-06 | test_lnk_tracker_environment_and_opaque_items | Machine/GUIDs, literal environment target and opaque PIDL |
| EX-07 | test_lnk_unknown_extra_and_unresolved_are_diagnosed | Unknown block metadata and unresolved target diagnostics |
| EX-08 | test_lnk_invalid_sizes_offsets_and_missing_terminal | Invalid offsets, size loops and missing terminal rejection |
| EX-09 | test_every_lnk_truncated_prefix_fails | Every truncated prefix of a structured LNK fixture fails |
| EX-10 | test_lnk_invalid_utf16_and_filetime_preserved | Escaped invalid text and retained overflowing raw time |
| EX-11 | test_prefetch_versions_and_v30_variants | Version-specific counters, time slots, references and volumes |
| EX-12 | test_prefetch_version_and_size_rejection | Unknown version/layout and declared size mismatch |
| EX-13 | test_prefetch_section_bounds_and_unterminated_strings | Out-of-range sections/counts and missing string terminator |
| EX-14 | test_every_prefetch_truncated_prefix_fails | Every truncated prefix of a Prefetch fixture fails |
| EX-15 | test_mam_prefetch_portable_decompression | MAM04 fixture decoded and parsed with standard library |
| EX-16 | test_xpress_overlapping_match_and_extended_length | Overlap and byte/16-bit extended match lengths |
| EX-17 | test_xpress_multiple_blocks | More than 64 KiB decoded using multiple Huffman blocks |
| EX-18 | test_xpress_invalid_table_match_and_truncation | Invalid trees, backward references, overflow and truncation |
| EX-19 | test_mam_checksum_and_size_limits_fail | MAM84 and excessive/short advertised size rejection |
| EX-20 | test_mixed_browser_execution_json_sqlite_and_source_hashes | Mixed sources, current version 4, JSON/SQLite values and unchanged bytes |
| EX-21 | test_execution_cli_strict_and_fatal_atomicity | Strict warning output and no partial file on later failure |
| EX-22 | test_execution_file_size_limit_and_changing_input | Input read cap and changed-source detection |
| EX-23 | test_mutated_binary_inputs_never_escape_contract_errors | Deterministic byte mutations produce records or contract errors |
| EX-24 | test_review_xpress_direct_api_limits | Direct decompressor call output bounds and integer size type |
| EX-25 | test_review_unicode_volume_and_network | Unicode volume label and network share offsets |
| EX-26 | test_review_prefetch_volume_bounds_and_overflow_time | Volume path overlap and FILETIME overflow |
| EX-27 | test_review_terminal_trailing_bytes_and_source_collision | Trailing bytes diagnostic and source overwrite refusal |
| EX-28 | test_review_prefetch_overlapping_sections_are_rejected | Known Prefetch section overlap rejected |
| EX-29 | test_review_lnk_suffix_with_leading_separator | Leading separator does not duplicate an existing suffix |
| EX-30 | test_review_empty_target_candidates_are_unresolved | Empty textual candidates produce an unresolved diagnostic |

## Code Review Findings

| Priority | Finding | Resolution / evidence |
| --- | --- | --- |
| High | An input can grow beyond the read cap during hash passes | Bounded hashes plus capped reads and before/read/after hash checks; EX-22 |
| High | Direct decoder calls originally lacked output-size validation | Integer size and 8 MiB limit before decoding; EX-24 |
| High | Separate in-range Prefetch sections can still overlap | Reject overlap among accessed top-level sections and volume paths; EX-26/EX-28 |
| Medium | A leading separator on a common suffix can duplicate a full target path | Strip leading separator for candidate comparison while raw suffix is retained; EX-29 |
| Medium | Unicode volume/network variants and malformed timestamps need coverage | Unicode offset fixtures and overflow raw-value checks; EX-25/EX-26 |
| Medium | Browser-only consumers otherwise silently receive extended tables | Explicit report/SQLite version 2 and source-kind fields, with migration guidance; EX-20 |

## Verification and Remaining Limits

The existing eleven EnScript contract tests, four generated references, bilingual links/technical literals/test mappings, source comparison and archive-only verification pass separately. Packaging is built/installed and the console command smoke-tested outside the checkout. The archive checker needs its original local backup ref; synthetic runtime tests do not.

All supported SCCA layouts have synthetic coverage, not real OS/profile validation. MAM04 literal/match/multiblock tests do not prove universal compressor compatibility. MAM84/checksums, opaque PIDL/ExtraData and detailed Prefetch internals remain unsupported. Windows/Linux, Python 3.10 execution, real acquired fixtures, independent parser comparisons and performance still need testing. LNK candidates are never executed or resolved, and execution traces are not proof of every program run. EnCase compilation/execution remains unverified.

See [usage, fields and format references](EXECUTION_CLI.md) and [the browser regression plan](PYTHON_TESTS.md).

## EVTX Regression Run (2026-10-15)

The EVTX port validation ran 95 cases: 33 browser, 30 execution and 32 EVTX. Install the optional extra to run all integrations; without it seven EVTX cases explicitly skip. Existing export regressions now assert schema version 3. See [EVTX reproduction and review](EVTX_TESTS.md); earlier validation dates above remain historical records.

## Recycle Bin Regression Run (2026-10-15)

The current suite passes 123 cases with the optional EVTX extra: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin. Without it, 115 execute and eight explicitly skip. Existing export assertions now check schema 4. See [reproduction and review](RECYCLE_BIN_TESTS.md); earlier dates/counts remain historical validation records.
