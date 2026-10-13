# Data Model and Output Contracts

**English** | [한국어](DATA_MODEL.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Storage Model

The source uses in-memory NameList rows, EnCase bookmarks/reports, local extracted evidence copies, delimited text, and multiple SQLite files. There is no observed foreign-key graph or universal event table. Tables retain artifact-specific columns, and integer primary keys are local row identifiers rather than cross-artifact identities.

| Output | Purpose | Important behavior |
| --- | --- | --- |
| User-selected CSV/SQLite path | Per-module menu export | ExportDialogClass prompts for destination |
| C:\WindowsArtifacts.sqlite | Default export destination in several handlers | User-selectable handler default; singular WindowsArtifact.sqlite exists only in comments |
| C:\TimeLineArtifacts.sqlite | Several standalone timeline helpers | Table existence and repeated writes need review |
| C:\TimeLineArtifacts_Total.sqlite | Integrated timeline build | Opened with WRITE; preserve prior outputs before rebuilding |
| Case export directory | Browser copies/intermediate files, link_files, lnk_parse.csv, help.txt | Multiple per-browser subdirectories and filenames |

The table lists runtime paths as they would appear on Windows, not escaped EnScript string literals or a centralized configuration interface. `C:\WindowsArtifact.sqlite` is mentioned only in comments; helpers actually use `C:\TimeLineArtifacts.sqlite`. Some `.csv` files are tab-separated, such as timeline `lnk_parse.csv`; delimiters and headers must be checked per writer.

## Table Families

| Family | Tables | Interpretation |
| --- | --- | --- |
| Computer/account | PC_UserAccount, PC_LogOnOff, PC_PowerOnOff | Account state and event records; SID/RID/LogonID have different meanings |
| File | File_Common, File_Hidden, File_Deleted, File_RecycleBin | File metadata, attributes and deletion information |
| Execution | App_PrefetchFile, App_PrefetchFile_Sorted, App_LinkFile, App_EXEFile | Parsed execution traces and aggregate chart data; traces are not proof of every execution |
| Documents | App_Documents | Viewer, filename, timestamps, size, drive type and path |
| USB | USB_EventLog | Device and connection event information |
| Web | Web_Visit, Web_Keyword, Web_Host, Web_Host_Union, Web_Download | Visits, searches, counts and downloads |
| Templates and delimited intermediates | Web_cr/ff/op names in browser helpers; viewer-specific CSV files | Many dynamic CREATE TABLE templates and all viewer-specific table declarations are commented out; names do not guarantee generated tables |

Literal SQL declarations and their locations are in [the schema reference](SCHEMA_REFERENCE.md). That appendix preserves variant declarations rather than silently creating a normalized schema.

## Timestamp and Identity Rules

File metadata and several binary formats use DateClass/FILETIME reads. Browser helpers contain separate epoch conversions; output frequently stores formatted timestamps as LONGVARCHAR. Fixed `-9*3600` formatting appears throughout. Preserve the original string and source artifact when comparing results; no common UTC-normalized event contract is implemented.

Source file paths, SID, RID, LogonID, machine IDs, device serials and GUIDs are heterogeneous fields. Matching strings across tables does not establish a declared relational join. Correlation of recent documents and LNK files is heuristic code, not an enforced foreign key.

## Schema and Export Limitations

Web_Visit has variants with and without title; App_EXEFile RunCount appears as LONGVARCHAR or INTEGER with constraints; Web_Download TotalBytes is declared with and without a type. Some account declarations spell LONGVARCHAR as LONGVARHAR. SQL strings and CSV quoting are not consistently escaped. No schema migration/version registry or universal idempotent export mechanism is present. A consumer must inspect the actual database schema before querying.

The table-family list covers the repository, not every individual output file. The total timeline build omits Web_Visit and Web_Host creation while helpers attempt writes to them. Recent-document per-viewer outputs are CSV files; active SQL writes target App_Documents. Web_Host_Union is a web-chart aggregation table. USB event CSV headers differ from the emitted event fields, so headers alone are not reliable field contracts.

## Suggested Inspection Queries

Run on a copy of a generated SQLite database, not on evidence inputs. These are inspection queries, not plugin APIs or a guaranteed browser contract.

```sql
SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name;
PRAGMA table_info('PC_LogOnOff');
SELECT COUNT(*) FROM PC_LogOnOff;
```

Only run the last two queries if the table exists. Record database hash, table columns, row counts, output path, selected evidence, host versions, and timestamp interpretation alongside results. Acceptance cases are defined in [the test plan](TEST_PLAN.md).
