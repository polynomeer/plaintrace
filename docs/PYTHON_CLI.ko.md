# Python 브라우저 CLI

[English](PYTHON_CLI.md) | **한국어**

현재 패키지는 0.11.0이며 모든 출력은 스키마 11입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [UserAssist 확장](USERASSIST_CLI.ko.md)을 따릅니다.

2026-10-14 병합 커밋 `bb476180453c76f7d38e5b6a9f1f025ad2273ce0`을 기준으로 브랜치 `codex/python-browser-cli`에서 구현했습니다. EnScript 파일 13개는 해당 커밋과 바이트가 같습니다. 원본 아카이브 태그 `archive/pre-improvements-2026-10-13`, 매니페스트와 2017년 합성 커밋 263개는 보존합니다. Python 구현은 독립 실행하며 EnScript 해석이나 EnCase 호스트 검증을 수행하지 않습니다.

## 범위와 요구 환경

표준 sqlite3 모듈이 있는 Python 3.10 이상이 필요합니다. 브라우저 파싱은 외부 런타임 의존성 없이 체크아웃에서 직접 실행할 수 있습니다. EVTX에는 별도 선택 extra가 필요하며 [EVTX 설치](EVTX_CLI.ko.md)를 확인하세요. 선택적 패키지 설치는 빌드 의존성 setuptools를 사용하며 다운로드할 수 있습니다. 이 작업 환경의 검증은 macOS와 Python 3.14에서 수행했으며 Windows/Linux 실행과 최소 지원 Python 버전은 여기서 확인하지 않았습니다.

지원 입력은 획득한 Chromium 계열 History DB와 Firefox places.sqlite입니다. Chrome/Opera 표기는 명시적으로 지정할 수 있습니다. 파일명 대신 테이블로 탐지하고 auto 모드는 Chrome과 Opera를 추측하지 않고 Chromium 계열로 표시합니다. IE index.dat/WebCache, 암호화 DB, 세션 파일, 증거 이미지 추출과 GUI는 브라우저 어댑터 범위 밖입니다. 실행 중인 프로필을 자동 검색하지 않습니다.

## 실행과 설치

저장소 루트에서 예시 경로를 획득한 DB 파일로 바꿉니다. JSON은 기본적으로 stdout으로 출력하고 SQLite는 출력 경로가 필요합니다. 입력 플래그를 반복하면 여러 출처를 결합합니다. 명시한 브라우저 표기는 모든 입력에 적용하므로 계열을 섞을 때는 auto 모드를 사용합니다.

```sh
python3 -m plaintrace --input /path/to/History --browser chrome --output report.json
python3 -m plaintrace --input /path/to/places.sqlite --browser firefox --format sqlite --output report.sqlite
python3 -m plaintrace --input /path/to/History --input /path/to/places.sqlite --strict
```

