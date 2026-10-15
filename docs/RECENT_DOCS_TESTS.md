# RecentDocs Tests and Code Review

**English** | [한국어](RECENT_DOCS_TESTS.ko.md)

Validated and self-reviewed on 2026-10-15 on macOS/Python 3.14. With the EVTX extra all 175 Python cases pass without skips: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin, 25 USB registry and 27 RecentDocs. Without it, 167 execute and eight existing integrations skip. RecentDocs itself has no extra dependency. See [the adapter contract](RECENT_DOCS_CLI.md). This is not external reviewer approval or acquired-file certification.

## Reproduction and Fixtures

Synthetic REGF hives encode root/extension/Folder scopes, known raw control bytes, sparse IDs, literal Unicode names and opaque trailing bytes in temporary directories. Independent expected orders, strings and FILETIME ticks are asserted rather than calculated with the adapter. No acquired evidence or exports are committed. Tests execute the native reader, actual CLI subprocesses and both exporters; limit cases use small patched budgets rather than a large-profile performance claim.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 0f3e9e4fec930332310c172df6b1e599249c8924 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| RD-01 | test_modern_sparse_order_unicode_and_key_time | Sparse MRU ranks, astral Unicode and separate key last-write |
| RD-02 | test_scopes_folder_and_duplicates_are_not_deduplicated | Root/extension/Folder scopes preserve duplicate document observations |
| RD-03 | test_legacy_mrulist_letters_and_regsz | Legacy letter order and REG_SZ entries |
| RD-04 | test_both_controls_are_ambiguous_no_ranks | Both controls retained with ambiguous status and null ranks |
| RD-05 | test_missing_control_and_empty_key_preserved | Missing order and empty-key metadata retained |
| RD-06 | test_valid_empty_control_is_not_missing | Valid empty order differs from missing control |
| RD-07 | test_invalid_modern_sentinel_length_type_and_duplicates | Invalid DWORD lengths/types/sentinels/duplicates invalidate all ranks |
| RD-08 | test_invalid_legacy_mru_keeps_raw | Legacy invalid ASCII/Unicode lookalikes/type/termination retains raw |
| RD-09 | test_missing_and_unlisted_entries_keep_rank_gaps | Missing references retain rank gaps and unlisted values remain |
| RD-10 | test_noncanonical_numeric_and_unknown_values_are_key_metadata | Unknown/noncanonical names retained as key metadata |
| RD-11 | test_opaque_shell_tail_and_literal_names_are_preserved | Literal names and opaque Shell Item tail bytes retained |
| RD-12 | test_missing_terminator_wrong_type_and_empty_name_retained | Wrong type/missing NUL/empty names retain raw records |
| RD-13 | test_unpaired_surrogate_and_aligned_nul | Invalid surrogate escape diagnostic and aligned NUL decoding |
| RD-14 | test_nested_scopes_are_diagnosed_not_traversed | Nested scopes diagnosed and excluded |
| RD-15 | test_missing_branch_and_wrong_hive_do_not_invent_documents | Missing RecentDocs branch is explicit empty result |
| RD-16 | test_regf_versions_indexes_and_case_insensitive_path | All native REGF versions/indexes and case-insensitive paths |
| RD-17 | test_key_document_and_output_budgets | Key/document/output and inherited value-byte budgets |
| RD-18 | test_dirty_corrupt_truncated_hives_fail | Dirty/corrupt/truncated hives fail |
| RD-19 | test_repeated_renamed_sources_hashes_and_offsets | Renamed/repeated source hashes and physical nk/vk lineage |
| RD-20 | test_json_sqlite_current_schema_and_raw_metadata_roundtrip | JSON/SQLite current schema, raw MRU objects and Unicode round trip |
| RD-21 | test_cli_real_subprocess_strict_and_sqlite | Real subprocess CLI, SQLite output and strict warning |
| RD-22 | test_later_failure_atomic_and_outputs_protected | Later failure publishes nothing and existing evidence/output protected |
| RD-23 | test_only_acquired_hive_opened_and_changing_input_rejected | Only acquired hive opened and changing input rejected |
| RD-24 | test_mixed_browser_usb_recycle_and_recent_lineage | Browser/USB/Recycle Bin and RecentDocs source ordering |
| RD-25 | test_review_mru_mutations_do_not_escape_contract | 100 seeded MRU mutations retain records with valid/invalid status |
| RD-26 | test_review_large_unsigned_slot_and_case_insensitive_legacy | Maximum unsigned slot and case-insensitive legacy reference |
| RD-27 | test_review_sqlite_key_lineage_foreign_key_rejects_orphan | SQLite composite key lineage rejects orphan and leaves no file |

## Manual Review and Independent Check

| Priority | Reviewed risk / correction | Evidence |
| --- | --- | --- |
| High | Key last-write can be mistaken for every document's open time | Separate key and document collections; no per-document timestamps; RD-01 |
| High | Broken or ambiguous MRU can create false chronology | No ranks for missing/invalid/both controls; preserve raw controls and references; RD-04/07/08/09 |
| High | Opaque Shell Item bytes can be mistaken for a verified path | Keep tail raw, diagnose it and never open targets; RD-11/23 |
| Medium | Invalid text diagnostics lacked value-level attribution | Escape text with the physical value offset in its diagnostic; RD-13 |
| Medium | Unicode case-insensitive regex can accept non-ASCII lookalike letters | Restrict legacy letter matching to ASCII; RD-08/26 |
| Medium | Document records can lose parent-key lineage on SQLite export | Composite source/key foreign key plus unique parent IDs; RD-20/27 |
| Medium | Schema extension silently changes consumer expectations | Report/SQLite version 7 and bilingual migration notes; RD-20/24 |

A separate python-registry 1.3.1 check reads all four generated index layouts, exact MRUListEx slots/sentinel, an astral Unicode entry and its extension scope. It is a temporary validation dependency, not a package/test requirement or independent real-hive parity result. The reviewed implementation includes bounded source reads, REGF reuse, rank semantics, decoding, output atomicity, schema migration and documentation.

## Verification and Remaining Limits

Installed plaintrace 0.6.0 is smoke-tested outside the checkout with modern/legacy RecentDocs, JSON/SQLite current schema, composite key lineage and unchanged input hashes. Eleven EnScript portable checks, four generated references, bilingual documentation/test mappings, whitespace/source comparison and archive-only checks pass separately. Original EnScript/archive refs/manifests/tree/README and all 263 synthetic 2017 commits remain preserved. Archive-only checks require the local original backup ref and are not compilation or runtime checks.

No actual acquired NTUSER, Windows/Linux, Python 3.10, independent real-hive comparison, large-case performance or live acquisition validation was performed. Shell Item/PIDL decoding, nested scopes, Office/HWP/Adobe application MRUs, Recent-folder/LNK correlation, Jump Lists, deleted records, attribution and sessions are unsupported. Native REGF restrictions and existing artifact limitations remain documented. Key last-write and relative order are not exact document-open times or proof of use. EnCase compilation/execution remains unverified.
