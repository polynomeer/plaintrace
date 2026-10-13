# Retrospectively Reconstructed Development History

**English** | [한국어](HISTORY.ko.md)

Archived implementation descriptions and review findings in this document refer to tag `archive/pre-improvements-2026-10-13`. See [the improvement record](IMPROVEMENTS.md) for changes and remaining validation on the current improvement branch.

Document date: **2026-10-13**. Commits dated **2017-07-01–2017-11-30 (+09:00)** are an **archival retrospective reconstruction** from the surviving final source snapshot. They are not recovered original Git records. Dates, development order, and work intervals were assigned for presentation and must not be used as evidence of actual historical activity or contributions.

## Reconstruction Method

- The five existing commits on `master` were not used as parents of the new chain.
- The original README and 13 EnScript files were preserved exactly. The initial README may itself contain material written later; it is not presented as an original document from 2017.
- The chosen order was README → system information → file metadata → accounts → Recycle Bin → logon/power → USB → Prefetch → LNK → recent documents → downloads → web visits/keywords → timeline → main assembly. This is an explanatory order, rather than a claim about the actual development sequence.
- The source was divided into 263 commits for class fields/constructors and individual methods. Small data classes were kept as class-level units; method bodies were not split into arbitrary line-count fragments.
- Dates were distributed evenly from 2017-07-01 10:00:00 to 2017-11-30 18:00:00. Author and committer dates were set to the same value, using the existing local Git author configuration. Historical contributions by individual authors were not inferred.
- Every subject starts with `archive:`, and every body discloses the retrospective reconstruction and synthetic dates/order.
- Temporary closing braces were added as classes were preserved progressively. Intermediate stages that depend on methods, modules, or shared classes introduced later are incomplete builds. Compilation of every commit is not guaranteed.
- The final 2017-dated commit has exactly the same Git tree as the previous final commit. Encodings, BOMs, CRLF line endings, comments, and existing implementation issues were preserved.
- Codex setup, analysis documents, and verification tools were separated into follow-up commits with actual work dates. After the initial local reconstruction, the remote `master` was updated on 2026-10-13 at the user's request.

## Inspecting the Archive

```sh
python3 tools/inspect_sources.py
python3 tools/inspect_sources.py Win_TimeLine.EnScript --start 2006 --end 2120
python3 tools/verify_archive.py --archive-only
git log --reverse --format='%h %aI %s' master
```

`docs/history-map.json` records sequence numbers, dates, files, subjects, and commit IDs. `docs/source-manifest.json` records SHA-256 hashes and sizes for the 14 original files. Because the README has since been updated, the verification tool checks its snapshot at the last reconstructed commit and the 13 current EnScript files.

UTF-16 diffs use the local setting `diff.enscript.textconv = python3 tools/enscript_textconv.py`. In a new clone, run the following once to enable decoded diffs. This does not change the original blobs.

```sh
git config --local diff.enscript.textconv 'python3 tools/enscript_textconv.py'
```

## Backup and Recovery

Previous final commit: `6814d18c75aa` (the full ID can be retrieved from the archive ref).

- Git ref: `refs/archive/pre-reconstruction`
- Git bundle containing the original refs: `.history-backup/original-6814d18c75aa.bundle` (an ignored local backup)
- The original history remains in the archive ref and bundle. Consequently, `git log --all` may also show the old history. Use `git log master` to inspect the new development history.

To recover the original repository in a separate directory, use the following commands. They do not overwrite the reconstructed history.

```sh
git bundle verify .history-backup/original-6814d18c75aa.bundle
git clone .history-backup/original-6814d18c75aa.bundle /tmp/plaintrace-original
```

Keep a separate copy of the bundle to protect the local backup. The remote `master` history was replaced using `--force-with-lease`, and its final commit was verified against the local branch immediately afterward. Subsequent documentation changes are recorded as ordinary follow-up commits.
