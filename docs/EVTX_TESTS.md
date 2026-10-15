# EVTX Tests and Code Review

**English** | [한국어](EVTX_TESTS.ko.md)

Validated and manually reviewed on 2026-10-15 on macOS/Python 3.14 with python-evtx 0.8.1. All 95 Python cases pass without skips: 33 browser, 30 LNK/Prefetch, 32 EVTX. This records a self-review and synthetic tests, not an external review or acquired-file certification. See [the EVTX contract](EVTX_CLI.md).

## Reproduction and Fixture Scope

Install the optional extra before discovery. Standard-library-only discovery passes with seven integration cases explicitly skipped; it is not a full EVTX result. Fixtures are independently assembled file/chunk/record headers, CRCs, literal BinXML template nodes, shared templates and Unicode WSTRING substitutions, created in temporary directories. XML oracles use known field values and 100 ns ticks. No real evidence or dependency source is committed. Full tests invoke the real decoder subprocess and real CLI, not just a mock XML provider. Failure/timeout/IPC boundary cases additionally use focused mocks and smaller limits; the timeout failure path is mocked, not a measured large-log benchmark.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 9f32324141810b257d4f680e84c849c013543900 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| EV-01 | test_common_fields_and_logon_details | System fields, UTC, raw 100 ns ticks and logon details |
| EV-02 | test_security_logoff_variants_and_system_accounts_preserved | 4634/4647 actions and retained system accounts |
| EV-03 | test_provider_and_channel_qualify_classification | Provider/channel-qualified logon and power classification |
| EV-04 | test_driver_frameworks_never_infers_usb_state | DriverFrameworks data never asserts USB state |
| EV-05 | test_repeated_unnamed_nested_data_and_user_data_preserved | Repeated/unnamed/empty EventData and namespaced UserData retained |
| EV-06 | test_unknown_and_namespace_free_events_retained | Unknown IDs and namespace-free Event accepted |
| EV-07 | test_invalid_and_missing_time_and_numeric_fields | Invalid/missing time and numeric values diagnosed |
| EV-08 | test_time_zone_precision_overflow_and_mismatch | Timezone/7-digit precision, overflow and XML/container mismatches |
| EV-09 | test_unsigned_record_ids_remain_text_in_sqlite | Unsigned 64-bit IDs preserved as SQLite text; current version 6 and FKs |
| EV-10 | test_xml_dtd_entities_roots_and_duplicate_system_rejected | DTD/entities, foreign root, missing/duplicate singleton rejection |
| EV-11 | test_xml_size_depth_and_node_limits | Per-record XML byte and depth bounds |
| EV-12 | test_container_versions_empty_and_dirty | 3.1/3.2 envelopes, empty chunks and dirty diagnostic |
| EV-13 | test_container_header_checksums_count_version_and_alignment | File signature/layout/version/flags/count/checksum/alignment failures |
| EV-14 | test_chunk_and_record_envelope_corruption_rejected | Chunk bounds/CRC, record signatures/sizes/trailers/last-offset failures |
| EV-15 | test_inactive_chunks_diagnosed_without_carving | Extra physical chunks omitted with diagnostic |
| EV-16 | test_record_and_input_limits_and_changing_file | Count/read caps and changed-file rejection |
| EV-17 | test_missing_or_wrong_dependency_is_actionable | Missing/wrong optional decoder dependency rejected explicitly |
| EV-18 | test_worker_timeout_and_exit_failure_abort | Timeout/worker failure yields fatal contract error |
| EV-19 | test_decoder_lineage_counts_and_output_caps | Decoder offset/count/JSON checks before accepting output |
| EV-20 | test_mutated_and_truncated_envelopes_only_raise_contract_errors | Boundary truncations and 100 seeded mutations produce contract errors |
| EV-21 | test_real_decoder_synthetic_binxml_end_to_end | Actual decoder/adapter: two synthetic records, source bytes/hash retained |
| EV-22 | test_cli_subprocess_mixed_inputs_json_sqlite_and_no_overwrite | Real CLI subprocess: all four input kinds, JSON/SQLite and no overwrite |
| EV-23 | test_multiple_logs_duplicate_ids_and_dirty_strict | Multiple logs retain duplicate IDs under separate source IDs; strict warning |
| EV-24 | test_empty_evtx_and_corrupt_binxml_fatal_atomicity | Actual decoder: empty source success, bad BinXML aborts whole output |
| EV-25 | test_review_shared_template_and_unicode_substitutions | Shared template and Unicode WSTRING substitution; duplicate ID warning |
| EV-26 | test_review_multiple_chunks_and_container_32 | Actual decoder: multiple physical chunks and version 3.2 envelope |
| EV-27 | test_review_non_data_nodes_cannot_supply_normalized_identity | Binary/foreign-namespace elements cannot spoof normalized user |
| EV-28 | test_review_missing_ids_and_overflow_filetime | Missing XML IDs and overflowing envelope time diagnosed; raw ticks retained |
| EV-29 | test_review_worker_and_parent_decoded_size_limits | Worker/parent reject excessive IPC/XML before report publication |
| EV-30 | test_review_xml_node_limit_and_integer_lexical_bounds | XML node cap and malformed/huge unsigned-ID text rejection |
| EV-31 | test_review_missing_dependency_cli_publishes_nothing | Missing extra in CLI leaves no output or stdout payload |
| EV-32 | test_review_binxml_invalid_chunk_reference_is_fatal | Actual decoder rejects an out-of-chunk template reference |

