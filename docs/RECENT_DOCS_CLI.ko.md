# Explorer RecentDocs Python CLI

**한국어** | [English](RECENT_DOCS_CLI.md)

현재 패키지는 0.14.0이며 모든 출력은 스키마 14입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [시스템 정보 확장](SYSTEM_INFO_CLI.ko.md)을 따릅니다.

2026-10-15 `0f3e9e4fec930332310c172df6b1e599249c8924`을 기준으로 `codex/python-recent-docs`에서 구현했습니다. EnScript 파일 13개, 아카이브 ref/매니페스트와 재구성된 2017년 커밋 263개를 보존합니다. 패키지 0.6.0/보고서 스키마 6은 독립 Python 이식판의 확장입니다.

## 실행과 입력 범위

획득한 NTUSER.DAT 하이브의 Explorer RecentDocs를 분석합니다. --recent-docs 플래그를 반복할 수 있고 이름을 바꾼 바이너리 REGF도 받으며 파일명으로 소유자나 형식을 입증하지 않습니다. Python 3.10 이상을 선언하고 macOS/Python 3.14로 검증했습니다. 기존 표준 라이브러리 REGF 리더를 사용하며 새 의존성은 없습니다. EVTX에는 계속 선택 extra가 필요합니다. 지원 입력 하나 이상이 필요하며 JSON은 기본 stdout, SQLite는 --output이 필요합니다. strict는 경고/보고서를 쓰고 1, 치명적 오류는 부분 파일 게시 없이 2를 반환합니다. 기존 출력/입력/SQLite 사이드카 보호를 유지합니다.

```sh
python3 -m plaintrace --recent-docs /path/to/NTUSER.DAT --output recent.json
python3 -m plaintrace --recent-docs /case-a/NTUSER.DAT --recent-docs /case-b/NTUSER.DAT --format sqlite --output recent.sqlite
python3 -m plaintrace --input /path/to/History --usb-system /path/to/SYSTEM --recent-docs /path/to/NTUSER.DAT --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --recent-docs /path/to/NTUSER.DAT
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --recent-docs C:\acquired\NTUSER.DAT --output recent.json
```

입력은 상한을 적용하고 원본 수정 없이 읽기 전/본문/후 해시를 비교합니다. 지정 하이브만 열며 LOG1/LOG2 재생, 라이브 레지스트리, 원래 이름의 파일시스템 조회나 대상 실행은 없습니다. 해시 안정성은 원자적 획득, 진위나 증거 완전성을 입증하지 않습니다. RecentDocs 출처는 USB를 포함한 기존 그룹 뒤에 오며 그룹 내 지정 순서를 유지합니다. 같은 하이브를 USB와 RecentDocs에 지정하면 별도 source ID로 처리하고 자동 결합하지 않습니다.

## 키, MRU와 해석

Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs와 확장자/Folder를 포함한 모든 바로 아래 범위를 읽습니다. 루트 category는 null이고 하위 category는 그대로의 키 이름입니다. 루트와 하위의 같은 항목은 별도로 유지합니다. 더 깊은 후손은 순회하지 않고 경고합니다. 분기가 없으면 명시적 진단과 빈 결과를 만들며 존재하는 빈 키는 키 메타데이터로 보존합니다.

| 제어 값 | 지원 표현과 순서 |
| --- | --- |
| MRUListEx | 최종 0xffffffff 종료자를 가진 REG_BINARY 리틀 엔디언 부호 없는 DWORD 슬롯 배열; 표준 십진 항목 이름 0..4294967294 |
| MRUList | NUL로 끝나는 REG_SZ UTF-16LE ASCII 알파벳 순서; 한 글자 항목 이름을 대소문자 무관하게 비교 |
| 제어 값 누락/오류 | 원시 제어/항목 데이터 보존; 순위는 모두 null |
| 두 제어 값 존재 | 모호함으로 처리; 둘 다 보존하고 선택/순위 할당하지 않음 |

순위 0은 해당 키 안의 가장 최근 사용 참조이며 시각이나 실제 열람 증거가 아닙니다. 중복 MRU 슬롯, 잘못된 타입, 누락/중간 종료자, 후미 데이터, 잘못된 길이나 구형 문자는 전체 순서를 무효로 합니다. 조용히 중복 제거하거나 부분 순서를 추정하지 않습니다. 정상 참조가 없는 항목을 가리키면 경고하고 mru_order 슬롯을 유지하여 기존 순위의 간격을 보존합니다. 목록 밖 항목도 null 순위와 경고로 유지합니다. 정상 빈 제어 값과 누락을 구분합니다. 비표준/미지 값 이름은 문서로 만들지 않고 other_values로 보존합니다.

현대식/누락/모호한 제어 값의 항목은 REG_BINARY를 지원하며 구형 MRUList는 REG_SZ도 지원합니다. 첫 2바이트 경계의 UTF-16LE NUL에서 저장 문서 이름을 끝냅니다. 종료자 누락이나 타입 오류는 전체 원시 값과 null 이름으로 유지합니다. 잘못된 UTF-16은 이스케이프하고 값 출처 오프셋으로 진단합니다. 빈 이름도 경고와 함께 빈 값으로 남깁니다. NUL 이후 바이트는 0을 포함해 경고와 미해석 trailing_data_hex로 보존합니다. Shell Item/PIDL 타입, 크기, 확장, 대상이나 시각은 해석/검증하지 않습니다. 저장 이름을 확인된 전체 경로로 간주하거나 해결, 정규화, 열지 않습니다.

## 시각, 출처와 원본 모듈

