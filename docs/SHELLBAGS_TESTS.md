# ShellBags Tests and Code Review

**English** | [한국어](SHELLBAGS_TESTS.ko.md)

Validated and self-reviewed on 2026-10-15 on macOS/Python 3.14. All 278 cases pass without skips with the EVTX extra: 236 existing and 42 ShellBags cases. Without it, 270 execute and eight existing integrations skip. ShellBags itself has no extra dependency. See [contracts and limits](SHELLBAGS_CLI.md). This is not external reviewer approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

An independent synthetic REGF writer builds NTUSER/UsrClass paths, sparse MRU controls, NodeSlot and view trees in temporary directories. Shell Item writers encode GUID, drive, network, file/directory, version-specific extensions and fixed FAT times. Expected names/hierarchies/times are fixed oracles, not adapter-computed values. Tests mutate pointers/names/lengths and patch small resource budgets. Deterministic mutations sample controlled errors rather than comprehensive fuzzing. No real evidence or generated exports are committed.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 9bc15c8f765ea2c10d2259049a39222375f5d61c -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| SB-01 | test_hierarchy_guid_volume_long_names_and_same_hive_views | hierarchy guid volume long names and same hive views |
| SB-02 | test_ntuser_and_usrclass_root_layouts_are_role_explicit | ntuser and usrclass root layouts are role explicit |
| SB-03 | test_mru_sparse_order_is_rank_not_timestamp | mru sparse order is rank not timestamp |
| SB-04 | test_invalid_ambiguous_and_missing_mru_keep_raw_no_ranks | invalid ambiguous and missing mru keep raw no ranks |
| SB-05 | test_unlisted_and_noncanonical_values_are_not_dropped | unlisted and noncanonical values are not dropped |
| SB-06 | test_valid_empty_mru_and_absent_roots | valid empty mru and absent roots |
| SB-07 | test_node_slot_type_missing_bag_and_raw_controls | node slot type missing bag and raw controls |
| SB-08 | test_node_slot_belongs_to_key_not_child_value | node slot belongs to key not child value |
| SB-09 | test_missing_parent_value_propagates_unresolved_ancestry | missing parent value propagates unresolved ancestry |
| SB-10 | test_unknown_ancestor_is_not_guessed_and_explicit_volume_can_anchor | unknown ancestor is not guessed and explicit volume can anchor |
| SB-11 | test_noncanonical_child_is_diagnosed_and_not_traversed | noncanonical child is diagnosed and not traversed |
| SB-12 | test_duplicate_paths_and_separate_roots_are_preserved | duplicate paths and separate roots are preserved |
| SB-13 | test_file_entry_extension_versions_and_exact_fat_bytes | file entry extension versions and exact fat bytes |
| SB-14 | test_unknown_extension_version_retains_primary_without_guess | unknown extension version retains primary without guess |
| SB-15 | test_malformed_extension_offsets_sizes_and_backlinks_keep_whole_raw | malformed extension offsets sizes and backlinks keep whole raw |
| SB-16 | test_ansi_codepage_and_unicode_names | ansi codepage and unicode names |
| SB-17 | test_invalid_unicode_does_not_become_path | invalid unicode does not become path |
| SB-18 | test_network_unc_and_folder_hierarchy_literal | network unc and folder hierarchy literal |
| SB-19 | test_unsupported_volume_network_and_namespace_variants_stay_opaque | unsupported volume network and namespace variants stay opaque |
| SB-20 | test_root_guid_not_mapped_and_opaque_tail_retained | root guid not mapped and opaque tail retained |
| SB-21 | test_dot_and_separator_names_not_composed_or_normalized | dot and separator names not composed or normalized |
| SB-22 | test_item_list_multiple_components_and_optional_terminal | item list multiple components and optional terminal |
| SB-23 | test_trailing_bytes_empty_and_wrong_type_keep_raw | trailing bytes empty and wrong type keep raw |
| SB-24 | test_malformed_list_bounds_and_strings_are_observations | malformed list bounds and strings are observations |
| SB-25 | test_zero_invalid_fat_times_keep_raw_no_epoch_guess | zero invalid fat times keep raw no epoch guess |
| SB-26 | test_item_and_extension_budgets_are_fatal_not_malformed_rows | item and extension budgets are fatal not malformed rows |
| SB-27 | test_key_view_entry_output_and_path_budgets | key view entry output and path budgets |
| SB-28 | test_hierarchy_and_view_depth_are_bounded | hierarchy and view depth are bounded |
| SB-29 | test_regf_versions_indexes_case_paths_and_dirty_hives | regf versions indexes case paths and dirty hives |
| SB-30 | test_role_and_encoding_validation_are_fatal | role and encoding validation are fatal |
| SB-31 | test_cli_repeated_roles_hashes_and_schema | cli repeated roles hashes and schema |
| SB-32 | test_json_sqlite_raw_roundtrip_and_composite_relationships | json sqlite raw roundtrip and composite relationships |
| SB-33 | test_deferred_orphan_parent_fails_without_publishing_output | deferred orphan parent fails without publishing output |
| SB-34 | test_mixed_adapters_do_not_join_users_or_duplicate_sources | mixed adapters do not join users or duplicate sources |
| SB-35 | test_cli_strict_fatal_atomic_and_evidence_protection | cli strict fatal atomic and evidence protection |
| SB-36 | test_only_supplied_hive_opened_and_changing_read_rejected | only supplied hive opened and changing read rejected |
| SB-37 | test_deterministic_mutations_raise_only_controlled_errors | deterministic mutations raise only controlled errors |
| SB-38 | test_view_metadata_offsets_raw_values_and_slot_reuse | view metadata offsets raw values and slot reuse |
| SB-39 | test_mru_sentinel_missing_embedded_and_trailing_are_invalid | mru sentinel missing embedded and trailing are invalid |
| SB-40 | test_invalid_long_name_falls_back_to_explicit_primary | invalid long name falls back to explicit primary |
| SB-41 | test_cli_shellbag_codepage_option_and_sqlite | cli shellbag codepage option and sqlite |
| SB-42 | test_network_description_comments_and_non_unc_remain_literal | network description comments and non unc remain literal |

