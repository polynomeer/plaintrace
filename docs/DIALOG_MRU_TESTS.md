# Common Dialog MRU Tests and Code Review

**English** | [한국어](DIALOG_MRU_TESTS.ko.md)

Validated and self-reviewed on 2026-10-16 on macOS/Python 3.14. All 314 cases pass without skips with the EVTX extra: 278 existing and 36 dialog MRU cases. Without it, 306 execute and eight existing integrations skip. This adapter itself has no extra dependency. See [contracts and limits](DIALOG_MRU_CLI.md). This is not external reviewer approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

An independent synthetic REGF writer builds root/extension/wildcard scopes, MRU orders and numeric binary values. Application prefixes directly encode UTF-16 Unicode/emoji and exact terminators before length-framed PIDLs. Existing independent Shell Item writers provide GUID/volume/directory/file/network/extensions and raw times. Expected strings/offsets/ranks are fixed oracles; no real evidence/exports are committed. Patched budgets and deterministic mutations sample controlled errors, not large-input performance or comprehensive fuzzing.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 2c6a4203770834c6e197e86b9a1888ea5c4c5d68 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| DM-01 | test_both_lists_categories_application_and_folder_references | both lists categories application and folder references |
| DM-02 | test_open_save_root_is_container_without_fabricated_order | open save root is container without fabricated order |
| DM-03 | test_open_save_root_numeric_values_are_preserved | open save root numeric values are preserved |
| DM-04 | test_last_visited_utf16_prefix_and_pidl_offsets_are_exact | last visited utf16 prefix and pidl offsets are exact |
| DM-05 | test_application_literal_not_normalized_or_verified_executable | application literal not normalized or verified executable |
| DM-06 | test_invalid_application_unicode_does_not_hide_independent_pidl | invalid application unicode does not hide independent pidl |
| DM-07 | test_empty_application_label_is_not_attributed | empty application label is not attributed |
| DM-08 | test_unterminated_application_never_searches_for_pidl_signature | unterminated application never searches for pidl signature |
| DM-09 | test_unterminated_pidl_keeps_components_but_no_path | unterminated pidl keeps components but no path |
| DM-10 | test_trailing_pidl_and_empty_lists_retained | trailing pidl and empty lists retained |
| DM-11 | test_wrong_value_types_do_not_decode_application_or_pidl | wrong value types do not decode application or pidl |
| DM-12 | test_malformed_pidl_lengths_strings_and_extensions_keep_raw | malformed pidl lengths strings and extensions keep raw |
| DM-13 | test_unknown_item_classes_do_not_create_guessed_paths | unknown item classes do not create guessed paths |
| DM-14 | test_explicit_absolute_anchor_and_namespace_or_relative_bases | explicit absolute anchor and namespace or relative bases |
| DM-15 | test_dot_device_and_separator_components_are_not_resolved | dot device and separator components are not resolved |
| DM-16 | test_mru_sparse_missing_and_unlisted_ranks_keep_gaps | mru sparse missing and unlisted ranks keep gaps |
| DM-17 | test_invalid_mru_types_sentinels_duplicates_keep_no_ranks | invalid mru types sentinels duplicates keep no ranks |
| DM-18 | test_missing_legacy_and_ambiguous_controls_never_guess_order | missing legacy and ambiguous controls never guess order |
| DM-19 | test_canonical_names_unknown_metadata_and_raw_offsets | canonical names unknown metadata and raw offsets |
| DM-20 | test_missing_branches_and_valid_empty_key_are_distinct | missing branches and valid empty key are distinct |
| DM-21 | test_nested_scopes_diagnosed_not_silently_traversed | nested scopes diagnosed not silently traversed |
| DM-22 | test_duplicate_paths_across_categories_and_apps_remain_independent | duplicate paths across categories and apps remain independent |
| DM-23 | test_key_filetimes_and_item_fat_times_are_not_entry_open_times | key filetimes and item fat times are not entry open times |
| DM-24 | test_ansi_codepage_and_unicode_application_are_separate | ansi codepage and unicode application are separate |
| DM-25 | test_invalid_codepage_is_fatal | invalid codepage is fatal |
| DM-26 | test_item_diagnostics_are_adapter_scoped_and_value_identified | item diagnostics are adapter scoped and value identified |
| DM-27 | test_key_entry_application_path_output_budgets_are_fatal | key entry application path output budgets are fatal |
| DM-28 | test_shell_item_resource_limits_are_not_downgraded | shell item resource limits are not downgraded |
| DM-29 | test_regf_versions_indexes_case_and_dirty_inputs | regf versions indexes case and dirty inputs |
| DM-30 | test_cli_repeated_hives_source_hash_and_schema | cli repeated hives source hash and schema |
| DM-31 | test_json_sqlite_schema_raw_unicode_and_foreign_keys | json sqlite schema raw unicode and foreign keys |
| DM-32 | test_cli_codepage_option_and_sqlite | cli codepage option and sqlite |
| DM-33 | test_mixed_adapters_keep_source_order_and_no_automatic_joins | mixed adapters keep source order and no automatic joins |
| DM-34 | test_cli_strict_later_failure_atomic_and_evidence_protection | cli strict later failure atomic and evidence protection |
| DM-35 | test_only_supplied_hive_opened_and_changes_rejected | only supplied hive opened and changes rejected |
| DM-36 | test_mutated_hives_have_controlled_failures | mutated hives have controlled failures |

## Self-Review and Corrections

Reviewed scope discovery/enumeration, container-versus-list handling, MRU controls, application-prefix/PIDL logical offsets, partial shared decoding/resource limits, raw lineage and export foreign keys. Require a zero terminal item for PIDL path composition, distinct from ShellBags optional termination. Invalid application text is not verified executable identity; an independently framed PIDL remains separate. Missing prefix termination never triggers signature searching or printable-string path guesses.

An OpenSave root without controls/numeric values remains a normal container without a false missing-order warning. Rank gaps and duplicate observations remain; OpenSave and LastVisited are not arbitrarily correlated. Shared-decoder codes are scoped to this adapter with numeric value identities and resource failures are not downgraded to malformed observations. Existing decoder behavior is unchanged; all adapters run against schema 10.

## Independent Comparison and Validation Results

Independently compared synthetic key/value names, types, entire raw bytes and nk/vk offsets with python-registry 1.3.1. Explicitly checked the four-byte cell-header versus payload offset difference. This is not independent certification of full PIDL semantics or actual hives. Installed 0.10.0 console checks run outside checkout for JSON/SQLite schema 10, repeated-source hashes, parent foreign keys and unchanged inputs.

Also ran eleven EnScript static regressions, four generated source references, document/language/test mappings and archive validation. Thirteen EnScript files and manifests match the base; the original archive tree/README and 263 reconstructed 2017 commits are preserved. These checks do not validate EnCase execution.

## Remaining Validation and Unsupported Structures

Actual Windows/application-version NTUSER dialog MRUs, Windows/Linux execution, Python 3.10, independent real PIDL semantics, large-input performance and acquisition races remain unvalidated. Legacy/other dialog keys, deeper scopes, unsupported Shell Item/extensions/namespaces and native REGF restrictions remain excluded. No log replay, deleted/slack carving, signature/printable-string recovery or automatic user/artifact joins occur. Key last-write/MRU/item FAT fields do not prove successful file opening/saving or execution. EnCase compilation/execution remains unverified; originals and archives remain preserved.
