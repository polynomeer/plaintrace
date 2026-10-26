# Application MRU Python CLI

**English** | [한국어](APPLICATION_MRU_CLI.ko.md)

The current package is 0.15.0 and every output uses schema 15. Earlier version introductions/test results below describe their release context; see [the SAM account extension](SAM_ACCOUNTS_CLI.md) for the current contract.

Implemented on 2026-10-15 on codex/python-application-mru from 4b88c0a8d8699920ecdd5622400484bbef956c89. Package 0.7.0/report schema 7 adds independent Office, HWP and Adobe registry MRU observations. All thirteen EnScript files, archive refs/manifests and 263 reconstructed 2017 commits remain preserved.

## Run and Input Scope

The repeatable --application-mru flag accepts explicit acquired stable NTUSER.DAT REGF files, including renamed files. Python 3.10+ is declared; validation used macOS/Python 3.14. This adapter uses the existing standard-library REGF reader; only EVTX needs its optional extra. JSON defaults to stdout; SQLite requires --output. Strict mode writes the complete report and returns 1 for warnings; fatal input/output errors return 2 without publishing partial output. Existing outputs, input files and SQLite sidecars are protected.

```sh
python3 -m plaintrace --application-mru /path/to/NTUSER.DAT --output applications.json
python3 -m plaintrace --application-mru /case-a/NTUSER.DAT --application-mru /case-b/NTUSER.DAT --format sqlite --output applications.sqlite
python3 -m plaintrace --recent-docs /path/to/NTUSER.DAT --application-mru /path/to/NTUSER.DAT --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --application-mru /path/to/NTUSER.DAT
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --application-mru C:\acquired\NTUSER.DAT --output applications.json
```

Source files are bounded and hashed before/read/after without modification. No live registry access, LOG1/LOG2 replay, path lookup, document opening, target execution or network retrieval occurs. Repeated sources keep separate IDs; application inputs follow all previous source groups. Supplying one hive to USB, RecentDocs and application MRU creates three sources without joins. Hash stability alone does not prove atomic acquisition or authenticity.

## Supported Lists and Decoding

| Family | Registry paths beneath Software |
| --- | --- |
| Office | Microsoft\Office\version\Word, Excel, PowerPoint: File MRU / Place MRU; also User MRU\opaque-account\File MRU / Place MRU |
| HWP | Hnc\Hwp\version\HwpFrame_KOR or HwpFrame\RecentFile; Hnc\Common\version\CommonFrame\RecentFile |
| Adobe | Adobe\Acrobat Reader or Adobe Acrobat\version\AVGeneral\cRecentFiles\cN |

Office and HWP version names are numeric major.minor with one or two digits per component. Adobe version names are enumerated literally, including DC. These are recognized layouts, not a claim of universal compatibility across all application releases. Office User MRU scope is the literal child-key name, not verified account ownership. HWP scope identifies the frame. Unsupported families, applications, version names and other branches are not scanned. Missing family branches and no supported lists produce diagnostics; existing empty lists remain key records.

Office canonical Item N values start at 1; HWP fileN starts at 0; Adobe direct cN slots start at 1 and select tDIText. Numbers have at most nine digits and no leading zero. Matching is ASCII case-insensitive. Existing values/children are enumerated without stopping at missing numbers; duplicate paths across slots/scopes remain separate. slot_number is the stored label, not a universal chronology or asserted MRU rank. Output follows reader enumeration order. Nested descendants of lists/slots are diagnosed and not traversed; unknown Adobe slot names are diagnosed without interpreting their descendants. Unknown direct values remain metadata_values with value_offset, name, type and data_hex.

Office and Adobe accept REG_SZ/REG_EXPAND_SZ UTF-16LE. HWP additionally accepts REG_BINARY UTF-16LE with optional little-endian BOM; big-endian BOM is unsupported. No environment expansion occurs. Terminal NULs are removed from decoded text but preserved in value_data_hex; missing termination warns while retaining decodable text. Embedded NUL, unsupported type or invalid UTF-16 selects no path; malformed text is escaped where decodable and raw bytes always remain. Empty paths remain empty with a warning. HWP binary decoding is layout-specific and is not a general-purpose binary-string detector.

