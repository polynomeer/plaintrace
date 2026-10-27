# Workbench hosted CI validation

**English** | [한국어](WORKBENCH_CI.ko.md)

2026-10-27 · Branch `codex/ui-workbench`; package 0.15.0 / report schema 15 retained.

## Outcome and tested revision

The [six-host workflow](https://github.com/polynomeer/plaintrace/actions/runs/40513174605) passed all six Python lanes plus static-integrity at commit `2061db68a08891418790d3ee7cbd14af0ebef020`. Every lane ran 500 tests with python-evtx 0.8.1/hexdump 3.3 and zero skips, failures, errors or expected failures. Each also passed the installed CLI smoke and the new installed-workbench gate. The [model workflow](https://github.com/polynomeer/plaintrace/actions/runs/40513184693) passed all 12 cases with zero skips/failures on Node 22.23.3 at the same commit. This is synthetic-data and package/server validation, not acquired-evidence accuracy, browser rendering or every OS release.

| CI lane | Actual Python / SQLite | Actual OS / CPU | Image build | Result |
| --- | --- | --- | --- | --- |
| [macos-14 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903928) | 3.10.11 / 3.40.1 | macOS 14.8.9 / arm64 | 20260831.0302.1 | 500 / CLI / UI pass |
| [macos-14 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903907) | 3.14.7 / 3.50.4 | macOS 14.8.9 / arm64 | 20260831.0302.1 | 500 / CLI / UI pass |
| [ubuntu-24.04 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903941) | 3.10.22 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 20261023.334.3 | 500 / CLI / UI pass |
| [ubuntu-24.04 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219904158) | 3.14.8 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 20261023.334.3 | 500 / CLI / UI pass |
| [windows-2022 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903961) | 3.10.11 / 3.40.1 | Windows Server 2022 / 10.0.20348 / AMD64 | 20261022.344.1 | 500 / CLI / UI pass |
| [windows-2022 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903898) | 3.14.9 / 3.50.4 | Windows Server 2022 / 10.0.20348 / AMD64 | 20261022.344.1 | 500 / CLI / UI pass |

Windows Python 3.10 reports platform.release as 10; the Server 2022 image/build establishes the actual host, not Windows 10 client support. The original M0 qualification in [support.json](../compatibility/support.json) is preserved as historical evidence; this new UI run does not silently replace its commit-scoped results or expand supported OS versions.

## Changes and failure review

The initial UI commit `66830db58f35d8963eeb025df35f735ff5f398d1` was pushed and its [model run](https://github.com/polynomeer/plaintrace/actions/runs/40512909841) passed. Review found that the existing installed CLI smoke compared Python modules but did not exercise packaged web assets. Commit `2061db6` adds [verify_workbench_install.py](../tools/verify_workbench_install.py) to every Python lane: isolated import outside checkout, all wheel asset bytes, console/module help and all 30 loopback HTTP routes with exact content, MIME and CSP. This closes a validation gap; no failing parser/UI test, host-specific skip or failure waiver was needed in the final run.

[Workflow definitions](../.github/workflows/portability.yml) and the [model workflow](../.github/workflows/ui.yml) passed actionlint locally. The strict local suite also passed 500 cases; the local Python 3.10.22 installed-workbench gate passed before pushing the extension. Archive-only verification preserved all 13 EnScript files and 263 synthetic historical commits. Static CI checked documentation/source references, EnScript contracts and preserved baseline blobs/manifests.

## Retained result digests

Downloaded suite records were checked for the exact tested SHA/run, 500 tests and empty failure/skip lists. Every recorded Python source digest matched the tested Git commit, accounting for Windows checkout CRLF. Installed CLI and UI records share the same wheel digest within each lane. Raw generated result JSON, logs and wheels remain outside Git; the table retains reviewed SHA-256 summaries. Actions artifacts expire after 14 days and are not permanent evidence custody or a reproducible-build claim.

| CI lane | Suite record SHA-256 | CLI smoke record SHA-256 | UI smoke record SHA-256 | Wheel SHA-256 |
| --- | --- | --- | --- | --- |
| macos-14 / 3.10 | bd59aeff8387123b61ae31300dd6d78cd43fb7d7a0e2d563153c88276d8ee94a | a83b5e812b68279a28acb59462a19adadf9a6668bbd1ed8b5051ed8fc52700a0 | 071438231e693db81b98a5960f576e2ac13b162e71d3e2e6f8aed37b7a4ec6c2 | e83eb3573b6959ed51c444f1bfa78898f9638918ea089457632fa1b1bf87e118 |
| macos-14 / 3.14 | fe2847e07b5b71c2c14aa760137d145b077092623963715ce412f3f31a232688 | 8631ba07bf4fb38af1109bd3fa11dcaeb47f173aca899e6cdece59967e3e531a | 9e0d1a6e05f5828eedcd16c8a6a8b5b84a5c93ddd9aa95ab0ccfa8b42e96157c | 33d2ec78cfc649a3968050f3aca5c8f74b2f51db56b8a70925eca394cae18bb6 |
| ubuntu-24.04 / 3.10 | af5cc9e9b676297e31e0a29bb2664adaa374c4652140e036f99a2465a0349c05 | 164c4e26631606df017fca5a77d8963bd6311cf9ca0b9fbce37f0d6bd63f4f2e | 48dd1fba47930608f7436b54c0880ea9121f5bbff3f17cf59e03882c23bc1f9e | 8954b1dab94bbf76d3369d20fb8422de9a6cd17cf9b0fe0e3776c2fbaf5c8a14 |
| ubuntu-24.04 / 3.14 | 2877f810b1f158adbe2df17cd4e10509c1846667a86abe76d8f51e53fbaf2dc8 | 6bf9931c49f4e3c5aeb75f536eeaf679a2f7efcc09c1579d4f69b499696b175b | f211a3218276d5c08e8a7bddf048204a191d9e40867e79d56517aeeed82df820 | 182fbe155439a501c53717c8314bfc6446467a94c19b805b8bc5258986b02b11 |
| windows-2022 / 3.10 | 94a18224663e41ca28dc82b4c19609758a98483a55fc50d2f4c6de082ad5cd54 | 16e6e49679b5894a537411eafd092cfbcdb9af7d2d234c920b4cecfda3992cd2 | 497ef0e3f762ff979c81e832a6b0386cc0f4d0cb765cddf4da72eaae43239508 | 3d832a22d6c751cef57084b7b0b549f72d9f6a33b6efb3d1ea9be0b5c786b6aa |
| windows-2022 / 3.14 | 4683f25d8f2318e09127c2260f43cf64739821ae47139c222237959169d4e109 | d901d5126046315cab94c887c4330b996c05301e88f3d9e38379c08f1f59fb00 | 6970c7614cebbaa27d0f83c0fe1eced525c37825579a979fc70d4a1864f5f728 | 3c2f9cfca2aa0b084776349664db88ccb5ee88296c28fbb0407761019c935f24 |

## Reproduction and limits

Use the commands in [workbench tests](WORKBENCH_TESTS.md) and [M0 baseline](M0_BASELINE.md). CI writes `workbench.json` beside the existing smoke result and retains it in each `portability-<runner>-py<minor>` artifact. Browser DOM/visual behavior, Safari/Firefox, assistive technology, Windows/Linux UI rendering, Windows clients and other OS builds/architectures still require separate validation. No EnCase compilation/runtime claim is made. Documentation follow-up commits describe this exact tested revision and trigger their own CI; they do not retroactively change these recorded results.
