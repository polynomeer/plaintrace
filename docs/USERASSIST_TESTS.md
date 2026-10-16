# UserAssist Tests and Code Review

**English** | [한국어](USERASSIST_TESTS.ko.md)

Validated and self-reviewed on 2026-10-16 on macOS/Python 3.14. All 346 Python cases pass with the EVTX extra: 314 existing and 32 UserAssist cases, without skips. Without the extra, 338 execute and eight existing EVTX integrations skip; that is not full EVTX validation. UserAssist itself has no extra runtime dependency. See [contracts and limits](USERASSIST_CLI.md). This is self-review, not external approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

The existing independent synthetic REGF writer creates GUID/Count/Settings scopes with exact Version DWORDs. Payloads are constructed directly with independently specified little-endian offsets and fixed UTC/100 ns oracles, not a production encoder. Cases include both layouts, Unicode/emoji, ROT13/plain/unknown policies, raw metadata and malformed controls. Temporary hives and exports are removed; no actual evidence is committed. Patched budgets and seeded payload mutations are controlled checks, not performance testing or exhaustive fuzzing.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code caa66102c4c46ebc7ab0e81153c36801bdfc8d67 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| UA-01 | test_v3_offsets_unicode_and_unadjusted_count | v3 offsets unicode and unadjusted count |
| UA-02 | test_v5_metrics_and_opaque_ranges_are_exact | v5 metrics and opaque ranges are exact |
| UA-03 | test_session_control_never_becomes_run_record | session control never becomes run record |
| UA-04 | test_session_control_name_case_and_entry_sized_payload | session control name case and entry sized payload |
| UA-05 | test_zero_and_out_of_range_filetimes | zero and out of range filetimes |
| UA-06 | test_unsigned_counts_and_no_legacy_bias_correction | unsigned counts and no legacy bias correction |
| UA-07 | test_noencrypt_one_preserves_plain_names_and_control | noencrypt one preserves plain names and control |
| UA-08 | test_noencrypt_zero_default_and_nonascii_names | noencrypt zero default and nonascii names |
| UA-09 | test_invalid_noencrypt_does_not_guess_names_or_controls | invalid noencrypt does not guess names or controls |
| UA-10 | test_missing_version_retains_values_without_size_guessing | missing version retains values without size guessing |
| UA-11 | test_unsupported_version_and_wrong_version_type | unsupported version and wrong version type |
| UA-12 | test_wrong_size_truncation_tail_and_cross_version_rejected | wrong size truncation tail and cross version rejected |
| UA-13 | test_wrong_registry_type_not_parsed | wrong registry type not parsed |
| UA-14 | test_keys_raw_metadata_parent_links_and_physical_offsets | keys raw metadata parent links and physical offsets |
| UA-15 | test_absent_and_empty_supported_roots | absent and empty supported roots |
| UA-16 | test_unknown_guid_version_supported_without_identity_mapping | unknown guid version supported without identity mapping |
| UA-17 | test_non_guid_children_missing_count_and_nested_scopes | non guid children missing count and nested scopes |
| UA-18 | test_case_insensitive_paths_versions_settings | case insensitive paths versions settings |
| UA-19 | test_all_regf_index_and_version_layouts | all regf index and version layouts |
| UA-20 | test_dirty_and_corrupt_hives_rejected | dirty and corrupt hives rejected |
| UA-21 | test_key_entry_and_output_budgets | key entry and output budgets |
| UA-22 | test_duplicate_values_and_aliases_rejected | duplicate values and aliases rejected |
| UA-23 | test_json_sqlite_schema_and_foreign_keys | json sqlite schema and foreign keys |
| UA-24 | test_repeated_sources_hashes_and_input_unchanged | repeated sources hashes and input unchanged |
| UA-25 | test_cli_subprocess_json_strict_and_sqlite | cli subprocess json strict and sqlite |
| UA-26 | test_mixed_dialog_and_userassist_sources | mixed dialog and userassist sources |
| UA-27 | test_fatal_later_input_publishes_no_partial_output | fatal later input publishes no partial output |
| UA-28 | test_evidence_and_existing_outputs_protected | evidence and existing outputs protected |
| UA-29 | test_missing_input_and_sqlite_destination_rejected | missing input and sqlite destination rejected |
| UA-30 | test_no_decoded_target_is_opened | no decoded target is opened |
| UA-31 | test_changed_input_hash_rejected | changed input hash rejected |
| UA-32 | test_seeded_binary_payload_mutations_are_bounded | seeded binary payload mutations are bounded |

## Self-Review and Corrections

Reviewed scope discovery, per-group Version, setting-aware name decoding, session-control exclusion, exact binary lengths, integer timestamp/counter preservation, limits and source/export integration. Corrected control-name comparison to be case-insensitive and added a regression where its payload has an ordinary entry size; controls must still remain opaque. Invalid NoEncrypt does not guess a cipher or expose metrics from a possible control. Version is never guessed by length, legacy counters are never silently corrected and unsupported values are not dropped. Unknown GUIDs retain literal identifiers without assigning application identity; decoded names are never opened or expanded.

All existing adapters receive schema 11, with prior field meanings and decoder behavior unchanged. Reviewed raw key/value offsets, separate key and run times, parent links, repeated/mixed sources, SQLite foreign keys, strict warning exits, all-or-nothing publication and input/output protections. Original EnScript and historical data are unchanged.

## Independent Comparison and Validation Results

Compared synthetic REGF key/value names, types, full raw data and physical offsets against python-registry 1.3.1, accounting for its payload offsets being four bytes after cell headers. Explicit fixed-offset unpacking independently checks version-3/5 DWORDs and FILETIMEs. An installed 0.11.0 console smoke test outside the checkout checks repeated-source hashes, JSON/SQLite schema 11, foreign keys and unchanged input. These checks do not independently certify Windows semantics or actual acquired NTUSER data.

The full 346-test suite with EVTX passes. Eleven EnScript static regressions, four generated source references, paired documentation/link/test mappings and archive validation pass. Thirteen EnScript files and original manifests match the base; archive tree/README and 263 reconstructed 2017 commits remain preserved. Static checks do not establish EnCase compilation or execution.

## Remaining Validation and Unsupported Structures

Actual acquired NTUSER UserAssist across Windows/GUID/version/settings variants, Windows/Linux execution, Python 3.10, independent real-record interpretation, large collections and acquisition races remain unvalidated. Unknown versions, beta Vigenère/mixed encodings, deeper scopes and native REGF restrictions remain unsupported. No dirty-hive log replay, deleted/slack recovery, path expansion, inferred ownership/session, execution success or cross-artifact joins. Key time is not an entry run time; raw counters/focus fields are not verified frequency or active-use duration. EnCase compilation/execution remains unverified. See the CLI document for exact limits and status precedence.