키 수정 시각은 recent_doc_keys에만 존재하며 별도 UTC 마이크로초 표시와 정확한 십진 FILETIME 틱을 남깁니다. 100 ns 소수는 정수 절삭하고 0은 null, 범위 초과는 경고합니다. 순위 0도 문서별 열람/접근/생성/삭제 시각을 추론하지 않습니다. 키 수정은 목록 변경을 반영할 수 있으며 모든 항목에 배정하지 않습니다. MRU 상태는 완전한 시간순 이력이나 사용자 의도/소유 증거가 아닙니다.

보존된 EnScript 모듈은 주로 Office/HWP/Adobe 애플리케이션 MRU와 LNK 연계를 처리합니다. 이번 확장은 Explorer RecentDocs이며 원본의 모든 뷰어별 동작이 아닙니다. Office 목록, Adobe/HWP MRU, Recent 폴더 검색, LNK 연계, Jump Lists, OpenSave/LastVisited, ShellBags, 삭제 레코드, 사용자/SID 식별과 세션 복원은 범위 밖입니다. 기존 명시적 LNK 분석은 유지합니다.

## 버전 10 출력과 구조

다른 유형만 입력해도 모든 보고서의 JSON format_version과 SQLite user_version은 10입니다. 버전 6은 recent_doc_keys/recent_docs와 두 개수를 추가합니다. 과거 보고서는 재작성/마이그레이션하지 않으며 소비자는 버전 10을 명시적으로 인식해야 합니다. 기존 아티팩트 필드 의미는 유지합니다. sources는 source_kind recent_docs, schema_family registry_ntuser, 획득 전체 파일 sha256과 null browser/database/WAL 필드를 사용합니다.

| 컬렉션/테이블 | 필드와 의미 |
| --- | --- |
| recent_doc_keys | source_id, record_id, key_path, category, key_last_written, key_last_write_raw, mru_format, mru_status, mru_order, mru_values, other_values |
| recent_docs | source_id, record_id, key_id, key_path, category, value_name, value_type, mru_rank, document_name, name_utf16_hex, trailing_data_hex, value_data_hex |

키 record_id는 물리 nk 셀 헤더 오프셋의 십진 텍스트이고 문서 record_id는 vk 셀 헤더 오프셋입니다. 둘 다 source_id 범위이며 key_id는 부모 키 레코드를 가리킵니다. SQLite는 출처 외래 키, 출처/키 ID 고유성과 문서-키 복합 외래 키를 적용합니다. 바인딩 삽입으로 Unicode/따옴표/개행을 보존합니다. MRU/기타 값 객체는 value_offset, name, type, data_hex를 포함합니다. 객체/배열은 JSON에서 그대로, SQLite에서 JSON 텍스트로 남깁니다. name_utf16_hex는 NUL을 제외하고 value_data_hex는 원래 값 전체 바이트를 포함합니다. 미지 디코딩 필드는 null이며 정상 이름 뒤에 후미가 없으면 빈 hex 문자열입니다.

[recent_docs.py](../plaintrace/recent_docs.py)는 [registry_hive.py](../plaintrace/registry_hive.py)로 MRU 상태와 이름을 해석합니다. 출처 결합, CLI, 모델과 출력기에 플래그, 출처와 스키마를 추가합니다. 하이브별 제한은 기존 REGF 입력 64 MiB, 접근 값별 16344바이트, 접근 값 데이터/이름 16 MiB, 셀/인덱스/이름 상한에 RecentDocs 키 1024개, 문서 10000개와 직렬화 어댑터 출력 32 MiB를 추가합니다. 직접 호출에도 적용하며 정상 대형 입력도 거부할 수 있습니다. 출력 크기는 할당 후 검사하고 결합 보고서는 메모리에 유지하며 네이티브 시간 제한/메모리 샌드박스는 없습니다. [REGF 구조와 제한](USB_REGISTRY_CLI.ko.md)을 확인하세요.

## 테스트와 남은 검증

[테스트와 수동 리뷰](RECENT_DOCS_TESTS.ko.md)는 신규 27개를 대응합니다. EVTX extra가 있으면 175개가 통과하고 없으면 167개를 실행하며 기존 통합 8개를 건너뜁니다. 생성한 REGF로 현대식/구형 순서, 희소/누락/중복 참조, 범위, 잘못된 이름, 미해석 후미, 상한, 출처 전용 읽기, 실제 CLI와 JSON/SQLite 출처를 검사합니다. 별도 python-registry 1.3.1 비교는 합성 MRU 바이트/이름을 읽으며 런타임 의존성이나 실제 하이브 검증이 아닙니다.

Windows 릴리스별 실제 획득 NTUSER, Windows/Linux, Python 3.10, 독립 실제 아티팩트 비교, 대형 컬렉션과 획득 경합은 미검증입니다. dirty 하이브/로그 재생, 미지원 REGF 버전, 분할 big data, 휘발성/링크/삭제/슬랙과 Shell Item 해석은 미지원입니다. 기존 브라우저/LNK/Prefetch/EVTX/휴지통/USB 한계도 유지합니다. EnCase 컴파일/실행도 여전히 미검증이며 테스트가 호스트 API를 검증하지 않습니다.

## 참고 자료

[libyal MRU/RecentDocs 지식 기반](https://winreg-kb.readthedocs.io/en/latest/sources/explorer-keys/Most-recently-used.html), [RegRipper RecentDocs 구현](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/recentdocs.pl), [REGF 작업 명세](https://github.com/libyal/libregf/blob/main/documentation/Windows%20NT%20Registry%20File%20%28REGF%29%20format.asciidoc)를 참고했습니다. 의존성 소스를 포함하지 않습니다. [원본 모듈 분석](ANALYSIS.ko.md)을 확인하세요.
