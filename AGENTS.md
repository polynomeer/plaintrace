# Plaintrace / Plain View of Multi Artifacts

Legacy Windows forensic artifact plugin written in EnCase EnScript, originally developed during the 2017 BoB digital forensics project.

- Read `docs/ANALYSIS.md` and `docs/HISTORY.md` before changing archived code or history.
- Preserve original `.EnScript` bytes, BOM, mixed UTF-8/UTF-16LE encodings and CRLF. Never apply a repository-wide formatter or encoding conversion.
- Use `python3 tools/inspect_sources.py` to read decoded source and inspect classes. Plain `rg` will miss UTF-16 files.
- Use `python3 tools/verify_archive.py` to verify the archived snapshot. This is integrity validation, not compilation or behavioral testing.
- Runtime validation requires Windows, EnCase and its EnScript APIs; no SDK, case fixture or portable compiler is bundled. Do not claim runtime tests passed on macOS.
- Keep generated exports, evidence, caches and backup bundles out of Git.
- History dated July–November 2017 is a retrospective reconstruction from a final snapshot. Its dates and task order are synthetic, not evidence of actual historical work.
- Modern agent tooling and analysis must use actual creation dates, outside the reconstructed historical chain.

## Improvement branch

- The user authorized source improvements on `codex/prioritized-code-fixes`; preserve the baseline at tag `archive/pre-improvements-2026-10-13` and never rewrite master or the 2017 history.
- Read `docs/IMPROVEMENTS.md` for the branch's behavior and remaining host-validation requirements. Keep file encodings, BOMs and CRLF when editing.
- Use `python3 tools/verify_archive.py --archive-only` to validate historical blobs on an improvement branch. Default verification intentionally requires unchanged working source.
- Run `python3 tools/test_improvements.py` and regenerate source references after source changes. Portable tests do not establish EnCase compilation or execution.

## Python port branch

- Python changes belong on `codex/python-browser-cli`; preserve all thirteen EnScript files byte-for-byte against merged commit `bb476180453c76f7d38e5b6a9f1f025ad2273ce0` and preserve all archive refs/manifests/history.
- Read `docs/PYTHON_CLI.md` and `docs/PYTHON_TESTS.md`. Run `python3 -m unittest discover -s tests -v` for actual Python behavior; these results do not certify EnCase.
- Analyze acquired stable DB/WAL snapshots only. Keep real evidence and exports out of Git; synthetic test databases are created in temporary directories.

## Execution artifact port

- LNK/Prefetch development belongs on `codex/python-lnk-prefetch`, based on `d1830099999cb1669f8f868506d5c323acdb8ca5`. Preserve EnScript, original manifests, archive tags and all historical commits.
- Read `docs/EXECUTION_CLI.md` and `docs/EXECUTION_TESTS.md`; run both browser and execution test modules via unittest discovery. Report schema version 2 deliberately extends version 1 and must be documented.
- Enforce binary input/decoded-output limits and bounds on offsets, counts, strings and XPRESS references. Never execute shortcut targets or infer drive letters from device IDs.

## Event log port

- EVTX development belongs on `codex/python-evtx`, based on `9f32324141810b257d4f680e84c849c013543900`. Preserve EnScript, archive tags/manifests and the reconstructed history.
- Read `docs/EVTX_CLI.md` and `docs/EVTX_TESTS.md`. Full unittest discovery must run with the optional `.[evtx]` extra; skipped integration tests are not complete EVTX validation.
- Report schema version 3 adds events. Preserve rendered XML, exact envelope FILETIME, source offsets and duplicate values. Qualify classifications by provider/channel; never infer USB state from equal-time event counts.
- Keep container/record/XML/output limits and decoder timeout. No carving, repair, message DLL loading, target execution or Windows/EnCase runtime claim.

## Recycle Bin port

- Recycle Bin development belongs on `codex/python-recycle-bin`, based on `e0d0145cfb7b649c1713d66776ea140a43f891a3`. Preserve all EnScript bytes, archive refs/manifests and 2017 history.
- Read `docs/RECYCLE_BIN_CLI.md` and `docs/RECYCLE_BIN_TESTS.md`. Full unittest discovery includes the EVTX extra; Recycle Bin-only parsing uses the standard library.
- Report schema 4 adds recycle_bin. Bound input and UTF-16 code-unit counts, retain exact FILETIME/unsigned size/path bytes and warn about padding/trailing data.
- Analyze acquired explicit $I files only. Do not infer SID/ownership or $R presence/restoration, open original paths, repair shifted layouts or claim Windows/EnCase validation.

## USB registry port

