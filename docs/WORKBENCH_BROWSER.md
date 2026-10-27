# Workbench browser validation

**English** | [한국어](WORKBENCH_BROWSER.ko.md)

2026-10-27 · Browser behavior is separate from Python-host qualification and the schema-15 model tests.

## Scope and executable mapping

[Browser tests](../tests/browser/workbench.spec.mjs) run against the installed package using isolated Python. [Configuration](../playwright.config.mjs) selects Chromium, Firefox or WebKit; [CI](../.github/workflows/ui.yml) runs each engine on Ubuntu 24.04 and Windows Server 2022. These Playwright-managed headless engines do not certify branded Chrome/Edge, Safari, Windows clients or all OS/browser versions. Viewport changes test CSS layout, not physical mobile/touch devices. Test data is authored synthetic JSON, not acquired evidence.

| ID | Browser behavior |
| --- | --- |
| B-01 | Empty state, keyboard skip link, modal Escape and returned focus |
| B-02 | Source filters/search, details, diagnostics, scoped timeline and support |
| B-03 | Native file chooser, literal hostile/Unicode text and exact raw references |
| B-04 | Invalid schema/UTF-8 rejection retains the current workspace |
| B-05 | Download matches original selected bytes including whitespace |
| B-06 | Source/record pagination retains correct source associations |
| B-07 | Light/dark/system/reduced motion, six viewport widths and screenshots |
| B-08 | Clear removes source/record/raw-dialog content from the DOM |
| B-09 | Empty storage, fresh navigation and exact environment attachment |

Every case fails on uncaught page errors, foreign HTTP requests or failed asset responses. Retries are disabled; focused-only tests are forbidden. Four full-page screenshots per engine/host cover light/dark at 1440 and 390 CSS pixels; geometry assertions also cover 1024, 850, 768 and 560. Screenshot review is separate from a pixel-diff baseline, formal accessibility audit or browser security certification.

## Reproduction and retained records

Node dependencies are development-only and pinned in package-lock.json. The production viewer still needs no Node runtime/build. The test server uses `python -I -m plaintrace.ui`, so install the package first. Run browser tests on the intended OS; no user-agent-only OS simulation is used.

```sh
python -m pip install .
npm ci
npx playwright install --with-deps chromium firefox webkit
npm run test:browser
```

Generated JSON, screenshots, traces and downloaded reports remain outside Git. Set PLAINTRACE_BROWSER_RESULTS to an external directory; the local default is an OS temporary directory. CI retains one artifact per host/engine for 14 days. Environment attachments record the OS/kernel/CPU, image build, Node/browser versions, user agent, commit and run. Traces are kept on failure only. The Python 500-case suite and JavaScript 12-case model checks remain independent gates.

