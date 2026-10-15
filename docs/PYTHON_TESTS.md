# Python CLI Test Plan and Results

**English** | [한국어](PYTHON_TESTS.ko.md)

Validated on 2026-10-14 on macOS with Python 3.14. Tests exercise actual Python adapters/CLI and generated synthetic SQLite fixtures, not EnScript. No real evidence or generated databases are committed. See [the implementation contract](PYTHON_CLI.md).

## Reproduction

Run from the checkout root. No third-party runtime/test libraries are required. The archive checker additionally needs the original local backup ref; this is separate from the portable Python tests. The final comparison verifies all EnScript files and historical manifests against the branch base.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code bb476180453c76f7d38e5b6a9f1f025ad2273ce0 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

All 33 cases passed. Fixtures use explicitly known UTC times and expected strings; Firefox annotation IDs/order are intentionally unrelated to the EnScript assumptions. Temporary test data is removed after each case.

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| PY-01 | test_chromium_visits_keywords_and_downloads | Individual times, repeated UTF-8 query terms, stored terms and redirect chain |
| PY-02 | test_firefox_correlates_annotation_names_and_place | Arbitrary annotation IDs/order, JSON metadata and download event time |
| PY-03 | test_url_summary_is_not_a_visit | Summary fallback explicitly distinguished from visits |
| PY-04 | test_missing_downloads_are_diagnosed | Unavailable downloads produce a diagnostic |
| PY-05 | test_firefox_malformed_metadata_and_duplicate_annotations | Malformed latest metadata retained; duplicate annotation warning |
| PY-06 | test_iso_firefox_endtime_and_invalid_numeric_metadata | Timezone-aware ISO conversion; invalid numeric metadata rejected |
| PY-07 | test_invalid_timestamp_and_query_preserve_records | Out-of-range time and invalid UTF-8 query retain the visit |
| PY-08 | test_unknown_empty_and_corrupt_databases_fail_without_output | Unknown/corrupt/missing inputs do not publish reports |
| PY-09 | test_multiple_profiles_and_browser_label_conflict | Mixed family provenance and incompatible explicit label rejection |
| PY-10 | test_json_and_sqlite_roundtrip_and_no_overwrite | Unicode/string values, foreign keys, output refusal and evidence bytes |
| PY-11 | test_wal_committed_records_and_input_bytes_unchanged | Read committed WAL data without changing DB/WAL/SHM |
| PY-12 | test_changed_snapshot_and_rollback_journal_rejected | Copy mismatch and nonempty rollback journal rejection |
| PY-13 | test_cli_stdout_strict_and_sqlite_output | Stdout JSON, strict warning exit and SQLite output; subprocess execution |
| PY-14 | test_minimal_chromium_schema_without_optional_fields | Missing optional columns, Opera label and literal filesystem path |
| PY-15 | test_firefox_summary_missing_downloads_and_incomplete_annotation | Firefox summary, annotation proxy and absent metadata/tables |
| PY-16 | test_orphan_visits_and_annotation_urls_are_not_silently_dropped | Orphan rows retained with raw Firefox transition |
| PY-17 | test_empty_supported_database_is_successful | Supported empty schema succeeds without fabricated rows |
| PY-18 | test_malformed_required_and_ambiguous_schemas_are_rejected | Malformed required columns and mixed schema ambiguity |
| PY-19 | test_fragment_and_literal_bad_escape_query | Fragment exclusion, empty terms and literal malformed escapes |
| PY-20 | test_sqlite_cli_requires_destination | SQLite output requires a destination before input is opened |
| PY-21 | test_output_race_preserves_other_writer | Another writer wins output publication without replacement |
| PY-22 | test_all_or_nothing_multiple_inputs | Later input failure publishes no partial report |
| PY-23 | test_output_publication_failure_leaves_no_report_or_temp | Unsupported hard links clean up temporary output |
| PY-24 | test_epoch_precision_and_unknown_values | Epoch offsets, microsecond precision, unknown and invalid times |
| PY-25 | test_invalid_unrelated_query_does_not_drop_valid_terms | Malformed unrelated/recognized fields do not discard valid neighboring terms |
| PY-26 | test_dangling_output_symlink_is_not_followed | Dangling final output symlink remains untouched |
| PY-27 | test_existing_output_sqlite_sidecars_are_preserved | Existing output WAL/SHM/journal files block publication |
| PY-28 | test_stdout_serialization_failure_has_no_partial_json | Binary/nonfinite JSON values fail before stdout emission |
| PY-29 | test_browser_views_are_not_accepted_as_native_tables | Canonical browser names must identify real tables |
| PY-30 | test_orphan_stored_keyword_is_diagnosed | Unmatched stored term URL is diagnosed and retained |
| PY-31 | test_download_lineage_and_inconsistent_times | Selected annotation/event IDs exported; reversed time ordering diagnosed |
| PY-32 | test_unsupported_export_format_fails_explicitly | Unsupported API export format cannot silently select JSON |
| PY-33 | test_iso_timezone_overflow_is_diagnostic_not_exception | ISO timezone normalization overflow returns a diagnostic |

## Additional Checks

A wheel was built and installed in an isolated temporary virtual environment; the installed console command reports version 0.2.0 and is smoke-tested outside the checkout. The existing eleven EnScript portable contract tests, generated references, bilingual documentation checks and historical archive-only verification remain separate checks. Python package build artifacts are ignored.

## Remaining Validation

Test real acquired Chrome/Opera/Firefox profiles across versions and platforms, very large profiles, browser shutdown/acquisition workflows and unusual Unicode/metadata/schema variants before relying on casework results. Hash-based copy stability is not atomic acquisition; the tests do not prove evidence completeness or detect all live writer races. EnCase compilation/execution remains outstanding. The Python tests neither run the original EnScript nor establish parity with its host API behavior.

See [the code review](PYTHON_REVIEW.md) for follow-up fixes and remaining limits.

## EVTX Regression Run (2026-10-15)

The EVTX port validation ran 95 cases: 33 browser, 30 execution and 32 EVTX. Install the optional extra to run all integrations; without it seven EVTX cases explicitly skip. Existing export regressions now assert schema version 3. See [EVTX reproduction and review](EVTX_TESTS.md); earlier validation dates above remain historical records.

## Recycle Bin Regression Run (2026-10-15)

The current suite passes 123 cases with the optional EVTX extra: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin. Without it, 115 execute and eight explicitly skip. Existing export assertions now check schema 4. See [reproduction and review](RECYCLE_BIN_TESTS.md); earlier dates/counts remain historical validation records.

## USB Registry Regression Run (2026-10-15)

Current full discovery passes 148 cases: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin and 25 USB registry. Without the EVTX extra, 140 execute and eight skip. Current export assertions use schema 5; earlier counts/schema introductions are historical records. See [USB reproduction and review](USB_REGISTRY_TESTS.md).

## RecentDocs Regression Run (2026-10-15)

Current full discovery passes 175 tests: previous 148 plus 27 RecentDocs cases. Without the EVTX extra, 167 execute and eight existing integrations skip. Current export assertions use schema 6; earlier validation counts/schema introductions remain historical records. See [RecentDocs reproduction and review](RECENT_DOCS_TESTS.md).
