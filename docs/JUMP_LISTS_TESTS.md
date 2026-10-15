# Jump Lists Tests and Code Review

**English** | [한국어](JUMP_LISTS_TESTS.ko.md)

Validated and self-reviewed on 2026-10-15 on macOS/Python 3.14. All 235 cases pass without skips with the EVTX extra: 200 existing and 35 Jump Lists cases. Without it, 227 execute and eight existing integrations skip. Jump Lists itself has no extra dependency. See [contracts and limits](JUMP_LISTS_CLI.md). This is not external reviewer approval or acquired-evidence certification.

## Reproduction and Synthetic Fixtures

An independent synthetic writer creates CFB v3/v4, regular/mini/fragmented chains, extended DIFAT, DestList and custom categories in temporary directories. Tests assert raw GUIDs, FILETIME, paths and physical block starts. Invalid chains/pointers/records are explicitly mutated; deterministic mutations only sample controlled failures and are not comprehensive fuzzing. No evidence, public samples or generated exports are committed. Small patched budgets do not certify large-input performance.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 285f7f5020213042372e4d791fd001626a04231e -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| JL-01 | test_automatic_v1_raw_time_guid_and_link_association | automatic v1 raw time guid and link association |
| JL-02 | test_v3_v4_extensions_and_pinned_state | v3 v4 extensions and pinned state |
| JL-03 | test_destlist_version_two_and_future_rejected | destlist version two and future rejected |
| JL-04 | test_mini_and_regular_streams_cfb_v3_v4_fragmented | mini and regular streams cfb v3 v4 fragmented |
| JL-05 | test_ministream_many_mini_sectors_and_physical_offsets | ministream many mini sectors and physical offsets |
| JL-06 | test_missing_empty_destlist_and_unassociated_links | missing empty destlist and unassociated links |
| JL-07 | test_missing_links_and_orphans_are_not_discarded | missing links and orphans are not discarded |
| JL-08 | test_duplicate_ids_ambiguous_no_silent_join | duplicate ids ambiguous no silent join |
| JL-09 | test_numbered_stream_case_and_unknown_metadata_retained | numbered stream case and unknown metadata retained |
| JL-10 | test_declared_count_trailing_bytes_retained_not_carved | declared count trailing bytes retained not carved |
| JL-11 | test_invalid_utf16_nul_and_unknown_pin_retained | invalid utf16 nul and unknown pin retained |
| JL-12 | test_zero_overflow_and_pinned_count_diagnostic | zero overflow and pinned count diagnostic |
| JL-13 | test_invalid_embedded_lnk_raw_retained | invalid embedded lnk raw retained |
| JL-14 | test_lnk_diagnostics_use_unique_entry_identity | lnk diagnostics use unique entry identity |
| JL-15 | test_cfb_fat_cycle_overlap_and_truncation_rejected | cfb fat cycle overlap and truncation rejected |
| JL-16 | test_cfb_minifat_cycle_and_duplicate_ownership_rejected | cfb minifat cycle and duplicate ownership rejected |
| JL-17 | test_cfb_directory_cycle_nested_unreachable_and_duplicate_names | cfb directory cycle nested unreachable and duplicate names |
| JL-18 | test_cfb_header_counts_format_and_stream_size_limits | cfb header counts format and stream size limits |
| JL-19 | test_cfb_extended_difat_and_large_regular_stream | cfb extended difat and large regular stream |
| JL-20 | test_destlist_truncated_path_and_extension_are_fatal | destlist truncated path and extension are fatal |
| JL-21 | test_custom_named_tasks_known_categories_and_full_lnk | custom named tasks known categories and full lnk |
| JL-22 | test_custom_clsid_body_preserves_original_and_normalized_lnk | custom clsid body preserves original and normalized lnk |
| JL-23 | test_custom_does_not_split_embedded_signatures | custom does not split embedded signatures |
| JL-24 | test_custom_lnk_sections_codepage_and_extra_blocks | custom lnk sections codepage and extra blocks |
| JL-25 | test_custom_empty_file_and_empty_category | custom empty file and empty category |
| JL-26 | test_custom_unsupported_version_category_footer_trailing_rejected | custom unsupported version category footer trailing rejected |
| JL-27 | test_custom_declared_count_and_lnk_length_are_bounded | custom declared count and lnk length are bounded |
| JL-28 | test_input_entry_category_path_link_output_budgets | input entry category path link output budgets |
| JL-29 | test_cli_repeated_inputs_renamed_detection_hash_and_app_hint | cli repeated inputs renamed detection hash and app hint |
| JL-30 | test_json_sqlite_schema_lineage_raw_roundtrip | json sqlite schema lineage raw roundtrip |
| JL-31 | test_mixed_inputs_preserve_previous_ids_and_no_link_duplication | mixed inputs preserve previous ids and no link duplication |
| JL-32 | test_cli_strict_fatal_atomic_and_output_protection | cli strict fatal atomic and output protection |
| JL-33 | test_only_supplied_input_opened_and_changing_read_rejected | only supplied input opened and changing read rejected |
| JL-34 | test_invalid_codepage_is_fatal_not_a_bad_link | invalid codepage is fatal not a bad link |
| JL-35 | test_mutated_containers_fail_with_controlled_errors | mutated containers fail with controlled errors |

