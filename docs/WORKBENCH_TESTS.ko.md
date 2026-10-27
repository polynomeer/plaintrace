# 작업대 테스트·화면 검증

[English](WORKBENCH_TESTS.md) | **한국어**

2026-10-27 · 로컬 보고서 작업대 구현. 보고서 스키마 15·기존 파서 의미 유지.

## 범위·실행 사례 매핑

Python 신규 9개로 기존 491개 suite를 500개로 확장했습니다. Node 기본 테스트 12개는 DOM 없이 브라우저 데이터 모델을 검증합니다. 브라우저 검토는 단위 테스트와 구분하며 접근성·브라우저 전반의 인증이 아닙니다. 합성 fixture·생성 결과는 Git 밖에 둡니다.

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

## 수행한 검증

2026-10-27 macOS/Python 3.14.8·python-evtx 0.8.1에서 Python 500개가 skip 없이 통과했습니다. Node 23.10.0에서 모델 12개가 통과했고 정밀도·중첩·문자열·크기 제한, 고아/중복 ID, 미지원 스키마/counts, 비활성 HTML/prototype 키, UTC 정밀도·페이지 처리를 검증했습니다. 서버 테스트는 패키지 경로만 제공, loopback 바인딩, 명시 MIME, 업로드·경로 이탈·외부 Origin 거부, 응답 헤더를 확인합니다. Python HTTP handler는 잘못된 이중 슬래시 경로를 정규화해 403 대신 404로 거부할 수 있으며 둘 모두 내용 제공을 거부해야 합니다.

JavaScript CI는 Ubuntu 24.04의 Node 22를 대상으로 실행해 통과했습니다. 정확한 커밋·환경과 Python 6개 트랙 결과는 [CI 결과 기록](WORKBENCH_CI.ko.md)에 보관합니다.

## 브라우저 검토·남은 검증

macOS의 in-app 브라우저에서 합성 데모 내비게이션·소스 선택·원시 레코드 modal·타임라인을 검토했습니다. 실제 CLI로 만든 합성 Chromium 보고서를 브라우저 선택기로 불러와 소스 1개·관측 12개, 소스 해시, Unicode·개행·원시 레코드 참조를 확인했습니다. 획득 증거는 사용하지 않았습니다.

1,050·850·560 CSS 픽셀 breakpoint, 라이트/다크/시스템 토큰, reduced-motion 규칙을 구현했습니다. 이 소스 규칙을 모바일·스크린리더·터치·모든 브라우저의 검증 완료라고 주장하지 않습니다. 최초 로컬 검토 시 Windows/Linux 렌더링과 다른 엔진은 미검증이었습니다. 이후 Windows/Linux Chromium·Firefox·WebKit 실행과 수정 결과는 [브라우저 검증](WORKBENCH_BROWSER.ko.md)에 기록합니다. 상표 Safari·구형 버전·대형 보고서·보조 기술은 해당 게이트 범위 밖입니다. 원시 DB 분석·라이브 획득은 기존 CLI 또는 뷰어 범위 밖입니다.

Python 3.10.22에서 체크아웃 밖의 설치 wheel 스모크 검증도 통과했습니다. `site-packages`에서 패키지를 가져왔고, 패키지 자산 경로 30개와 `plaintrace-ui --help`를 확인했습니다. 이는 패키징과 CLI 시작 검증이며 Windows/Linux 브라우저 렌더링 검증은 아닙니다.

## 설치된 작업대 CI 게이트

6개 Python 호스트 트랙은 체크아웃 밖에서 격리 Python으로 [verify_workbench_install.py](../tools/verify_workbench_install.py)도 실행합니다. 설치된 모든 웹 자산을 빌드 wheel과 비교하고, 콘솔/모듈 도움말 및 루프백 HTTP 경로 30개의 바이트·MIME·CSP를 확인합니다. 생성된 `workbench.json`은 smoke 아티팩트에 보관하며 브라우저 렌더링은 검증하지 않았다고 명시합니다. 소스 테스트만으로는 패키지 자산 포함 여부가 검증되지 않습니다.

```sh
python -I /absolute/path/to/plaintrace/tools/verify_workbench_install.py --wheel /absolute/path/to/plaintrace-0.15.0-py3-none-any.whl
```

해당 wheel을 설치한 뒤 임시 디렉터리에서 실행합니다. 로컬 macOS/Python 3.10.22에서 경로 30개와 wheel 자산 30개로 통과했습니다. 호스팅 결과는 [CI 결과 기록](WORKBENCH_CI.ko.md)에 보관합니다.

[호스팅 CI 결과](WORKBENCH_CI.ko.md): Python 6개 트랙, 설치된 CLI/UI와 Node 모델 검증이 통과했습니다.

[Windows/Linux 브라우저 검증과 수정 기록](WORKBENCH_BROWSER.ko.md)
