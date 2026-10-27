# M0 cross-platform baseline

**English** | [한국어](M0_BASELINE.ko.md)

2026-10-27 · M0 implementation and validation record. Package 0.15.0 / report schema 15 retained.

## Scope and milestone status

M0 supplies an auditable baseline, a support inventory and a six-lane CI workflow. Two portability defects discovered by exercising the declared minimum interpreter are fixed. The evidence parser families, CLI flags, output schema and package version remain unchanged; this is an unreleased revision of 0.15.0, identified by source/wheel digests rather than version alone.

The named M0 hosted gate has passed; see [remote CI results](M0_CI.md). These are separate from the initial local macOS/Debian container results, and Server tests do not certify Windows 11 client. M1–M6 and the proposed GUI/schema 16 are not implemented here. See [results and remaining gates](M0_TESTS.md).

## Machine-readable inventory

[Support registry](../compatibility/support.json) inventories 17 implemented, deliberately partial artifact adapters and four planned adapters. Every implemented entry links a module, contract, CLI inputs, test files, format predicates, dependencies and exclusions. The 475 original tests form a per-module minimum inventory; new tests may extend it. This is a development inventory, not M1 runtime plugin discovery or a universal OS-version map.

Implementation maturity, evidence qualification and host qualification remain separate. Existing formats have synthetic coverage; macOS plist/Safari and Linux metadata/journal export remain planned and unvalidated. Local validation tuples include exact OS/kernel/CPU/Python/SQLite/dependency versions and a reviewed documentation reference. A runner label alone cannot set tested status. Hosted qualification requires both Python minors on matching OS/runner tuples, exact commit/run URLs and skip-free results; M0 completion requires every named host to pass.

Fixture generators and independent expected values live in source. Persistent binary fixture and golden-result-bundle hashes remain null because such bundles do not exist. The tooling records generator/test-source hashes instead and labels them as code hashes. No acquired evidence, exports or caches are committed. Structural validation checks claim consistency; it does not authenticate a reviewer or replace evidence review.

## Verification tools

[portability.py](../tools/portability.py) offers three development commands. The validate command rejects missing/escaping references, duplicate IDs, version/schema drift, missing artifact-test inventory and unsupported validation claims. The suite command requires python-evtx 0.8.1 before discovery and fails on skips, expected failures, unexpected successes, empty discovery, failures or errors. Every original artifact module must retain its baseline test count.

The smoke command runs under isolated Python, rejects a checkout import, compares installed module bytes against the supplied wheel, and invokes the installed console plus isolated module entry point in a temporary directory. An independently built SQLite fixture checks Unicode/quotes/newlines, exact timestamp conversion, source hashes/preservation, JSON/SQLite schema 15 parity, foreign keys and no-overwrite behavior. EVTX integration belongs to the full suite; the smoke input is browser-only.

Generated records contain an allowlisted environment, source/configuration hashes and test outcomes; they never dump the whole environment. Results must use a new directory outside the checkout. These are development records, not schema 15 case reports. This tooling does not acquire or process user evidence.

## CI host matrix and limits

[Workflow](../.github/workflows/portability.yml) defines Ubuntu 24.04, macOS 14 and Windows Server 2022, each on Python 3.10 and 3.14. It builds and installs a wheel with the EVTX extra, checks dependencies, validates inventory, runs the strict full suite and verifies installation outside checkout. Each lane retains environment/result artifacts for 14 days, including failures. Actions are pinned to official repository commit SHAs; permissions are read-only and no secrets or deployment are required. After the initial local task, the branch was pushed and hosted workflows were executed; exact commits and lane results are in the [CI record](M0_CI.md).

The native-shell steps use Python for wheel discovery and subprocess invocation, avoiding Bash-only path assumptions on Windows. Exact image build and architecture are recorded at runtime because OS-version labels still receive image updates. Interpreter minor selectors resolve patch versions, which are recorded rather than advertised as fixed. Build isolation resolves setuptools and transitive packages; this is not a complete dependency lock or a byte-reproducible build claim. Full locking/release reproducibility remains M6 work.

A separate Linux job checks EnScript static contracts, source references, bilingual documentation and baseline source/manifests. Full archive-only validation runs locally because the remote lacks the original local backup ref. CI never fabricates that reference. Windows symlink capability is not silently skipped by the strict gate; a missing capability fails that lane and requires an explicit support decision.

Runner selection and setup behavior were checked against the official [runner images](https://github.com/actions/runner-images) and [setup-python documentation](https://github.com/actions/setup-python) on 2026-10-27. These sources describe CI mechanics, not Plaintrace execution results.

## Compatibility fixes

SQLite snapshot connections now explicitly enable URI interpretation while retaining read-only mode. Previously, a build without default URI interpretation tried to open the URI as a filename, causing browser and mixed-input failures. A new regression uses an escaped Unicode staging path, verifies read-only behavior and unchanged input bytes.

EVTX display conversion now pads/truncates accepted fractional seconds to six digits before datetime conversion, supporting Python 3.10 as well as newer interpreters. Original XML, exact envelope FILETIME and raw SystemTime text remain unchanged. The regression covers one through seven fractional digits with UTC and explicit offsets. No new format, timestamp precision claim or schema field is introduced.

## Reproduction

Use an isolated virtual environment on the intended interpreter, then run the shared commands below from the repository root. The result/wheel directories are examples outside the checkout; choose fresh result directories for each run. Installation may access the package index; parser tests use temporary synthetic data. To reproduce the container offline, prepare a wheelhouse first, mount source read-only and use the digest in the results document.

```sh
python -m pip install ".[evtx]" build==1.6.1
python tools/portability.py validate
python -m unittest discover -s tests -v
python tools/portability.py suite --output ../plaintrace-validation/suite
python -m build --wheel --outdir ../plaintrace-validation/wheel
python -m pip install --force-reinstall --no-deps ../plaintrace-validation/wheel/plaintrace-0.15.0-py3-none-any.whl
python -I tools/portability.py smoke --wheel ../plaintrace-validation/wheel/plaintrace-0.15.0-py3-none-any.whl --output ../plaintrace-validation/smoke
python tools/verify_documentation.py
python tools/verify_archive.py --archive-only
git diff --check
```

The archive command requires the original local backup ref; the source-reference and static checks remain distinct from EnCase compilation/execution.
