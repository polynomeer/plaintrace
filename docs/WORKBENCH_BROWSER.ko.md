# 작업대 브라우저 검증

**한국어** | [English](WORKBENCH_BROWSER.md)

2026-10-27 · 브라우저 동작은 Python 호스트 검증 및 스키마 15 모델 테스트와 구분합니다.

## 범위와 실행 매핑

[브라우저 테스트](../tests/browser/workbench.spec.mjs)는 격리 Python으로 설치 패키지를 실행합니다. [설정](../playwright.config.mjs)에서 Chromium·Firefox·WebKit을 선택하며 [CI](../.github/workflows/ui.yml)는 Ubuntu 24.04와 Windows Server 2022에서 각 엔진을 실행합니다. Playwright 관리 headless 엔진은 상표 Chrome/Edge, Safari, Windows 클라이언트 또는 모든 OS/브라우저 버전 검증을 의미하지 않습니다. 화면 폭 변경은 CSS 배치 검사이며 실제 모바일/터치 기기 검증은 아닙니다. 데이터는 직접 작성한 합성 JSON이며 획득 증거가 아닙니다.

| ID | 브라우저 동작 |
| --- | --- |
| B-01 | 빈 화면, 키보드 건너뛰기 링크, 모달 Escape와 포커스 복귀 |
| B-02 | 소스 필터/검색, 상세, 진단, 소스별 타임라인과 지원 범위 |
| B-03 | 네이티브 파일 선택, HTML/유니코드 문자와 정확한 원시 참조 |
| B-04 | 잘못된 스키마/UTF-8 거부와 기존 워크스페이스 유지 |
| B-05 | 공백까지 선택 원본 바이트와 일치하는 다운로드 |
| B-06 | 소스/관측 페이지 이동과 올바른 소스 연결 유지 |
| B-07 | 라이트/다크/시스템/동작 줄이기, 화면 폭 6개와 스크린샷 |
| B-08 | 비우기 후 소스/관측/원시 대화상자 DOM 내용 제거 |
| B-09 | 빈 저장소, 새 탐색 및 정확한 환경 첨부 |

모든 테스트에서 미처리 페이지 오류, 외부 HTTP 요청 또는 자산 응답 실패를 실패 처리합니다. 재시도는 없고 단일 집중 실행 표시는 금지합니다. 호스트/엔진별 전체 화면 스크린샷 4개는 1440·390 CSS 픽셀의 라이트/다크를 기록하며, 배치 검사는 1024·850·768·560도 포함합니다. 스크린샷 검토는 픽셀 차이 기준선, 정식 접근성 감사 또는 브라우저 보안 인증과 구분합니다.

## 재현과 보관 기록

Node 의존성은 개발 전용이며 package-lock.json에 고정합니다. 실제 뷰어에는 여전히 Node 실행 환경/빌드가 필요 없습니다. 테스트 서버는 `python -I -m plaintrace.ui`를 사용하므로 먼저 패키지를 설치합니다. 대상 OS에서 브라우저를 직접 실행하며 user-agent만 변경해 OS를 흉내 내지 않습니다.

```sh
python -m pip install .
npm ci
npx playwright install --with-deps chromium firefox webkit
npm run test:browser
```

생성 JSON·스크린샷·trace·다운로드 보고서는 Git 밖에 둡니다. PLAINTRACE_BROWSER_RESULTS를 외부 디렉터리로 지정하며 로컬 기본값은 OS 임시 디렉터리입니다. CI는 호스트/엔진별 아티팩트를 14일 보관합니다. 환경 첨부에는 OS/커널/CPU·이미지 빌드·Node/브라우저 버전·user agent·커밋·실행을 기록합니다. trace는 실패할 때만 보관합니다. Python 500개 테스트와 JavaScript 모델 12개 검사는 독립 게이트로 유지합니다.

공식 [브라우저 프로젝트](https://playwright.dev/docs/test-projects), [웹 서버](https://playwright.dev/docs/test-webserver), [CI](https://playwright.dev/docs/ci) 문서를 참고했습니다. 이전 패키지/서버 검증은 [호스팅 결과](WORKBENCH_CI.ko.md)에 보관합니다.

## 최초 실패와 수정

커밋 `e6b8fcb`의 [첫 브라우저 실행](https://github.com/polynomeer/plaintrace/actions/runs/40516981679)에서 Windows Firefox/Chromium의 B-08이 실패했습니다. 비우기는 이전 작업대를 숨기기만 해서 소스/관측 DOM과 원시 텍스트가 남았습니다. 커밋 `d0f99ea`는 비우기 시 보고서 상태와 DOM 내용을 제거하고, 비우기 또는 정상 보고서 교체 시 원시 모달 텍스트도 폐기합니다. 참조 보존을 줄이는 것이며 안전한 메모리 삭제나 사용자 다운로드/클립보드 제거를 보장하지 않습니다.

Windows WebKit에서는 B-01/B-03 키보드·포커스 검사도 실패했습니다. 커밋 `e7823b4`에서 건너뛰기 링크를 명시적 탭 대상으로 지정하고, 모달을 닫을 때 클릭 시 포커스 동작에 의존하지 않고 실제 시작 컨트롤로 포커스를 돌려줍니다. 해당 검사를 회귀 테스트에 유지합니다.

최초 아티팩트 업로드도 `..`를 포함한 경로를 거부했습니다. 워크플로는 RUNNER_TEMP 기반의 정규화된 출력 경로를 GITHUB_ENV로 기록하도록 변경했습니다. 이 오류로 최초 원시 trace/스크린샷은 업로드하지 못했고 작업 로그에서 실패 메시지를 확인했습니다. 최종 리비전을 우선 실행하도록 이전 실행을 중단했으며, 취소 작업을 통과 결과로 세지 않습니다.

스크린샷 검토에서 390px 관측 표가 너무 좁게 줄바꿈되는 점을 발견했습니다. `dded72c`는 표 최소 폭과 키보드 가로 스크롤 영역을 추가했습니다. B-07은 문서 전체 넘침 없이 표 내부에서 스크롤되는지 확인하고, 테마 색상 전환 완료 후 애니메이션을 멈춰 캡처합니다.
