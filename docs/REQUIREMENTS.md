# Requirements and Use Cases

**English** | [한국어](REQUIREMENTS.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Basis

These are retrospective requirements mapped to source, not recovered original specifications. “Observed” means code is present; it does not mean an acceptance test passed.

| ID | Requirement | Implementation evidence | Status / constraint |
| --- | --- | --- | --- |
| FR-01 | Open a multi-module view for a Windows case | MainClass.Main / MainDialogClass | Observed; entry loop stops at the first matching volume |
| FR-02 | Review system and account data | Win_SystemInfo / Win_UserAccount | Observed; registry/version assumptions |
| FR-03 | Examine file and deletion metadata | Win_FileMetaData / Win_RecycleBin | Observed; fixed $I layout |
| FR-04 | Inspect execution and recent documents | Win_PrefetchFile / Win_LinkFile / Win_RecentDocuments | Observed; fixed offsets and correlation limitations |
| FR-05 | Examine logon, power, and USB history | Win_PowerLogOnOff / Win_USBInfo | Observed; selected event IDs/paths |
| FR-06 | Examine browser activity and downloads | Win_WebVisitKeyword / Win_WebDownloads | Observed; legacy database layouts |
| FR-07 | Filter, bookmark, and export results | Handler/menu/dialog implementations | Observed; per-module behavior varies |
| FR-08 | Build a consolidated timeline database | TimeLineThreadClass.Run | Observed; separate duplicated parsers |
| FR-09 | Display an interactive web timeline | TimeLineDialogClass browser buttons | Incomplete in this archive: external assets missing |
| NFR-01 | Preserve archived source bytes | source-manifest.json / verify_archive.py | Verified in the reconstruction workspace |
| NFR-02 | Retain result traceability | Case entries, bookmarks, paths and exports | Partial; no universal provenance/event model |
| NFR-03 | Handle malformed inputs and repeat runs | Existing checks and database calls | Unvalidated; review required |
| NFR-04 | Run inside EnCase on Windows | Host API dependencies | Exact host version unconfirmed |

## Use Cases

| ID | Actor / precondition | Main flow | Completion / alternative |
| --- | --- | --- | --- |
| UC-01 | Examiner; case contains a Windows volume | Run entry script → open module → search | Results/bookmark or no matching volume |
| UC-02 | Examiner; a module has results | Filter list → inspect row → choose CSV/SQLite export | Output file or export error |
| UC-03 | Examiner; matching Prefetch/LNK/Recycle evidence | Select supported extraction action and destination | Extracted local file; action availability varies |
| UC-04 | Examiner; selected evidence and writable output paths | Timeline → Build DB → wait for completion | Consolidated database; errors need output inspection |
| UC-05 | Examiner; external visualization restored and paths reviewed | Launch browser → select database → choose interval | Intended historical flow only; blocked by missing assets here |

## Acceptance Boundary

Each functional requirement needs the runtime cases in [the test plan](TEST_PLAN.md). Database creation alone does not demonstrate correct timestamps, complete coverage, or reliable activity inference. No performance, availability, or cross-version support target survives in the repository; measurements and thresholds must be agreed before a future release.
