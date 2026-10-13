# Project Overview

**English** | [한국어](PROJECT_OVERVIEW.ko.md)

Prepared on 2026-10-13 from the archived source. This is retrospective documentation, not an original 2017 deliverable.

## Identity and Purpose

Plain View of Multi Artifacts (PVMA), now archived in `plaintrace`, is an EnCase EnScript plugin for examining Windows user activity through multiple forensic artifacts. The author describes it as an undergraduate BoB digital forensics project developed from July to November 2017. It joins artifact browsing, extraction, tabular review, and database preparation in one host interface.

## Stakeholders and Scope

| Stakeholder | Need |
| --- | --- |
| Examiner | Inspect Windows artifacts in an EnCase case and export findings |
| Reviewer | Trace a displayed value to its source parser and evaluate limitations |
| Maintainer | Preserve the legacy implementation and understand dependencies |
| Project reader | Understand the 2017 background and reconstructed archive |

The surviving scope covers system information, file metadata, accounts, deleted files, Prefetch, LNK, recent documents, logon/power events, USB, browser artifacts, and timeline database construction. A complete standalone forensic application, acquisition engine, mobile/cloud analysis, and the missing web visualization are outside the surviving implementation.

## Provenance and Evidence

| Statement | Evidence and interpretation |
| --- | --- |
| Original title and BoB period | Author's account; not inferred from synthetic commit dates |
| 13 source files / 12 included modules | Entry file and source inventory |
| Version 2.0 / Windows 7 / December 17, 2017 | Help text in Win_TimeLine.EnScript lines 2173–2175; embedded labels, not a validated release manifest |
| Historical commit sequence | 263 retrospective archive commits; see [history](HISTORY.md) |
| JavaScript visualization | Browser launch commands exist; HTML/JS assets are absent |

The December help label does not establish when every source change occurred. It does not replace the author's July–November project period. EnCase version, actual release packages, original design diagrams, test results, and individual task allocations are unknown.

## Current Deliverables

The repository contains the original EnScript bytes, bilingual README and design documents, a class/method index, extracted SQL declarations, archive manifests, and Python inspection/verification utilities. The project documentation index is [here](README.md). These are present-day descriptions of a preserved snapshot.
