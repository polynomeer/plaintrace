# Windows EVTX Python CLI

**한국어** | [English](EVTX_CLI.md)

현재 패키지는 0.15.0이며 모든 출력은 스키마 15입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [SAM 계정 확장](SAM_ACCOUNTS_CLI.ko.md)을 따릅니다.

2026-10-15 병합 커밋 `9f32324141810b257d4f680e84c849c013543900`을 기준으로 `codex/python-evtx`에서 구현했습니다. EnScript 파일 13개와 과거 매니페스트는 브랜치 기준과 바이트가 같습니다. 아카이브 태그와 재구성된 2017년 커밋 263개를 보존합니다. 버전 `0.3.0`은 독립 Python 이식판의 확장이며 EnScript를 실행하지 않습니다.

## 설치와 실행

Python 3.10 이상을 선언하며 이 작업 환경에서는 macOS/Python 3.14로 검사합니다. 브라우저/LNK/Prefetch 파싱은 계속 표준 라이브러리를 사용합니다. EVTX에는 정확히 고정한 선택 의존성 `python-evtx==0.8.1` 디코더가 추가로 필요하며 설치 시 hexdump도 설치합니다. 외부 소스를 저장소에 포함하지 않습니다. 가상환경에서 extra를 설치하세요. 디코더가 없거나 버전이 다르면 설치 안내 오류를 반환하며 보고서를 게시하지 않습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/plaintrace --evtx /path/to/Security.evtx --output events.json
.venv/bin/plaintrace --evtx /path/to/System.evtx --evtx /path/to/Security.evtx --format sqlite --output events.sqlite
.venv/bin/plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --evtx /path/to/Security.evtx --strict
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install '.[evtx]'
.venv\Scripts\plaintrace.exe --evtx C:\acquired\Security.evtx --output events.json
```

여러 획득 파일에는 `--evtx`를 반복합니다. `--input`, `--lnk`, `--prefetch`, `--evtx`, `--recycle-bin` 중 하나 이상이 필요합니다. 브라우저와 LNK 코드페이지 옵션은 각각 기존 입력에만 적용합니다. JSON은 기본 stdout이며 SQLite는 `--output`이 필요합니다. 기존 파일/SQLite 사이드카와 입력 경로는 덮어쓸 수 없습니다. 치명적 오류는 게시 전에 전체 입력 처리를 중단합니다. 경고는 보고서와 stderr에 남으며 `--strict`는 보고서를 만든 후 1을 반환합니다. [공통 출력과 종료 규칙](PYTHON_CLI.ko.md)을 확인하세요.

## 획득, 컨테이너와 디코더 경계

라이브 Windows 로그가 아닌 안정적으로 획득한 파일을 분석합니다. 원본은 읽기만 수행하며 읽기 전/본문/후 해시를 비교합니다. 캡처 바이트는 별도 임시 복사본에서 디코딩하고 실패를 포함해 처리 후 삭제합니다. SHA-256은 출처 바이트를 식별하지만 안정성 검사가 원자적 획득, 완전성이나 증거 인계를 입증하지는 않습니다.

지원 컨테이너는 4096바이트 파일 헤더와 65536바이트 청크를 사용하는 EVTX 3.1/3.2입니다. BinXML 디코딩 전에 헤더 서명/레이아웃, 선언 청크 개수/정렬, 파일/청크/데이터 CRC32, 빈 공간 경계, 할당 레코드 서명, 정렬된 크기, 후미 크기 일치와 마지막 레코드 오프셋을 검증합니다. 미지원 플래그, 잘못된 컨테이너나 체크섬 불일치는 치명적 오류입니다. CRC 검사는 진위를 입증하거나 CRC를 다시 계산한 의도적 수정을 탐지할 수 없습니다. 컨테이너가 유효한 dirty 파일은 경고를 남기며 dirty 헤더에서 빠진 레코드/청크를 복구하지 않습니다. 선언 개수 이후의 물리 청크는 경고와 함께 제외합니다.

EVTX 입력마다 64 MiB와 할당 레코드 100000개를 제한합니다. 별도 디코더 프로세스는 파일당 60초 제한, 레코드당 UTF-8 렌더링 XML 1 MiB, 파일당 JSONL 출력 32 MiB 제한을 적용합니다. BinXML은 한 번에 청크 버퍼 하나만 사용하므로 참조가 다른 청크를 읽을 수 없습니다. 부모 측에서도 출력 크기, 개수와 출처 오프셋을 다시 검사합니다. XML은 DTD/entity 선언, 미지원 루트/네임스페이스, 중복 단일 필드, 노드 10000개 초과나 깊이 64 초과를 거부합니다. 표준 Windows Event XML 네임스페이스와 네임스페이스 없는 Event 문서를 허용합니다. 이는 외부 인터페이스의 제한이며 모든 BinXML 내부 구조 검증이나 운영체제 보안 샌드박스는 아닙니다. 의존성은 XML 크기 검사 전에 메모리를 할당할 수 있으며 강제 메모리 상한은 구현하지 않았습니다. 큰 정상 로그도 크기/시간 제한을 초과할 수 있습니다. 결합 보고서는 메모리에 유지하며 제한은 전체 보고서 합계가 아닌 입력별입니다.

선언 청크와 할당 레코드만 물리 파일 순서로 읽습니다. 시각이나 논리 링 버퍼 순서로 정렬하지 않습니다. 삭제 레코드/슬랙 카빙, 수리, 재동기화, EVT 파싱, 증거 이미지 추출, 라이브 Windows API 접근, 공급자 DLL 메시지 렌더링이나 외부 XML 입력은 구현하지 않았습니다. 디코더 예외는 레코드를 조용히 누락시키지 않고 전체 실패로 처리합니다. 특이한 BinXML 템플릿/타입은 실패할 수 있으며 모든 Windows 버전/공급자 호환을 주장하지 않습니다.

## 해석과 원본 동작

미지 공급자/ID와 시스템 계정을 포함해 모든 디코딩 이벤트를 보존합니다. 이름, Unicode, 중복, 무명 값, EventData XML과 UserData XML을 남깁니다. 로그온 정규화 값에는 허용한 이벤트 네임스페이스의 Data 요소만 사용합니다. 중복이 있으면 값을 추정해 선택하지 않고 정규화 필드를 null로 남기며 경고합니다. 공급자/채널 이름은 리터럴 일치로 확인하고 파일명으로 추정하지 않습니다.

| 공급자 / 채널 / ID | category와 action |
| --- | --- |
| Microsoft-Windows-Security-Auditing / Security / 4624 | logon / logon |
| Microsoft-Windows-Security-Auditing / Security / 4634 | logon / logoff |
| Microsoft-Windows-Security-Auditing / Security / 4647 | logon / user_initiated_logoff |
| Microsoft-Windows-Kernel-General / System / 12 | power / os_started |
| Microsoft-Windows-Kernel-General / System / 13 | power / os_shutdown_started |
| Microsoft-Windows-DriverFrameworks-UserMode / 모든 채널 또는 ID | driver_frameworks / null |
| 그 외 조합 | event / null |

로그온 details에는 TargetUserName, TargetDomainName, TargetUserSid, TargetLogonId, LogonType, IpAddress와 LogonGuid를 문자열로 보존하며 없는 값은 null입니다. System의 보안 SID와 TargetUserSid는 별개입니다. 이벤트 ID는 공급자별 의미가 있으므로 ID만으로 분류하지 않습니다. OS 종료 시작 이벤트는 종료 완료의 증거가 아닙니다. Logon ID는 전역 고유 값이 아니며 세션을 자동 연결하지 않습니다.

EnScript와 달리 NT AUTHORITY 계정을 제외하거나 고정 시간대 보정, XML 부분 문자열 위치 추출, 같은 시각 이벤트 개수로 USB mounted/unmounted 상태 추정을 수행하지 않습니다. DriverFrameworks 이벤트만으로 USB 연결을 주장하지 않습니다. 레지스트리 연계, 드라이브 문자 매핑, 장치 식별자 합성이나 물리 장치 상태를 추론하지 않습니다. 명시적 분석 계약이며 검증된 EnCase 출력 동등성이 아닙니다.

## 시각과 출처

레코드 컨테이너 FILETIME은 십진 문자열 `container_filetime_raw`로 보존하며 100 ns 틱을 마이크로초로 절삭한 UTC `container_time`으로 표시합니다. 별도로 입증된 기록 시각이 아닙니다. XML TimeCreated/SystemTime은 `time_created_raw`에 남기고 명시적 시간대와 최대 7자리 소수초로 별도 UTC `created_at`을 계산합니다. 디코더가 BinXML 렌더링 중 시각 정밀도를 이미 줄였을 수 있으며 렌더링 XML은 디스크의 원본 텍스트가 아닙니다. 정확한 컨테이너 틱은 계속 남습니다. 0 컨테이너 시각은 null이고 잘못된/범위 초과 시각은 경고합니다. XML/컨테이너 시각이 마이크로초 정밀도에서 다르면 경고하며 어느 하나를 조용히 우선하지 않습니다.

`record_id`는 출처 파일 내 바이트 오프셋의 십진 문자열이며 `source_id` 범위에서 식별합니다. `event_record_id`는 XML EventRecordID이고 `container_record_id`는 컨테이너의 부호 없는 ID입니다. 둘 다 SQLite의 부호 있는 정수 범위를 넘는 값도 보존하도록 십진 텍스트로 저장합니다. 누락/잘못된 XML 식별자는 null이며 경고합니다. 불일치와 중복 컨테이너 ID를 경고하며 서로 다른 출처 오프셋을 별도 레코드로 유지합니다. 별도 입력 출처 사이의 같은 ID도 중복 제거하지 않습니다.

## 현재 출력과 구조

브라우저 전용을 포함한 모든 보고서의 JSON `format_version`과 SQLite `user_version`은 10입니다. 버전 3은 `events`와 개수를 도입했으며 버전 2의 브라우저/LNK/Prefetch 필드는 유지합니다. sources의 `source_kind`와 `schema_family`는 evtx, `sha256`은 전체 파일 해시이고 browser/database/WAL 필드는 null입니다. 기존 버전 1/2/3 파일은 마이그레이션하거나 재작성하지 않으며 소비자는 버전 10을 명시적으로 지원해야 합니다. 버전 4는 recycle_bin을 추가하며 [휴지통 계약](RECYCLE_BIN_CLI.ko.md)을 확인하세요. 아래 배열/객체는 JSON에서 그대로, SQLite에서 JSON 텍스트로 저장합니다. 출처 외래 키와 바인딩 삽입을 유지합니다.

| 이벤트 필드 | 의미 |
| --- | --- |
| source_id, record_id, chunk_index, record_offset | 입력과 물리 레코드 출처; 청크 인덱스는 0부터 시작 |
| container_record_id, container_filetime_raw, event_record_id | 텍스트로 저장하는 부호 없는 ID와 정확한 컨테이너 틱 |
| event_id, provider, provider_guid, channel, computer | 이벤트 출처 식별 |
| level, task, opcode, version, qualifiers, keywords | System 메타데이터; 숫자는 범위 검사, qualifiers/keywords는 텍스트 유지 |
| process_id, thread_id, user_sid, activity_id, related_activity_id | 실행, 보안과 상관 메타데이터 |
| created_at, time_created_raw, container_time | 별도 UTC 표시와 렌더링 XML 시각 |
| category, action, details | 조건을 확인한 분류와 정규화 로그온 필드; 다른 이벤트는 추론하지 않음 |
| event_data, user_data_xml, xml | 순서 있는 이름/값/XML 항목, 직렬화 UserData와 전체 디코더 렌더링 XML |

`evtx.py`는 컨테이너 검증, 디코더 실행과 XML 해석을 담당하고 `evtx_worker.py`는 시간 제한 프로세스에서 선택 BinXML 라이브러리를 연결합니다. `execution.py`는 출처를 결합하고 `model.py`는 버전 10을 선언하며 `exports.py`는 이벤트/메타데이터를 쓰고 `cli.py`는 반복 입력 플래그를 추가합니다. 기존 LNK/Prefetch 입력/압축 해제 상한은 계속 8 MiB이며 EVTX가 변경하지 않습니다.

## 테스트, 리뷰와 남은 검증

[EVTX 테스트와 리뷰 기록](EVTX_TESTS.ko.md)은 기존 브라우저 33개 및 LNK/Prefetch 30개 회귀 검사와 함께 EVTX 32개를 대응합니다. 전체 검사는 extra를 설치하고 공유 템플릿과 Unicode 치환을 포함해 생성한 EVTX/BinXML 바이트를 실제 디코더로 실행합니다. 획득 증거는 커밋하지 않습니다. extra가 없으면 디코더 통합 검사 7개를 명시적으로 건너뛰며 해당 실행은 완전한 EVTX 검증이 아닙니다.

실제 획득 EVTX, 실제 공급자/버전/템플릿 변형, 독립 파서 대조, Windows/Linux, Python 3.10, 성능과 라이브 획득 절차는 미검증입니다. 기존 브라우저/LNK/Prefetch의 실제 파일 및 미지원 구조 한계도 해당 문서에 유지합니다. EnCase 컴파일/실행도 여전히 미검증이며 합성 Python 테스트가 이 한계를 해소하지는 않습니다.

## 참고 자료

[python-evtx 0.8.1 소스와 XML API](https://github.com/williballenthin/python-evtx/tree/v0.8.1), [libevtx EVTX 작업 명세](https://github.com/libyal/libevtx/blob/main/documentation/Windows%20XML%20Event%20Log%20%28EVTX%29.asciidoc), [Microsoft Event 스키마](https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-schema), [Microsoft 4634](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4634), [Microsoft 4647](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4647), [Microsoft 시스템 이벤트 지침](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-unexpected-reboots-system-event-logs)을 참고했습니다. 해석을 위한 자료이며 획득 사건의 정확성을 인증하지 않습니다.

## 휴지통 확장

[휴지통 사용법](RECYCLE_BIN_CLI.ko.md)과 [테스트/리뷰](RECYCLE_BIN_TESTS.ko.md)에 0.4.0/스키마 4 도입을 설명합니다. EVTX 필드와 디코더 한계는 유지합니다. 전체 discovery는 이제 123개이며 extra가 없으면 휴지통/EVTX 혼합 하나를 포함한 8개를 건너뜁니다.

## USB 레지스트리 확장

0.5.0에서 스키마 5와 usb_registry 관찰을 도입했습니다. 위의 이전 스키마 도입은 과거 맥락이며 기존 아티팩트 필드 의미는 유지합니다. [USB 레지스트리 계약](USB_REGISTRY_CLI.ko.md)과 [테스트/리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 확장

패키지 0.6.0은 도입 당시 스키마 6과 recent_doc_keys/recent_docs를 추가했습니다. 위의 이전 확장 도입은 과거 맥락이며 현재 소비자는 스키마 15을 지원해야 합니다. [RecentDocs 계약](RECENT_DOCS_CLI.ko.md)과 [테스트/리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요. 기존 필드 의미는 유지합니다.

## M0 호환성 검증 후속 기록

2026-10-27 Python 3.10에서 SQLite URI 모드·EVTX 소수초 변환의 호환성 문제를 수정했습니다. macOS/Python 3.10·3.14 및 Linux ARM64 컨테이너의 최종 489개 검사와 설치 검증, 미검증 환경은 [M0 결과](M0_TESTS.ko.md)에 기록했습니다. 원시 값·보고서 스키마 15는 유지하며 기존 날짜의 결과 기록은 당시 검증 범위입니다.
