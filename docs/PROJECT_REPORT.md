# Project Report and Deliverable Status

**English** | [한국어](PROJECT_REPORT.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Original Project

PVMA was developed during the author's undergraduate BoB digital forensics project period, July–November 2017. The surviving source implements a multi-tab EnCase plugin covering 12 Windows artifact modules. UI development and EnScript artifact extraction/parsing are described in the original README. That description also records an Acorn Publishing contract, Grand Prix competition eligibility and an invited DOUZONE Bizon presentation; supporting contracts, presentation files and assessment records are not in this repository.

## Technical Outcome and Limitations

| Deliverable | Available evidence | Current status |
| --- | --- | --- |
| EnScript plugin | 13 source files, 11,573 lines | Preserved source; exact EnCase runtime unvalidated |
| Artifact collectors | Registry, binary, event and browser parsers | Implementation present; correctness requires fixtures |
| Result interface | Dialogs, tables, filters, reports, charts, bookmarks | Source present; host UI not executed in this documentation work |
| Export/integration | CSV/SQLite writers and timeline rescanning | Source present; variants and known defects documented |
| Web visualization | Browser launch/help code | HTML/JS missing |
| Original design/test artifacts | No original GDD/UML/test report supplied | Current documents are retrospective |

## Present-day Archival Work

The existing five-commit chain was replaced on master with 263 explicitly synthetic archive commits dated July–November 2017. The final archive tree matches the prior final tree. Original records remain in a local backup ref and verified bundle. Later documentation/tooling uses actual work dates, and the reconstructed branch was published at the author's request. See [history](HISTORY.md) for exact scope and [the document index](README.md) for the deliverable set.

## Verification Evidence

The reconstruction workspace passed checks of 13 current EnScript file hashes, the archived README hash, 263 commit dates/parents/changed files, and the original tree. Documentation work checks relative links, bilingual document pairs, source index locations, and SQL references. EnCase compilation, parser ground truth, browser rendering, performance and forensic reliability remain not run or blocked. No historical test success or release certification is claimed.

## Handover

A reader can navigate from requirements to architecture, implementation references, data outputs and planned acceptance cases. A maintainer needs the original backup for complete baseline verification and a recorded EnCase environment for runtime work. The first follow-up should establish that environment and fixture inventory before expanding support or repairing visualization. Open issues and suggested sequencing are in [maintenance](MAINTENANCE.md).
