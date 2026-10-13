# Static Project Analysis

**English** | [한국어](ANALYSIS.ko.md)

Analysis date: 2026-10-13. According to the project author's account, the original name was **Plain View of Multi Artifacts**, developed during undergraduate studies from July to November 2017 in the digital forensics track of Korea's Best of the Best (BoB) security leader training program. This analysis examines the surviving final source snapshot. It does not infer the actual development schedule or individual contributions.

## Architecture and Runtime

The repository contains 13 EnScript files. The entry point is `MainClass.Main` in `Plain View of Multi Artifacts.EnScript`. It includes 12 Windows modules, locates a Windows volume in the case, and creates a bookmark folder and a tabbed `MainDialogClass`. Data rows generally derive from `NameListClass`; tables use `HandlerClass` and `TreeTableEditClass`; collection runs through `ThreadClass`; and `DialogClass` handles search, progress, and closing. The shared export path dialog, `ExportDialogClass`, is defined in the entry file.

The code depends on EnCase host APIs, including `CaseClass`, `EntryClass`, `RegistryClass`, `EventLogParserClass`, and `SQLiteClass`. The EnCase version, SDK, test cases, and build configuration are absent. It is not a standalone C++ or Java program and cannot be validated with a general-purpose compiler. The README mentions JavaScript and the source includes HTML launch commands, but the web timeline's HTML/JavaScript assets are not included.

## Module Inventory

| Module | Inputs and Core Processing | Outputs and Interface |
| --- | --- | --- |
| Plain View of Multi Artifacts | Windows volume checks, 12 includes, bookmark creation, and module assembly | Export path dialog; system, file, account, execution, web, and timeline tabs |
| Win_SystemInfo | Selected file/volume information; OS details and product key from SOFTWARE; computer name and shutdown time from SYSTEM; user counts from SAM | FileReportClass, VolumeReportClass, and OSReportClass documents; file distribution charts |
| Win_FileMetaData | Extensions, categories, sizes, paths, and modification/access/creation timestamps of selected items; separate lists based on deleted/hidden attributes | Ordinary/hidden/deleted tables, CSV, File_Common/File_Hidden/File_Deleted SQLite tables, and deleted-file data for the timeline |
| Win_UserAccount | F/V binary records under SAM Users/Names and RID keys; logon and password change times, counts, account state, and string fields | AccountListClass, search/progress controls, CSV, and PC_UserAccount SQLite table |
| Win_RecycleBin | $Recycle paths and SIDs; $I headers, 8-byte sizes, deletion FILETIME, and Unicode original paths | Original metadata/MD5 and deletion information table, file extraction, CSV, and File_RecycleBin SQLite table |
| Win_PowerLogOnOff | Security events 4624/4634/4647 and power events 12/13; users, logon IDs, addresses, and other fields from XML data | Logon/power lists, logon type reference document, CSV, and PC_LogOnOff/PC_PowerOnOff SQLite tables |
| Win_USBInfo | SYSTEM USBSTOR/USB/DeviceClasses/MountedDevices; SOFTWARE device/profile information; DriverFrameworks Operational.evtx | USB registry reporting/extraction; event table with connection states, times, and identifiers; CSV; USB_EventLog SQLite table |
| Win_PrefetchFile | .pf files under Prefetch; executable names, times, counts, and reference lists read at fixed offsets; device path mapping | Execution/reference lists, file extraction, CSV, App_PrefetchFile/App_EXEFile SQLite tables, and execution frequency charts |
| Win_LinkFile | LNK headers, path blocks, and extra data; original file timestamps/sizes and drive, machine, and MAC identifiers; separate Recent path collection | Link/Recent lists, file extraction, CSV, and App_LinkFile/App_EXEFile SQLite tables |
| Win_RecentDocuments | Recent document registry records correlated with extracted LNK files; separate PowerPoint/Word/Excel/HWP/Adobe handling | RecentDoc list, LNK CSV, intermediate tables by viewer, and App_Documents SQLite table |
| Win_WebDownloads | Chrome/Opera History downloads, Firefox places.sqlite moz_annos, and binary searches of IE WebCache; browser-specific time conversion | Extracted databases/CSV, Web_Download SQLite table, and download paths, times, sizes, and URLs |
| Win_WebVisitKeyword | Chrome/Opera urls, Firefox moz_places, and IE index.dat/WebCache; URL decoding, keyword extraction, and host frequencies | Visit/keyword lists, CSV, Web_Visit/Web_Keyword/Web_Host SQLite tables, and charts of the most frequent hosts |
| Win_TimeLine | Reimplements multiple standalone parsers; first pass collects deleted files, USB, logon, power, accounts, Prefetch, and LNK; second pass collects recent documents and web artifacts | C:\TimeLineArtifacts_Total.sqlite, LNK CSV, a readme document, and buttons that launch external HTML in Chrome/IE/Firefox |

For exact encodings, line counts, and class names, run `python3 tools/inspect_sources.py`. Original byte counts and hashes are in `docs/source-manifest.json`. All class/method preservation stages are recorded in `docs/history-map.json`.

## Preserved Limitations and Follow-up Review

The reconstruction was limited to archival work, so these implementations were left unchanged. The points below are source observations or issues requiring further review, rather than runtime reproduction results.

- SQL statements are mostly assembled by string concatenation. Apostrophes in filenames or URLs may cause syntax or data preservation problems. CSV output also frequently uses simple comma concatenation, so fields containing commas, newlines, or quotes need validation.
- Some `SELECT COUNT(*) FROM sqlite_master WHERE name 'App_EXEFile'` strings in `Win_LinkFile` and `Win_PrefetchFile` lack a comparison operator. These should be reviewed together with export error handling.
- In `Win_PowerLogOnOff`, logon list copying (line 425) and filtered list reconstruction (lines 761/767) pass arguments in an order that differs from the constructor declaration. Power list copying (line 567) passes `n.event` where the event timestamp belongs.
- Prefetch parsing uses fixed offsets such as 0x80/0x98, with no identified format-version branching or decompression. Recycle Bin parsing reads a string after a fixed $I header. The source does not establish support across Windows versions.
- Many timestamp displays use the fixed value `-9*3600`. The semantics of EnCase's time APIs and browser-specific epoch conversions require validation against actual cases.
- Numerous paths are hardcoded on drive C, and the code mixes `WindowsArtifacts.sqlite`, `WindowsArtifact.sqlite`, `TimeLineArtifacts.sqlite`, and `TimeLineArtifacts_Total.sqlite`. Table creation, repeated runs, and file locking need review.
- The first-pass WebArtifact call in `Win_TimeLine.Run` is commented out, but the second pass calls it for non-volume items. Web collection is therefore not entirely disabled.
- Timeline launch buttons use a `C:\PlainView.html` variable but browser commands point to `C:\PlainView\PlainView.html`. Those assets are missing from the repository, so the snapshot cannot establish that the complete web visualization runs.
- Standalone modules and timeline parsers contain duplicate implementations. Changes to a standalone collection path do not automatically update the timeline path.
- Progress updates and semaphore release occur mainly on the normal execution path. Early exits, empty selections, multiple devices, and malformed binary input require separate validation.

## Verification Scope

All 13 files were decoded according to their BOMs, and class/method boundaries were extracted statically. Checks cover balanced braces outside comments and strings, byte equality at each file's final reconstruction stage, equality of the complete final Git tree, the hash manifest, and commit parents, author/committer dates, and changed files. These checks do not establish compilation, artifact accuracy, security, or the ability to run every intermediate commit.
