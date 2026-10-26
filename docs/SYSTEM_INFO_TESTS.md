# System Information Tests and Code Review

**English** | [한국어](SYSTEM_INFO_TESTS.ko.md)

Validated and self-reviewed on 2026-10-26 on macOS/Python 3.14. All 440 Python tests pass without skips with the EVTX extra: 407 existing and 33 system information cases. Without that extra, 432 execute and eight existing EVTX integrations skip; this is not complete EVTX validation. The new adapter itself uses only the standard library. See [contracts and limits](SYSTEM_INFO_CLI.md). This is self-review, not external approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

The existing independent REGF fixture writer generates SOFTWARE version values, SYSTEM Select/Current pointing to ControlSet002, conflicting configured/active/TCPIP labels, signed timezone DWORDs and fixed binary FILETIMEs. Explicit UTC and unsigned/two's-complement byte oracles check conversions; values in ControlSet001 intentionally differ. Unknown/license fields remain synthetic opaque bytes. No actual evidence or generated exports are committed; temporary files are deleted. Patched budgets and seeded payload mutations are controlled checks, not exhaustive fuzzing or large-input performance validation.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 4638b5101ef3c5ec389d7d77418fe62acd8557c4 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| SYS-01 | test_software_version_owner_and_build_fields_kept_separate | software version owner and build fields kept separate |
| SYS-02 | test_install_date_seconds_and_install_time_exact_filetime | install date seconds and install time exact filetime |
| SYS-03 | test_select_current_not_default_or_controlset001 | select current not default or controlset001 |
| SYS-04 | test_control_selection_metadata_and_conflicting_names_remain | control selection metadata and conflicting names remain |
| SYS-05 | test_timezone_signed_biases_are_not_applied_to_timestamps | timezone signed biases are not applied to timestamps |
| SYS-06 | test_shutdown_binary_filetime_precision_and_no_boot_claim | shutdown binary filetime precision and no boot claim |
| SYS-07 | test_key_lastwrite_is_separate_from_embedded_times | key lastwrite is separate from embedded times |
| SYS-08 | test_opaque_unknown_and_license_values_never_decoded | opaque unknown and license values never decoded |
| SYS-09 | test_strings_expandable_tokens_and_no_normalization | strings expandable tokens and no normalization |
| SYS-10 | test_unsigned_dword_maximum_and_zero | unsigned dword maximum and zero |
| SYS-11 | test_zero_and_overflow_filetimes_retained | zero and overflow filetimes retained |
| SYS-12 | test_wrong_types_not_coerced_for_known_fields | wrong types not coerced for known fields |
| SYS-13 | test_wrong_numeric_sizes_and_trailing_bytes_not_recovered | wrong numeric sizes and trailing bytes not recovered |
| SYS-14 | test_unterminated_odd_empty_and_invalid_utf16 | unterminated odd empty and invalid utf16 |
| SYS-15 | test_aligned_terminators_tails_and_invalid_status_precedence | aligned terminators tails and invalid status precedence |
| SYS-16 | test_missing_software_branch_and_optional_fields_diagnosed | missing software branch and optional fields diagnosed |
| SYS-17 | test_missing_optional_system_branches_no_invented_rows | missing optional system branches no invented rows |
| SYS-18 | test_missing_invalid_or_unavailable_control_selection_fatal | missing invalid or unavailable control selection fatal |
| SYS-19 | test_high_controlset_and_case_insensitive_names | high controlset and case insensitive names |
| SYS-20 | test_nested_scopes_not_traversed_and_roles_not_auto_detected | nested scopes not traversed and roles not auto detected |
| SYS-21 | test_physical_key_and_value_offsets_raw_bytes | physical key and value offsets raw bytes |
| SYS-22 | test_all_regf_versions_indexes_and_duplicate_names | all regf versions indexes and duplicate names |
| SYS-23 | test_dirty_and_corrupt_hives_rejected | dirty and corrupt hives rejected |
| SYS-24 | test_observation_value_string_output_budgets | observation value string output budgets |
| SYS-25 | test_json_sqlite_schema_values_and_foreign_keys | json sqlite schema values and foreign keys |
| SYS-26 | test_repeated_hives_source_hashes_and_input_bytes | repeated hives source hashes and input bytes |
| SYS-27 | test_cli_roles_source_order_json_and_sqlite | cli roles source order json and sqlite |
| SYS-28 | test_mixed_adapters_do_not_join_host_or_user | mixed adapters do not join host or user |
| SYS-29 | test_strict_warning_and_fatal_later_input_atomic | strict warning and fatal later input atomic |
| SYS-30 | test_input_existing_output_and_sidecar_protection | input existing output and sidecar protection |
| SYS-31 | test_missing_input_and_sqlite_destination | missing input and sqlite destination |
| SYS-32 | test_only_supplied_files_opened_and_changes_rejected | only supplied files opened and changes rejected |
| SYS-33 | test_seeded_shutdown_payload_mutations_are_controlled | seeded shutdown payload mutations are controlled |

## Self-Review

Reviewed original scope versus portable implementation, selected roots/fields, role boundaries, strict Select/Current resolution and absence of ControlSet001/default fallback. Configured/active/TCPIP names, version/release labels and install timestamps remain separate without a guessed merged identity. Optional/version-specific omissions warn without fabricated fields. Unknown and license values stay opaque rather than becoming guessed product keys.

Reviewed exact registry types/lengths, integer epoch conversions and signed bias handling, raw timestamps versus key times, invalid Unicode/tail status precedence, limits, physical cell offsets, repeated/mixed sources, schema 14, JSON/SQLite source foreign keys and atomic output protections. Biases never modify other timestamps; stored shutdown data never becomes uptime/boot/clean-shutdown proof. Shared decoders and EnScript bytes are unchanged. No remaining blocking findings in self-review; real-host validation remains open.

## Independent Comparison and Validation Results

Compared synthetic SOFTWARE/SYSTEM keys, names, types, raw bytes and physical nk/vk offsets against python-registry 1.3.1, explicitly accounting for the four-byte header-versus-payload offset difference. Fixed DWORD/FILETIME and signed-bias checks independently verify selected values. Installed 0.14.0 console checks outside checkout exercise both role flags, repeated sources, schema 14 JSON/SQLite, raw nested values, source hashes, foreign keys and unchanged inputs. These checks do not certify real Windows settings semantics or actual acquired hives.

The full 440-case suite with EVTX passes. Eleven EnScript static regressions, four generated source-reference documents, bilingual link/structure/test mappings and archive validation pass. All thirteen EnScript files and original manifests match the base; archive tree/README and 263 reconstructed 2017 commits remain preserved. These are integrity/static checks, not EnCase compilation or execution.

## Remaining Validation and Unsupported Structures

Actual acquired SOFTWARE/SYSTEM across Windows versions, Windows/Linux execution, Python 3.10, independent real-record semantics, large-input performance and acquisition races remain unvalidated. EnCase compilation/execution remains unverified. File/volume/GUI/chart APIs, SAM account analysis, product-key derivation, historical control sets, deeper/other inventories and native REGF 1.6/big-data/volatile/link/deleted/slack structures remain unsupported. No log replay, recovery, timezone application to past events, inferred OS/user ownership, boot/uptime/clean-shutdown claims or automatic joins. The CLI document defines fields, status precedence and limits.
