# SAM Account Tests and Code Review

**English** | [한국어](SAM_ACCOUNTS_TESTS.ko.md)

Validated and self-reviewed on 2026-10-26 on macOS/Python 3.14. All 475 Python tests pass without skips with the EVTX extra: 440 existing and 35 SAM metadata cases. Without that extra, 467 execute and eight existing EVTX integrations skip; this is not full EVTX validation. SAM metadata uses only the standard library. See [contracts and limits](SAM_ACCOUNTS_CLI.md). This is self-review, not external approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

An independent synthetic REGF writer builds canonical RID and Names keys. A fixed 80-byte F writer uses explicit known offsets, raw flags/counters and fixed 100 ns/UTC oracles. A separate 204-byte V header writer directly frames nine UTF-16 descriptor fields, Unicode/emoji and literal paths. No credential records, boot keys, cryptographic fixture or actual acquired evidence is included. Temporary hives/exports are deleted. Patched budgets and seeded mutations are controlled checks, not comprehensive fuzzing or large-input performance certification.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code def0c228b0ef2721470d63e3adbf14719311428c -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| SAM-01 | test_account_unicode_name_mapping_and_rid | account unicode name mapping and rid |
| SAM-02 | test_fixed_offsets_unsigned_counts_country_and_flags | fixed offsets unsigned counts country and flags |
| SAM-03 | test_exact_filetimes_three_fields_and_separate_key_time | exact filetimes three fields and separate key time |
| SAM-04 | test_zero_and_sentinel_times_not_calendar_dates | zero and sentinel times not calendar dates |
| SAM-05 | test_out_of_range_time_warns_without_losing_raw_ticks | out of range time warns without losing raw ticks |
| SAM-06 | test_unknown_flags_and_maximum_counters_preserved | unknown flags and maximum counters preserved |
| SAM-07 | test_f_rid_mismatch_retained_and_not_overwritten | f rid mismatch retained and not overwritten |
| SAM-08 | test_f_wrong_type_size_missing_do_not_guess_layout | f wrong type size missing do not guess layout |
| SAM-09 | test_missing_v_still_retains_f_metadata | missing v still retains f metadata |
| SAM-10 | test_v_wrong_type_and_short_header_retained_as_summary | v wrong type and short header retained as summary |
| SAM-11 | test_v_relative_offsets_descriptor_bytes_and_literals | v relative offsets descriptor bytes and literals |
| SAM-12 | test_v_empty_length_is_not_missing | v empty length is not missing |
| SAM-13 | test_v_invalid_bounds_keep_descriptors_without_repair | v invalid bounds keep descriptors without repair |
| SAM-14 | test_v_odd_offset_or_length_not_shifted | v odd offset or length not shifted |
| SAM-15 | test_v_invalid_unicode_and_embedded_nul_preserved | v invalid unicode and embedded nul preserved |
| SAM-16 | test_v_overlapping_ranges_diagnosed_without_silent_repair | v overlapping ranges diagnosed without silent repair |
| SAM-17 | test_unselected_v_payload_and_other_values_not_exported | unselected v payload and other values not exported |
| SAM-18 | test_names_default_type_is_rid_not_data_integer | names default type is rid not data integer |
| SAM-19 | test_orphan_invalid_and_duplicate_name_mappings_retained | orphan invalid and duplicate name mappings retained |
| SAM-20 | test_missing_names_unmapped_rid_no_invented_username | missing names unmapped rid no invented username |
| SAM-21 | test_missing_empty_users_and_noncanonical_children | missing empty users and noncanonical children |
| SAM-22 | test_descendants_and_container_values_not_traversed | descendants and container values not traversed |
| SAM-23 | test_physical_cell_offsets_and_key_filetimes | physical cell offsets and key filetimes |
| SAM-24 | test_case_insensitive_paths_and_record_names | case insensitive paths and record names |
| SAM-25 | test_regf_versions_indexes_and_duplicate_values | regf versions indexes and duplicate values |
| SAM-26 | test_dirty_and_corrupt_hive_rejected | dirty and corrupt hive rejected |
| SAM-27 | test_account_mapping_value_string_and_output_budgets | account mapping value string and output budgets |
| SAM-28 | test_json_sqlite_schema_raw_strings_and_foreign_keys | json sqlite schema raw strings and foreign keys |
| SAM-29 | test_repeated_sources_hashes_and_unchanged_input | repeated sources hashes and unchanged input |
| SAM-30 | test_cli_json_strict_and_sqlite | cli json strict and sqlite |
| SAM-31 | test_mixed_sources_do_not_attribute_machine_or_sid | mixed sources do not attribute machine or sid |
| SAM-32 | test_later_failure_no_partial_report | later failure no partial report |
| SAM-33 | test_input_existing_output_and_sidecar_protected | input existing output and sidecar protected |
| SAM-34 | test_missing_input_sqlite_destination_and_only_hive_reads | missing input sqlite destination and only hive reads |
| SAM-35 | test_seeded_f_payload_mutations_keep_controlled_status | seeded f payload mutations keep controlled status |