선택적으로 가상환경에 설치하면 plaintrace 콘솔 명령을 생성합니다. 첫 예시는 macOS/Linux, 두 번째는 Windows PowerShell용입니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --version
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --version
```

## 입력 보존과 WAL

분석 전에 안정된 DB와 대응하는 WAL을 함께 획득해야 합니다. CLI는 DB와 인접 WAL을 임시 디렉터리로 복사하고 원본의 복사 전후 해시와 복사본을 대조합니다. SQLite는 임시 복사본만 읽기 전용/query-only 모드로 열고 quick_check를 수행합니다. 원본 SHM은 건드리지 않으며 복사한 WAL을 읽을 때 임시 SHM을 생성할 수 있습니다. 비어 있지 않은 롤백 저널, 감지한 변경, 손상과 필수 스키마 미지원은 치명적 오류로 처리합니다.

복사 중 해시 안정성이 실행 중인 브라우저의 원자적 획득이나 DB/WAL의 대응 관계를 입증하지 않으며 모든 동시 변경/ABA 상황을 탐지하지는 못합니다. 누락된 WAL을 DB만 보고 추론할 수도 없습니다. 실행 중인 파일의 복사본을 완전한 획득이 검증된 자료로 간주해서는 안 됩니다. 출처 해시는 획득한 바이트를 식별하며 완전한 증거 인계 기록을 입증하지 않습니다.

## 파싱 계약

| 계열 / 아티팩트 | 해석 |
| --- | --- |
| Chromium 방문 | visits.url과 urls.id를 결합하고 visit_time 사용; transition이 있으면 원시 값 유지 |
| Firefox 방문 | moz_historyvisits.place_id와 moz_places.id를 결합하고 visit_date 사용; 원시 visit_type을 transition으로 유지 |
| URL 요약 | 이벤트 테이블이 없으면 last_visit_time/last_visit_date를 사용하고 url_summary 및 진단 표시; 개별 방문을 생성하지 않음 |
| 쿼리 검색어 | 비어 있지 않은 모든 q/query/search_query 값을 추출하며 반복 매개변수 유지; UTF-8 디코딩 전에 경계 분리; 프래그먼트 무시 |
| 저장된 Chromium 검색어 | keyword_search_terms를 따로 읽고 stored_search_term 표시; URL 최종 방문 시각은 요약 대리 값이며 독립적인 검색 시각이 아님 |
| Chromium 다운로드 | id, start_time 및 current_path 또는 target_path 필요; 비어 있지 않은 target_path 우선; downloads_url_chains 순서와 최종 URL을 referrer와 별도로 유지 |
| Firefox 다운로드 | moz_annos를 place_id와 downloads/destinationFileURI, downloads/metaData 주석 이름으로 결합; 고정 속성 ID나 번갈아 나오는 행 순서 가정 없음 |

Firefox 다운로드는 annotation_summary이며 place별 현재 주석 집합 하나를 나타내고 모든 과거 다운로드를 재구성하지 않습니다. 중복 주석은 최신 수정/생성 시각과 ID를 기준으로 선택하며 경고를 남깁니다. 시작 시각은 가장 최근 visit_type 7 이벤트를 우선하고, 없으면 annotation dateAdded를 명시적인 대리 값으로 표시합니다. 메타데이터는 JSON으로 파싱하고 원문을 유지하며 endTime은 밀리초 또는 시간대가 있는 ISO 시각일 수 있습니다. 대상 file URI는 표시용 경로로 디코딩하고 원시 URI와 브라우저 URL은 유지합니다. Chromium 파일 경로는 URL 디코딩하지 않습니다.

쿼리 매개변수는 검색어 후보이며 웹사이트가 해당 이름을 다른 목적으로 사용할 수 있습니다. URL에서 추출한 검색어와 저장된 검색어는 별도 행으로 유지하고 중복 제거하지 않습니다. 잘못된 퍼센트 이스케이프는 경고와 함께 유지하며 잘못된 UTF-8 검색 매개변수는 개별 진단 후 건너뛰며 정상 인접 검색어와 원본 방문은 남깁니다. 빈 쿼리 값은 검색어 행을 생성하지 않습니다. 선택적 테이블/열 누락은 null 또는 사용 불가 진단으로 표현하고 필수 테이블의 잘못된 구조는 입력 실패로 처리합니다. 대응 URL이 없는 방문/주석 행도 유지하고 진단합니다.

## 시간과 숫자 값

Chromium 시각은 UTC 1601-01-01 이후의 정수 마이크로초입니다. Firefox 방문/주석은 UTC 1970-01-01 이후의 마이크로초이고 숫자형 메타데이터 endTime은 밀리초입니다. ISO 종료 시각은 명시적인 시간대가 있어야 하며 UTC로 정규화합니다. 정수 연산으로 마이크로초를 유지하고 고정된 지역 시간 오프셋을 적용하지 않습니다. 원시 값과 단위를 출력에 유지합니다. 0과 누락 시각은 null이며 음수, 정수가 아닌 값과 범위 초과 시각은 진단 후 null로 둡니다. 크기/상태 값은 브라우저 센티널을 포함한 부호 있는 64비트 정수를 허용하고 잘못된 값은 진단 후 null로 둡니다. Firefox 원본 메타데이터도 유지합니다.

이 선택은 EnScript의 고정 시간대 조정, URL 전체 디코딩과 위치/행 순서 가정에서 의도적으로 달라집니다. 명시적인 Python 계약이며 EnCase와 출력 바이트가 같다는 주장은 아닙니다.

## 출력 계약

JSON의 format_version은 6이며 tool/tool_version, 아래 브라우저 컬렉션 5개, links, prefetch, events, recycle_bin, usb_registry, recent_doc_keys, recent_docs 및 counts를 포함합니다. SQLite의 user_version은 6이며 대응하는 브라우저 테이블 5개, links, prefetch, events, recycle_bin과 usb_registry, recent_doc_keys, recent_docs 및 JSON 텍스트 값을 담은 metadata를 포함합니다. source ID는 각 입력을 식별하고 record ID와 source_table은 행 출처를 유지합니다. transition은 원시 값이며 계열별 의미가 다릅니다.

| 컬렉션 / 테이블 | 필드 |
| --- | --- |
| sources | source_id, path, browser, schema_family, database_sha256, wal_sha256, source_kind, sha256 |
| visits | source_id, browser, record_id, source_table, record_kind, url, title, visited_at, timestamp_raw, timestamp_unit, transition |
| keywords | source_id, browser, record_id, source_table, derivation, visit_record_id, parameter, keyword, url, searched_at, time_basis |
| downloads | source_id, browser, record_id, source_table, record_kind, path, destination_uri, url, url_chain, referrer, state, started_at, ended_at, start_time_raw, end_time_raw, start_time_unit, end_time_unit, start_time_basis, received_bytes, total_bytes, metadata_raw, annotation_ids, start_visit_id |
| diagnostics | source_id, severity, code, message, record_id |

SQLite 삽입은 매개변수를 바인딩하고 Unicode/따옴표/줄바꿈을 유지하며 출처 외래 키를 적용합니다. 다운로드 URL 체인은 JSON 출력에서는 배열이고 SQLite에서는 JSON 텍스트입니다. 시각은 UTC ISO 문자열이며 알 수 없는 필드는 null입니다. 저장 검색어의 time_basis와 다운로드의 start_time_basis를 확인한 뒤 대리 시각을 해석해야 합니다. EnScript Web_* 스키마와 별개이며 기존 소비자 호환성을 의미하지 않습니다.

출력 파일은 대상 디렉터리에서 완성한 뒤 하드 링크로 게시하고 분석 중 새로 생긴 파일도 덮어쓰지 않습니다. 파일시스템은 하드 링크를 지원해야 하고 상위 디렉터리가 존재하며 쓰기 가능해야 합니다. 덮어쓰기 플래그는 없습니다. 입력 사이드카용으로 예약한 경로도 출력으로 사용할 수 없습니다. 치명적인 입력 오류는 출력 게시 전에 전체 명령을 중단하고 부분 보고서는 게시하지 않습니다. stdout 리다이렉션은 셸이 수행하므로 파일 게시 보장이 적용되지 않습니다. 결과는 현재 메모리에 저장하므로 큰 프로필은 상당한 RAM이 필요할 수 있습니다.

## 종료 코드와 진단

| 종료 | 의미 |
| --- | --- |
| 0 | 보고서 생성; 경고가 있을 수 있음 |
| 1 | strict 모드에서 경고가 있는 보고서 생성 |
| 2 | 잘못된 인자, 입력/출력 실패, 변경/손상 DB 또는 필수 스키마 미지원 |

경고는 stderr와 diagnostics에 기록합니다. 빈 컬렉션을 해석하기 전에 확인해야 합니다. strict 모드도 보고서를 숨기지 않습니다. 모든 브라우저 버전 호환, 삭제 행 카빙, 미커밋 트랜잭션 복구나 암호화 DB 지원을 주장하지 않습니다.

## 코드 구조

| 파일 | 역할 |
| --- | --- |
| [evidence.py](../plaintrace/evidence.py) | DB/WAL의 독립 복사본, 해시 검사, 읽기 전용 SQLite와 무결성 검사 |
| [browser.py](../plaintrace/browser.py) | 스키마 탐지, 방문/검색어/다운로드 어댑터와 주석 결합 |
| [model.py](../plaintrace/model.py) | 보고서 버전, 정확한 UTC 시각 변환, 쿼리 검색어 추출과 진단 |
| [exports.py](../plaintrace/exports.py) | JSON/SQLite 직렬화, 매개변수 삽입과 출력의 배타적 게시 |
| [cli.py](../plaintrace/cli.py) | 인자, 종료 코드, stdout/stderr 분리 |
| [pyproject.toml](../pyproject.toml) | 선택적 설치용 콘솔 진입점 |
| [test_browser_cli.py](../tests/test_browser_cli.py) | 합성 SQLite 픽스처와 실제 Python 실행 검사 |

## 테스트와 남은 검증

[Python 테스트 계획](PYTHON_TESTS.ko.md)에 실행 가능한 합성 픽스처 검사 33개를 정리했습니다. 커밋된 WAL 행과 원본 DB/WAL/SHM 바이트 유지, 실제 CLI 서브프로세스 실행, 출력 트랜잭션과 덮어쓰기 경합을 포함합니다. 임시 독립 환경에서 설치한 콘솔 진입점도 스모크 검증합니다. 실제 Python 테스트이며 정적 EnScript 검사와 별개입니다.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
```

