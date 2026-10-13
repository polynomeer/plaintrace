# Documentation Verification Report

**English** | [한국어](VERIFICATION.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Scope

Report date: 2026-10-13. This report covers retrospective documentation of the preserved implementation. Changes are limited to documentation and documentation validation tools; archived EnScript remains preserved at the baseline tag; this branch contains separately tested source changes. Checks below establish repository consistency, not runtime correctness.

## Checks Performed

| Check | Method | Result |
| --- | --- | --- |
| Archived source and historical metadata | python3 tools/verify_archive.py --archive-only in original workspace | Passed: 13 historical sources, archived README, 263 commits and baseline tree |
| Generated source references | python3 tools/generate_source_reference.py --check | Passed: both language versions match source extraction |
| Source line citations | Decode target files; compare cited classes/methods/SQL locations | Passed within the generator's explicitly limited coverage |
| Relative document links | Resolve paths and file/line anchors from each Markdown file | Passed for repository-local targets |
| Bilingual coverage | English/Korean pairs and mutual language links | Passed for every documentation topic |
| Translation structure | Compare section, table-row and code-block counts per pair | Passed; technical IDs and commands retained |
| Diagram structure | Inspect Mermaid block delimiters and diagram declarations | Passed static inspection; visual rendering not performed |
| Whitespace | git diff --check | Passed |

## Not Performed

EnCase compilation/execution, evidence parsing ground truth, GUI interactions, database export round trips, web timeline rendering, cross-version compatibility and performance measurements were not performed. HTML-dependent runtime tests are blocked by missing assets. Original 2017 test and design records were not supplied.

## Reproduction

```sh
python3 tools/inspect_sources.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
```

Full archive verification requires the original local backup ref; see [setup](USER_GUIDE.md). Planned runtime acceptance cases and recording fields are in [the test plan](TEST_PLAN.md). The generated SQL appendix is a declaration inventory, not a successfully executed migration.

## Full Source and Translation Review

The review compared the entry point, all twelve included modules, active SQL and export handlers with both language versions. Commented code was distinguished from active implementation. The following documentation corrections were made without modifying archived source.

| Finding | Corrected description |
| --- | --- |
| Database paths | WindowsArtifact.sqlite occurs in comments; active defaults use WindowsArtifacts.sqlite and the two timeline destinations |
| Recent Documents | Viewer outputs are CSV; viewer SQL definitions are commented; App_Documents is active |
| Charts | System charts inspect selected items; Prefetch/web charts query SQLite |
| Total timeline | Nine initial table declarations omit Web_Visit/Web_Host; browser inserts are attempts, not verified successful consolidation |
| Browser keywords | Reader reuse after CSV conversion is a source-level risk |
| Incomplete controls and helpers | Recent SQLite handling and shutdown-time conversion are incomplete |
| USB exports | Registry/event capabilities differ; event header does not describe emitted fields correctly |
| Translation | Runtime path spelling, technical literals and descriptions synchronized |

The test plan now includes chart and extraction regression cases and targeted checks for these findings. Automated translation checks compare inline technical literals and language-specific document links in addition to structural coverage. They cannot establish prose equivalence or runtime success; those conclusions require manual review and host testing respectively.

## Improvement Branch Validation

The current improvement branch passed eleven portable regression cases, generated-reference checks, 36-document bilingual validation and historical archive-only verification. The original baseline remains tagged separately. Changes and remaining host tests are recorded in [the improvement record](IMPROVEMENTS.md). The portable checks exercise extracted SQL/output contracts and source structure; no EnCase compilation or runtime pass is claimed.

## Follow-up Review

[The branch review](REVIEW.md) records additional fixes for rerun copy lists, query parsing/decoder bounds, keyword SQL quoting and setup, and timeline finalization failures, with eleven portable regression cases. Keyword writes now escape text; other browser writers still require review.
