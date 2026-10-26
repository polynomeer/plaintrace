# Explorer RecentDocs Python CLI

**English** | [한국어](RECENT_DOCS_CLI.ko.md)

The current package is 0.15.0 and every output uses schema 15. Earlier version introductions/test results below describe their release context; see [the SAM account extension](SAM_ACCOUNTS_CLI.md) for the current contract.

Implemented on 2026-10-15 on `codex/python-recent-docs`, based on `0f3e9e4fec930332310c172df6b1e599249c8924`. All thirteen EnScript files, archive refs/manifests and 263 reconstructed 2017 commits are preserved. Package 0.6.0/report schema 6 extends the independent Python port.

## Run and Input Scope

Analyze Explorer RecentDocs in an acquired NTUSER.DAT hive. The repeatable --recent-docs flag accepts renamed binary REGF files; filenames do not establish ownership or format. Python 3.10+ is declared; validation used macOS/Python 3.14. This adapter uses the existing standard-library REGF reader and has no new dependency. EVTX still needs its optional extra. At least one supported artifact input is required. JSON defaults to stdout; SQLite requires --output. Strict mode writes warnings/report and returns 1; fatal errors return 2 without publishing a partial file. Existing output/input/SQLite-sidecar protections apply.

```sh
python3 -m plaintrace --recent-docs /path/to/NTUSER.DAT --output recent.json
python3 -m plaintrace --recent-docs /case-a/NTUSER.DAT --recent-docs /case-b/NTUSER.DAT --format sqlite --output recent.sqlite
python3 -m plaintrace --input /path/to/History --usb-system /path/to/SYSTEM --recent-docs /path/to/NTUSER.DAT --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --recent-docs /path/to/NTUSER.DAT
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --recent-docs C:\acquired\NTUSER.DAT --output recent.json
```

Inputs are bounded and hashed before/read/after without modifying originals. Only supplied hives are opened; no LOG1/LOG2 replay, live registry access, original-name filesystem lookup or target execution occurs. Hash stability does not establish atomic acquisition, authenticity or complete evidence. RecentDocs sources follow existing source groups, including USB, and retain supplied order within their group. Supplying the same hive to USB and RecentDocs creates separate source IDs without automatic joins.

## Keys, MRU and Interpretation

The adapter reads Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs and all direct child scopes, including extensions and Folder. The root category is null; child category is the literal key name. Root and child duplicates remain distinct observations. Nested descendants are not traversed and produce a warning. Missing branches produce an explicit diagnostic with an empty result, while an existing empty key is retained as key metadata.

| Control | Supported representation and ranking |
| --- | --- |
| MRUListEx | REG_BINARY array of little-endian unsigned DWORD slots with a final 0xffffffff sentinel; canonical decimal entry names 0..4294967294 |
| MRUList | REG_SZ UTF-16LE ASCII letter sequence ending in NUL; single-letter entry names matched case-insensitively |
| Missing/invalid control | Retain raw control/entry data; all ranks null |
| Both controls present | Ambiguous; retain both, select neither and assign no ranks |

Rank 0 is the most recently used stored reference within its key, not a timestamp or proof of opening. Duplicate MRU slots, wrong types, missing/embedded sentinels, trailing data, malformed lengths or invalid legacy letters invalidate the entire ordering. The parser does not silently deduplicate or guess a partial order. A valid reference to an absent entry produces a warning and retains its slot in mru_order; existing ranks keep the resulting gaps. Unlisted entries remain present with null rank and a warning. A valid empty control differs from a missing control. Noncanonical/unknown value names are retained in other_values rather than invented as documents.

Entry decoding supports REG_BINARY for modern/missing/ambiguous controls; legacy MRUList also supports REG_SZ. The first two-byte-aligned UTF-16LE NUL ends the stored document name. Missing terminators or wrong types retain the entire raw value with null decoded name. Invalid UTF-16 is escaped and diagnosed at the value's source offset. Empty names remain empty with a warning. Bytes after the NUL remain opaque trailing_data_hex with a diagnostic, including zero bytes. Shell Item/PIDL types, sizes, extensions, targets and timestamps are not interpreted or validated. Stored names are literal and are not promoted to verified full paths, resolved, normalized or opened.

## Time, Lineage and Original Module

