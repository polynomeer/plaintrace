# 애플리케이션 MRU Python CLI

[English](APPLICATION_MRU_CLI.md) | **한국어**

현재 패키지는 0.8.0이며 모든 출력은 스키마 8입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [Jump Lists 확장](JUMP_LISTS_CLI.ko.md)을 따릅니다.

2026-10-15에 4b88c0a8d8699920ecdd5622400484bbef956c89 기반 codex/python-application-mru에서 구현했습니다. 패키지 0.7.0/보고서 스키마 7은 Office, HWP, Adobe 레지스트리 MRU 관찰을 독립적으로 추가합니다. EnScript 13개, 아카이브 참조/매니페스트와 재구성된 2017년 커밋 263개를 보존합니다.

## 실행과 입력 범위

반복 가능한 --application-mru는 이름이 변경된 파일을 포함하여 명시적으로 획득한 안정된 NTUSER.DAT REGF 파일을 받습니다. 요구 환경은 Python 3.10+이며 macOS/Python 3.14에서 검증했습니다. 기존 표준 라이브러리 REGF 판독기를 사용하며 EVTX만 선택 의존성이 필요합니다. JSON 기본 출력은 stdout, SQLite는 --output이 필요합니다. 엄격 모드는 전체 보고서를 쓰고 경고가 있으면 1을 반환하며, 치명적 입출력 오류는 부분 결과를 게시하지 않고 2를 반환합니다. 기존 출력, 입력 파일과 SQLite 사이드카를 보호합니다.

```sh
python3 -m plaintrace --application-mru /path/to/NTUSER.DAT --output applications.json
python3 -m plaintrace --application-mru /case-a/NTUSER.DAT --application-mru /case-b/NTUSER.DAT --format sqlite --output applications.sqlite
python3 -m plaintrace --recent-docs /path/to/NTUSER.DAT --application-mru /path/to/NTUSER.DAT --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --application-mru /path/to/NTUSER.DAT
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --application-mru C:\acquired\NTUSER.DAT --output applications.json
```

입력은 크기를 제한하고 읽기 전/중/후 해시를 비교하며 수정하지 않습니다. 실시간 레지스트리, LOG1/LOG2 재생, 경로 조회, 문서 열기, 대상 실행이나 네트워크 조회는 없습니다. 반복 출처는 별도 ID이며 애플리케이션 입력은 기존 모든 출처 그룹 뒤에 옵니다. 같은 하이브를 USB, RecentDocs와 애플리케이션 MRU에 전달하면 조인 없이 출처 3개가 됩니다. 해시 안정성만으로 원자적 획득이나 진본성을 증명하지 않습니다.

## 지원 목록과 디코딩

| Family | Registry paths beneath Software |
| --- | --- |
| Office | Microsoft\Office\version\Word, Excel, PowerPoint: File MRU / Place MRU; also User MRU\opaque-account\File MRU / Place MRU |
| HWP | Hnc\Hwp\version\HwpFrame_KOR or HwpFrame\RecentFile; Hnc\Common\version\CommonFrame\RecentFile |
| Adobe | Adobe\Acrobat Reader or Adobe Acrobat\version\AVGeneral\cRecentFiles\cN |

Office와 HWP 버전 이름은 각 구성 요소가 한두 자리인 숫자 major.minor 형식입니다. Adobe 버전은 DC를 포함하여 이름 그대로 열거합니다. 인식하는 레이아웃이며 모든 애플리케이션 버전의 호환성을 보장하지 않습니다. Office User MRU scope는 하위 키의 원문 이름이며 계정 소유권을 확인하지 않습니다. HWP scope는 프레임을 식별합니다. 미지원 제품군, 애플리케이션, 버전 이름과 다른 분기는 스캔하지 않습니다. 제품군 분기 부재와 지원 목록 없음은 진단하며 기존 빈 목록은 키 레코드로 보존합니다.

