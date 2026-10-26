# LNK와 Prefetch Python CLI

[English](EXECUTION_CLI.md) | **한국어**

현재 패키지는 0.15.0이며 모든 출력은 스키마 15입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [SAM 계정 확장](SAM_ACCOUNTS_CLI.ko.md)을 따릅니다.

2026-10-14 codex/python-lnk-prefetch에서 d1830099999cb1669f8f868506d5c323acdb8ca5를 기준으로 구현하고 리뷰했습니다. 모든 EnScript와 과거 매니페스트는 브랜치 기준과 바이트가 같으며 아카이브 태그와 재구성된 2017년 커밋 263개를 보존합니다. 버전 0.2.0은 독립 Python 확장이고 EnScript 런타임이 아닙니다.

## 사용법과 호환성

표준 sqlite3이 있는 Python 3.10 이상을 요구하며 여기서는 macOS/Python 3.14로 검증했습니다. LNK/Prefetch는 XPRESS Huffman을 포함하여 외부 런타임 라이브러리가 필요하지 않습니다. EVTX에는 선택 extra가 필요합니다. 획득 파일 여러 개에는 --lnk와 --prefetch를 반복하고 --input, --lnk, --prefetch, --evtx, --recycle-bin 중 하나 이상이 필요합니다. 브라우저 옵션은 SQLite 입력에만 적용합니다. --lnk-codepage는 기본 cp1252이며 ANSI LNK 필드에만 적용합니다. 해당 획득 환경에 맞는 cp949 같은 ANSI 호환 인코딩을 지정할 수 있습니다. Unicode 필드는 UTF-16LE입니다. 디렉터리를 재귀 검색하지 않습니다.

```sh
python3 -m plaintrace --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --output execution.json
python3 -m plaintrace --lnk /path/to/example.lnk --lnk-codepage cp949 --strict
python3 -m plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --format sqlite --output artifacts.sqlite
```

기존 브라우저 명령 구문은 유지하지만 보고서 format_version과 SQLite user_version은 0.2.0에서 2로 확장되었습니다. 0.3.0은 버전 3에 events를 추가했습니다. 현재 출력은 버전 10이며 [휴지통 스키마 변경](RECYCLE_BIN_CLI.ko.md)을 확인하세요. 버전 2는 브라우저 전용 보고서에도 links/prefetch 컬렉션/테이블 및 source_kind/sha256 출처 필드를 추가합니다. 기존 버전 1 출력은 덮어쓰거나 마이그레이션하지 않으며 소비자는 새 버전을 명시적으로 인식해야 합니다. 선택적 pip 설치도 동일한 plaintrace 명령을 제공합니다. [설치와 브라우저 동작](PYTHON_CLI.ko.md)을 확인하세요.

## LNK 파싱

ShellLinkHeader 크기와 CLSID를 확인하고 플래그, 대상 속성/크기와 대상 생성/접근/쓰기 FILETIME을 읽습니다. 선택적 IDList/LinkInfo/StringData/ExtraData 영역의 범위를 확인하며 순회하고 종료 블록을 요구합니다. 로컬 ANSI/Unicode 경로, 볼륨 유형/시리얼/레이블, 네트워크 공유 경로, 길이 있는 문자열, 추적 머신/GUID와 환경 대상 문자열을 지원합니다.

후보 경로는 각각 근거를 유지합니다. 완전한 로컬 경로에 공통 접미사를 중복하지 않으며 Unicode LinkInfo를 우선합니다. 상대 경로는 저장된 작업 디렉터리와 문자열 수준으로 결합하고 환경 변수는 리터럴로 둡니다. 대상을 실행하거나 네트워크 공유에 접근하거나 환경 변수를 확장하거나 파일시스템에서 후보를 해석하지 않습니다. LNK 존재와 대상 시각이 실행을 입증하지는 않습니다.

PIDL 셸 항목은 불투명 hex로 보존하고 진단을 남깁니다. 알 수 없는 ExtraData는 필드를 추측하지 않고 시그니처/크기/오프셋과 진단을 유지합니다. 추적 GUID를 보존하며 물리 MAC 주소를 추론하지 않습니다. 헤더의 아이콘/표시/핫키 세부 정보, PIDL/property-store 대상 해석과 여러 ExtraData 유형은 필드 해석 범위 밖입니다. 파일만으로 ANSI 코드페이지를 신뢰성 있게 추론하지 못합니다. 디코딩할 수 없는 텍스트는 이스케이프와 경고로 표시하고 획득 파일/해시를 바이트 수준의 기준으로 유지합니다.

