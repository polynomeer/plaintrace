# Workbench tests and visual verification

**English** | [한국어](WORKBENCH_TESTS.ko.md)

2026-10-27 · Local report-workbench implementation. Report schema 15 and parser semantics retained.

## Scope and executable mapping

Nine new Python cases extend the existing 491-case suite to 500. Twelve Node built-in tests exercise the browser's data model without a DOM. Browser inspection is separate from these unit tests and is not an accessibility or cross-browser certification. Synthetic fixtures and generated outputs stay outside Git.

| ID | Test method |
| --- | --- |
| UI-01 | test_only_packaged_assets_and_loopback_bind |
| UI-02 | test_scripts_styles_and_icons_have_explicit_types |
| UI-03 | test_no_working_directory_or_traversal_served |
| UI-04 | test_host_and_cross_origin_requests_rejected |
| UI-05 | test_no_upload_or_mutation_methods |
| UI-06 | test_head_security_headers_and_query_do_not_expose_files |
| UI-07 | test_support_projection_matches_registry |
| UI-08 | test_invalid_port_and_help_do_not_start_server |
| UI-09 | test_asset_bundle_has_no_remote_dependencies_or_inline_scripts |

| ID | JavaScript model case |
| --- | --- |
| JS-01 | demo is complete schema 15 with scoped sources and unmodified raw values |
| JS-02 | schema collection set mirrors Python report collections |
| JS-03 | version, malformed JSON and count mismatch reject without mutating model |
| JS-04 | duplicate, orphan, object and absent source IDs are rejected |
| JS-05 | format filters and search never infer browser evidence OS |
| JS-06 | timeline preserves UTC precision, duplicates and never maps registry key times |
| JS-07 | summary/proxy labels remain distinct and original raw ticks remain exact |
| JS-08 | invalid calendar and unzoned times never become timeline events |
| JS-09 | numeric precision, deeply nested data and long strings are bounded |
| JS-10 | hostile HTML, URLs, paths and prototype keys remain inert data |
| JS-11 | pagination clamps and retains every row without sorting or deduplication |
| JS-12 | oversized byte length and excessive source counts reject |

## Executed validation

On 2026-10-27, macOS/Python 3.14.8 with python-evtx 0.8.1 passed all 500 Python tests without skips. Node 23.10.0 passed all twelve model cases, including precision/depth/string/size limits, orphan/duplicate IDs, unknown schema/counts, inert HTML/prototype keys, UTC precision and pagination. The server tests confirm packaged-only routes, loopback binding, explicit MIME, denied uploads/traversal/foreign origins and response headers. Python's HTTP handler may normalize an invalid double-slash path to 404 rather than 403; both are required to reject content.

The JavaScript CI workflow targets Node 22 on Ubuntu 24.04. Subsequent hosted execution passed; see the [CI result record](WORKBENCH_CI.md) for exact commits, environments and all six Python lanes.

## Browser review and remaining checks

Manual in-app browser review on macOS exercised synthetic demo navigation, source selection, raw-record modal and timeline. A real CLI-generated synthetic Chromium report was selected through the browser picker and displayed one source/twelve observations, a source hash, literal Unicode/newlines and raw record references. No acquired evidence was used.

The implementation includes responsive breakpoints at 1,050, 850 and 560 CSS pixels, light/dark/system tokens and reduced-motion rules. These source rules are not a claim of completed mobile, screen-reader, touch-device or all-browser validation. At this initial local-review stage Windows/Linux UI rendering and other engines were untested. Subsequent Windows/Linux Chromium/Firefox/WebKit execution and repairs are recorded in [browser validation](WORKBENCH_BROWSER.md). Branded Safari, older versions, very large reports and assistive technology remain outside that gate. Raw DB analysis and live acquisition remain in the CLI/outside this viewer.

Installed-wheel smoke verification also passed outside the checkout on Python 3.10.22: the wheel imported from `site-packages`, exposed 30 packaged asset routes, and `plaintrace-ui --help` succeeded. This verifies packaging and CLI startup, not Windows/Linux browser rendering.

## Installed workbench CI gate

Each of the six Python host lanes also runs [verify_workbench_install.py](../tools/verify_workbench_install.py) with isolated Python outside the checkout. It compares every installed web asset to the built wheel, checks console/module help, and fetches all 30 loopback HTTP routes with exact bytes, MIME and CSP checks. The generated `workbench.json` is retained with the smoke artifact; it explicitly records that browser rendering is not tested. Source tests alone do not verify package-data inclusion.

```sh
python -I /absolute/path/to/plaintrace/tools/verify_workbench_install.py --wheel /absolute/path/to/plaintrace-0.15.0-py3-none-any.whl
```

Run from a temporary directory after installing that wheel. Python 3.10.22 on local macOS passed this gate with 30 routes and 30 wheel assets. Hosted results are recorded in the [CI result record](WORKBENCH_CI.md).

[Hosted CI results](WORKBENCH_CI.md): all six Python lanes, installed CLI/UI and Node model checks passed.

[Windows/Linux browser validation and repairs](WORKBENCH_BROWSER.md)

[Windows client/vendor browser results and Windows 10 gap](WORKBENCH_VENDOR_BROWSERS.md)
