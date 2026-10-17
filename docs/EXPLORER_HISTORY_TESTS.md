# Explorer History Tests and Code Review

**English** | [한국어](EXPLORER_HISTORY_TESTS.ko.md)

Validated and self-reviewed on 2026-10-17 on macOS/Python 3.14. All 407 Python tests pass without skips with the EVTX extra: 376 existing and 31 Explorer history cases. Without that extra, 399 execute and eight existing EVTX integrations skip; this is not full EVTX validation. These adapters themselves need no extra runtime dependency. See [contracts and limits](EXPLORER_HISTORY_CLI.md). This is self-review, not external approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

The existing independent synthetic REGF writer builds both roots and explicit REG_SZ/REG_BINARY UTF-16 payloads. Fixed numeric slots, MRUListEx ranks/gaps, Unicode/emoji, raw cell offsets and exact FILETIMEs provide oracles independent of the production decoder. Commands/queries contain literal whitespace, operators, tokens, URLs and suffixes. Temporary acquired-like hives and exports are deleted; no actual evidence is committed. Patched budgets and seeded mutations are controlled checks, not large-input performance tests or comprehensive fuzzing.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code e94cee173fffdcfdd9b960c29c0e9f81a1067236 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| EH-01 | test_typed_unicode_slots_not_mru_ranks | typed unicode slots not mru ranks |
| EH-02 | test_wordwheel_binary_unicode_and_order | wordwheel binary unicode and order |
| EH-03 | test_literals_duplicates_and_no_path_or_query_normalization | literals duplicates and no path or query normalization |
| EH-04 | test_wordwheel_missing_refs_keep_rank_gaps | wordwheel missing refs keep rank gaps |
| EH-05 | test_wordwheel_unlisted_entries_keep_null_rank | wordwheel unlisted entries keep null rank |
| EH-06 | test_missing_control_no_size_or_slot_rank_guess | missing control no size or slot rank guess |
| EH-07 | test_invalid_mrulistex_type_alignment_sentinel_duplicates | invalid mrulistex type alignment sentinel duplicates |
| EH-08 | test_legacy_and_ambiguous_controls_not_selected | legacy and ambiguous controls not selected |
| EH-09 | test_valid_empty_mru_differs_from_missing | valid empty mru differs from missing |
| EH-10 | test_typed_unexpected_controls_never_add_ranks | typed unexpected controls never add ranks |
| EH-11 | test_noncanonical_names_preserved_as_metadata | noncanonical names preserved as metadata |
| EH-12 | test_zero_and_maximum_slots_and_case_insensitive_names | zero and maximum slots and case insensitive names |
| EH-13 | test_artifact_specific_registry_types_no_coercion | artifact specific registry types no coercion |
| EH-14 | test_unterminated_and_odd_text_kept_raw | unterminated and odd text kept raw |
| EH-15 | test_invalid_utf16_is_byte_escaped | invalid utf16 is byte escaped |
| EH-16 | test_aligned_terminator_tails_padding_and_status_precedence | aligned terminator tails padding and status precedence |
| EH-17 | test_empty_strings_retained_with_diagnostic | empty strings retained with diagnostic |
| EH-18 | test_key_time_raw_offsets_and_entry_lineage | key time raw offsets and entry lineage |
| EH-19 | test_absent_empty_roots_and_descendants | absent empty roots and descendants |
| EH-20 | test_unknown_artifact_rejected | unknown artifact rejected |
| EH-21 | test_regf_versions_indexes_and_duplicate_names | regf versions indexes and duplicate names |
| EH-22 | test_dirty_and_corrupt_regf_rejected | dirty and corrupt regf rejected |
| EH-23 | test_entry_string_and_output_limits | entry string and output limits |
| EH-24 | test_json_sqlite_schema_raw_values_and_foreign_keys | json sqlite schema raw values and foreign keys |
| EH-25 | test_repeated_mixed_sources_hashes_and_input_preservation | repeated mixed sources hashes and input preservation |
| EH-26 | test_cli_flags_source_groups_json_and_sqlite | cli flags source groups json and sqlite |
| EH-27 | test_strict_warning_and_later_failure_atomic_publication | strict warning and later failure atomic publication |
| EH-28 | test_input_existing_output_and_sidecar_protection | input existing output and sidecar protection |
| EH-29 | test_missing_input_and_sqlite_destination | missing input and sqlite destination |
| EH-30 | test_no_stored_target_open_and_changed_input_rejected | no stored target open and changed input rejected |
| EH-31 | test_seeded_payload_mutations_keep_raw_values | seeded payload mutations keep raw values |

## Self-Review

Reviewed artifact-specific registry types/scopes, canonical slots, TypedPaths labels versus WordWheelQuery MRU ranks, strict sentinel/duplicate handling, absent references and unlisted values. TypedPaths never derives rank from a slot or unexpected control. WordWheelQuery order remains separate from text validity. Labels are bounded unsigned decimal values without leading zeros; unknown names stay raw metadata. Enumeration/duplicate observations remain unchanged rather than sorted or deduplicated.

Reviewed aligned UTF-16 boundaries, invalid text/tail status precedence, literal preservation, exact key times versus absent per-entry times, byte/entry/output limits, raw nk/vk lineage, mixed/repeated source groups, schema 13, foreign keys and exclusive all-or-nothing exports. Existing decoders are unchanged. No remaining blocking findings in self-review; real-host and acquired-data validation remain open.

## Independent Comparison and Results

Compared both synthetic scopes with python-registry 1.3.1 for key/value names, types, full raw bytes and physical nk/vk offsets, accounting for four-byte cell-header versus payload differences. Explicit UTF-16 and DWORD-array checks independently verify literal text, slot labels and MRU order. Installed 0.13.0 console checks outside checkout exercise both flags, repeated sources, schema 13 JSON/SQLite, source hashes, foreign keys and unchanged input. These checks do not certify Windows navigation/search semantics or real acquired NTUSER data.

All 407 tests pass with EVTX. Eleven EnScript static regressions, four source-reference documents, paired document/link/test mappings and archive validation pass. Thirteen EnScript files and original manifests match the base; original archive tree/README and 263 reconstructed 2017 commits remain preserved. These static checks do not establish EnCase compilation/execution.

## Remaining Validation and Unsupported Structures

Actual acquired NTUSER TypedPaths/WordWheelQuery across Windows versions, Windows/Linux execution, Python 3.10, independent real-record semantics, large-input performance and acquisition races remain unvalidated. Other scopes/typed histories, unsupported registry/control types, noncanonical names, ambiguous/malformed ordering and native REGF restrictions are documented. No dirty-hive replay, deleted/slack recovery, target access/execution, user/session attribution, per-entry key times, navigation/search-success inference or cross-artifact joins. EnCase compilation/execution remains unverified. Exact limits and status precedence are in the CLI document.