- USB registry development belongs on `codex/python-usb-registry`, based on `d174bc8c7f57aa5f91e0e3c87113e4af78ce3eb1`. Preserve EnScript, archive refs/manifests and the synthetic historical chain.
- Read `docs/USB_REGISTRY_CLI.md` and `docs/USB_REGISTRY_TESTS.md`; run full discovery with the EVTX extra. Registry parsing itself uses the standard library.
- Schema 5 adds usb_registry observations. Preserve raw values, source offsets and FILETIMEs. Resolve Select/Current rather than assuming ControlSet001; key last-write is not a connection time.
- Enforce REGF cell/index/value/output bounds. No dirty-hive log replay, deleted-cell recovery, guessed serials/drive letters/users, cross-hive joins or Windows/EnCase runtime claims.

## RecentDocs port

- RecentDocs work belongs on `codex/python-recent-docs`, based on `0f3e9e4fec930332310c172df6b1e599249c8924`. Preserve EnScript, original refs/manifests and 2017 history.
- Read `docs/RECENT_DOCS_CLI.md` and `docs/RECENT_DOCS_TESTS.md`; run full discovery with the EVTX extra. RecentDocs uses the existing standard-library REGF reader.
- Schema 6 adds recent_doc_keys/recent_docs. Preserve MRU control bytes, rank gaps, source offsets and raw value/tail bytes. Missing/invalid/ambiguous MRU gets no guessed ranks.
- Key last-write is not a per-document open time. No Shell Item target resolution, automatic Office/LNK/Jump List correlation, SID attribution, log replay or host-validation claims.

## Application MRU port

- Application MRU work belongs on `codex/python-application-mru`, based on `4b88c0a8d8699920ecdd5622400484bbef956c89`. Preserve all EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/APPLICATION_MRU_CLI.md` and `docs/APPLICATION_MRU_TESTS.md`; run full discovery with the EVTX extra. Reuse the bounded standard-library REGF reader.
- Schema 7 adds application_mru_keys/application_mru. Preserve sparse slots, literal paths, metadata tokens, raw bytes, physical source offsets and exact FILETIMEs.
- Slot labels are not universal ranks; key last-write is not a document open time. No guessed Adobe drive mapping, pinned state, ownership, cross-artifact joins, log replay or host-validation claims.

## Jump Lists port

- Jump Lists work belongs on `codex/python-jump-lists`, based on `285f7f5020213042372e4d791fd001626a04231e`. Preserve all EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/JUMP_LISTS_CLI.md` and `docs/JUMP_LISTS_TESTS.md`; run full discovery with the EVTX extra. Jump Lists/CFB parsing uses the standard library.
- Schema 8 adds jump_lists/jump_list_entries. Bound CFB FAT/DIFAT/miniFAT chains, directory references, lengths, categories, records and output; do not carve signatures or infer missing associations.
- Preserve exact raw bytes/FILETIMEs, literal paths and fragmented stream mappings. DestList record lineage and linked-stream names are separate. No inferred execution, opening, MAC/owner/app identity or EnCase/Windows/Linux validation claims.

## ShellBags port

- ShellBags work belongs on `codex/python-shellbags`, based on `9bc15c8f765ea2c10d2259049a39222375f5d61c`. Preserve all EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/SHELLBAGS_CLI.md` and `docs/SHELLBAGS_TESTS.md`; run full discovery with the EVTX extra. Reuse the bounded standard-library REGF reader.
- Schema 9 adds shellbag_views/shellbag_keys/shellbag_entries. Preserve raw MRU/NodeSlot/item/view bytes, hierarchy, source offsets and exact key FILETIMEs; bound both trees, items, extensions, paths and output.
- NodeSlot belongs to its BagMRU key. Do not invent missing ancestry, normalize unsupported components, assign FAT timezones, infer folder access/ownership or claim Windows/Linux/EnCase validation. Same-root Bags references do not authorize cross-hive/user joins.

## Common Dialog MRU port

- Dialog MRU work belongs on `codex/python-dialog-mru`, based on `2c6a4203770834c6e197e86b9a1888ea5c4c5d68`. Preserve all EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/DIALOG_MRU_CLI.md` and `docs/DIALOG_MRU_TESTS.md`; run full discovery with the EVTX extra. Reuse bounded REGF/Shell Item readers without changing existing decoder semantics.
- Schema 10 adds dialog_mru_keys/dialog_mru_entries. Preserve raw MRU controls, UTF-16 application prefixes, PIDL offsets/bytes, rank gaps and exact key FILETIMEs. Bound scopes, entries, prefixes, items and output.
- Require PIDL terminal items for path candidates. Do not infer success/open-versus-save, app execution/identity, per-entry key times, users or cross-list joins. Actual acquired NTUSER/Windows/Linux/EnCase validation remains outstanding.

## UserAssist port