여러 브라우저 버전의 실제 획득 프로필, Windows/Linux, 큰 프로필, 경쟁하는 라이브 작성자, 전원 손실 내구성과 미지원 스키마는 추가 검증이 필요합니다. EnCase 컴파일/실행은 여전히 미검증이며 Python 테스트 결과로 그 한계를 해소하지 않습니다.

## 스키마 참고 자료

[Chromium 히스토리 SQL 픽스처](https://chromium.googlesource.com/chromium/src/+/77a7f22877f83aca6844991cfb17db3edd6f0947/components/test/data/history/history.30.sql)와 [Mozilla 다운로드 히스토리 구현](https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/downloads/DownloadHistory.sys.mjs)을 참고했습니다. 테이블/주석의 의미를 확인하는 자료이며 모든 버전의 지원을 입증하지 않습니다. 기존 [EnScript 분석](ANALYSIS.ko.md)은 별도로 유지합니다.

## 후속 리뷰 계약

[리뷰 보고서](PYTHON_REVIEW.ko.md)에 회귀 사례 9개를 추가했습니다. 출력 경로의 최종 요소가 dangling symlink을 포함한 심볼릭 링크이면 거부하며 SQLite 출력의 기존 WAL/SHM/저널 사이드카도 쓰기 전과 게시 전에 검사하여 거부합니다. 모든 사이드카 이름을 경쟁 작성자에 대해 원자적으로 예약하는 것은 아닙니다. 지원하지 않는 값이나 비유한 값의 JSON 직렬화는 stdout 쓰기 전에 실패하지만 스트림 전달 실패는 여전히 부분 stdout을 남길 수 있습니다. 표준 스키마 이름은 뷰가 아닌 테이블이어야 합니다.

다운로드에는 선택한 Firefox 주석 ID와 시작 이벤트 ID를 추가합니다. Chromium은 빈 주석 맵과 null 시작 이벤트 ID를 사용합니다. 주석 맵은 SQLite에서 JSON 텍스트입니다. 시작보다 빠른 종료 시각은 수정하지 않고 진단과 함께 보존합니다. 첫 미병합 format-version-1 구현의 추가 필드입니다. ISO 정규화 범위 초과와 대응 URL이 없는 저장 검색어도 진단합니다.

## 실행 아티팩트 확장

0.2.0 확장은 브라우저 입력과 함께 LNK와 Prefetch를 지원합니다. [실행 아티팩트 사용법](EXECUTION_CLI.ko.md), [테스트와 리뷰](EXECUTION_TESTS.ko.md)를 확인하세요. 형식 버전 2에 links/prefetch 컬렉션과 테이블 및 source_kind/sha256 출처 필드를 추가합니다. 버전 1 보고서는 재작성하거나 마이그레이션하지 않습니다. 소비자는 새 스키마를 읽기 전에 버전을 확인해야 합니다. DB 해시와 기존 브라우저 필드의 의미는 유지합니다.

## EVTX 확장과 버전 3

0.3.0 확장에서 선택 디코더를 통한 획득 Windows EVTX, events와 명시적 보고서/SQLite 버전 3을 도입했습니다. 기존 브라우저 필드 의미를 유지하며 과거 보고서는 마이그레이션하지 않습니다. [EVTX 계약과 설치](EVTX_CLI.ko.md), [테스트와 리뷰](EVTX_TESTS.ko.md)를 확인하세요. 도입 당시 브라우저 전용 보고서도 버전 3을 사용했으며 현재 보고서는 버전 11입니다.

## 휴지통 확장과 버전 4

0.4.0에서 명시적으로 획득한 $I 메타데이터 입력, recycle_bin과 모든 보고서의 스키마 버전 4를 추가합니다. 브라우저 필드 의미는 유지합니다. [사용법, 필드와 한계](RECYCLE_BIN_CLI.ko.md), [테스트/리뷰](RECYCLE_BIN_TESTS.ko.md)를 확인하세요. 위의 버전 3 확장은 도입 당시 설명이며 현재 출력은 버전 10입니다.

## USB 레지스트리 확장

0.5.0에서 스키마 5와 usb_registry 관찰을 도입했습니다. 위의 이전 스키마 도입은 과거 맥락이며 기존 아티팩트 필드 의미는 유지합니다. [USB 레지스트리 계약](USB_REGISTRY_CLI.ko.md)과 [테스트/리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 확장

패키지 0.6.0은 도입 당시 스키마 6과 recent_doc_keys/recent_docs를 추가했습니다. 위의 이전 확장 도입은 과거 맥락이며 현재 소비자는 스키마 11을 지원해야 합니다. [RecentDocs 계약](RECENT_DOCS_CLI.ko.md)과 [테스트/리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요. 기존 필드 의미는 유지합니다.
