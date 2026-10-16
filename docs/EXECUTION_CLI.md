# LNK and Prefetch Python CLI

**English** | [한국어](EXECUTION_CLI.ko.md)

The current package is 0.11.0 and every output uses schema 11. Earlier version introductions/test results below describe their release context; see [the UserAssist extension](USERASSIST_CLI.md) for the current contract.

Implemented and reviewed on 2026-10-14 on codex/python-lnk-prefetch, based on d1830099999cb1669f8f868506d5c323acdb8ca5. Every EnScript file and historical manifest remains byte-identical to the branch base; archive tags and 263 reconstructed 2017 commits are preserved. Version 0.2.0 is an independent Python extension, not an EnScript runtime.

## Usage and Compatibility

Python 3.10+ with standard-library sqlite3 is the declared requirement; validation here used macOS/Python 3.14. LNK/Prefetch require no third-party runtime libraries, including for XPRESS Huffman. EVTX needs an optional extra. Repeat --lnk and --prefetch for multiple acquired files; at least one --input, --lnk, --prefetch, --evtx or --recycle-bin is required. Browser options apply only to SQLite inputs. --lnk-codepage defaults to cp1252 and applies only to ANSI LNK fields; specify an ANSI-compatible encoding such as cp949 for appropriate acquisitions. Unicode fields remain UTF-16LE. The CLI does not recursively scan directories.

```sh
python3 -m plaintrace --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --output execution.json
python3 -m plaintrace --lnk /path/to/example.lnk --lnk-codepage cp949 --strict
python3 -m plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --format sqlite --output artifacts.sqlite
```

Existing browser command syntax is retained, but report format_version and SQLite user_version were extended to 2 in 0.2.0. The 0.3.0 release added events in version 3. Current output uses version 10; see [Recycle Bin schema migration](RECYCLE_BIN_CLI.md). Version 2 added links/prefetch collections/tables and source_kind/sha256 source fields even for browser-only reports. Existing version 1 output is never overwritten or migrated; consumers must explicitly recognize the new version. Optional pip installation provides the same plaintrace console command; see [installation and browser behavior](PYTHON_CLI.md).

## LNK Parsing

The parser checks the ShellLinkHeader size and CLSID, reads flags, target attributes/size and target creation/access/write FILETIMEs, walks bounded optional IDList/LinkInfo/StringData/ExtraData sections, and requires a terminal block. It supports local ANSI/Unicode paths, volume type/serial/label, network share paths, counted strings, tracker machine/GUID fields and environment target strings.

All candidate paths retain their basis. Local full paths are not duplicated with the common suffix. Unicode LinkInfo fields take priority. Relative paths are combined textually with a stored working directory; environment variables remain literal. The CLI never executes a target, accesses a network share, expands environment variables, or resolves candidates against a filesystem. LNK presence and target timestamps are not proof that the target executed.

PIDL shell items remain opaque hex and produce a diagnostic. Unknown ExtraData blocks retain signature/size/offset and produce a diagnostic, rather than guessed fields. Tracker GUIDs are preserved; no physical MAC address is inferred. Header icon/show/hotkey details, PIDL/property-store target resolution and many ExtraData types remain outside interpreted fields. ANSI codepage choice cannot be inferred reliably from the file. Undecodable text is escaped with a warning; the acquired file/hash remain the byte-level source of truth.

## Prefetch Versions and Sections

| Version / layout | Supported interpretation |
| --- | --- |
| 17 / 152 | One run-time slot; version-specific run counter |
| 23 / 240 | One run-time slot; version-specific run counter |
| 26 / 304 | Eight stored run-time slots |
| 30 / 304 or 296 | Both checked information-layout variants; separate run-counter offsets |
| 31 / 296 | Referenced v31 layout; eight stored run-time slots; synthetic fixture coverage |

The parser validates signature, declared payload size, information-layout discriminator, metric/trace ranges, UTF-16 filename pool and volume bounds. It reports executable name, Prefetch hash, counter, every stored time slot (including null zero slots), referenced strings, exact-basename executable path candidates and volume device path/creation time/serial. Device paths are retained; no mapping of HARDDISKVOLUME numbers to drive letters is guessed. Prefetch references/counters are traces rather than a complete execution audit.

Detailed metrics, trace chains, volume file references, directory strings and hash-string contents are not interpreted and are listed in unparsed_sections. Bounds are checked for accessed sections; this is not full semantic validation of every ignored substructure. Declared-size mismatches and unknown versions/layouts fail rather than being interpreted using a legacy fixed offset. Real files across the listed Windows variants remain unvalidated here.

## Compressed Prefetch

MAM04 is decoded with a local bounded XPRESS Huffman implementation following the published protocol. Canonical tables must be complete, bit/length reads must fit, and matches cannot refer before the output or expand beyond the advertised size. Overlapping matches and multiple 64 KiB blocks are handled. Decoded output must then pass the same SCCA checks.