Key last-write timestamps exist only in recent_doc_keys, with separate UTC microsecond displays and exact decimal FILETIME ticks. Display truncates 100 ns fractions using integer arithmetic; zero is null and overflow is diagnosed. No per-document opened/accessed/created/deleted time is inferred, even for rank 0. The key's last-write can reflect a list change and is not assigned to every entry. MRU state is not an exhaustive chronological history or proof of user intent/ownership.

The preserved EnScript module primarily handles Office/HWP/Adobe application MRUs and LNK correlation. This extension specifically implements Explorer RecentDocs, not the complete original viewer-specific behavior. Office application lists, Adobe/HWP MRUs, Recent-folder scanning, LNK correlation, Jump Lists, OpenSave/LastVisited, ShellBags, deleted records, user/SID attribution and session reconstruction are outside this adapter. Existing explicit LNK analysis is unchanged.

## Version 10 Output and Architecture

JSON format_version and SQLite user_version are 10 for every report, including other-only inputs. Version 6 adds recent_doc_keys/recent_docs and both counts. Earlier reports are never rewritten/migrated; consumers must explicitly recognize version 10. Existing artifact field meanings remain unchanged. Sources have source_kind recent_docs, schema_family registry_ntuser, full acquired-file sha256 and null browser/database/WAL fields.

| Collection/table | Fields and meaning |
| --- | --- |
| recent_doc_keys | source_id, record_id, key_path, category, key_last_written, key_last_write_raw, mru_format, mru_status, mru_order, mru_values, other_values |
| recent_docs | source_id, record_id, key_id, key_path, category, value_name, value_type, mru_rank, document_name, name_utf16_hex, trailing_data_hex, value_data_hex |

Key record_id is the physical nk cell-header offset as decimal text; document record_id is the vk cell-header offset. Both are scoped by source_id; key_id points to the parent key record. SQLite enforces source foreign keys, unique source/key IDs and the composite document-to-key foreign key. Inserts bind parameters and preserve Unicode/quotes/newlines. MRU/other value objects contain value_offset, name, type and data_hex. Objects/arrays are native JSON and JSON text in SQLite. name_utf16_hex excludes the NUL; value_data_hex includes every original value byte. Unknown decoding fields are null, while an absent tail after a valid name is an empty hex string.

[recent_docs.py](../plaintrace/recent_docs.py) interprets MRU state and names using [registry_hive.py](../plaintrace/registry_hive.py). Source assembly, CLI, model and export modules add the flag, lineage and schema. Limits per hive: inherited 64 MiB REGF input, 16344 bytes per accessed value, 16 MiB accessed value data/name bytes, native cell/index/name limits, plus 1024 RecentDocs keys, 10000 documents and 32 MiB serialized adapter output. Limits apply to direct calls too and may reject valid large inputs. Output checks occur after allocation; combined reports remain in memory and there is no native timeout/memory sandbox. See [REGF structures and limits](USB_REGISTRY_CLI.md).

## Tests and Remaining Validation

[Tests and manual review](RECENT_DOCS_TESTS.md) map 27 new cases. All 175 tests pass with the EVTX extra; without it, 167 execute and eight existing integrations skip. Generated REGF fixtures cover modern/legacy orders, sparse/missing/duplicate references, scopes, malformed names, opaque tails, budgets, source-only reads, actual CLI and JSON/SQLite lineage. A separate python-registry 1.3.1 comparison reads synthetic MRU bytes/names; it is not a runtime dependency or real-hive validation.

Actual acquired NTUSER hives across Windows releases, Windows/Linux, Python 3.10, independent real-artifact comparisons, large collections and acquisition races remain unvalidated. Dirty-hive/log replay, unsupported REGF versions, segmented big data, volatile/link/deleted/slack structures and Shell Item decoding remain unsupported. Existing browser/LNK/Prefetch/EVTX/Recycle Bin/USB limitations remain documented. EnCase compilation/execution is still unverified; these tests do not validate its host APIs.

## References

Structure interpretation uses [libyal MRU/RecentDocs knowledge base](https://winreg-kb.readthedocs.io/en/latest/sources/explorer-keys/Most-recently-used.html), [RegRipper RecentDocs implementation](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/recentdocs.pl) and [the REGF working specification](https://github.com/libyal/libregf/blob/main/documentation/Windows%20NT%20Registry%20File%20%28REGF%29%20format.asciidoc). No dependency source is vendored. See [the archived module analysis](ANALYSIS.md).
