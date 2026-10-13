# Maintenance and Risk Register

**English** | [한국어](MAINTENANCE.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Working Rules

Read AGENTS.md, [analysis](ANALYSIS.md), and [history](HISTORY.md). Decode source using the provided tools; do not convert UTF-16/UTF-8, BOMs or CRLF in the archived baseline. New fixes should have actual dates and explicit behavior changes, rather than rewriting synthetic history. Document a new baseline separately if intentionally changing archived source; do not silently replace its manifest hashes.

For a parser fix, identify both its standalone implementation and its counterpart in TimeLineThreadClass. Check exports, row constructors, copied lists, schema variants and timestamp formatting. Validate both paths against the same fixture. Keep English and Korean descriptions synchronized.

## Risk Register

Priorities below are present-day review priorities, not original severity ratings or reproduced incidents.

| ID | Priority | Risk / evidence | Proposed next action |
| --- | --- | --- | --- |
| R-01 | High | Fixed Prefetch/$I layouts can misinterpret unsupported formats | Detect versions and reject unsupported layouts before extending support |
| R-02 | High | Fixed timezone adjustments and separate browser epochs | Define timestamp contract; test original and normalized values |
| R-03 | High | SQL concatenation and delimited export formatting | Use host-supported parameter/escaping mechanisms; round-trip special characters |
| R-04 | High | Known copied-row argument mismatches | Compare constructors and restore filter invariance with fixtures |
| R-05 | High | WRITE-mode total DB and repeated table creation | Define output ownership, overwrite and rerun behavior before a change |
| R-06 | Medium | Duplicated module/timeline parsers | Fix in both paths; consider a common parser layer after regression coverage |
| R-07 | Medium | Error handling and semaphore release vary | Establish cleanup and result/error contract in recorded host version |
| R-08 | Medium | Missing visualization, hardcoded launch paths | Recover original assets or implement a separately documented replacement |
| R-09 | Medium | No full source lineage fields in every table | Add explicit provenance in a future version, with schema migration |
| R-10 | Medium | Local backup ref/bundle absent in a new clone | Preserve bundle separately and document validation prerequisites |

## Data Handling Boundaries

The plugin reads case evidence and writes derived local artifacts; bookmarks are host-managed case state. Usernames, account fields, document paths, URLs and device identifiers can appear in outputs. Keep case fixtures and generated exports outside Git, and record access/retention decisions in the actual case workflow. The source does not implement encryption, an access-control service, tamper-evident output signing, or a complete audit trail. Archive SHA-256 checks establish source integrity, not chain of custody for generated evidence.

## Suggested Modernization Sequence

1. Establish a reproducible EnCase test workstation and controlled fixture inventory.
2. Correct reproducible row-copy/export/time/schema defects without unrelated formatting changes.
3. Add explicit format detection, output ownership and completion/error reporting.
4. Introduce shared parser/result interfaces only after module/timeline regression coverage.
5. Restore or replace visualization with an explicit schema and timezone contract.

This is proposed future work, not implemented functionality. No schedule, budget or owner is assigned by this document.

## Change Review Checklist

Record the source commit and fixture, affected standalone/timeline paths, old/new output examples, schema impact, original encoding preservation, runtime evidence, and English/Korean documentation changes. Run appropriate archive checks only when retaining the baseline. A modified parser deliberately changes source hashes and requires a documented new baseline instead of claiming the old hash test passed.

## Additional Source Review Findings

| ID | Priority | Risk / evidence | Proposed next action |
| --- | --- | --- | --- |
| R-11 | High | Total timeline omits browser table creation and contains an IE insert without VALUES | Reproduce and validate complete schema and insert contracts |
| R-12 | High | CSV conversion consumes the reader reused for keyword extraction | Use independent queries or explicitly reset supported readers, then compare keyword fixtures |
| R-13 | Medium | Unfinished shutdown helper, unhandled Recent SQLite action, USB event header mismatch | Define supported UI/output behavior and validate every exposed action |