The approach follows the official [browser projects](https://playwright.dev/docs/test-projects), [web server](https://playwright.dev/docs/test-webserver) and [CI](https://playwright.dev/docs/ci) documentation. See [prior hosted results](WORKBENCH_CI.md) for the earlier package/server checks.

## Initial failures and repairs

The [first browser run](https://github.com/polynomeer/plaintrace/actions/runs/40516981679) at `e6b8fcb` exposed B-08 on Windows Firefox/Chromium: clearing only hid the old workspace; source/record DOM and raw text remained. Commit `d0f99ea` now releases report state, removes these DOM contents and discards raw modal text on clear or successful report replacement. This reduces retained references; it is not secure memory erasure and does not remove user downloads/clipboard copies.

Windows WebKit additionally failed B-01/B-03 keyboard/focus assertions. Commit `e7823b4` makes the skip link an explicit tab stop and returns modal focus to the actual initiating control on close, rather than relying on pointer-focus behavior. Assertions remain in the regression suite.

The initial artifact upload also rejected the path containing `..`. The workflow now writes a canonical RUNNER_TEMP-based output path through GITHUB_ENV. Initial raw traces/screenshots could not be uploaded due to that error; failure messages were read from job logs. Superseded runs were canceled to prioritize the final revision; canceled jobs are not passing results.

Screenshot review found excessively narrow wrapping in the 390px observation table. Commit `dded72c` adds a table minimum width and keyboard-focusable horizontal scroll region. B-07 checks internal table scrolling without document overflow and waits for final theme colors before disabling animations for capture.

## Final execution results

The [browser run](https://github.com/polynomeer/plaintrace/actions/runs/40522922787) at commit `5f3b3203098f8fa15fa559ce7ec39b558a1110ea` passed nine cases per lane, 54 total, with zero skipped/failed/flaky cases and no automatic test retries. The same workflow's 12 model tests passed. The [six Python hosts/static job](https://github.com/polynomeer/plaintrace/actions/runs/40518755665) passed at code revision `dded72c`; `5f3b320` adds documentation only. Each Python lane ran 500 EVTX-inclusive tests and installed CLI/UI verification. These Python results are scoped to that earlier run rather than unfinished follow-up jobs. Playwright 1.64.1 is pinned.

| Lane | Actual OS/kernel/CPU | Engine version | Node | Image build | Result |
| --- | --- | --- | --- | --- | --- |
| [ubuntu-24.04 / chromium](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580849) | Ubuntu 24.04 / 6.17.0-1022-azure / x64 | 156.0.8078.4 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [ubuntu-24.04 / firefox](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580193) | Ubuntu 24.04 / 7.0.0-1017-azure / x64 | 157.0 | v22.23.4 | 20261026.354.1 | 9 pass / 4 PNG |
| [ubuntu-24.04 / webkit](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580518) | Ubuntu 24.04 / 6.17.0-1022-azure / x64 | 27.2 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [windows-2022 / chromium](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580103) | Windows Server 2022 / 10.0.20348 / x64 | 156.0.8078.4 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |
| [windows-2022 / firefox](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580222) | Windows Server 2022 / 10.0.20348 / x64 | 157.0 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |
| [windows-2022 / webkit](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580131) | Windows Server 2022 / 10.0.20348 / x64 | 27.2 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |

WebKit's user agent contains macOS text even on real Windows/Linux hosts. OS identity was checked from the process environment and runner image, not user-agent text. Representative Windows/Linux screenshots were inspected for text/icons, selection, light/dark themes and narrow-table layout; all 24 captures remain in artifacts. Automated geometry checks ran on every engine; this is not manual review of every pixel or a formal accessibility audit.

## Result digests and remaining scope

Result JSON was checked for the tested SHA/run, nine expected passes, zero skipped and zero flaky cases. The screenshot digest hashes a compact key-sorted JSON map of filename to SHA-256. Generated reports/screenshots remain outside Git; only reviewed digests are committed. Initial failures remain recorded, and later documentation commits are distinct from this tested revision.

| Lane | Result JSON SHA-256 | Screenshot map SHA-256 |
| --- | --- | --- |
| ubuntu-24.04 / chromium | 2ffc589cef6838f020f401b6924e4a8bab66037925512d67a34fe9f5e8f2b150 | 320ef3da01996410ca831c50175a46229d812f1563a57e783b6cda5e5ea732b8 |
| ubuntu-24.04 / firefox | 0cb5b1fb2d25498f14c06ee662dde7da1b13b0db363e9dd87416ae181f441804 | 7a22234a29695e6ebadaa4f4af7167d1e8053b4bdbde0c4dea13f6129a1eebeb |
| ubuntu-24.04 / webkit | 23dfc62bbbd8b8f8227edb231da140e93996c95ba2d4a80e1fc41a4b7d8c28c7 | 0d9f396450086ab2bc8fe017819546b8b3c0af3184cfc486527eaf09ac647615 |
| windows-2022 / chromium | 8615ab166698596073491391afdac9d4e1b3f16751053f17d04334db06ef82fc | 6d28e48c87f9570fa4249fafa4274b4e0aabd8cb19ff118824a681c926ab0b7c |
| windows-2022 / firefox | 6d5fc3d8f0e1a24cc203d9d63e88eb4047eea549e637c5d90b5d56127bff7ac6 | 164e742c3702f987b7e58d3ff9b3129c18e11431c59b6fbf9075cd126290c8d3 |
| windows-2022 / webkit | d02f848e9e6d919a9bd78d1948e064c95f0909781c858f4af6882c00d49db32b | e4e6d403d0e13c9e6c8d52b328d014d56d2d438baeda4b1512d58e6b9df22c93 |

Windows 10/11 clients, other Linux distributions/architectures, branded Chrome/Edge/Safari, older browsers, physical touch devices/screen readers and large acquired reports require separate qualification. Local archive-only verification preserved 13 original EnScript files and 263 synthetic historical commits. No new EnCase-runtime or evidence-interpretation accuracy claim is made.

The earlier `dded72c` run had prolonged Linux WebKit runner/setup delays; cancellation and runner re-request were attempted. Pending/canceled states were never counted as passes. The final table uses only the new documentation-inclusive `5f3b320` run where all six lanes completed successfully.
