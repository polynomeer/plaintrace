# Windows clients and vendor browser validation

**English** | [한국어](WORKBENCH_VENDOR_BROWSERS.ko.md)

2026-10-28 · Branch `codex/ui-workbench`; package 0.15.0 / report schema 15 unchanged.

## Outcome and explicit incomplete scope

At commit `1058df858aa6706314ebcd609930af8eec1ba7e5`, the [vendor workflow](https://github.com/polynomeer/plaintrace/actions/runs/40610687294) passed all seven jobs: six Chrome/Edge lanes with nine cases each (54) and actual Safari with nine checks, 63 total. No automatic test retry, skip, failure or flaky result was used. The [Python host workflow](https://github.com/polynomeer/plaintrace/actions/runs/40610687356) also passed all six lanes (500 cases each), installed CLI/UI checks and static-integrity. These are measured tuples, not every Windows/browser release.

**Windows 10 remains unvalidated.** No Windows 10 runner or VM is connected; the repository runner inventory was empty and the local host is macOS. A Windows 10 environment was requested from the user. Server 2022, Windows 11, Wine/CrossOver or a Windows 10 user-agent are not substitutes. The [manual Windows 10 gate](../.github/workflows/windows10-browser.yml) is prepared but was not dispatched and has no passing result. This prevents claiming the entire requested Windows 10/11 scope is complete.

## Exact executed environments

[Playwright configuration](../playwright.config.mjs) uses vendor `chrome`/`msedge` channels rather than relabeling managed Chromium. Windows 11 uses the image's already-installed vendor browsers; macOS/Linux resolve stable vendor packages during setup. Versions below were measured. Windows-client attestation uses Win32_OperatingSystem Caption, ProductType=1 and build >=22000, separately from browser user-agent. Both Windows 11 jobs reported Microsoft Windows 11 Enterprise / 10.0.26200 / ARM 64-bit Processor. Node ARM64 does not establish browser-process architecture or qualify Windows x64 clients.

| Job | Actual OS/kernel/CPU | Browser version | Node/Python | Image build | Result |
| --- | --- | --- | --- | --- | --- |
| [macos-14 / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198445) | darwin / 23.6.0 / arm64 | 156.0.8078.74 | v22.23.2 | 20260831.0302.1 | 9 pass / 4 PNG |
| [macos-14 / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198496) | darwin / 23.6.0 / arm64 | 156.0.4314.50 | v22.23.2 | 20260831.0302.1 | 9 pass / 4 PNG |
| [ubuntu-24.04 / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198395) | linux / 6.17.0-1022-azure / x64 | 156.0.8078.73 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [ubuntu-24.04 / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198629) | linux / 6.17.0-1022-azure / x64 | 156.0.4314.50 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [windows-11-arm / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198821) | win32 / 10.0.26200 / arm64 | 156.0.8078.48 | v22.23.4 | 20261022.194.1 | 9 pass / 4 PNG |
| [windows-11-arm / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198328) | win32 / 10.0.26200 / arm64 | 156.0.4314.42 | v22.23.4 | 20261022.194.1 | 9 pass / 4 PNG |
| [macos-14 / Safari](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198172) | macOS-14.8.9-arm64-arm-64bit-Mach-O | 26.6 | Python 3.14.7 | 20260831.0302.1 | 9 pass / 2 PNG |

Safari runs headed through `/usr/bin/safaridriver` and requests browserName=safari; capabilities record Safari 26.6, macOS 14.8.9 and simulator=false. It is the installed Safari app, not Playwright WebKit or Safari Technology Preview. CI enables Safari automation only in the disposable macOS runner. Local Safari 26.6.2 on macOS 26.6.2/build 25G83 also showed the empty workbench, keyboard skip link, Escape/focus return and a synthetic report selected through the native file chooser. Literal HTML/Unicode appeared as text. That manual review is separate from the CI check count and does not establish download-byte or responsive coverage for Safari.

## Test scope and first failure

Chrome/Edge reuse B-01–B-09 in [browser validation](WORKBENCH_BROWSER.md), including native picker, rejected UTF-8/schema, exact original download, source/record pagination, six viewport widths, theme/focus/clear behavior and no external HTTP requests/page errors. Each produces four light/dark, 1440/390 screenshots. Synthetic data only; generated reports/images stay outside Git.

[Safari checks](../tests/browser/safari_webdriver.py) use the standard-library WebDriver client and the installed isolated Python server. They have a deliberately different, narrower scope:

| ID | Safari check |
| --- | --- |
| S-01 | empty workspace |
| S-02 | native help modal |
| S-03 | demo source and record rendering |
| S-04 | source format filtering |
| S-05 | explicit-field timeline |
| S-06 | raw values and source references |
| S-07 | theme switching |
| S-08 | clear removes report DOM and raw cache |
| S-09 | no automatic report persistence |

Safari CI does not automate file upload/download, clipboard, viewport emulation, network/page-error instrumentation or screen-reader auditing. The first [Safari run](https://github.com/polynomeer/plaintrace/actions/runs/40610628667) at `889cced` failed S-06 because the harness expected a visit after a Windows-format filter had retained the event source. Repair `1058df8` explicitly selects the browser source before opening its record; the same raw-value assertion then passed. This was a test setup error, not a demonstrated UI defect. No product code was changed to force green tests; earlier focus/clear/table fixes remain covered.

## Retained records

The result JSON was checked for the exact SHA/run, nine passes and zero skipped/flaky/unexpected results. Windows attestation hashes identify client OS records; Safari result includes capability and screenshot hashes. Reviewed representative screenshots show labels/icons, themes and selected-source layout; this is not a full pixel-diff or accessibility audit. Raw records, traces, downloads and images remain outside Git. Artifacts expire after 14 days; the digests below are not permanent evidence custody.

| Job | Result JSON SHA-256 | Windows client attestation SHA-256 |
| --- | --- | --- |
| macos-14 / chrome | 0cd3c6b9607d480654b53feb91e129ab9bbcceedce52aa0eacdbe7727cd0578a | — |
| macos-14 / msedge | ede80323928bfb867a90522c435c8effeb3d9955d9a50bdb6f8a3e21f797bac2 | — |
| ubuntu-24.04 / chrome | 56abbdf2c0d85b883f686927d3b5cde4ecbc71dbfe9f050bde51b097f556c32d | — |
| ubuntu-24.04 / msedge | f7756e40eac95d418a4dba668242596bb395455c0dd0ca96a294a7fe0a8177a8 | — |
| windows-11-arm / chrome | 704751c9c790925dc070cb4dd0d311c951a618eb4069ad034014ca88b7eaf98a | f82127403f99a7ed60098f4d0b3d42f23cac69223d92a03285165385f0dac676 |
| windows-11-arm / msedge | 738f72a16715d692a23302a5124733532c591d9ea0f5da33211a13f6bc620212 | f82127403f99a7ed60098f4d0b3d42f23cac69223d92a03285165385f0dac676 |
| macos-14 / Safari | 09f7198d722573264661a0ed1a146cc3002bbdbefba2867c690ce466fc1b691f | — |

## Windows 10 prerequisites and remaining action

The manual gate requires an owner-provided, dedicated Windows 10 x64 runner labeled `plaintrace-windows10`, Node/Python setup access and preinstalled genuine Chrome/Edge. It rejects Server and builds outside 19041–21999, installs Plaintrace in a temporary virtual environment, and never replaces host browsers. It is a prepared procedure, not validation. Older Windows 10 builds and other architectures remain separate. Do not dispatch it before a suitable runner is connected. GitHub workflow_dispatch also requires the workflow to be registered on the repository default branch; this feature-branch commit does not authorize merging into master or registering a runner. The equivalent browser commands may be run directly on an approved Windows 10 host, after checking its OS identity:

```sh
python -m pip install .
npm ci
npm run test:browser -- --project=chrome
npm run test:browser -- --project=msedge
```

Keep generated results outside the checkout and retain OS/client attestation, exact browser versions and all nine test outcomes per channel. Windows 10 cannot be promoted to tested status until those records exist.

## References and tooling

Runner availability was checked against the official [hosted runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) and [Windows 11 image](https://github.com/actions/runner-images/blob/main/images/windows/Windows11-Arm64-Readme.md). Vendor channels follow [Playwright browser guidance](https://playwright.dev/docs/browsers); Safari uses [Apple WebDriver guidance](https://developer.apple.com/documentation/webkit/testing-with-webdriver-in-safari). Local actionlint 1.7.7 predates the hosted Windows 11 label; [lint configuration](../.github/actionlint.yaml) supplies it and the manual Windows 10 label explicitly. These lint labels do not register runners or establish support. All workflows pass that lint configuration. EnScript/archive refs and reconstructed history are preserved; no EnCase or acquired-evidence accuracy claim is added.
