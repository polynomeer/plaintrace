# Windows EVTX Python CLI

**English** | [한국어](EVTX_CLI.ko.md)

The current package is 0.12.0 and every output uses schema 12. Earlier version introductions/test results below describe their release context; see [the RunMRU extension](RUN_MRU_CLI.md) for the current contract.

Implemented on 2026-10-15 on `codex/python-evtx`, based on merged commit `9f32324141810b257d4f680e84c849c013543900`. All thirteen EnScript files and historical manifests remain byte-identical to the branch base. The archive tag and 263 reconstructed 2017 commits are preserved. Version `0.3.0` extends the independent Python port; it does not run EnScript.

## Install and Run

Python 3.10+ is declared; this workspace tests macOS/Python 3.14. Browser/LNK/Prefetch parsing still uses the standard library. EVTX additionally requires the optional, exactly pinned `python-evtx==0.8.1` decoder; its installation also installs hexdump. No third-party source is vendored. Install the extra in a virtual environment. Missing or different decoder versions fail with an actionable error and no report publication.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/plaintrace --evtx /path/to/Security.evtx --output events.json
.venv/bin/plaintrace --evtx /path/to/System.evtx --evtx /path/to/Security.evtx --format sqlite --output events.sqlite
.venv/bin/plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --evtx /path/to/Security.evtx --strict
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install '.[evtx]'
.venv\Scripts\plaintrace.exe --evtx C:\acquired\Security.evtx --output events.json
```

Repeat `--evtx` for multiple acquired files. At least one of `--input`, `--lnk`, `--prefetch`, `--evtx`, `--recycle-bin` is required. Browser and LNK codepage options apply only to their existing inputs. JSON defaults to stdout; SQLite requires `--output`. Existing files/SQLite sidecars and input paths cannot be overwritten. Fatal errors abort all supplied inputs before publication; warnings appear in the report and stderr, and `--strict` returns 1 after producing a report. See [shared output and exit rules](PYTHON_CLI.md).

## Acquisition, Container and Decoder Boundaries

Analyze stable acquired files, not live Windows logs. Original files are read only and hashed before/read/after. The captured bytes are decoded from a private temporary copy that is removed after use, including on failure. SHA-256 identifies source bytes; stability checks do not establish atomic acquisition, completeness or chain of custody.

Supported envelopes are EVTX 3.1/3.2 with a 4096-byte file header and 65536-byte chunks. Before BinXML decoding, Plaintrace validates header signatures/layout, declared chunk count/alignment, file/chunk/data CRC32, free-space bounds, allocated record signatures, aligned sizes, matching trailing sizes and last-record offsets. Unsupported flags, malformed envelopes or checksum failures are fatal. CRC checks cannot establish authenticity or detect deliberate edits with recomputed CRCs. Dirty files with valid envelopes produce a warning; records/chunks omitted by a dirty header are not recovered. Physical chunks beyond the declared count are omitted with a warning.

Each EVTX input is limited to 64 MiB and 100000 allocated records. A separate decoder subprocess has a 60-second timeout per file, 1 MiB of UTF-8 rendered XML per record, and 32 MiB of JSONL output per file. BinXML operates on one chunk buffer at a time, so references cannot read another chunk. Parent-side decoding checks output size, count and source offsets again. XML rejects DTD/entity declarations, unsupported roots/namespaces, duplicate singleton fields, more than 10000 nodes or depth greater than 64. Standard Windows Event XML namespaces and namespace-free Event documents are accepted. These are bounded outer interfaces, not complete validation of all BinXML internals or an operating-system security sandbox. The dependency can allocate memory before an XML-size check; a hard memory ceiling is not implemented. Large valid logs may exceed the limits/timeout. Combined reports reside in memory, and limits are per input rather than an aggregate report budget.

Only declared chunks and allocated records are read in physical file order. This is not a sort by time or logical ring-buffer order. No deleted-record/slack carving, repair, resynchronization, EVT parsing, evidence-image extraction, live Windows API access, provider-DLL message rendering or external XML import is implemented. Decoder exceptions are fatal rather than silently dropping records. Unusual BinXML templates/types may fail; universal Windows-version/provider compatibility is not claimed.

## Interpretation and Original Behavior

All decoded events are retained, including unknown providers/IDs and system accounts. Names, Unicode, duplicates, unnamed values, EventData XML and UserData XML remain available. Normalized logon values use only Data elements in the accepted event namespace; duplicates leave a normalized field null with a warning, rather than selecting a guessed value. Provider/channel names are literal matches, not filename guesses.

| Provider / channel / ID | Category and action |
| --- | --- |
| Microsoft-Windows-Security-Auditing / Security / 4624 | logon / logon |
| Microsoft-Windows-Security-Auditing / Security / 4634 | logon / logoff |
| Microsoft-Windows-Security-Auditing / Security / 4647 | logon / user_initiated_logoff |
| Microsoft-Windows-Kernel-General / System / 12 | power / os_started |
| Microsoft-Windows-Kernel-General / System / 13 | power / os_shutdown_started |
| Microsoft-Windows-DriverFrameworks-UserMode / any channel or ID | driver_frameworks / null |
| Other combinations | event / null |

Logon details preserve TargetUserName, TargetDomainName, TargetUserSid, TargetLogonId, LogonType, IpAddress and LogonGuid as strings; absent values are null. The System security SID is separate from TargetUserSid. Event IDs are provider-specific, so matching an ID alone does not classify an event. An OS shutdown-start event is not proof of completed shutdown. Logon IDs are not globally unique and no automatic session pairing is attempted.

Unlike the EnScript, the port does not exclude NT AUTHORITY accounts, apply a fixed timezone adjustment, extract fields by XML substring position, or infer USB mounted/unmounted state from counts of equal-time events. DriverFrameworks events alone are not asserted to represent USB connections. No registry correlation, drive-letter mapping, device identity synthesis or physical device state is inferred. This is an explicit analysis contract, not verified EnCase output parity.

## Time and Lineage

The record envelope FILETIME is retained as decimal `container_filetime_raw` and displayed as UTC `container_time`, truncating 100 ns ticks to microseconds; it is not an independently established write time. XML TimeCreated/SystemTime is retained as `time_created_raw` and separately normalized to UTC `created_at` with an explicit timezone and up to seven fractional digits. The decoder may already reduce timestamp precision while rendering BinXML; rendered XML is not original on-disk text. Exact envelope ticks remain available. Zero envelope times are null; invalid/overflow times are diagnosed. XML/container times that differ at microsecond precision produce a warning; neither silently overrides the other.

`record_id` is the decimal byte offset within its source file, scoped by `source_id`. `event_record_id` is XML EventRecordID; `container_record_id` is the unsigned envelope ID. Both are decimal text to preserve values above SQLite's signed integer range. Missing/invalid XML identities are null and diagnosed. Mismatches and repeated envelope IDs are diagnosed while distinct source offsets remain separate. Duplicate IDs across separately supplied sources are not deduplicated.

## Current Output and Architecture

JSON `format_version` and SQLite `user_version` are 10 for every report, including browser-only reports. Version 3 introduced `events` and its count, while retaining version-2 browser/LNK/Prefetch fields. Sources use `source_kind` and `schema_family` evtx, full-file `sha256`, and null browser/database/WAL fields. Existing version-1/2/3 files are never migrated or rewritten; consumers must explicitly support version 10. Version 4 adds recycle_bin; see [the Recycle Bin contract](RECYCLE_BIN_CLI.md). Arrays/objects below are native JSON and JSON text in SQLite. Source foreign keys and bound inserts remain enforced.

| Event fields | Meaning |
| --- | --- |
| source_id, record_id, chunk_index, record_offset | Input and physical record lineage; chunk index is zero-based |
| container_record_id, container_filetime_raw, event_record_id | Unsigned IDs and exact envelope ticks stored as text |
| event_id, provider, provider_guid, channel, computer | Event source identity |
| level, task, opcode, version, qualifiers, keywords | System metadata; numeric fields are range-checked, qualifiers/keywords retained as text |
| process_id, thread_id, user_sid, activity_id, related_activity_id | Execution, security and correlation metadata |
| created_at, time_created_raw, container_time | Separate UTC displays and rendered XML timestamp |
| category, action, details | Qualified classification and normalized logon fields; no inference for other events |
| event_data, user_data_xml, xml | Ordered name/value/XML entries, serialized UserData and full decoder-rendered XML |

`evtx.py` validates envelopes, launches decoding and interprets XML; `evtx_worker.py` bridges the optional BinXML library in a timed subprocess. `execution.py` combines sources, `model.py` declares version 10, `exports.py` writes events and metadata, and `cli.py` adds the repeatable input flag. The existing LNK/Prefetch input/decompression cap remains 8 MiB; EVTX does not change it.

## Tests, Review and Remaining Validation

[The EVTX test and review record](EVTX_TESTS.md) maps 32 cases alongside 33 browser and 30 LNK/Prefetch regressions. Full tests install the extra and execute the actual decoder against generated EVTX/BinXML bytes, including a shared template and Unicode substitutions. No acquired evidence is committed. Without the extra, seven decoder integration tests explicitly skip; that run is not a complete EVTX validation.

Actual acquired EVTX files, real provider/version/template variations, independent parser comparisons, Windows/Linux, Python 3.10, performance and live acquisition workflows remain unvalidated. Existing browser/LNK/Prefetch real-file and unsupported-structure limitations remain in their documents. EnCase compilation/execution is still unverified. Synthetic Python tests do not close these limits.

## References

Implementation uses the [python-evtx 0.8.1 source and XML API](https://github.com/williballenthin/python-evtx/tree/v0.8.1), [libevtx working EVTX format specification](https://github.com/libyal/libevtx/blob/main/documentation/Windows%20XML%20Event%20Log%20%28EVTX%29.asciidoc), [Microsoft Event schema](https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-schema), [Microsoft 4634](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4634), [Microsoft 4647](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4647) and [Microsoft system event guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-unexpected-reboots-system-event-logs). References guide interpretation; they do not certify acquired-case accuracy.

## Recycle Bin Extension

[Recycle Bin usage](RECYCLE_BIN_CLI.md) and [tests/review](RECYCLE_BIN_TESTS.md) document the 0.4.0/schema-4 introduction. EVTX fields and decoder limits are unchanged. Full discovery now contains 123 cases; without the extra eight cases skip, including one mixed Recycle Bin/EVTX case.

## USB Registry Extension

The 0.5.0 release introduced schema 5 and usb_registry observations. Previous schema introductions above remain historical context; existing artifact field meanings are unchanged. See [USB registry contracts](USB_REGISTRY_CLI.md) and [tests/review](USB_REGISTRY_TESTS.md).

## RecentDocs Extension

Package 0.6.0 introduced schema 6 and recent_doc_keys/recent_docs. Earlier extension introductions above remain historical context; current consumers must support schema 12. See [RecentDocs contracts](RECENT_DOCS_CLI.md) and [tests/review](RECENT_DOCS_TESTS.md). Existing fields keep their meanings.
