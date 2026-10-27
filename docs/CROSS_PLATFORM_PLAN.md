# Cross-platform expansion plan

**English** | [한국어](CROSS_PLATFORM_PLAN.ko.md)

2026-10-27 · Proposed extension design, not an implementation or compatibility certification. Current package 0.15.0 / report schema 15 remains unchanged.

## Purpose and baseline

Turn Plaintrace into an offline evidence analysis toolkit for Windows, macOS and Linux, independent of the examiner workstation. Preserve the EnScript archive as a separate historical product. The Python implementation already covers browser SQLite, LNK/Prefetch, EVTX, Recycle Bin and bounded registry-based artifacts through SAM metadata. It does not currently implement native macOS/Linux artifact families.

The repository declares Python 3.10+; the latest recorded full run is 475 tests on macOS/Python 3.14 with the EVTX extra, dated 2026-10-26. This does not establish Windows/Linux execution or support for every artifact version. See [current contracts](SAM_ACCOUNTS_CLI.md) and [recorded validation](SAM_ACCOUNTS_TESTS.md).

## Users and workflow

Primary users are forensic examiners and incident responders with previously acquired data. Workflow: register explicit acquired files or a manifest; verify hashes and companion files; probe format capabilities; inspect a dry-run plan; run bounded parsers; review raw observations and diagnostics; export JSON/SQLite with provenance. A separate optional presentation layer may later display timelines using the same parser results.

A modern Linux workstation must be able to analyze an acquired Windows hive; a modern Windows workstation must be able to parse an acquired macOS plist. Host-native collection, if ever added, is a separate product surface requiring explicit scope and acquisition validation.

## Requirements and acceptance

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| CP-01 | Separate host, evidence OS and format revision | One acquired fixture yields equivalent observations on three host families |
| CP-02 | Preserve inputs and source lineage | Before/after hashes, denied-write checks, original offsets and acquisition manifest retained |
| CP-03 | Admit only recognized layouts | Unknown revision is unsupported or explicitly partial, never silent fallback |
| CP-04 | Bound every parser and report | Limit and timeout tests produce controlled diagnostics without partial publication |
| CP-05 | Preserve source semantics | Raw time/path/duplicate-field round trips and independent expected values |
| CP-06 | Expose compatibility honestly | Release support entries link exact environments and fixture results |
| CP-07 | Keep old reports reproducible | Schema 15 regression and opt-in next-schema migration comparisons |
| CP-08 | Preserve the archive | Historical blob/ref checks and unchanged EnScript/manifests |

## Scope and priorities

P0: establish host compatibility, manifest/provenance contracts and a support registry before claiming portability. P1: bounded macOS plist/system metadata and Linux os-release/account metadata plus common browser validation. P2: Linux journal export and selected macOS application databases with version-specific adapters. P3: legacy format coverage, richer filesystem metadata and an optional read-only report UI.

Deferred behind separate decisions: raw disk-image/filesystem drivers, encrypted volumes, deleted-data recovery, live agents, remote collection, automatic identity correlation and native unified-log/Spotlight/FSEvents decoding. No credential decryption, target execution or report-driven network requests. Missing artifacts mean unavailable evidence, not absence of activity.

## Deliverables and decisions

Use the existing Python core rather than rewriting EnScript or introducing a service. Start with explicit offline files, not automatic host scanning. Compatibility depends on measured format capabilities, not OS marketing names. Preserve observations first; derived interpretations must carry rules and source links.

Read [compatibility policy](CROSS_PLATFORM_COMPATIBILITY.md), [architecture and contracts](CROSS_PLATFORM_ARCHITECTURE.md), and [delivery and validation](CROSS_PLATFORM_ROADMAP.md). These documents are the design deliverable; implementation, CI execution, packaging and acquisitions remain future work.
