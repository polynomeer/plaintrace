# Application MRU Tests and Code Review

**English** | [한국어](APPLICATION_MRU_TESTS.ko.md)

Validated and self-reviewed on 2026-10-15 on macOS/Python 3.14. All 200 tests pass without skips with the EVTX extra: 175 existing cases plus 25 application MRU cases. Without the extra, 192 execute and eight existing integrations skip. Application MRU itself has no extra dependency. See [the adapter contract](APPLICATION_MRU_CLI.md). This is not external reviewer approval or acquired-file certification.

## Reproduction and Fixtures

An independent REGF fixture builder creates all three families, sparse slots and raw strings in temporary directories. Expected paths and FILETIMEs are fixed independent oracles, not adapter-computed values. No real evidence or exports are committed. Existing read/output protections are reused, with actual CLI and both export formats exercised. Patched small budgets do not establish large-input performance.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 4b88c0a8d8699920ecdd5622400484bbef956c89 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| APP-01 | test_three_families_sparse_slots_and_raw_time | three families sparse slots and raw time |
| APP-02 | test_office_versions_apps_places_and_user_scopes | office versions apps places and user scopes |
| APP-03 | test_office_prefix_delimiter_and_opaque_flags | office prefix delimiter and opaque flags |
| APP-04 | test_invalid_and_duplicate_office_times_do_not_guess | invalid and duplicate office times do not guess |
| APP-05 | test_office_zero_and_overflow_filetime | office zero and overflow filetime |
| APP-06 | test_unrecognized_prefix_retains_raw_without_path | unrecognized prefix retains raw without path |
| APP-07 | test_plain_office_path_no_time_or_normalization | plain office path no time or normalization |
| APP-08 | test_hwp_frames_versions_binary_bom_and_regsz | hwp frames versions binary bom and regsz |
| APP-09 | test_hwp_big_endian_not_interpreted | hwp big endian not interpreted |
| APP-10 | test_adobe_products_versions_and_literal_paths | adobe products versions and literal paths |
| APP-11 | test_adobe_missing_path_unknown_slot_and_metadata | adobe missing path unknown slot and metadata |
| APP-12 | test_noncanonical_names_retained_as_metadata | noncanonical names retained as metadata |
| APP-13 | test_case_insensitive_canonical_names | case insensitive canonical names |
| APP-14 | test_wrong_type_and_invalid_unicode_keep_bytes | wrong type and invalid unicode keep bytes |
| APP-15 | test_embedded_nul_unterminated_and_empty_text | embedded nul unterminated and empty text |
| APP-16 | test_duplicates_key_time_and_offsets_are_scoped | duplicates key time and offsets are scoped |
| APP-17 | test_missing_families_and_existing_empty_key | missing families and existing empty key |
| APP-18 | test_regf_supported_indexes_and_dirty_header | regf supported indexes and dirty header |
| APP-19 | test_adapter_budgets_reject_without_partial_output | adapter budgets reject without partial output |
| APP-20 | test_cli_repeated_sources_hashes_and_schema | cli repeated sources hashes and schema |
| APP-21 | test_json_sqlite_roundtrip_and_parent_foreign_key | json sqlite roundtrip and parent foreign key |
| APP-22 | test_mixed_registry_sources_no_automatic_joins | mixed registry sources no automatic joins |
| APP-23 | test_cli_strict_fatal_output_and_evidence_collision | cli strict fatal output and evidence collision |
| APP-24 | test_nested_list_keys_are_diagnosed | nested list keys are diagnosed |
| APP-25 | test_deterministic_mutations_have_controlled_failures | deterministic mutations have controlled failures |

## Self-Review and Corrections

Reviewed reader bounds, source assembly, text/metadata separation, time semantics and output contracts against the original module. Enumerating siblings avoids missing-slot termination and cumulative Adobe child paths. Ambiguous Office T tokens and invalid UTF-16 retain raw bytes without guessed interpretation. Added explicit nested-key diagnostics instead of silently ignoring descendants. Slot numbers never become ranks and key times never become per-document open times. Composite foreign keys and schema 7 for previous-artifact-only reports are verified.

An independent python-registry 1.3.1 comparison reads synthetic Office/HWP/Adobe value names/types/bytes. Reinstalled-package smoke checks run the installed console outside the checkout and verify JSON/SQLite schema and unchanged input hashes. Eleven EnScript static regressions, source references, bilingual links/structures/test mapping and archive integrity checks also run. These checks do not remove the host-validation limits below.

## Remaining Validation

Actual application NTUSER hives, Windows/Linux, Python 3.10, independent parsers on real evidence, large-input performance and acquisition races remain unvalidated. Unsupported version-specific layouts, other products/apps and nested slots, legacy Adobe REG_BINARY paths, dirty-hive/log replay, REGF 1.6/big data/volatile/link/deleted/slack structures remain excluded. Stored references do not prove path existence, ownership or document opening; automatic correlation is absent. EnCase compilation/execution remains unverified, and original EnScript/archive content is preserved.