Office의 정규 Item N 값은 1, HWP fileN은 0, Adobe의 직접 cN 슬롯은 1부터이며 tDIText를 선택합니다. 번호는 최대 9자리이며 선행 0이 없습니다. ASCII 대소문자를 구분하지 않습니다. 실제 값/자식을 열거하므로 빈 번호에서 중단하지 않으며 슬롯/범위의 중복 경로를 별도 보존합니다. slot_number는 저장된 표지이며 보편적 시간 순서나 확정 MRU 순위가 아닙니다. 출력은 판독기의 열거 순서입니다. 목록/슬롯의 중첩 자식은 진단하고 탐색하지 않으며, 알 수 없는 Adobe 슬롯 이름은 진단하고 자식을 해석하지 않습니다. 알 수 없는 직접 값은 value_offset, name, type, data_hex를 가진 metadata_values로 남습니다.

Office와 Adobe는 REG_SZ/REG_EXPAND_SZ UTF-16LE를 받습니다. HWP는 선택적 리틀엔디언 BOM을 가진 REG_BINARY UTF-16LE도 지원하며 빅엔디언 BOM은 미지원입니다. 환경변수를 확장하지 않습니다. 끝 NUL은 디코딩 텍스트에서 제거하지만 value_data_hex에 보존하며, 종결 누락은 경고하고 읽을 수 있는 텍스트를 유지합니다. 내부 NUL, 미지원 타입이나 잘못된 UTF-16은 경로를 선택하지 않으며 잘못된 텍스트는 가능한 경우 이스케이프하고 원시 바이트를 항상 보존합니다. 빈 경로는 경고와 함께 빈 문자열로 남습니다. HWP 바이너리 디코딩은 해당 레이아웃 전용이며 범용 바이너리 문자열 탐지가 아닙니다.

Office 일반 값은 그대로 유지합니다. 앞부분의 문자 태그 대괄호 토큰 연속과 뒤따르는 별표를 분리하며 이후 별표는 경로에 속합니다. 모든 토큰은 tag/raw 객체로 metadata_tokens에 남습니다. 정확히 16자리 16진수인 단일 T 토큰이 embedded_filetime_raw와 embedded_at을 제공하며 중복/잘못된 T는 시각을 선택하지 않습니다. 앞 대괄호 구문이 잘못되면 raw_text를 보존하고 경로를 선택하지 않습니다. F/O와 다른 플래그는 불투명하며 고정 상태를 추정하지 않습니다. Adobe 장치 독립 tDIText 경로는 슬래시와 퍼센트 이스케이프를 포함해 그대로 유지하며 aFS/sDI 메타데이터를 보존하되 드라이브 매핑이나 대체 디코딩은 하지 않습니다.

## 시각, 출력과 구조

키 마지막 쓰기는 application_mru_keys에만 정확한 10진 FILETIME과 별도 UTC 표시로 남습니다. Office 내장 T는 저장된 연결 시각이며 실제 열람 사건을 증명하지 않습니다. HWP/Adobe의 문서별 시각은 만들어내지 않습니다. 표시 시각은 정수 연산으로 100 ns 단위를 마이크로초로 절삭하며 0은 null, 범위 초과는 진단합니다. 목록은 변경 가능한 상태이며 완전한 사용 이력, 사용자 귀속이나 세션 재구성이 아닙니다.

해당 입력이 없어도 모든 보고서의 JSON format_version과 SQLite user_version은 8입니다. 버전 7은 application_mru_keys/application_mru와 개수를 추가하며 기존 필드 의미는 유지합니다. 이전 보고서는 마이그레이션/재작성하지 않으며 소비자는 버전 8을 지원해야 합니다. 출처의 source_kind는 application_mru, schema_family는 registry_ntuser, sha256은 전체 파일 해시이며 browser/database/WAL 필드는 null입니다.

| Collection/table | Fields |
| --- | --- |
| application_mru_keys | source_id, record_id, key_path, family, application, application_version, scope, list_kind, key_role, key_last_written, key_last_write_raw, metadata_values |
| application_mru | source_id, record_id, key_id, key_path, family, application, application_version, scope, list_kind, slot_name, slot_number, value_name, value_type, raw_text, stored_path, path_basis, metadata_tokens, embedded_filetime_raw, embedded_at, value_data_hex |

