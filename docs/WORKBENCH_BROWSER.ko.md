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

## 최종 실행 결과

커밋 `5f3b3203098f8fa15fa559ce7ec39b558a1110ea`의 [브라우저 실행](https://github.com/polynomeer/plaintrace/actions/runs/40522922787)에서 6개 트랙이 각각 9개, 총 54개를 스킵·실패·flaky·테스트 자동 재시도 없이 통과했습니다. 같은 워크플로의 모델 12개도 통과했습니다. [Python 호스트 6개/정적 검사](https://github.com/polynomeer/plaintrace/actions/runs/40518755665)는 코드 리비전 `dded72c`에서 통과했으며 `5f3b320`은 문서만 추가합니다. 각 Python 트랙은 EVTX를 포함한 500개와 설치 CLI/UI 검증을 통과했습니다. 이 Python 결과를 미완료 후속 작업의 결과로 간주하지 않습니다. Playwright 1.64.1을 고정해 실행했습니다.

| 트랙 | 실제 OS/커널/CPU | 엔진 버전 | Node | 이미지 빌드 | 결과 |
| --- | --- | --- | --- | --- | --- |
| [ubuntu-24.04 / chromium](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580849) | Ubuntu 24.04 / 6.17.0-1022-azure / x64 | 156.0.8078.4 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [ubuntu-24.04 / firefox](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580193) | Ubuntu 24.04 / 7.0.0-1017-azure / x64 | 157.0 | v22.23.4 | 20261026.354.1 | 9 pass / 4 PNG |
| [ubuntu-24.04 / webkit](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580518) | Ubuntu 24.04 / 6.17.0-1022-azure / x64 | 27.2 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [windows-2022 / chromium](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580103) | Windows Server 2022 / 10.0.20348 / x64 | 156.0.8078.4 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |
| [windows-2022 / firefox](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580222) | Windows Server 2022 / 10.0.20348 / x64 | 157.0 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |
| [windows-2022 / webkit](https://github.com/polynomeer/plaintrace/actions/runs/40522922787/job/122254580131) | Windows Server 2022 / 10.0.20348 / x64 | 27.2 | v22.23.4 | 20261022.344.1 | 9 pass / 4 PNG |

WebKit user-agent는 실제 Windows/Linux에서도 macOS 문자열을 포함합니다. OS는 user-agent가 아닌 프로세스 환경과 러너 이미지로 확인했습니다. 대표 Windows/Linux 스크린샷의 글자·아이콘·선택 상태·라이트/다크·좁은 표 배치를 직접 검토했으며, 전체 24개 캡처는 아티팩트에 보관합니다. 자동 배치 검사는 모든 엔진에서 실행했지만 모든 픽셀의 수동 검토 또는 정식 접근성 감사를 주장하지 않습니다.

## 결과 해시와 남은 범위

결과 JSON의 환경 커밋/실행과 9개 통과·0 스킵·0 flaky를 대조했습니다. 스크린샷 해시는 파일명→SHA-256 맵을 키 정렬한 공백 없는 JSON으로 직렬화해 다시 SHA-256한 값입니다. 생성 보고서·스크린샷은 Git 밖에 보관하고 검토한 다이제스트만 커밋합니다. 초기 실패 이력도 유지하며 이후 문서 커밋을 이 검증 커밋과 구분합니다.

| 트랙 | 결과 JSON SHA-256 | 스크린샷 맵 SHA-256 |
| --- | --- | --- |
| ubuntu-24.04 / chromium | 2ffc589cef6838f020f401b6924e4a8bab66037925512d67a34fe9f5e8f2b150 | 320ef3da01996410ca831c50175a46229d812f1563a57e783b6cda5e5ea732b8 |
| ubuntu-24.04 / firefox | 0cb5b1fb2d25498f14c06ee662dde7da1b13b0db363e9dd87416ae181f441804 | 7a22234a29695e6ebadaa4f4af7167d1e8053b4bdbde0c4dea13f6129a1eebeb |
| ubuntu-24.04 / webkit | 23dfc62bbbd8b8f8227edb231da140e93996c95ba2d4a80e1fc41a4b7d8c28c7 | 0d9f396450086ab2bc8fe017819546b8b3c0af3184cfc486527eaf09ac647615 |
| windows-2022 / chromium | 8615ab166698596073491391afdac9d4e1b3f16751053f17d04334db06ef82fc | 6d28e48c87f9570fa4249fafa4274b4e0aabd8cb19ff118824a681c926ab0b7c |
| windows-2022 / firefox | 6d5fc3d8f0e1a24cc203d9d63e88eb4047eea549e637c5d90b5d56127bff7ac6 | 164e742c3702f987b7e58d3ff9b3129c18e11431c59b6fbf9075cd126290c8d3 |
| windows-2022 / webkit | d02f848e9e6d919a9bd78d1948e064c95f0909781c858f4af6882c00d49db32b | e4e6d403d0e13c9e6c8d52b328d014d56d2d438baeda4b1512d58e6b9df22c93 |

Windows 10/11 클라이언트, 다른 Linux 배포판/아키텍처, 상표 Chrome/Edge/Safari, 구형 브라우저, 실제 터치 기기·스크린리더와 대형 획득 보고서는 별도 검증이 필요합니다. 로컬 archive-only 검증은 원본 EnScript 13개와 합성 역사 커밋 263개 보존을 확인했습니다. EnCase 실행·증거 해석 정확도에 대한 새 주장은 없습니다.

이전 `dded72c` 실행에서는 마지막 Linux WebKit의 러너 배정과 설치가 지연돼 취소·러너 재요청을 시도했습니다. 그 대기/취소 상태를 통과로 간주하지 않았습니다. 최종 표는 문서 포함 커밋 `5f3b320`의 새 실행에서 6개가 모두 완료된 결과만 사용합니다.
