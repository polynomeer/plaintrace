# USB Registry Python CLI

**English** | [한국어](USB_REGISTRY_CLI.ko.md)

The current package is 0.14.0 and every output uses schema 14. Earlier version introductions/test results below describe their release context; see [the system information extension](SYSTEM_INFO_CLI.md) for the current contract.

Implemented on 2026-10-15 on `codex/python-usb-registry`, based on `d174bc8c7f57aa5f91e0e3c87113e4af78ce3eb1`. EnScript files, archive refs/manifests and 263 reconstructed 2017 commits are preserved. Package 0.5.0/report schema 5 extends the independent Python implementation.

## Usage and Acquisition

Python 3.10+ is declared; validation used macOS/Python 3.14. Registry parsing uses the standard library, with no new runtime dependency. Supply stable acquired binary REGF hives with explicit roles; filenames are not used for detection. Each role flag is repeatable and independent. Mixing roles or machines never automatically joins device identities. Source ordering is existing browser/LNK/Prefetch/EVTX/Recycle Bin inputs, then SYSTEM, SOFTWARE, NTUSER groups in supplied order within each group. The optional EVTX extra is required only for EVTX inputs/full integration discovery.

```sh
python3 -m plaintrace --usb-system /path/to/SYSTEM --output usb.json
python3 -m plaintrace --usb-system /path/to/SYSTEM --usb-software /path/to/SOFTWARE --usb-ntuser /path/to/NTUSER.DAT --format sqlite --output usb.sqlite
python3 -m plaintrace --usb-system /case-a/SYSTEM --usb-system /case-b/SYSTEM --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --usb-system /path/to/SYSTEM
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --usb-system C:\acquired\SYSTEM --output usb.json
```

Use acquired, clean/synchronized hives, not live registry files. Reads are bounded and hashed before/read/after; only supplied files are opened. LOG1/LOG2, transaction files and live Windows APIs are not accessed. Dirty sequence numbers are fatal and no log replay or repair is attempted. A clean sequence/checksum does not establish complete acquisition or authenticity. Output rules, strict warning exit 1, fatal exit 2, all-input atomic publication and no-overwrite/source-sidecar protection are inherited from [the common CLI](PYTHON_CLI.md).

## Observations and Timestamp Basis

SYSTEM requires a unique DWORD Select/Current in 1..999 and the corresponding ControlSet. There is no ControlSet001 fallback. Names are looked up case-insensitively; ambiguous names fail. Only the selected control set is interpreted. Missing optional branches/property slots produce explicit diagnostics rather than invented times.

| Observation kind | Source and interpretation |
| --- | --- |
| usbstor | SYSTEM selected ControlSet Enum/USBSTOR device/instance keys; literal instance ID, vendor/product/revision tokens and FriendlyName |
| usb | SYSTEM selected ControlSet Enum/USB device/instance keys; VID/PID tokens and literal instance IDs; not restricted to storage |
| device_interface | Direct children of disk/volume DeviceClasses GUIDs; contextual key/value observations, not proven USB identity |
| mounted_devices | SYSTEM MountedDevices key and raw values; no automatic drive/volume association |
| portable_device | SOFTWARE Microsoft/Windows Portable Devices/Devices direct children; contextual FriendlyName and values |
| mount_point | NTUSER Software/Microsoft/Windows/CurrentVersion/Explorer/MountPoints2 direct children; no user/SID attribution |

All paths in output use literal registry backslashes. Context branches can include non-USB devices. They are retained without substring joins, guessed drive letters, hardware serial-number claims, cross-hive identity correlation or user ownership claims. No EVTX pairing or session reconstruction is performed. Registry state is a snapshot; it is not a complete ordered list of every connection.

`key_last_written` and `key_last_write_raw` are the key's last-write metadata, not first connection, first connection after boot, last connection or per-value modification times. Device times are separately read under device/instance Properties/{83da6326-97a6-4088-9453-a1923f573b29}. Supported property keys use a unique default or 00000000 value of type REG_BINARY or 16, exactly eight bytes. Ambiguous/malformed values remain raw and have null interpreted time. Missing slots are omitted with a warning. Deeper alternate property encodings are unsupported.

| Property key | Meaning |
| --- | --- |
| 0064 | install_date; installation/driver update timestamp, not necessarily first physical connection |
| 0065 | first_install_date; first installation of this device instance on this system |
| 0066 | last_arrival_date; latest stored device arrival |
| 0067 | last_removal_date; latest stored device removal |

Raw FILETIMEs remain unsigned decimal text; UTC displays use integer truncation from 100 ns to microseconds, without fixed timezone adjustments. Zero times are null, overflow is diagnosed with raw ticks retained. Installation/arrival/removal properties can be absent or stale and do not establish a complete session, current connected state, user intent or physical device identity. Unlike the original EnScript, key last-write times are never relabeled as connection times and ControlSet001/string-substring assumptions are not reused.

## REGF Reader and Limits