## Prefetch 버전과 영역

| 버전 / 레이아웃 | 지원하는 해석 |
| --- | --- |
| 17 / 152 | 실행 시각 슬롯 1개; 버전별 실행 카운터 |
| 23 / 240 | 실행 시각 슬롯 1개; 버전별 실행 카운터 |
| 26 / 304 | 저장 실행 시각 슬롯 8개 |
| 30 / 304 또는 296 | 확인한 정보 레이아웃 2개와 서로 다른 실행 카운터 오프셋 |
| 31 / 296 | 참조한 v31 레이아웃과 슬롯 8개; 합성 픽스처 검사 |

시그니처, 선언한 페이로드 크기, 정보 레이아웃 식별값, 메트릭/트레이스 범위, UTF-16 파일명 영역과 볼륨 범위를 검증합니다. 실행 파일명, Prefetch 해시, 카운터, 0/null을 포함한 모든 저장 시각 슬롯, 참조 문자열, 정확한 파일명으로 일치한 경로 후보와 볼륨 디바이스 경로/생성 시각/시리얼을 출력합니다. 디바이스 경로를 그대로 유지하고 HARDDISKVOLUME 번호로 드라이브 문자를 추측하지 않습니다. Prefetch 참조/카운터는 흔적이며 완전한 실행 감사 기록이 아닙니다.

상세 메트릭, 트레이스 체인, 볼륨 파일 참조, 디렉터리 문자열과 해시 문자열 내용은 해석하지 않으며 unparsed_sections에 표시합니다. 접근한 영역의 범위를 확인하는 것이며 무시한 모든 하위 구조를 의미적으로 검증하지는 않습니다. 크기 불일치와 알 수 없는 버전/레이아웃은 기존 고정 오프셋으로 해석하지 않고 실패합니다. 나열한 Windows 변형의 실제 파일은 여기서 미검증입니다.

## 압축 Prefetch

MAM04를 공개 프로토콜을 따른 자체의 범위 제한 XPRESS Huffman 구현으로 디코딩합니다. 정규 Huffman 테이블이 완전해야 하고 비트/길이 읽기가 범위에 맞아야 하며 역참조가 출력 시작 전이나 선언한 크기 밖으로 확장되어서는 안 됩니다. 겹치는 매치와 여러 64 KiB 블록을 처리하고 디코딩 결과에도 같은 SCCA 검사를 적용합니다.

체크섬이 있는 MAM84와 다른 플래그는 명시적으로 거부합니다. 압축 패딩/사용하지 않은 뒤쪽 비트는 인증하지 않으며 체크섬이나 일반적인 손상 복구를 보장하지 않습니다. 문서의 바이트/16비트 확장 길이를 처리하며 다른 변형은 실패합니다. 독립적으로 인코딩한 리터럴/매치 스트림으로 검사했고 실제 획득 MAM이나 독립 포렌식 도구의 인증은 아닙니다. 입력과 선언한 디코딩 결과 모두 8 MiB로 제한합니다.

## 시간, 출처와 출력

FILETIME 원시 tick은 십진수 문자열로 보존합니다. UTC 표시는 부동소수점 반올림 없이 100 ns를 마이크로초로 버림하며 원시 나머지도 확인할 수 있습니다. 0은 미상/null이고 범위를 넘는 시각은 만들어내지 않고 진단합니다. LNK 시각은 저장된 대상의 시각이며 소스 파일의 파일시스템 시각으로 대체하지 않습니다. Prefetch 볼륨/실행 시각도 별도 의미를 유지합니다.

바이너리 입력은 읽기만 수행하고 크기를 제한하며 읽기 전/본문/후 해시를 대조해 별도 source ID를 부여합니다. MAM의 sha256은 획득한 압축 바이트를 식별하고 prefetch.file_size는 디코딩한 SCCA 크기입니다. 브라우저 입력은 기존 DB/WAL 해시를 유지하며 source_kind browser 및 DB 바이트의 sha256 별칭을 추가합니다. 해시 안정성은 원자적 획득이나 증거 인계 인증이 아닙니다.

