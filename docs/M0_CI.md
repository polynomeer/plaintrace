# M0 hosted CI validation

**English** | [한국어](M0_CI.ko.md)

2026-10-27 · Results are scoped to the recorded run, commit and exact environments.

## Outcome and qualification scope

All six host lanes and the static-integrity job passed in the [verified run](https://github.com/polynomeer/plaintrace/actions/runs/40446197093). The tested commit is a8943e4fc58e6b7924bb20a9eea7e6d2542e8a60; every lane executed 489 tests with the EVTX extra and zero skips, failures or errors, then passed installed-wheel smoke. This satisfies the named M0 environment gate, not every OS version or acquired-evidence accuracy.

| CI lane | Actual Python / SQLite | Actual OS / CPU | Result |
| --- | --- | --- | --- |
| [windows-2022 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963992) | 3.10.11 / 3.40.1 | Windows Server 2022 / 10.0.20348 / AMD64 | 489 pass; smoke pass |
| [windows-2022 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997964093) | 3.14.9 / 3.50.4 | Windows Server 2022 / 10.0.20348 / AMD64 | 489 pass; smoke pass |
| [macos-14 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963902) | 3.10.11 / 3.40.1 | macOS 14.8.9 / arm64 | 489 pass; smoke pass |
| [macos-14 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963993) | 3.14.7 / 3.50.4 | macOS 14.8.9 / arm64 | 489 pass; smoke pass |
| [ubuntu-24.04 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997964000) | 3.10.22 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 489 pass; smoke pass |
| [ubuntu-24.04 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963936) | 3.14.8 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 489 pass; smoke pass |

Image/build/CPU and Python patch versions above were measured. Python 3.10 reports Windows platform.release as 10; this does not certify Windows 10 client, because the runner/build is Server 2022. Windows 11, other distributions/CPUs and legacy/future releases require their own validation.

## Initial failure, repair and revalidation

The [first run](https://github.com/polynomeer/plaintrace/actions/runs/40446042052) for f823c64 failed workflow validation before any job was created. Job-level env referenced the unavailable runner.temp context; plain YAML parsing did not detect this semantic restriction.

Repair commit a8943e4 reads the built-in RUNNER_TEMP and GITHUB_WORKSPACE environment variables instead. actionlint 1.7.7 reproduced the original error and passed the repaired workflow. The [retry](https://github.com/polynomeer/plaintrace/actions/runs/40446197093) passed 489 tests and installed-wheel smoke on all six lanes. No Windows-specific parser repair, skip or failure waiver was needed.

The registry gate was strengthened to require both Python minors, matching OS/runner, exact commit/run URL and skip-free results before marking a host tested. Two new regressions bring the suite to 491 cases. The first table shows the count actually executed in its linked run.

## Retained records and reproducibility

The machine-readable [support registry](../compatibility/support.json) retains six hosted tuples, image builds, dependency versions, job URLs and source/configuration/wheel/result/artifact hashes. Each host references two validated tuples. [Local results](M0_TESTS.md) remain a historical record separate from hosted qualification.

Windows Python checkouts use CRLF, so raw source hashes can differ from Unix hosts. For the first passing run, every Windows Python hash was compared against the commit content represented with CRLF and matched. No encoding conversion was used to force matching hashes; EnScript bytes/BOM/CRLF remain preserved. Wheel hashes may also differ due to build metadata; each installed copy was checked against its own wheel.

Raw logs, result JSON, wheels and caches stay outside Git; reviewed summaries and digests are committed. Actions artifacts expire after 14 days, so this is not permanent evidence custody or a byte-reproducible build claim. Documentation/static checks and baseline source/manifests passed in the separate static job; local archive-only verification checks preservation of 263 synthetic historical commits. This does not certify EnCase compilation/execution.

## Context-rule reference

Checked the [GitHub context availability table](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) on 2026-10-27: runner context is unavailable in job env but allowed in step env/run. This constraint and actionlint verification guided the repair.
