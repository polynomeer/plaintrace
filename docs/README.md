# Documentation Index

**English** | [한국어](README.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Reading Paths

- Project reader: overview → requirements → architecture → project report.
- Examiner: setup/user guide → data model → test plan.
- Maintainer: code structure → detailed design → schema reference → analysis → maintenance.
- Archive reviewer: reconstructed history → verification report → JSON manifests.

## Deliverable Catalog

| Document | Contents |
| --- | --- |
| [Project overview and provenance](PROJECT_OVERVIEW.md) | Purpose, background, scope and evidence |
| [Requirements and use cases](REQUIREMENTS.md) | FR/NFR IDs, use cases and acceptance boundary |
| [Architecture](ARCHITECTURE.md) | Context, component and deployment views |
| [Detailed system design](SYSTEM_DESIGN.md) | Selection, lifecycle, interfaces and timeline flow |
| [Code structure](CODE_STRUCTURE.md) | All source classes and extracted method locations |
| [Data model](DATA_MODEL.md) | Storage paths, table families, timestamps and contracts |
| [SQL declaration reference](SCHEMA_REFERENCE.md) | Literal definitions and schema variants from source |
| [Setup and user guide](USER_GUIDE.md) | Prerequisites, module workflow and troubleshooting |
| [Verification and test plan](TEST_PLAN.md) | Test cases, oracles and future acceptance criteria |
| [Documentation verification report](VERIFICATION.md) | Performed checks and validation limitations |
| [Maintenance and risks](MAINTENANCE.md) | Review priorities, change rules and proposed follow-up |
| [Project report](PROJECT_REPORT.md) | Deliverable status, verification evidence and handover |
| [Static analysis](ANALYSIS.md) | Original module inventory and source observations |
| [Reconstructed history](HISTORY.md) | Synthetic dates, archive method and backup recovery |

## Interpretation Rules

Source observations, author's historical account, and proposed future work are distinguished throughout. Diagrams describe the surviving code; tests are planned unless explicitly marked as performed. The original EnCase version and HTML/JS assets are unknown or missing. Embedded Windows 7/version/date help labels are source evidence, not a release certification. English and Korean documents share technical identifiers and references.

Machine-readable records: [commit map](history-map.json) and [source manifest](source-manifest.json). Return to the [project README](../README.md).

## Python Port

[Python CLI](PYTHON_CLI.md) · [Python tests](PYTHON_TESTS.md)

[Python CLI review](PYTHON_REVIEW.md)

[Execution CLI](EXECUTION_CLI.md) · [Execution tests and review](EXECUTION_TESTS.md)

[EVTX CLI](EVTX_CLI.md) · [EVTX tests and review](EVTX_TESTS.md)

[Recycle Bin CLI](RECYCLE_BIN_CLI.md) · [Tests and review](RECYCLE_BIN_TESTS.md)

[USB registry CLI](USB_REGISTRY_CLI.md) · [Tests and review](USB_REGISTRY_TESTS.md)

[RecentDocs CLI](RECENT_DOCS_CLI.md) · [Tests and review](RECENT_DOCS_TESTS.md)

## Application MRU Extension

Package 0.7.0 adds Office/HWP/Adobe MRUs and schema 7.

[CLI](APPLICATION_MRU_CLI.md) · [Tests and review](APPLICATION_MRU_TESTS.md)

## Jump Lists Extension

Package 0.8.0 adds automatic/custom Jump Lists and schema 8.

[CLI](JUMP_LISTS_CLI.md) · [Tests and review](JUMP_LISTS_TESTS.md)

## ShellBags Extension

Package 0.9.0 adds ShellBags hierarchies, partial Shell Item decoding, referenced Bags metadata and schema 9.

[CLI](SHELLBAGS_CLI.md) · [Tests and review](SHELLBAGS_TESTS.md)

## Common Dialog MRU Extension

Package 0.10.0 adds OpenSavePidlMRU/LastVisitedPidlMRU and schema 10.

[CLI](DIALOG_MRU_CLI.md) · [Tests and review](DIALOG_MRU_TESTS.md)