- UserAssist work belongs on `codex/python-userassist`, based on `caa66102c4c46ebc7ab0e81153c36801bdfc8d67`. Preserve EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/USERASSIST_CLI.md` and `docs/USERASSIST_TESTS.md`; run full discovery with the EVTX extra. Reuse the bounded REGF reader without changing decoder semantics.
- Schema 11 adds userassist_keys/userassist_entries. Require explicit Version 3/5, exact REG_BINARY sizes and NoEncrypt-aware ASCII ROT13/plain names; retain unsupported values, controls, offsets, raw counters and exact FILETIMEs. Bound keys, entries and output.
- No size-based version guessing, legacy count correction, focus-duration claims, target expansion/execution, ownership or cross-artifact joins. Actual NTUSER/Windows/Linux/EnCase validation remains outstanding.

## RunMRU port

- RunMRU work belongs on `codex/python-runmru`, based on `53f0d510b2d06f991394cf5858be22f54416a1f4`. Preserve EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/RUN_MRU_CLI.md` and `docs/RUN_MRU_TESTS.md`; run full discovery with the EVTX extra. Reuse the bounded REGF reader without changing decoder semantics.
- Schema 12 adds run_mru_keys/run_mru_entries. Preserve literal REG_SZ commands, raw controls/tails/values, source offsets, rank gaps and exact key FILETIMEs. Require strict MRUList for ranks; no MRUListEx guess. Bound entries, strings and output.
- No suffix trimming, command execution/expansion, per-entry key-time assignment, execution-success/ownership inference or automatic joins. Actual NTUSER/Windows/Linux/EnCase validation remains outstanding.

## Explorer address/search history port

- TypedPaths/WordWheelQuery work belongs on `codex/python-explorer-history`, based on `e94cee173fffdcfdd9b960c29c0e9f81a1067236`. Preserve EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/EXPLORER_HISTORY_CLI.md` and `docs/EXPLORER_HISTORY_TESTS.md`; run full discovery with the EVTX extra. Reuse the bounded REGF reader without changing existing decoder semantics.
- Schema 13 adds explorer_history_keys/explorer_history_entries. Keep TypedPaths slot labels separate from WordWheelQuery MRUListEx ranks; retain raw controls/text/tails/values, physical source offsets, rank gaps and exact key FILETIMEs. Bound entries, strings and output.
- No inferred TypedPaths ranks, per-entry key times, navigation/search success, user attribution, target resolution/execution or automatic joins. Actual NTUSER/Windows/Linux/EnCase validation remains outstanding.

## Windows system information port

- System information work belongs on `codex/python-system-info`, based on `4638b5101ef3c5ec389d7d77418fe62acd8557c4`. Preserve EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/SYSTEM_INFO_CLI.md` and `docs/SYSTEM_INFO_TESTS.md`; run full discovery with the EVTX extra. Reuse bounded REGF/FILETIME readers without changing existing decoder semantics.
- Schema 14 adds system_info observations. Resolve Select/Current without fallback; retain separate name/version/configuration fields, raw values/offsets and exact key/value times. Bound rows, values, strings and output.
- No product-key derivation, guessed OS/owner identity, timezone application to past events, boot/uptime/clean-shutdown inference or cross-hive joins. Actual SOFTWARE/SYSTEM/Windows/Linux/EnCase validation remains outstanding.

## SAM account metadata port

- SAM account work belongs on `codex/python-sam-accounts`, based on `def0c228b0ef2721470d63e3adbf14719311428c`. Preserve EnScript bytes, archive refs/manifests and reconstructed history.
- Read `docs/SAM_ACCOUNTS_CLI.md` and `docs/SAM_ACCOUNTS_TESTS.md`; run full discovery with the EVTX extra. Reuse bounded REGF/FILETIME readers without changing existing semantics.
- Schema 15 adds sam_accounts/sam_name_mappings. Decode exact 80-byte binary F metadata and bounded selected V strings; retain RID/name discrepancies, raw selected fields/offsets and exact times. Full V/credential payload is not exported. Bound accounts, mappings, values, strings and output.
- No boot-key/hash extraction or decryption, SID/group/admin identity inference, guessed password expiry or automatic cross-hive joins. Actual SAM/Windows/Linux/EnCase validation remains outstanding.

## Cross-platform M0 baseline

- M0 implementation lives on `codex/cross-platform-m0`, based on design commit `c042136`. Read `docs/M0_BASELINE.md` and `docs/M0_TESTS.md` before changing portability tooling or support claims.
- Preserve EnScript, archive refs/manifests and reconstructed history. Package 0.15.0/report schema 15 remain unchanged in this unreleased compatibility revision.
- Keep `compatibility/support.json` consistent with code/contracts/tests. Implementation maturity, synthetic/acquired evidence qualification and exact host validation are separate; runner labels alone never establish tested support.
- Run full unittest discovery with `.[evtx]`, `python tools/portability.py validate`, and the strict suite gate. Validate the installed wheel with isolated Python outside checkout. Keep generated result directories, wheelhouses and evidence out of Git.
- Named CI targets remain unvalidated until their actual runs pass; local macOS and Linux container results do not certify Windows or other builds/architectures. Full archive verification requires the original local backup ref; do not fabricate/rewrite it in CI.