## Self-Review and Corrections

Reviewed hierarchy/value relations, NodeSlot ownership, supported layouts/unknown variants, string/extension boundaries, resource budgets, relative/namespace/absolute candidates and time semantics. Children without parent values are traversed without inventing ancestry. Device namespaces are not misclassified as server/share UNC anchors. Dot/separator names are not normalized into filesystem paths; unsupported Shell Items remain bytes. Invalid text is escaped only for display and excluded from composition, with independent valid primary-name fallback tested. Resource limits and malformed observations use separate exception types.

SQLite creates all tables before inserts and defers parent-entry constraints until commit to support reciprocal key/item references. Missing parent/view/child relations fail without publishing a partial file. Tests keep MRU rank distinct from file/key times and prevent copying NodeSlot onto child values. All existing adapters also run against schema 9.

## Independent Comparison and Validation Results

Independently compared synthetic hive key/value names, types, raw bytes and nk/vk positions with python-registry 1.3.1. Its record offsets address cell payloads, so the four-byte cell-header difference is explicitly checked. This does not independently certify full Shell Item semantics or acquired hives. Installed 0.9.0 console checks run outside the checkout for both roles in JSON/SQLite, verifying schema 9, source hashes, relational integrity and unchanged inputs.

Also verified eleven EnScript static regressions, four generated source references, document/language/test mappings and archive integrity. All thirteen EnScript files and existing manifests match the base; the original archived tree/README and 263 reconstructed 2017 commits are preserved. These checks do not validate EnCase execution.

## Remaining Validation and Unsupported Structures

Actual NTUSER/UsrClass ShellBags, Windows/application-version acquisitions, Windows/Linux execution, Python 3.10, independent real Shell Item semantics, large-input performance and acquisition races remain unvalidated. Dirty-hive/log replay, REGF 1.6/big data/volatile/link/deleted/slack, unreferenced Bags, legacy MRUList ranking and unsupported Shell Item/extensions/properties/namespaces remain excluded. FAT displays get no timezone; key last-write/MRU/NodeSlot do not prove folder viewing, access, execution or ownership. EnCase compilation/execution remains unverified; originals and archives remain preserved.
