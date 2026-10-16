# RunMRU Tests and Code Review

**English** | [한국어](RUN_MRU_TESTS.ko.md)

Validated and self-reviewed on 2026-10-16 on macOS/Python 3.14. All 376 Python tests pass without skips with the EVTX extra: 346 existing and 30 RunMRU cases. Without that extra, 368 execute and eight existing EVTX integrations skip; this is not full EVTX validation. RunMRU itself needs no extra runtime dependency. See [contracts and limits](RUN_MRU_CLI.md). This is self-review, not external approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

The existing independent REGF fixture writer creates exact MRUList REG_SZ controls and letter entry values. UTF-16 bytes, fixed ranks/gaps, raw offsets and exact FILETIMEs provide independent oracles. Cases include Unicode/emoji, literal suffixes versus control characters, quotes/whitespace, malformed controls, unsupported data and atomic CLI failures. All generated hives/exports use temporary directories; no acquired evidence is committed. Patched budgets and seeded payload mutations do not constitute large-input performance testing or comprehensive fuzzing.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 53f0d510b2d06f991394cf5858be22f54416a1f4 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| RUN-01 | test_unicode_literal_commands_and_order | unicode literal commands and order |
| RUN-02 | test_no_suffix_whitespace_argument_or_environment_normalization | no suffix whitespace argument or environment normalization |
| RUN-03 | test_duplicates_retained_across_slots | duplicates retained across slots |
| RUN-04 | test_missing_references_keep_rank_gaps | missing references keep rank gaps |
| RUN-05 | test_unlisted_entry_has_null_rank | unlisted entry has null rank |
| RUN-06 | test_missing_control_does_not_guess_alphabetical_rank | missing control does not guess alphabetical rank |
| RUN-07 | test_invalid_controls_never_assign_rank | invalid controls never assign rank |
| RUN-08 | test_mrulistex_and_ambiguous_controls_not_selected | mrulistex and ambiguous controls not selected |
| RUN-09 | test_valid_empty_order_distinct_from_missing | valid empty order distinct from missing |
| RUN-10 | test_ascii_single_letter_names_and_unknown_metadata | ascii single letter names and unknown metadata |
| RUN-11 | test_case_insensitive_control_path_and_slots | case insensitive control path and slots |
| RUN-12 | test_wrong_value_types_kept_raw_without_string_decoding | wrong value types kept raw without string decoding |
| RUN-13 | test_unterminated_and_odd_strings_retained | unterminated and odd strings retained |
| RUN-14 | test_invalid_utf16_escaped_and_bytes_preserved | invalid utf16 escaped and bytes preserved |
| RUN-15 | test_first_aligned_terminator_and_trailing_bytes | first aligned terminator and trailing bytes |
| RUN-16 | test_empty_command_kept_with_warning | empty command kept with warning |
| RUN-17 | test_key_time_and_physical_offsets_not_per_command_times | key time and physical offsets not per command times |
| RUN-18 | test_absent_empty_and_nested_scopes | absent empty and nested scopes |
| RUN-19 | test_all_regf_versions_and_index_kinds | all regf versions and index kinds |
| RUN-20 | test_dirty_corrupt_and_duplicate_aliases_rejected | dirty corrupt and duplicate aliases rejected |
| RUN-21 | test_entry_string_and_output_limits | entry string and output limits |
| RUN-22 | test_json_sqlite_schema_raw_data_and_foreign_keys | json sqlite schema raw data and foreign keys |
| RUN-23 | test_repeated_sources_hashes_and_input_unchanged | repeated sources hashes and input unchanged |
| RUN-24 | test_cli_subprocess_json_strict_and_sqlite | cli subprocess json strict and sqlite |
| RUN-25 | test_mixed_adapters_preserve_source_groups | mixed adapters preserve source groups |
| RUN-26 | test_later_failure_publishes_no_partial_report | later failure publishes no partial report |
| RUN-27 | test_input_existing_output_and_sidecar_protection | input existing output and sidecar protection |
| RUN-28 | test_missing_input_and_sqlite_destination | missing input and sqlite destination |
| RUN-29 | test_no_target_open_and_changed_input_rejected | no target open and changed input rejected |
| RUN-30 | test_seeded_string_mutations_preserve_full_raw_values | seeded string mutations preserve full raw values |

## Self-Review and Corrections

Reviewed single-key scope, ASCII slots, strict control validation, missing/invalid/ambiguous ordering, rank gaps/unlisted observations, Unicode framing and raw lineage. Kept literal suffixes and whitespace unchanged rather than adopting suffix-stripping heuristics. String boundaries use aligned NULs, never arbitrary byte searches; wrong registry types are not coerced. Invalid Unicode display uses byte backslash escapes; corrected the test oracle to expect those exact escapes rather than a decoded surrogate notation. Raw bytes remain authoritative.

Reviewed source ordering, repeated/mixed inputs, schema bump for all adapters, JSON/SQLite values and foreign keys, exact key times versus absent per-command times, budgets and input/output failure handling. Shared decoders remain unchanged. There were no remaining blocking findings in this self-review; real-host validation remains open.

## Independent Comparison and Validation Results

Synthetic key/value names, types, full raw bytes and physical nk/vk offsets were compared with python-registry 1.3.1, accounting for the four-byte cell-header versus payload offset difference. Explicit UTF-16/control checks independently verify the stored command suffixes and MRU order. Installed 0.12.0 console checks run outside the checkout for JSON/SQLite schema 12, repeated-source hashes, foreign keys and unchanged input. These checks do not independently certify Windows Run dialog behavior or real acquired NTUSER data.

All 376 Python tests pass with EVTX. Eleven EnScript static regressions, four generated source-reference documents, bilingual document/link/test mappings and archive validation pass. Thirteen EnScript files and original manifests match the base; archive tree/README and 263 reconstructed 2017 commits remain preserved. Static integrity tests do not establish EnCase compilation/execution.

## Remaining Validation and Unsupported Structures

Actual acquired NTUSER RunMRU across Windows versions, Windows/Linux execution, Python 3.10, independent real-record interpretation, large-input performance and acquisition races remain unvalidated. Other scopes, unsupported value/control formats, noncanonical slots, malformed/ambiguous ordering and existing REGF restrictions remain explicit. No dirty-hive replay, deleted/slack recovery, target execution/expansion, ownership/session or success inference, per-entry key-time assignment or cross-artifact joins. Key last-write and MRU rank are not command execution times. EnCase compilation/execution remains unverified. Exact status precedence and limits are in the CLI document.
