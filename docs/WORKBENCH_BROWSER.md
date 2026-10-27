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
