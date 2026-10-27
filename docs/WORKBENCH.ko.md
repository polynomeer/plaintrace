# 로컬 보고서 작업대

[English](WORKBENCH.md) | **한국어**

2026-10-27 · 로컬 보고서 작업대 구현. 보고서 스키마 15·기존 파서 의미 유지.

## 실행·사용 흐름

제안한 3개 영역 화면을 실제 실행 가능한 읽기 전용 보고서 뷰어로 구현했습니다. 내비게이션·소스 목록·출처 상세·페이지 단위 관측 목록을 제공합니다. checkout에서 실행하거나 wheel 설치 후 console 진입점을 사용합니다. 서버가 선택한 loopback URL을 출력하며 명시적으로 요청할 때만 브라우저를 엽니다. UI 사용에는 Node.js·프런트엔드 빌드·CDN·추가 Python 런타임 패키지가 필요하지 않습니다.

```sh
python -m plaintrace.ui --open
plaintrace-ui --open
python -m plaintrace.ui --port 8767
python -m plaintrace --input /path/to/History --output report.json
```

보고서 선택기로 JSON을 엽니다. 검증에 성공해야 현재 작업대를 교체합니다. 기본 화면은 비어 있고 선택적 데모는 합성 데이터라고 표시하며 비울 수 있습니다. 출력 URL에 demo 쿼리 인수를 추가하면 데모를 미리 볼 수 있습니다. 분석은 기존 CLI에서 수행합니다. 이 화면은 원시 DB·하이브·EVTX를 직접 파싱하거나 SQLite 보고서를 불러오지 않습니다.

## 구현한 인터랙션

소스 검색·형식 필터는 보고서 필드만 사용하며 증거 OS를 추정하지 않습니다. 소스를 선택하면 경로·해시·원시 소스 정보·관측·소스별 진단을 표시합니다. 스키마 15의 30개 컬렉션을 지원하고 중복 레코드와 원래 참조를 유지합니다. 원시 레코드 dialog는 데이터를 텍스트로 렌더링하고 사용자가 요청하면 클립보드로 복사합니다. 저장은 파싱한 숫자를 재직렬화하지 않고 선택한 원래 File/Blob을 내려받습니다.

타임라인은 visits·keywords·downloads·events·휴지통의 명시적 UTC 필드만 사용합니다. 다운로드 시작·종료는 별도 참조이고 URL 요약·대리 검색 시각은 구분합니다. 레지스트리 키 시각을 행위 이벤트로 승격하지 않습니다. 정규 문자열 비교로 소수초 최대 7자리 순서를 유지하며 밀리초 Date 정렬을 사용하지 않습니다. 표시용 투영이며 새 보고서 컬렉션·신원 결합·실행/성공 추정·인과관계 주장이 아닙니다.

라이트·다크·시스템 테마에 동일한 제품 토큰을 적용합니다. native 버튼·select, 본문 건너뛰기, 보이는 focus, native modal dialog, reduced-motion 규칙을 포함합니다. 소스·관측·타임라인은 각각 30/20/30개씩 표시하고 전체 레코드를 한 번에 DOM에 만들지 않습니다. 지원 정보는 M0 등록부의 검사된 투영으로 제한된 파서·계획 중인 macOS/Linux 계열·과거 Python 호스트 CI를 구분합니다.

## 한도·보존 계약

UTF-8 Plaintrace JSON 스키마 15만 허용합니다. 선언 counts·필수 컬렉션·소스 식별자 중복·레코드 참조를 검사합니다. 한도를 함께 적용합니다: 입력 16 MiB, 소스·진단을 포함한 전체 컬렉션 레코드 100,000개, 소스 1,000개, 중첩 64단계, 디코딩 JSON 노드 300,000개, 디코딩 문자열당 UTF-16 코드 유닛 1,048,576개. 복잡한 보고서는 레코드 상한 전에 구조 제한에 걸릴 수 있습니다. 비유한 값·안전하게 표현할 수 없는 크기의 숫자는 거부하며 원시 FILETIME·카운터 문자열은 문자열로 유지합니다.

원시 레코드 표시·복사는 2 MiB로 제한하고 초과하면 원본 보고서 저장을 안내합니다. 소스별 진단은 전체 개수를 표시하면서 처음 50개만 보여줍니다. 경로·URL·명령·XML은 비활성 텍스트이며 대상 이동·경로 확장·실행을 하지 않습니다. 보고서 데이터는 localStorage·IndexedDB·쿠키·서버 파일에 저장하지 않습니다. 비우기·새로고침은 작업대 참조를 제거하지만 포렌식 secure erase를 보장하지 않습니다. 사용자가 저장한 파일·클립보드 복사본은 별도로 관리해야 합니다.

## 로컬 서버·패키징

Python 표준 라이브러리 실행기는 IPv4 loopback에만 바인딩합니다. 고정된 메모리 자산 허용 목록으로 패키지 HTML/CSS/ES 모듈/SVG만 제공하며 현재 디렉터리·임의 증거 파일·파서 API를 노출하지 않습니다. 정적 GET/HEAD만 구현하고 변경·업로드 경로는 없습니다. Host/Origin 검사, no-store·no-referrer·nosniff·frame 거부와 네트워크 연결을 막는 CSP를 적용합니다. 인증된 다중 사용자 서비스가 아니므로 포트 포워딩·reverse proxy로 공개하지 않습니다.

setuptools package data로 화면을 포함해 checkout과 설치 console이 같은 자원을 사용합니다. native HTML/CSS/ES 모듈을 사용해 별도 운영 JavaScript 빌드가 필요하지 않습니다. Lucide 0.468.0의 선별 SVG·라이선스를 포함하고 CDN에 요청하지 않습니다. 기준 등록부가 바뀌면 공통 도구로 지원 정보 투영을 갱신합니다.

```sh
python tools/build_workbench_support.py
python tools/build_workbench_support.py --check
node --test tests/test_ui_model.mjs
python -m unittest discover -s tests -v
```

[검증·제약](WORKBENCH_TESTS.ko.md)을 참조하세요. M0 호스트 결과는 기존 Python 분석 기반을 대상으로 하며 이번 브라우저 UI나 신규 입력 포맷을 인증하지 않습니다.

[Windows/Linux 브라우저 검증과 수정 기록](WORKBENCH_BROWSER.ko.md)
