# Setup and User Guide

**English** | [한국어](USER_GUIDE.ko.md)

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Prerequisites and Readiness

Use a Windows workstation with an EnCase environment capable of running these EnScript APIs. The exact version is unknown. The embedded help names Windows 7 as the target; this is not proof of support for every Windows 7 image or later systems. Obtain a test case and writable local output locations before trying runtime validation. No packaged installer, dependency download, sample evidence or working HTML timeline is supplied.

## Setup

1. Keep all 13 `.EnScript` files together and confirm EnCase can resolve their include names. Preserve their BOMs and line endings.
2. Open a case containing Windows evidence and note the device, volume, visible view, and selection. The entry uses CURRENTVIEW while workers often use CURRENTVIEW_SELECTED.
3. Review hardcoded paths in the relevant module using `tools/inspect_sources.py`. Check drive C outputs and the case export directory. Preserve existing generated databases before a new run.
4. Run `Plain View of Multi Artifacts.EnScript` through the host's EnScript execution facility. Exact menu names depend on the EnCase version and are not established here.
5. If the main dialog does not appear, inspect console messages and confirm a Windows volume is visible. The entry stops after the first matching volume.

## Working with a Module

Choose the relevant tab and use its Search action where available. Wait for the worker to finish, inspect the row count and sample fields, and compare values with original evidence. Use keyword controls to filter; filters and search fields are module-specific. Clear the keyword to restore rows where supported. Available context-menu actions include CSV, SQLite and, in certain modules, file extraction. System information uses reports and charts rather than the same worker flow as every artifact tab.

Do not treat an empty table as proof of no activity: selection scope, unavailable source artifacts, parser assumptions, and errors may all produce empty results. Inspect console output and the expected source paths.

## Timeline

The Timeline tab exposes Build DB, browser buttons, and Help. Build DB performs its own two-pass collection, not simply a merge of currently displayed tabs. It writes the total SQLite database at a fixed path; verify schemas and row counts before interpreting it. The help suggests launching a browser, choosing an SQLite file, and setting a time interval. Those final steps cannot be completed from this archive without recovering the missing HTML/JS and reconciling the hardcoded browser/HTML paths.

## Troubleshooting

| Symptom | First checks |
| --- | --- |
| Include or host API error | All 13 sources present; host version; encoding retained |
| No main dialog | Open case; Windows volume in visible view; console message |
| Empty or partial results | Selected items/device scope; expected artifact paths; format version |
| Export cannot open | Destination exists/is writable; file locks; actual path spelling |
| SQL error/repeated-run conflict | Existing table schema; malformed SQL; apostrophes in values |
| Different values after filtering | Row copy/constructor argument order; compare unfiltered output |
| Browser launch fails | Browser executable path; HTML location; absent assets |
| Still Processing or blocked closure | Worker/semaphore state; preserve logs and inspect completion; no verified cancellation contract |

## Archive Verification in a Fresh Clone

`python3 tools/inspect_sources.py` works with Python 3 and no EnCase installation. `tools/verify_archive.py` additionally expects the local `refs/archive/pre-reconstruction` ref and full reconstructed commits. A normal remote clone does not automatically contain that local backup ref or ignored bundle. Full baseline-tree validation therefore requires the original reconstruction workspace or its separately preserved backup. Do not report an unavailable baseline as a runtime failure.

## Run Record

Record run date, source commit, EnCase/Windows versions, evidence identifiers, visible/selected scope, source timezone, output paths/hashes, per-table counts, sample comparisons and console errors. Keep generated evidence and exports outside repository commits. See [the validation plan](TEST_PLAN.md) and [maintenance](MAINTENANCE.md).
