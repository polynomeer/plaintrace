# Improvement Record

**English** | [한국어](IMPROVEMENTS.ko.md)

## Baselines and Scope

Branch: `codex/prioritized-code-fixes`. Preserved baseline: tag `archive/pre-improvements-2026-10-13` at commit `758bfc5`; master and all 263 synthetic 2017 commits are unchanged. Original hashes remain in source-manifest.json. Source changes retain each file's encoding, BOM and CRLF and use present-day commits. This is a maintenance improvement, not a new historical reconstruction.

Handwritten retrospective documents describe the tagged archive unless stated otherwise. Generated [code structure](CODE_STRUCTURE.md) and [schema reference](SCHEMA_REFERENCE.md) describe this branch. This record supersedes baseline defect descriptions for the fixes below.

## Prioritized Changes

| Priority / risk | Change | Validation and limits |
| --- | --- | --- |
| High / R-11 | Total timeline creates Web_Visit and Web_Host alongside the other nine tables; IE WebCache insert includes column names and VALUES | All eleven initial declarations execute in portable SQLite; source-derived IE inserts tested |
| High / R-12 | Standalone and timeline web visit helpers issue a fresh query through a separate command/reader before keyword extraction | Checks both Chrome/Opera urls and Firefox moz_places paths; host API lifetime still needs validation |
| High / R-04 | Logon copy/filter constructors preserve all eleven fields; power copy preserves eventTime; logon keyword filtering matches its stored fields | Constructor field mappings statically checked; keyword clearing preserves original order |
| High / R-05, R-07 | Timeline refuses an existing readable output and stops on file/DB/command/schema setup failure, releasing its semaphore and busy state | Prevents ordinary rerun truncation; partial failed outputs require inspection/removal; not a race-proof file ownership protocol |
| Medium / R-03, R-13 | USB event CSV has twelve matching headers/fields, consistent quoted cells and doubled quotes; default name is USB_EventLog.csv | Source-derived output round trips commas, quotes, newlines and Korean text |
| Medium / R-13 | Recent SQLite action writes App_RecentFile in a transaction with SQL quote escaping, rollback on insert/commit failure and success reporting only after commit | New standalone table preserves eleven displayed fields; append semantics can duplicate rows on reruns |
| Medium / R-13 | Shutdown helper reads an exactly eight-byte registry FILETIME using existing MemoryFileClass/ReadWinDate APIs; active computer-name command lookup corrected | Missing, wrong-sized or unreadable values return empty; retains existing fixed timezone adjustment pending timestamp contract validation |

The new App_RecentFile table contains id plus FileName, OriginalFile, AccessedTime, CreatedTime, WrittenTime, FileSize, MachineID, Volume, DriveType, SerialNumber and MACaddress. It is a standalone Recent export, not an extra integrated timeline family. No historical manifest is replaced.

## Validation

```sh
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
```

Seven portable regression cases check source encodings/structure, timeline schemas and IE insert templates, independent browser queries, row-copy mappings, USB CSV special characters, Recent SQLite special characters and shutdown evidence-reading code. Python SQLite executes SQL extracted from source; output tests evaluate only selected string expressions and model the documented escaping operations. These checks do not compile or execute EnScript and do not establish API compatibility. EnCase/Windows compilation and T-02/T-08/T-09/T-10/T-11/T-12 remain required. In particular, confirm fresh-reader lifetimes, FILETIME interpretation and output failure cleanup in the actual host.

Archive-only verification reads historical Git blobs, checks all 263 records and compares the historical tree with the original local backup ref. Default archive verification still rejects changed working source; do not label this branch byte-identical to the archive. A normal clone needs the separately preserved local backup ref for full original-tree comparison. Portable improvement tests require the preserved baseline tag.

## Remaining Work

Fixed-offset Prefetch/$I format support (R-01), timezone interpretation (R-02), SQL escaping and export round trips outside the corrected handlers (R-03), chart/rerun behavior and file races (R-05), generalized worker cleanup (R-07), missing HTML/JS and hardcoded browser launch paths (R-08), and provenance/schema migration (R-09) remain open. Supporting additional formats or replacing timestamp semantics requires independently known fixtures and host validation. No synthetic evidence results or historical test passes are claimed.

Browser insertion templates outside the tested ordinary URL/title values still concatenate unescaped text. Do not infer that the schema and VALUES fixes solve apostrophes across all browser writers. Recycle Bin extraction still requires distinguishing metadata from recovered content.