## Code Review Findings

| Priority | Finding | Resolution / evidence |
| --- | --- | --- |
| High | Event ID alone can misclassify another provider's event | Require provider and channel for logon/power; EV-03 |
| High | BinXML shared pointers, cycles and expansion need bounded failure | Strict envelope checks, chunk-local decoder buffers, timed subprocess, bounded IPC/XML and fatal exceptions; EV-13/14/18/19/29/32 |
| High | Non-Data or foreign-namespace elements can spoof normalized identity | Normalize only Data in the accepted namespace; preserve other XML; EV-27 |
| Medium | Unsigned 64-bit record IDs overflow SQLite signed integers | Decimal text and independent source offsets; EV-09/23/25 |
| Medium | Calling envelope FILETIME a write time overstates semantics | Separate container_time from XML TimeCreated, preserve raw values/mismatch warning; EV-01/08/28 |
| Medium | Duplicate data/session IDs and USB count inference can fabricate conclusions | Null ambiguous normalized fields, retain all offsets/accounts, no session pairing or USB-state inference; EV-02/04/05/25 |
| Medium | Optional dependency can silently skip crucial tests | Exact pin, actionable error and documented full-extra run versus seven skips; EV-17/31 |
| Medium | Adding events silently changes consumer expectations | Explicit schema version 3 for all reports and migration notes; EV-09/22 |

## Validation and Remaining Limits

The full suite runs in an isolated environment with the actual optional decoder. A second run without the decoder executes 88 tests and explicitly skips seven. Package installation/console execution is smoke-tested outside the checkout. Existing eleven EnScript portable checks, four generated references, bilingual documentation/test mappings, byte comparison and archive-only verification pass separately; none is EnCase runtime validation. The archive checker needs the original local backup ref.

Generated literal/shared-template/string-substitution fixtures exercise the decoder but do not establish compatibility with real Windows template caches, conditional substitutions, typed/array substitutions, uncommon BinXML tokens or all providers. No acquired EVTX, Windows/Linux, Python 3.10, independent parser parity, large-log performance or live acquisition testing was performed. CRC enforcement deliberately rejects corrupt/no-checksum variants rather than offering recovery. Per-file limits can reject valid large logs; the timed worker is not a memory sandbox. Deleted/slack recovery, message DLL rendering, EVT, session correlation and USB registry/state correlation are unsupported. The original browser/LNK/Prefetch limitations and unverified Windows/EnCase execution remain documented. Synthetic tests are not casework acceptance.

## Recycle Bin Regression Run (2026-10-15)

The current suite passes 123 cases with the optional EVTX extra: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin. Without it, 115 execute and eight explicitly skip. Existing export assertions now check schema 4. See [reproduction and review](RECYCLE_BIN_TESTS.md); earlier dates/counts remain historical validation records.

## USB Registry Regression Run (2026-10-15)

Current full discovery passes 148 cases: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin and 25 USB registry. Without the EVTX extra, 140 execute and eight skip. Current export assertions use schema 5; earlier counts/schema introductions are historical records. See [USB reproduction and review](USB_REGISTRY_TESTS.md).

## RecentDocs Regression Run (2026-10-15)

Current full discovery passes 175 tests: previous 148 plus 27 RecentDocs cases. Without the EVTX extra, 167 execute and eight existing integrations skip. Current export assertions use schema 6; earlier validation counts/schema introductions remain historical records. See [RecentDocs reproduction and review](RECENT_DOCS_TESTS.md).
