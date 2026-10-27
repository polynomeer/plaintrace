# Implementation roadmap and validation gates

**English** | [한국어](CROSS_PLATFORM_ROADMAP.ko.md)

2026-10-27 · Proposed extension design, not an implementation or compatibility certification. Current package 0.15.0 / report schema 15 remains unchanged.

## Work packages and dependencies

Estimates are person-weeks for one experienced maintainer, exclude acquired-evidence access delays, and are not calendar commitments. Work starts from the current SAM baseline on ordinary modern branches; do not reuse/rewrite historical branches. Each implementation PR must carry bilingual contracts, fixtures, test results and a support-registry update.

| Stage | Estimate | Deliverable and dependency | Exit gate |
| --- | --- | --- | --- |
| M0 | 1–2 | Baseline inventory, support registry, three-host CI proposal | Current full suite and installation pass on named hosts; gaps listed |
| M1 | 2–3 | Manifest, probes, static registry, budgets; after M0 | Old CLI parity, adversarial inputs, exclusive publication |
| M2 | 2–3 | Proposed schema 16, exporters and schema selection; after M1 | JSON/SQLite parity, schema 15 compatibility and explicit conversion refusal |
| M3 | 3–5 | macOS XML/binary plist, system metadata, selected Safari DB; after M2 | Exact format fixtures, independent comparison, acquired-data review |
| M4 | 3–5 | Linux os-release, passwd/group metadata, journal export; after M2 | Binary/repeated fields, clocks, non-systemd cases and acquired-data review |
| M5 | 2–4 | Expanded Windows revision matrix and legacy research; after M1 | Per-revision gates and explicit unsupported layouts |
| M6 | 2–3 | Installed packages, reproducible release evidence, documentation; after M3–M5 | Mandatory lanes green and no unqualified support statements |

Sequential planning range is 15–25 person-weeks; staffing or evidence access changes it. M3/M4 can be independently scheduled after shared contracts stabilize. No native disk-image engine or native unified-log decoder is included in this estimate.

## Artifact-specific implementation tasks

macOS: first parse explicitly acquired SystemVersion-style plist values without inferring owner identity; preserve XML/binary types, dates and source locators. For Safari, admit only reviewed table/column schemas and independently specified timestamp units. Treat native unified logs, Spotlight and FSEvents as separate research tickets with no support claim.

Linux: parse os-release assignments without executing or sourcing shell text; preserve literal fields and diagnostics. Parse passwd/group as account metadata, never shadow hashes or effective privilege claims. Start journaling with acquired journal export, not host journalctl invocation or a native .journal promise. Preserve binary and duplicate fields, cursor and boot/realtime/monotonic distinctions. Text-log dialects require explicit producer profiles and no guessed year/timezone.

Windows: retain all existing semantic exclusions. Inventory currently admitted revisions per adapter before expanding XP-era, modern client/server or new format coverage. Add a new revision only with bounded layout parsing and independent expected results. Correlation, carving and credential extraction are not bundled with compatibility work.

## Validation matrix and traceability

| Test group | Required cases | Requirements |
| --- | --- | --- |
| Host parity | Named OS/build/CPU/Python; installed wheel outside checkout; EVTX extra with zero unexpected skips | CP-01, CP-06 |
| Source preservation | DB/WAL snapshots, hash mismatch, missing companion, denied writes, repeated sources | CP-02 |
| Revision gates | Valid/unknown/ambiguous/truncated revisions and missing optional tables | CP-03 |
| Resource controls | Huge counts/offsets, deep nesting, decompression bombs, oversized output, timeout/cancel cleanup | CP-04 |
| Raw semantics | Invalid Unicode, byte paths, duplicate binary fields, exact ticks, clock domain and yearless times | CP-05 |
| Schema parity | JSON/SQLite null/bytes/wide integers, schema 15 round trip, no silent record loss | CP-07 |
| Archive integrity | Original blob/ref checks and source-reference verification | CP-08 |
| Publication | Existing destination/sidecars, symlink/reparse cases, competing writers, full disk and unsupported links | CP-02, CP-04 |

Use unit fixtures with independently constructed expected values, then property/metamorphic checks and mutation fuzzing in isolated runs. Cross-host comparison excludes explicit run metadata but not raw observations or diagnostics. Acquired fixtures need lawful provenance, consent/license and redaction review; keep them outside Git and identify them by digest. Independent tools are comparators, not unquestioned ground truth. Record disagreements and block only the affected support claim until resolved.

## CI, packaging and release gates

Pin runner OS images and log exact build/CPU/Python/dependency versions. Proposed PR lanes: three primary host families, minimum declared Python and release-selected stable Python; full optional EVTX integrations on every claimed host. Nightly/release lanes add other interpreter minors, ARM64, libc variants and legacy evidence fixtures. Hosted runner labels alone do not certify unsupported older versions. Missing runners or dependency wheels leave that tuple unvalidated.

Build a pure Python wheel first; optional native adapters stay separately packaged with pinned dependency/license inventories. Validate clean install, console entry point, offline operation and dependency absence diagnostics. Containers qualify only their Linux environment, not Windows/macOS behavior. Executable bundles, signing/notarization and installers require separate release work and host smoke tests.

Release requires full mandatory tests, no unresolved source mutation/data loss/bounds errors, schema migration review, support registry and documentation agreement, and preserved archive checks. Publish environment/results/digests without evidence content. On regression, withdraw the affected package/claim and offer the prior compatible version; never overwrite prior reports or evidence.

## Risks, ownership and next decision

Maintainer owns compatibility claims and archive protection; adapter implementer owns format predicates and raw semantics; reviewer owns independent expected values; release owner owns host evidence and packaging. These are roles to assign, not claims that people have been staffed.

Highest risks are unavailable legacy fixtures, macOS proprietary layout changes, Linux producer/configuration diversity, Windows publication semantics and unbounded decoded output. Mitigate through evidence-based scope, export-first adapters, explicit unsupported diagnostics, host tests and shared budgets. Freeze the first release around M0–M4 core formats if legacy research delays M5; narrow the claim rather than inventing coverage.

Next implementation decision: confirm named host builds/architectures, lawful fixture access and interpreter policy at M0. Native image parsing, collection agents and a GUI require separate scope approval after core compatibility evidence exists. This documentation does not start a scheduled task, deploy a service or change runtime code.

## Design-document validation

On 2026-10-27, the documentation checker passed for 106 documents and 1,568 local links, including bilingual structure and technical literals. Archive-only verification passed for 13 archived sources, the archived README, 263 synthetic commits and the original tree. A baseline Git comparison confirmed unchanged EnScript files and original manifests. Whitespace validation passed.

This change modifies documentation only. The Python behavioral suite was not rerun; existing 475-test results remain dated 2026-10-26. No Windows/Linux execution, new parser behavior, schema 16, CI workflow or native EnCase validation was performed for this design.

## M0 implementation follow-up

On 2026-10-27 the M0 inventory, verification tooling and CI were implemented. See [implementation contracts](M0_BASELINE.md) and [actual results and remaining gates](M0_TESTS.md). The six named lanes passed in [remote CI](M0_CI.md), completing the M0 host gate. Universal OS-version support beyond those tuples is not claimed.