## Self-Review and Corrections

Reviewed canonical RID discovery, Names default-type references, orphan/invalid/duplicate mappings, missing F/V records, RID/name discrepancies and source-local linkage. No preferred username, full SID, administrator membership or effective login policy is invented. Exact F layout is distinct from partial V descriptor decoding. Raw bit labels and counters retain their limits; zero/sentinel/overflow timestamps remain separate from key last-write and no fixed password-expiry interval is computed.

Reviewed V offset/length bounds and alignment, literal/invalid Unicode, embedded NULs, overlapping strings, raw selected-field provenance and output content boundaries. Full V/unselected payloads and other-value content are not exported; their sizes/digests remain available. No credential pointer, hash extraction/decryption or boot-key parser is added. The content selection is not an arbitrary-text redaction guarantee. Replaced repeated candidate-list membership and duplicate-mapping scans with offset sets and a counter to avoid unnecessary quadratic work. Existing decoder semantics and EnScript bytes are unchanged.

Reviewed input hashes, source ordering, schema 15, JSON/SQLite composite mapping foreign keys, bounds, strict exits and all-or-nothing output publication. No remaining blocking findings in self-review; acquired-data and host validation remain outstanding.

## Independent Comparison and Validation Results

Compared synthetic account/mapping key and value names, types, raw selected F/V string bytes and physical nk/vk offsets with python-registry 1.3.1, accounting for the four-byte cell-header/payload difference. Explicit fixed-offset integer/FILETIME and length-framed UTF-16 checks independently verify expected metadata. Installed 0.15.0 console checks outside checkout exercise repeated SAM inputs, schema 15 JSON/SQLite, source hashes, raw strings, mapping foreign keys and unchanged input. These checks do not certify actual Windows SAM layouts or identity semantics.

The independent reader's raw_data API returns four pointer bytes for this fixture's zero-length, nonstandard-type Names default value. That result is not payload data: checked its declared raw_data_length of zero, RID type and physical vk offset directly. Plaintrace follows the declared length and keeps an empty value; this comparison does not claim matching raw_data API behavior for that special case.

The full 475-test suite with EVTX passes. Eleven EnScript static regressions, four generated source-reference documents, bilingual documentation/link/test mappings and archive validation pass. Thirteen EnScript files and original manifests match the base; original archive tree/README and 263 reconstructed 2017 commits remain preserved. These are integrity/static checks, not EnCase compilation/execution.

## Remaining Validation and Unsupported Structures

Actual acquired SAM across Windows versions/F/V revisions, Windows/Linux execution, Python 3.10, independent real-record interpretation, large collections and acquisition races remain unvalidated. Alternative roots/layouts, unassigned fields, groups/aliases/domain policy/full SIDs, credential extraction/decryption and native REGF 1.6/big-data/volatile/link/deleted/slack structures remain unsupported. No log replay, recovery, privilege/expiry/ownership inference or automatic cross-hive joins. EnCase compilation/execution remains unverified. Exact fields, statuses and output limits are in the CLI document.