record_id는 물리 nk/vk 셀 헤더 오프셋의 10진 텍스트이며 source_id 범위로 식별합니다. key_id는 부모 키를 참조합니다. SQLite는 출처 외래 키, 고유 출처/키 ID와 복합 항목-키 외래 키를 적용합니다. Adobe는 list와 slot key_role 레코드를 가지며 항목은 자신의 슬롯 키를 참조합니다. 배열/객체는 JSON에서 그대로, SQLite에서 JSON 텍스트이며 값 바인딩으로 삽입합니다. 원시 값은 BOM/종결자를 포함합니다. 원문과 해석 경로는 별도이며 디코딩할 수 없는 필드는 null입니다.

[application_mru.py](../plaintrace/application_mru.py)는 [기존 REGF 판독기](../plaintrace/registry_hive.py)로 목록을 해석하고 execution, CLI, model과 exporter가 출처와 스키마를 구성합니다. 상속한 제한은 입력 64 MiB, 접근 값당 16344바이트, 접근 값/이름 16 MiB와 기본 셀/인덱스 제한입니다. 추가로 탐색 단계당 자식 4096개, 출력 키 1024개, 항목 10000개와 하이브당 직렬화 어댑터 출력 32 MiB를 제한합니다. 직접 호출에도 적용하며 정상 대용량 입력도 거부할 수 있습니다. 출력 제한은 할당 후 확인하며 통합 보고서는 메모리에 남고 자체 시간 제한이나 메모리 샌드박스가 없습니다. [REGF 지원과 한계](USB_REGISTRY_CLI.ko.md)를 확인하세요.

## 원본 모듈, 테스트와 남은 한계

원본 Win_RecentDocuments.EnScript는 Office 13/14/15/16, HWP 9.0과 Reader DC를 다룹니다. 번호를 순차적으로 읽다가 빈 번호에서 중단하며 Adobe 반복문은 자식 경로를 누적합니다. 이식판은 실제 형제 키를 열거하고 위의 명시적 추가 레이아웃을 지원하며 EnScript를 변경하지 않습니다. Explorer RecentDocs는 [별도 어댑터](RECENT_DOCS_CLI.ko.md)이며 Recent 폴더 스캔, LNK 상관분석, Jump Lists, OpenSave/LastVisited, ShellBags와 Office Resiliency/Pinned/Reading Locations는 이 어댑터 범위 밖입니다.

[테스트와 자체 리뷰](APPLICATION_MRU_TESTS.ko.md)는 신규 25개 사례를 다루며 EVTX extra를 포함한 200개 테스트가 모두 통과합니다. 실제 획득한 Windows/애플리케이션 버전별 하이브, Windows/Linux, Python 3.10, 독립 실제 자료 대조, 대규모 자료와 획득 경합은 미검증입니다. Dirty 하이브/로그 재생, REGF 1.6, 분할 big data, volatile/link/삭제/slack 구조와 미지원 레이아웃은 제외합니다. 기존 아티팩트 한계도 유지합니다. EnCase 컴파일/실행은 미검증이며 이식판 테스트는 호스트 API를 검증하지 않습니다.

## 참고 자료

[보존 모듈 분석](ANALYSIS.ko.md), [RegRipper Office 파서](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/msoffice.pl), [osquery Office MRU 구현](https://github.com/osquery/osquery/blob/master/osquery/tables/applications/windows/office_mru.cpp), [Adobe 환경설정 타입](https://www.adobe.com/devnet-docs/acrobatetk/tools/AdminGuide/preferences.html)과 [HWP CommonFrame 사례](https://speakerdeck.com/digitalisx99/pycon-kr-balpyojaryo-2018-gimdonghyeon)를 참고했습니다. 레이아웃 처리 근거이며 실제 사건 정확성을 입증하지 않습니다. 의존성 소스는 저장소에 복제하지 않았습니다.