Checksum-bearing MAM84 and other MAM flags are explicitly rejected. Compression padding/unused trailing bits are not authenticated; no checksum or general corruption-recovery guarantee is claimed. The decoder covers the documented byte/16-bit extended-length cases; other variants fail. Tests use independently encoded literal/match streams, not real acquired MAM files or independent forensic-tool certification. Both input and advertised decoded payload are limited to 8 MiB.

## Time, Provenance and Output

FILETIME raw ticks are preserved as decimal strings. UTC display truncates 100 ns ticks to microseconds without floating-point rounding; the raw remainder is still available. Zero is unknown/null, and out-of-range times are diagnosed rather than fabricated. LNK times describe the stored target; no source-file filesystem timestamps are substituted. Prefetch volume and run times retain separate meanings.

Binary inputs are read only, capped, hashed before/read/after and associated with distinct source IDs. sha256 identifies acquired compressed bytes for MAM; prefetch.file_size describes the decoded SCCA payload. Browser sources retain existing DB/WAL hashes and gain source_kind browser and a sha256 alias for the database bytes. Hash stability is not atomic acquisition or chain-of-custody certification.

| Collection / table | Fields |
| --- | --- |
| links | source_id, record_id, link_flags, file_attributes, target_size, created_at, accessed_at, written_at, filetimes_raw, local_base_path, common_path_suffix, network_share, volume, name, relative_path, working_directory, arguments, icon_location, target_candidates, tracker, environment_target, id_list_hex, extra_blocks |
| prefetch | source_id, record_id, version, compressed, layout, executable, prefetch_hash, file_size, run_count, last_run_times, last_run_times_raw, referenced_files, executable_path_candidates, volumes, metrics_count, trace_count, unparsed_sections |
| sources extension | source_kind, sha256; browser/database_sha256/wal_sha256 are null for binary inputs |

Objects/arrays are JSON values in JSON output and JSON text in SQLite. SQLite compressed is 0/1; links/prefetch record IDs include source-local offsets and are scoped by source_id. Table foreign keys, reserved source paths and exclusive output publication continue to apply. Fatal errors prevent publication of a partial file report; warnings remain visible and --strict returns 1 after producing a report. See [browser CLI exit/output contracts](PYTHON_CLI.md).

## Tests and Code Review

[The execution test and review record](EXECUTION_TESTS.md) maps 30 new tests alongside the existing 33 browser tests. Review corrected bounded hash reads for growing inputs and added limits to direct decompressor calls, Unicode volume/network coverage, volume-bound/time-overflow checks and source-collision checks. Tests include every truncated prefix of representative LNK/Prefetch fixtures, deterministic mutations, overlapping/extended compressed matches, multiblock decoding and mixed JSON/SQLite output.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d1830099999cb1669f8f868506d5c323acdb8ca5 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

Windows/Linux, Python minimum-version execution, real acquired LNK/Prefetch/MAM files, independent parser comparisons, large-case performance and remaining opaque structures need further validation. EnCase compilation/execution remains unverified and is not established by these actual Python tests.

## Format References

Structure interpretation refers to [Microsoft MS-SHLLINK](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/747629b3-b5be-452a-8101-b9a2ec49978c), [Microsoft MS-XCA processing](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-xca/26db8e62-bbd8-472c-a09e-623f6de10f0b) and [the libscca working format specification](https://github.com/libyal/libscca/blob/main/documentation/Windows%20Prefetch%20File%20%28PF%29%20format.asciidoc). These references guide implementation; they do not certify universal Windows-version compatibility. No dependency source is vendored.

## EVTX Extension

[EVTX usage](EVTX_CLI.md) and [tests/review](EVTX_TESTS.md) describe the optional decoder and events. LNK/Prefetch interpretation and the 8 MiB cap are unchanged.

## Recycle Bin Extension

[Recycle Bin metadata](RECYCLE_BIN_CLI.md) and [tests/review](RECYCLE_BIN_TESTS.md) describe the standard-library $I parser and current schema 4. LNK/Prefetch fields and limits are preserved.

## USB Registry Extension

The 0.5.0 release introduced schema 5 and usb_registry observations. Previous schema introductions above remain historical context; existing artifact field meanings are unchanged. See [USB registry contracts](USB_REGISTRY_CLI.md) and [tests/review](USB_REGISTRY_TESTS.md).

## RecentDocs Extension

Package 0.6.0 introduced schema 6 and recent_doc_keys/recent_docs. Earlier extension introductions above remain historical context; current consumers must support schema 11. See [RecentDocs contracts](RECENT_DOCS_CLI.md) and [tests/review](RECENT_DOCS_TESTS.md). Existing fields keep their meanings.
