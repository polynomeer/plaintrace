# Improvement Branch Review

**English** | [한국어](REVIEW.ko.md)

## Scope and Preservation

Reviewed on 2026-10-13 against the preserved baseline `archive/pre-improvements-2026-10-13` (`758bfc5`). The review covers all six modified EnScript files, archive/documentation tooling and bilingual deliverables. The baseline tag, original manifest and 263 reconstructed historical commits remain unchanged; integrating improvements into master adds modern commits without rewriting history. Source fixes retain each file's BOM, encoding and CRLF. This is a manual source review plus portable contract validation, not an independent external review or EnCase runtime certification.

## Findings Resolved

| Priority | Finding | Resolution |
| --- | --- | --- |
| High | Repeated logon/power searches clear displayed lists but accumulate CopyList rows, causing duplicate/stale rows when filtering | Clear each corresponding copy list at the start of collection |
| High | Fresh keyword readers activate previously hidden parameter bugs: standalone only accepts ampersand parameters, timeline mishandles first search_query parameter; decoding before delimiter removal truncates encoded ampersands | Parse exact q/query/search_query names after the question mark, stop at fragments and delimit before decoding; preserve timeline's existing raw keyword representation |
| High | Newly activated keyword inserts fail when URLs, keywords or titles contain apostrophes | Escape the keyword SQL text in both implementations and log insertion failures; other browser writers remain outside this fix |
| Medium | Existing decoder assumes three percent-encoded bytes, reads beyond short sequences, and mishandles two/four-byte UTF-8 | Validate hexadecimal pairs and bounds, decode contiguous encoded bytes through the existing UTF-8 host API; malformed sequences remain literal |
| Medium | Keyword setup continues after output/DB/command failure; repeated standalone schema creation reports failure | Stop failed setup with resource cleanup; create the standalone keyword table with IF NOT EXISTS |
| Medium | Timeline LNK output and final database reopen failures are unchecked and can still show a success message | Stop these failures and release busy/semaphore state; close SQLite before its backing file; completion message requires diagnostics/content validation |
| Medium | Original portable cases only check Recent rollback text, not transaction effects, and leave test connections open | Add a trigger-induced failed batch test that proves rollback retains the prior committed row; close test connections |

## Verification Results

| Check | Result |
| --- | --- |
| Portable regression suite | Passed 11 cases: original seven plus rerun list reset, query/keyword quoting, Recent failed-batch rollback and timeline/decoder boundaries |
| Generated source/schema references | Passed; four documents regenerated from the current source |
| Bilingual documentation and links | Passed repository checker, including technical literals and language-specific links |
| Historical archive-only verification | Passed: 13 archived sources, archived README, 263 commit records and original tree |
| Source encodings and structure | Passed portable checks of BOM, CRLF and balanced braces on changed sources |
| Whitespace | Passed git diff --check |
| Windows/EnCase compilation and execution | Not performed; no host/SDK/evidence fixture available |

Portable tests execute source-extracted SQL in Python SQLite and evaluate a limited string-expression subset. URL fixtures use a model with source-derived parameter names; decoder tests check bounds statically. These are not executions of the EnScript control flow or UTF-8 host decoder. The rollback test checks SQLite transaction semantics and the source's rollback branch; host file locking and API failure cleanup still require reproduction.

## Remaining Limits and Host Acceptance

Before treating this branch as runtime-ready, compile the complete entry and includes in a recorded EnCase/Windows environment. Run the [test plan](TEST_PLAN.md), particularly T-02, T-08 through T-13, T-17 and T-18. Verify fresh-reader lifetimes, empty/repeated selections, query and malformed UTF-8 fixtures, registry FILETIME/timezone interpretation, export locking/rollback, partial outputs and charts.

The existing-output guard checks whether a file can be opened for reading; it does not establish atomic creation or protect unreadable existing files and races. Setup failures can leave a partial output, and individual artifact helpers still do not propagate all errors. The final completion message therefore does not promise complete collection. Recent append exports can duplicate rows on reruns. Browser visit/download SQL outside keyword writes remains unescaped. Fixed-offset parsers, ControlSet001 assumptions, timezone semantics, missing HTML/JS, hardcoded paths, source provenance and Recycle Bin content recovery remain unresolved. UTF-8 replacement/truncation behavior for invalid bytes or percent-encoded NUL requires host validation; raw evidence URLs remain available.

Final integration is authorized through a normal merge commit. EnCase compilation and execution remain unverified after merging. No force push, historical redate or archive replacement is included. See [the improvement record](IMPROVEMENTS.md) for the complete branch behavior.