The native reader checks header signature/checksum, matching sequences, primary hive type, direct-memory format, versions 1.3/1.4/1.5 and exact declared bin extent. It indexes allocated cell boundaries across hbins and validates bin signatures/offsets, cell alignment/sizes, nk/vk references, parent links, counts, unique names, li/lf/lh/ri indexes and index cycles. Names support compressed Latin-1 or UTF-16LE; invalid names are fatal. Symbolic-link keys and volatile subkeys are rejected when accessed. Free cells are not traversed. Security/class records, index hashes/hints and unrelated data are not semantically validated.

Limits per hive: 64 MiB input; 250000 scanned allocated/free cells; 100000 accessed keys/index items/values; 4096 values per accessed key; 16344 bytes per accessed value; 16 MiB aggregate accessed value data/name bytes; 10000 emitted observations; 32 MiB serialized observation JSON. Cell buffers use views to avoid repeatedly copying large cells, and case-insensitive child indexes cache repeated path lookups. This is bounded parsing, not a memory sandbox; output-size checks occur after allocation and combined reports stay in memory. Limits may reject valid large hives. No native subprocess timeout is implemented.

Values retain name, type, physical value-cell offset and exact data hex. REG_SZ/EXPAND_SZ/MULTI_SZ decode UTF-16 without environment expansion; numeric DWORD/big-endian DWORD/QWORD values become decimal text. Unsupported types remain raw. Invalid strings/numeric widths are diagnosed and remain raw. No value-level timestamps are invented. Segmented big-data/db values over the direct-value limit, REGF 1.6/older layouts, transaction-log recovery, deleted-cell carving, hive slack, text .reg imports, registry links and additional USB correlation structures are unsupported. Accessed unsupported structures fail the complete report rather than silently dropping input.

## Current Schema and Code Structure

Every report now has JSON format_version 10 and SQLite user_version 10, including reports with no USB hive. Version 5 adds usb_registry and its count; prior collections retain field meanings. Existing report versions 1–5 are never rewritten or migrated. Consumers must recognize version 10. Sources use source_kind usb_registry and schema_family registry_system/registry_software/registry_ntuser, with acquired-file sha256 and null browser/database/WAL fields. record_id is the physical nk cell-header offset, scoped by source_id.

| JSON usb_registry field | Meaning |
| --- | --- |
| source_id, record_id, hive_role, observation_kind | Input lineage, physical record identity and interpretation scope |
| key_path, key_last_written, key_last_write_raw | Registry path, separate UTC last-write display and raw ticks |
| control_set, device_id, instance_id | Selected control set and literal Enum identifiers; context rows leave device IDs null |
| vendor, product, revision, vid, pid, friendly_name | Explicit tokens/REG_SZ FriendlyName, never a hardware identity guarantee |
| device_times | Property ID/meaning, property key path/offset, raw ticks, UTC time and raw property values |
| values | Ordered value_offset/name/type/data_hex/decoded objects; SQLite column is named values_json to avoid a SQL keyword |

Objects/arrays are native JSON and JSON text in SQLite; source foreign keys and bound inserts remain enforced. [registry_hive.py](../plaintrace/registry_hive.py) implements bounded REGF access; [usb_registry.py](../plaintrace/usb_registry.py) selects USB/context branches and timestamp semantics. CLI, source assembly, report model and exporters add role flags, provenance and schema 10.

## Validation and Remaining Limits

[Tests and manual review](USB_REGISTRY_TESTS.md) map 25 new tests. All 148 Python cases pass with the EVTX extra; without it 140 execute and eight existing integrations skip. Generated hives cover all supported index types, compressed/Unicode names, inline/external values, property timestamps, dirty/corrupt/cyclic inputs, limits, source preservation and actual CLI JSON/SQLite behavior. Independent python-registry 1.3.1 also reads the synthetic indexes/selected values; it is a temporary verification dependency, not a package dependency or real-hive parity certification.

Actual acquired SYSTEM/SOFTWARE/NTUSER hives across Windows versions, Windows/Linux, Python 3.10, large-case performance, live acquisition, independent real-hive comparisons and EnCase compilation/execution remain unvalidated. Existing browser/LNK/Prefetch/EVTX/Recycle Bin unsupported structures and host limitations remain documented. No exhaustive USB connection history, drive mapping, session correlation or evidence completeness is claimed.

## References

Interpretation follows [libregf working REGF specification](https://github.com/libyal/libregf/blob/main/documentation/Windows%20NT%20Registry%20File%20%28REGF%29%20format.asciidoc), [Microsoft devpkey.h property IDs](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/devpkey.h), [Microsoft FirstInstallDate semantics](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-firstinstalldate) and [RegRipper USBSTOR storage-layout examples](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/usbstor.pl). Property labels follow the Microsoft IDs where older forensic examples reverse installation labels. No dependency source is vendored. See [archived source analysis](ANALYSIS.md).

## RecentDocs Extension

Package 0.6.0 introduced schema 6 and recent_doc_keys/recent_docs. Earlier extension introductions above remain historical context; current consumers must support schema 14. See [RecentDocs contracts](RECENT_DOCS_CLI.md) and [tests/review](RECENT_DOCS_TESTS.md). Existing fields keep their meanings.
