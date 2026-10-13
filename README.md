# Plain View of Multi Artifacts (PVMA)

**English** | [한국어](README.ko.md)

An **EnScript plugin for EnCase** developed to collect and analyze Windows forensic artifacts and explore user activity over time. The repository is now named `plaintrace`; the project's original name is **Plain View of Multi Artifacts**.

## Background

The project was developed from **July to November 2017**, during the author's undergraduate studies, as part of the **digital forensics track of Best of the Best (BoB)**, Korea's next-generation security leader training program. Its goal was to bring different Windows artifacts into one interface and connect them through a timeline to support user activity analysis.

The work included UI development and Windows artifact extraction and parsing in EnScript. Technologies and tools used included EnCase, EnScript, SQLite, JavaScript, and StarUML. The original project description records a publishing contract with Acorn Publishing, eligibility to compete for the Grand Prix, and an invited presentation at DOUZONE Bizon.

## Main Features

| Area | Capabilities |
| --- | --- |
| System and accounts | Inspect operating system, volume, computer, user account, and logon information |
| Files | Analyze metadata for ordinary, hidden, and deleted files, plus Recycle Bin deletion times and original paths |
| Program execution | Extract execution traces, paths, and timestamps from Prefetch and LNK files |
| Recent documents | Correlate recent document records for Office, HWP, and Adobe applications with LNK files |
| Logon and power | Analyze logon, logoff, power-on, and power-off records from event logs |
| USB | Analyze device identifiers and connection traces from registry data and event logs |
| Web | Analyze browsing, search keyword, and download records from Chrome, Firefox, Opera, and Internet Explorer |
| Browsing and export | View tabbed lists, search results, selected frequency charts, and bookmarks; export to CSV and SQLite |
| Timeline | Consolidate artifacts into SQLite and launch an external HTML visualization |

## Runtime Environment

- **Windows and EnCase's EnScript runtime** are required. The plugin depends on EnCase APIs for cases, files, registry data, and event logs.
- The entry point is [`Plain View of Multi Artifacts.EnScript`](<Plain View of Multi Artifacts.EnScript>). Keep the other 12 `Win_*.EnScript` modules alongside it. The code is intended to run in EnCase against a case containing Windows evidence.
- The exact EnCase version, SDK, test evidence, and build configuration are not included in this repository. Compatibility and runtime behavior require separate validation.
- The source contains hardcoded database, browser, and HTML paths under `C:\`. Check these paths against the actual environment before running the plugin.
- **The web timeline's HTML and JavaScript assets are missing from this repository.** The source alone cannot reproduce the complete original visualization.

This repository preserves the surviving project source as an archive. Windows artifact format differences and existing implementation limitations are documented in the [static analysis report](docs/ANALYSIS.md).

## Reconstructed Commit History

**Commits dated July–November 2017 are a retrospective reconstruction created in October 2026 from the final source snapshot, rather than original Git records from the development period.**

The source was divided into 263 commits at the class and method level. Dates, task order, and intervals were assigned for archival purposes. Each reconstructed commit has an `archive:` subject and a body disclosing the reconstruction. This history does not establish the actual development schedule or individual contributions, and intermediate commits are not guaranteed to be runnable.

The final reconstructed source snapshot preserves the previous source byte for byte. Subsequent README updates, Codex setup, analysis documents, and verification tools are recorded in follow-up commits with their actual work dates.

- [Reconstruction method and original backup details](docs/HISTORY.md)
- [Commit dates, files, and task units](docs/history-map.json)
- [Original file sizes and SHA-256 hashes](docs/source-manifest.json)

## Exploring the Source

The EnScript files use a mixture of UTF-8 and UTF-16LE encodings. The Python 3 tools let you inspect them while preserving their original encodings and line endings.

```sh
python3 tools/inspect_sources.py
python3 tools/inspect_sources.py Win_TimeLine.EnScript --start 2006 --end 2120
python3 tools/verify_archive.py
```

The verification tool checks the integrity of the current EnScript source, the archived README snapshot, and the reconstructed commits. It does not compile the plugin or test its behavior in EnCase.

## Related Records

- [Current GitHub repository](https://github.com/polynomeer/plaintrace)
- [Original project GitHub URL](https://github.com/Polynomeer/PVMA)
- [Project Trello URL](https://trello.com/b/xIo5E0Ez/bobenscriptwork)
