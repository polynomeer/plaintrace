# USB Registry Tests and Code Review

**English** | [한국어](USB_REGISTRY_TESTS.ko.md)

Validated and manually reviewed on 2026-10-15 on macOS/Python 3.14. All 148 Python tests pass with the EVTX extra: 33 browser, 30 execution, 32 EVTX, 28 Recycle Bin, 25 USB registry. Without it, 140 execute and eight existing integrations skip. Registry tests require no new runtime/test dependency. See [usage and contracts](USB_REGISTRY_CLI.md). This is a self-review, not external approval.

## Reproduction and Fixtures

Synthetic REGF file headers, hbins, allocated/free cells, nk/vk records, li/lf/lh/ri indexes and inline/external values are independently assembled in temporary directories. Oracles use known Unicode strings, Select Current=2 and raw FILETIME with a known 100 ns remainder. No acquired hives/evidence or exports are committed. Tests execute the native reader, actual CLI subprocesses and JSON/SQLite exports. Resource-limit tests use small patched budgets rather than a large-case performance claim.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d174bc8c7f57aa5f91e0e3c87113e4af78ce3eb1 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## Executable Cases

| ID | Test method | Oracle / behavior |
| --- | --- | --- |
| USB-01 | test_active_controlset_and_device_identity | Select Current=2, parsed identity and last-write basis |
| USB-02 | test_property_filetime_meanings_raw_values_and_offsets | Four property meanings, exact ticks and physical lineage |
| USB-03 | test_usb_vid_pid_and_instance_not_physical_serial_claim | VID/PID and literal instance IDs, no serial claim |
| USB-04 | test_mounteddevices_kept_raw_without_drive_inference | MountedDevices raw bytes without drive assignment |
| USB-05 | test_software_and_ntuser_context_is_not_automatically_joined | SOFTWARE/NTUSER context without cross-hive identity joins |
| USB-06 | test_deviceclasses_context_not_usb_proof | DeviceClasses context is not proven USB connection |
| USB-07 | test_all_supported_index_layouts_and_regf_versions | li/lf/lh/ri indexes and REGF 1.3/1.4/1.5 |
| USB-08 | test_inline_dword_bigendian_qword_multisz_unknown | Inline DWORD, big-endian, QWORD, MULTI_SZ and opaque types |
| USB-09 | test_missing_select_or_bad_current_never_falls_back | Missing/wrong Select never guesses a control set |
| USB-10 | test_empty_branches_and_absent_properties_diagnosed | Empty/missing branches and absent property diagnostics |
| USB-11 | test_malformed_property_type_size_and_ambiguity_retained | Ambiguous/wrong-type/wrong-size property retains raw values |
| USB-12 | test_zero_overflow_property_and_invalid_text_preserved | Zero/overflow times and undecodable UTF-16 |
| USB-13 | test_dirty_checksum_version_and_extent_fail | Dirty/checksum/version/type/format/extent rejection |
| USB-14 | test_cell_reference_free_interior_bad_size_and_index_cycle | Allocated boundaries, malformed cells and RI cycles |
| USB-15 | test_duplicate_names_parent_alias_and_wrong_record_rejected | Duplicate names, parent mismatch and aliases rejected |
| USB-16 | test_counts_value_size_and_output_limits | Cell/item/value/row/output budgets and segmented-value limit |
| USB-17 | test_truncations_and_seeded_mutations_are_contract_errors | Boundary truncations and 100 seeded mutations |
| USB-18 | test_unicode_keys_case_insensitive_paths_and_value_names | Unicode keys and case-insensitive lookup |
| USB-19 | test_source_hashes_roles_and_json_sqlite_schema_five | Repeated source hashes, JSON/SQLite schema 6 and foreign keys |
| USB-20 | test_cli_subprocess_strict_and_multiple_roles | Real CLI subprocess with role provenance and strict warnings |
| USB-21 | test_later_bad_input_atomic_and_existing_output_protected | Fatal later hive is atomic and source cannot be overwritten |
| USB-22 | test_stable_read_and_no_logs_or_live_registry_access | Only acquired hive is opened; changed input rejected |
| USB-23 | test_review_inline_length_key_flags_and_name_corruption | Inline length/key flags/names/duplicate references and invalid values |
| USB-24 | test_review_header_size_cap_multibin_and_unknown_role | Input cap, multiple hbins and unknown-role rejection |
| USB-25 | test_review_mixed_existing_artifacts_and_usb_source_order | Existing browser/Recycle Bin inputs mix with USB lineage |

## Review Findings and Independent Comparison

| Priority | Reviewed risk / correction | Evidence |
| --- | --- | --- |
| High | Assuming ControlSet001 selects stale devices | Validate Select/Current and selected control set; USB-01/09 |
| High | Relabeling key last-write as connection history creates false times | Separate key metadata and typed property FILETIMEs; USB-02/11/12 |
| High | Corrupt counts/references, RI cycles or shared oversized values cause uncontrolled parsing | Allocated-cell boundaries, view buffers, cycles/count/name/data budgets, early duplicate-reference rejection; USB-14/15/16/23 |
| Medium | Repeated path scans can multiply work across device properties | Cache case-insensitive child maps; all index/property tests pass |
| Medium | Context key names can be mistaken for device IDs | Leave device/instance IDs null outside Enum observations; USB-04/05/06 |
| Medium | Cross-hive substring joins fabricate drive/user/serial associations | Preserve separate observations and explicit source roles; USB-03/05/19/20 |
| Medium | Schema extension silently breaks consumers | Explicit JSON/SQLite version 5 and bilingual migration notices; USB-19/25 |

In a separate manual check, python-registry 1.3.1 independently opened all four generated index layouts and matched Select Current=2, Unicode FriendlyName and exact raw arrival FILETIME. Its datetime rounded the 100 ns remainder to microseconds; this implementation deliberately truncates with integer arithmetic and retains raw ticks. That library was installed only in the temporary validation environment, is not a package/test dependency, and does not establish independent real-hive parity. Microsoft devpkey.h was checked to avoid reversing 0064 installation and 0065 first-installation labels found in older examples.

## Verification and Remaining Limits

Installed plaintrace 0.5.0 is smoke-tested outside the checkout using SYSTEM/SOFTWARE/NTUSER, JSON/SQLite schema 5, property values, source offsets and unchanged input hashes. Eleven EnScript portable checks, four generated source references, bilingual documentation/test mappings, whitespace/source comparison and archive-only verification pass separately. Archive refs, thirteen original EnScript sources, original README/tree and 263 synthetic 2017 commits remain preserved; archive verification needs the local original backup ref and is not compilation.

No actual acquired hive, Windows/Linux, Python 3.10, independent real-hive comparison, large-case benchmark or live acquisition validation was performed. Dirty/log replay, segmented big data, unsupported REGF versions, volatile/link/deleted/slack structures and alternate device property storage remain unsupported. No automatic drive/volume/device/user joining or complete USB session timeline is claimed. Key metadata is not a connection timestamp; latest stored arrival/removal values are not exhaustive history. Existing browser/LNK/Prefetch/EVTX/Recycle Bin limitations and unverified EnCase compilation/execution remain documented.

## RecentDocs Regression Run (2026-10-15)

Current full discovery passes 175 tests: previous 148 plus 27 RecentDocs cases. Without the EVTX extra, 167 execute and eight existing integrations skip. Current export assertions use schema 6; earlier validation counts/schema introductions remain historical records. See [RecentDocs reproduction and review](RECENT_DOCS_TESTS.md).