| 컬렉션 / 테이블 | 필드 |
| --- | --- |
| links | source_id, record_id, link_flags, file_attributes, target_size, created_at, accessed_at, written_at, filetimes_raw, local_base_path, common_path_suffix, network_share, volume, name, relative_path, working_directory, arguments, icon_location, target_candidates, tracker, environment_target, id_list_hex, extra_blocks |
| prefetch | source_id, record_id, version, compressed, layout, executable, prefetch_hash, file_size, run_count, last_run_times, last_run_times_raw, referenced_files, executable_path_candidates, volumes, metrics_count, trace_count, unparsed_sections |
| sources 확장 | source_kind, sha256; browser/database_sha256/wal_sha256 는 바이너리 입력에서 null |

객체/배열은 JSON에서는 실제 값이고 SQLite에서는 JSON 텍스트입니다. SQLite compressed는 0/1이며 links/prefetch record ID는 source별 오프셋을 포함하고 source_id로 범위를 구분합니다. 외래 키, 예약한 출처 경로와 배타적 출력 게시를 계속 적용합니다. 치명적 오류는 부분 파일 보고서 게시를 막고 경고는 유지하며 --strict는 보고서를 생성한 뒤 1을 반환합니다. [브라우저 CLI 종료/출력 계약](PYTHON_CLI.ko.md)을 확인하세요.

## 테스트와 코드 리뷰

[실행 테스트와 리뷰 기록](EXECUTION_TESTS.ko.md)에 신규 검사 30개와 기존 브라우저 검사 33개를 매핑했습니다. 리뷰에서 읽는 동안 커지는 입력의 해시 읽기를 제한하고 직접 압축 API 호출 제한, Unicode 볼륨/네트워크, 볼륨 범위/시각 초과와 출처 충돌 검사를 추가했습니다. 대표 LNK/Prefetch 픽스처의 잘린 모든 길이, 결정적 변형, 겹침/확장 압축 매치, 여러 블록 디코딩과 혼합 JSON/SQLite 출력 검사를 포함합니다.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d1830099999cb1669f8f868506d5c323acdb8ca5 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

Windows/Linux, 최소 Python 버전 실행, 실제 획득 LNK/Prefetch/MAM, 독립 파서 비교, 큰 사건 자료 성능과 남은 불투명 구조는 추가 검증이 필요합니다. EnCase 컴파일/실행은 미검증이며 실제 Python 테스트로 입증하지 않습니다.

## 형식 참조

[Microsoft MS-SHLLINK](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/747629b3-b5be-452a-8101-b9a2ec49978c), [Microsoft MS-XCA 처리](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-xca/26db8e62-bbd8-472c-a09e-623f6de10f0b), [libscca 작업 형식 명세](https://github.com/libyal/libscca/blob/main/documentation/Windows%20Prefetch%20File%20%28PF%29%20format.asciidoc)를 참조했습니다. 구현 자료이며 모든 Windows 버전 호환을 인증하지 않습니다. 의존성 소스를 포함하지 않습니다.

## EVTX 확장

[EVTX 사용법](EVTX_CLI.ko.md)과 [테스트/리뷰](EVTX_TESTS.ko.md)에 선택 디코더와 events를 설명합니다. LNK/Prefetch 해석과 8 MiB 상한은 유지합니다.

## 휴지통 확장

[휴지통 메타데이터](RECYCLE_BIN_CLI.ko.md)와 [테스트/리뷰](RECYCLE_BIN_TESTS.ko.md)에 표준 라이브러리 $I 파서와 현재 스키마 4를 설명합니다. LNK/Prefetch 필드와 한계는 유지합니다.

## USB 레지스트리 확장

0.5.0에서 스키마 5와 usb_registry 관찰을 도입했습니다. 위의 이전 스키마 도입은 과거 맥락이며 기존 아티팩트 필드 의미는 유지합니다. [USB 레지스트리 계약](USB_REGISTRY_CLI.ko.md)과 [테스트/리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 확장

패키지 0.6.0은 도입 당시 스키마 6과 recent_doc_keys/recent_docs를 추가했습니다. 위의 이전 확장 도입은 과거 맥락이며 현재 소비자는 스키마 15을 지원해야 합니다. [RecentDocs 계약](RECENT_DOCS_CLI.ko.md)과 [테스트/리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요. 기존 필드 의미는 유지합니다.