## Independent Comparison and Public Samples

Compared synthetic CFB v3/v4/fragmented/DIFAT stream bytes independently with olefile 0.47. The installed 0.8.0 console runs outside the checkout for JSON/SQLite schema 8, source hashes, parent foreign keys and unchanged inputs. olefile is comparison-only, not a runtime/test dependency.

Two public upstream automatic-list samples were also read only in temporary storage. The Windows 7 sample yielded DestList 1/four parsed links; the Windows 10 sample yielded DestList 3/nine parsed links. All active stream bytes matched olefile. Warnings were retained; this does not claim full PIDL/opaque ExtraData interpretation. Sample names are distributor environment labels, not local execution of those operating systems.

| Upstream sample | SHA-256 |
| --- | --- |
| [Win7/1b4dd67f29cb1962](https://github.com/EricZimmerman/JumpList/blob/master/JumpList.Test/TestFiles/Win7/1b4dd67f29cb1962.automaticDestinations-ms) | efb95b8477f4ed4968fb16c724845a52bcfc0ab671f4769a33ca05a25eef5379 |
| [Win10/f01b4d95cf55d32a](https://github.com/EricZimmerman/JumpList/blob/master/JumpList.Test/TestFiles/Win10/f01b4d95cf55d32a.automaticDestinations-ms) | a724713d2ff51d32e3f028c57ab906339f882de0c93dc9903f0f8b241c53fd56 |

## Self-Review and Corrections

Reviewed CFB allocation/cycles/aliases, directory traversal, mini-stream logical-to-physical mapping, DestList bounds, duplicate/missing IDs, custom framing and export foreign keys. Separated DestList lineage from the associated LNK stream; invalid codepages now fail as configuration errors rather than being swallowed as corrupt links. Distinguished synthetic CLSID-body HeaderSize from original bytes and attached text/LNK diagnostics to entry/category identities. Bounded allocation-table expansion and avoided repeated remaining-buffer copies for CLSID-body framing. No signature splitting or arbitrary duplicate-ID joins occur.

Verified full regressions, eleven EnScript static checks, four source references and document/language/test mappings. Archive validation covers thirteen sources, original tree/README and 263 reconstructed 2017 commits; EnScript/manifests are unchanged against the base. These checks do not validate EnCase execution.

## Remaining Validation and Unsupported Structures

User-acquired Jump Lists, public/real CustomDestinations, broad Windows/application versions, Windows/Linux execution, Python 3.10, extensive independent real-artifact interpretation, large-input performance and acquisition races remain unvalidated. Two public automatic samples do not replace that scope. Nested/unreachable active CFB structures, DestList 2/future versions, property extensions, non-LNK objects, nonconforming custom counts/envelopes, deleted/slack carving and ProgramsCache remain unsupported. CFB red-black/inactive-allocation semantics and DestList checksums are not certified. Existing LNK limitations remain; execution/opening/user attribution is not inferred. EnCase compilation/execution remains unverified; originals and archives are preserved.