Office plain values remain literal. A leading sequence of bracketed letter-tagged metadata tokens followed by an asterisk is parsed separately; later asterisks belong to the path. All tokens stay in metadata_tokens as tag/raw objects. One T token containing exactly 16 hexadecimal digits supplies embedded_filetime_raw and embedded_at; duplicate or malformed T tokens produce no selected time. Invalid leading bracket syntax retains raw_text without selecting a path. F/O and other flags remain opaque; pinned state is not inferred. Adobe device-independent tDIText paths remain literal, including slash syntax and percent escapes; aFS/sDI metadata is preserved without drive mapping or fallback decoding.

## Time, Output and Architecture

Key last-write timestamps appear only in application_mru_keys, with exact decimal FILETIME ticks and separate UTC displays. Office embedded T is a stored association timestamp, not proof of an actual open event. HWP/Adobe get no invented per-document time. Display truncates 100 ns fractions to microseconds using integer arithmetic; zero is null and overflow is diagnosed. Lists are mutable state, not exhaustive usage histories, user attribution or session reconstruction.

Every report uses JSON format_version 10 and SQLite user_version 10, even without this input. Version 7 adds application_mru_keys/application_mru and their counts; earlier field meanings remain unchanged. Existing reports are never migrated or rewritten; consumers must support version 10. Sources have source_kind application_mru, schema_family registry_ntuser, full-file sha256 and null browser/database/WAL fields.

| Collection/table | Fields |
| --- | --- |
| application_mru_keys | source_id, record_id, key_path, family, application, application_version, scope, list_kind, key_role, key_last_written, key_last_write_raw, metadata_values |
| application_mru | source_id, record_id, key_id, key_path, family, application, application_version, scope, list_kind, slot_name, slot_number, value_name, value_type, raw_text, stored_path, path_basis, metadata_tokens, embedded_filetime_raw, embedded_at, value_data_hex |

record_id is the physical nk/vk cell-header offset in decimal text, scoped by source_id. key_id references the parent key record. SQLite enforces source foreign keys, unique source/key IDs and a composite entry-to-key foreign key. Adobe has list and slot key_role records; entries reference their slot key. Arrays/objects remain native JSON and JSON text in SQLite; inserts bind values. Exact raw value bytes include BOM/terminators. Raw text and interpreted paths are separate; unavailable decoded fields are null.

[application_mru.py](../plaintrace/application_mru.py) interprets lists through [the native REGF reader](../plaintrace/registry_hive.py); execution, CLI, model and exporters assemble sources and schema. Inherited limits are 64 MiB input, 16344 bytes per accessed value, 16 MiB accessed value/name bytes and native cell/index limits. This adapter adds 4096 children per discovery step, 1024 emitted keys, 10000 entries and 32 MiB serialized adapter output per hive. Bounds apply to direct calls and can reject valid large inputs. Output limits are checked after allocation; combined reports remain in memory without a native timeout or memory sandbox. See [REGF support and limits](USB_REGISTRY_CLI.md).

## Original Module, Tests and Remaining Limits

The original Win_RecentDocuments.EnScript covers Office 13/14/15/16, HWP 9.0 and Reader DC. It iterates sequential slots until missing; its Adobe loop accumulates child paths. This port enumerates actual siblings and supports explicit additional layouts above, without changing EnScript. Explorer RecentDocs remains a [separate adapter](RECENT_DOCS_CLI.md); Recent-folder scanning, LNK correlation, Jump Lists, OpenSave/LastVisited, ShellBags and Office Resiliency/Pinned/Reading Locations are outside this adapter.

[Tests and self-review](APPLICATION_MRU_TESTS.md) cover 25 new cases; all 200 tests pass with the EVTX extra. Actual acquired application hives across Windows/application versions, Windows/Linux, Python 3.10, independent real-artifact comparisons, large collections and acquisition races remain unvalidated. Dirty-hive/log replay, REGF 1.6, segmented big data, volatile/link/deleted/slack structures and unsupported layouts remain excluded. Existing artifact limitations remain. EnCase compilation/execution is unverified; portable tests do not validate its host APIs.

## References

Interpretation uses the preserved [module analysis](ANALYSIS.md), [RegRipper Office parser](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/msoffice.pl), [osquery Office MRU implementation](https://github.com/osquery/osquery/blob/master/osquery/tables/applications/windows/office_mru.cpp), [Adobe preference types](https://www.adobe.com/devnet-docs/acrobatetk/tools/AdminGuide/preferences.html) and [HWP CommonFrame example](https://speakerdeck.com/digitalisx99/pycon-kr-balpyojaryo-2018-gimdonghyeon). These guide layout handling and do not establish real-case accuracy. No dependency source is vendored.
