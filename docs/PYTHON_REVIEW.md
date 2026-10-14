# Python CLI Code Review

**English** | [한국어](PYTHON_REVIEW.ko.md)

## Scope and Preservation

Reviewed on 2026-10-14 on codex/python-browser-cli, covering every Python module, packaging, executable fixtures and bilingual documentation. This is manual code review plus runtime tests on synthetic evidence; no independent reviewer or real acquired-profile certification is claimed. EnScript remains byte-identical to bb476180453c76f7d38e5b6a9f1f025ad2273ce0. The original archive tag, manifests and all 263 synthetic 2017 commits remain unchanged.

## Findings and Fixes

| Priority | Finding | Resolution |
| --- | --- | --- |
| High | Decoding an entire query fails on an unrelated malformed UTF-8 field and loses valid search terms | Decode recognized fields independently; diagnose invalid fields and retain valid neighbors |
| High | Resolving a dangling final output symlink silently writes its target | Resolve parent only and reject any existing final symlink |
| High | A new output DB can be published next to stale SQLite sidecars | Reject existing output WAL/SHM/journal before serialization and before publication |
| Medium | ISO timezone conversion can overflow and escape the documented failure handling | Convert overflow to invalid_timestamp diagnostic with raw value retained |
| Medium | JSON stdout can contain a partial object after unsupported-value serialization fails | Complete strict JSON serialization before writing stdout; reject nonfinite JSON values |
| Medium | Browser table names can identify views, causing inferred native-row provenance to be incorrect | Reject views masquerading as supported native tables |
| Medium | Firefox download summaries omit the selected annotation and event IDs | Export annotation_ids and start_visit_id and verify JSON/SQLite lineage |
| Medium | Orphan stored keywords and reversed download times are not diagnosed | Preserve values and emit targeted diagnostics |
| Low | Programmatic unsupported output format silently chooses JSON | Reject unsupported formats explicitly |

## Verified Results

| Check | Result |
| --- | --- |
| Actual Python fixture tests | 33 passed on macOS/Python 3.14, including nine review regressions |
| Existing EnScript contract tests | 11 passed; these remain portable static/SQL checks |
| Generated references | Four documents match the unchanged EnScript sources |
| Bilingual documentation | Repository checker verifies structures, technical literals, links and all 33 mapped Python cases |
| Archive and source preservation | Archive-only verifier and direct branch-base comparison pass |
| Packaging | Build/install and installed console smoke test in an isolated temporary environment |
| Whitespace | git diff --check passes |

The [test plan](PYTHON_TESTS.md) lists every executable case. The [usage contract](PYTHON_CLI.md) documents additive download lineage fields, diagnostics and output handling. Existing archive hashes are not replaced by hashes of the Python port.

## Remaining Limits

Real acquired profiles across browser versions, Windows/Linux, minimum-version Python execution, large datasets and power-loss behavior remain unvalidated here. Output filesystems must support hard links; sidecar checks are not an atomic reservation of all related paths. Hash stability does not make live acquisition atomic or prove a supplied WAL belongs to the DB. Results and serialized stdout reside in memory. Broken output streams can still produce partial transmitted stdout. Unsupported malformed row types may fail a command rather than be repaired. This CLI does not carve deleted rows, recover uncommitted transactions, open encrypted DBs, extract evidence images, or implement the remaining non-browser modules/IE artifacts.

EnCase compilation/execution remains unverified and is not established by Python tests. The user has authorized final integration through a normal merge after local checks. Merging does not establish real-profile, Windows/Linux or EnCase validation and does not rewrite EnScript, archive tags or historical commits.
