# USB 레지스트리 Python CLI

**한국어** | [English](USB_REGISTRY_CLI.md)

현재 패키지는 0.9.0이며 모든 출력은 스키마 9입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [ShellBags 확장](SHELLBAGS_CLI.ko.md)을 따릅니다.

2026-10-15 `d174bc8c7f57aa5f91e0e3c87113e4af78ce3eb1`을 기준으로 `codex/python-usb-registry`에서 구현했습니다. EnScript, 아카이브 ref/매니페스트와 재구성된 2017년 커밋 263개를 보존합니다. 패키지 0.5.0/보고서 스키마 5는 독립 Python 구현의 확장입니다.

## 사용과 획득

Python 3.10 이상을 선언하며 macOS/Python 3.14로 검증했습니다. 레지스트리 파싱에는 표준 라이브러리를 사용하고 새 런타임 의존성은 없습니다. 안정적으로 획득한 바이너리 REGF 하이브의 역할을 명시하며 파일명으로 탐지하지 않습니다. 역할 플래그는 각각 독립적으로 반복할 수 있습니다. 역할이나 컴퓨터를 섞어도 장치 식별자를 자동 결합하지 않습니다. 출처 순서는 기존 브라우저/LNK/Prefetch/EVTX/휴지통 이후 SYSTEM, SOFTWARE, NTUSER 그룹이며 각 그룹 안에서는 지정 순서입니다. 선택 EVTX extra는 EVTX 입력/전체 통합 discovery에만 필요합니다.

```sh
python3 -m plaintrace --usb-system /path/to/SYSTEM --output usb.json
python3 -m plaintrace --usb-system /path/to/SYSTEM --usb-software /path/to/SOFTWARE --usb-ntuser /path/to/NTUSER.DAT --format sqlite --output usb.sqlite
python3 -m plaintrace --usb-system /case-a/SYSTEM --usb-system /case-b/SYSTEM --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --usb-system /path/to/SYSTEM
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --usb-system C:\acquired\SYSTEM --output usb.json
```

라이브 레지스트리가 아닌 획득한 정상/동기화 하이브를 사용합니다. 읽기는 상한을 적용하고 읽기 전/본문/후 해시를 비교하며 지정 파일만 엽니다. LOG1/LOG2, 트랜잭션 파일과 라이브 Windows API에 접근하지 않습니다. dirty 시퀀스는 치명적 오류이며 로그 재생이나 복구를 시도하지 않습니다. 정상 시퀀스/체크섬도 완전한 획득이나 진위를 입증하지 않습니다. 출력, strict 경고 종료 1, 치명적 종료 2, 전체 입력 원자적 게시와 덮어쓰기/출처 사이드카 보호는 [공통 CLI](PYTHON_CLI.ko.md) 규칙을 유지합니다.

## 관찰 자료와 시각 근거

SYSTEM은 1..999의 고유 DWORD Select/Current와 해당 ControlSet을 요구합니다. ControlSet001로 대체하지 않습니다. 이름은 대소문자를 구분하지 않고 조회하며 모호한 이름은 실패합니다. 선택한 ControlSet만 해석합니다. 선택 분기/속성 슬롯이 없으면 시각을 만들어내지 않고 명시적 경고를 남깁니다.

| observation_kind | 출처와 해석 |
| --- | --- |
| usbstor | SYSTEM 선택 ControlSet Enum/USBSTOR의 장치/인스턴스 키; 그대로의 instance ID, vendor/product/revision 토큰과 FriendlyName |
| usb | SYSTEM 선택 ControlSet Enum/USB의 장치/인스턴스 키; VID/PID 토큰과 그대로의 instance ID; 저장 장치 전용이 아님 |
| device_interface | 디스크/볼륨 DeviceClasses GUID의 바로 아래 키; 맥락 키/값이며 입증된 USB 식별자가 아님 |
| mounted_devices | SYSTEM MountedDevices 키와 원시 값; 드라이브/볼륨 자동 연결 없음 |
| portable_device | SOFTWARE Microsoft/Windows Portable Devices/Devices 바로 아래 키; 맥락 FriendlyName과 값 |
| mount_point | NTUSER Software/Microsoft/Windows/CurrentVersion/Explorer/MountPoints2 바로 아래 키; 사용자/SID 식별 없음 |

출력 경로는 실제 레지스트리 역슬래시를 사용합니다. 맥락 분기에는 비 USB 장치도 있을 수 있습니다. 부분 문자열 결합, 드라이브 문자 추정, 하드웨어 일련번호 주장, 하이브 간 식별 연계나 사용자 소유 주장 없이 보존합니다. EVTX 연결이나 세션 복원을 수행하지 않습니다. 레지스트리는 상태 스냅샷이며 모든 연결의 완전한 시간순 목록이 아닙니다.

`key_last_written`과 `key_last_write_raw`는 키의 마지막 수정 메타데이터이며 최초 연결, 부팅 후 최초 연결, 마지막 연결이나 값별 수정 시각이 아닙니다. 장치 시각은 장치/인스턴스 Properties/{83da6326-97a6-4088-9453-a1923f573b29} 아래에서 별도로 읽습니다. 지원 속성 키는 정확히 8바이트인 REG_BINARY 또는 타입 16의 고유 기본 값이나 00000000 값을 사용합니다. 모호/잘못된 값은 원시 상태로 남기고 해석 시각은 null입니다. 없는 슬롯은 경고와 함께 제외합니다. 더 깊은 대체 속성 인코딩은 미지원입니다.

| 속성 키 | 의미 |
| --- | --- |
| 0064 | install_date; 설치/드라이버 갱신 시각이며 최초 물리 연결과 같지 않을 수 있음 |
| 0065 | first_install_date; 이 시스템에서 해당 장치 인스턴스의 최초 설치 |
| 0066 | last_arrival_date; 저장된 최근 장치 도착 |
| 0067 | last_removal_date; 저장된 최근 장치 제거 |

원시 FILETIME은 부호 없는 십진 텍스트로 남기고 UTC 표시는 고정 시간대 보정 없이 정수로 100 ns를 마이크로초까지 절삭합니다. 0 시각은 null, 범위 초과는 원시 틱 보존과 경고를 남깁니다. 설치/도착/제거 속성은 없거나 오래된 값일 수 있으며 완전한 세션, 현재 연결 상태, 사용자 의도나 물리 장치 식별을 입증하지 않습니다. 원본 EnScript와 달리 키 수정 시각을 연결 시각으로 바꾸지 않고 ControlSet001/부분 문자열 가정을 재사용하지 않습니다.

## REGF 리더와 제한

네이티브 리더는 헤더 서명/체크섬, 시퀀스 일치, 주 하이브 타입, 직접 메모리 형식, 버전 1.3/1.4/1.5와 정확한 선언 bin 범위를 확인합니다. hbin의 할당 셀 경계를 색인하고 bin 서명/오프셋, 셀 정렬/크기, nk/vk 참조, 부모 연결, 개수, 이름 고유성, li/lf/lh/ri 인덱스와 인덱스 순환을 검사합니다. 이름은 압축 Latin-1이나 UTF-16LE를 지원하며 잘못된 이름은 치명적 오류입니다. 접근한 심볼릭 링크 키와 휘발성 하위 키는 거부합니다. 비할당 셀은 순회하지 않습니다. 보안/클래스 레코드, 인덱스 해시/힌트와 무관한 데이터는 의미 검증하지 않습니다.

하이브별 제한은 입력 64 MiB, 검사한 할당/비할당 셀 250000개, 접근한 키/인덱스 항목/값 100000개, 접근 키별 값 4096개, 값별 16344바이트, 접근 값 데이터/이름 바이트 합계 16 MiB, 출력 관찰 10000개, 직렬화 관찰 JSON 32 MiB입니다. 셀 버퍼는 view를 사용해 큰 셀 반복 복사를 피하고 대소문자 무관 하위 키 색인은 반복 경로 조회에 캐시합니다. 제한된 파싱이며 메모리 샌드박스가 아닙니다. 출력 크기는 할당 후 검사하고 결합 보고서는 메모리에 남습니다. 정상 대형 하이브도 거부될 수 있습니다. 네이티브 프로세스 시간 제한은 구현하지 않았습니다.

값은 이름, 타입, 물리 값 셀 오프셋과 정확한 데이터 hex를 보존합니다. REG_SZ/EXPAND_SZ/MULTI_SZ는 환경 변수 확장 없이 UTF-16을 해독하고 DWORD/빅 엔디언 DWORD/QWORD는 십진 텍스트가 됩니다. 미지원 타입은 원시로 남깁니다. 잘못된 문자열/숫자 크기도 경고와 원시 값으로 보존합니다. 값별 시각을 만들지 않습니다. 직접 값 상한을 넘는 분할 big-data/db, REGF 1.6/구형 레이아웃, 트랜잭션 로그 복구, 삭제 셀 카빙, 하이브 슬랙, 텍스트 .reg 입력, 레지스트리 링크와 추가 USB 연계 구조는 미지원입니다. 접근한 미지원 구조는 입력을 조용히 누락하지 않고 전체 보고서를 실패시킵니다.

## 현재 스키마와 코드 구조

USB 하이브가 없는 보고서도 JSON format_version 9와 SQLite user_version 9를 사용합니다. 버전 5는 usb_registry와 개수를 추가하며 기존 컬렉션 의미를 유지합니다. 버전 1–5 보고서는 재작성/마이그레이션하지 않으며 소비자는 버전 9를 인식해야 합니다. sources의 source_kind는 usb_registry, schema_family는 registry_system/registry_software/registry_ntuser이며 획득 파일 sha256과 null browser/database/WAL 필드를 사용합니다. record_id는 source_id 범위의 물리 nk 셀 헤더 오프셋입니다.

| JSON usb_registry 필드 | 의미 |
| --- | --- |
| source_id, record_id, hive_role, observation_kind | 입력 출처, 물리 레코드 식별과 해석 범위 |
| key_path, key_last_written, key_last_write_raw | 레지스트리 경로, 별도 UTC 키 수정 표시와 원시 틱 |
| control_set, device_id, instance_id | 선택 ControlSet과 그대로의 Enum 식별자; 맥락 행의 장치 ID는 null |
| vendor, product, revision, vid, pid, friendly_name | 명시적 토큰/REG_SZ FriendlyName이며 하드웨어 식별 보장이 아님 |
| device_times | 속성 ID/의미, 속성 키 경로/오프셋, 원시 틱, UTC와 원시 속성 값 |
| values | 순서 있는 value_offset/name/type/data_hex/decoded 객체; SQL 키워드를 피하도록 SQLite 열 이름은 values_json |

객체/배열은 JSON에서 그대로, SQLite에서 JSON 텍스트로 저장하며 출처 외래 키와 바인딩 삽입을 유지합니다. [registry_hive.py](../plaintrace/registry_hive.py)는 제한된 REGF 접근을, [usb_registry.py](../plaintrace/usb_registry.py)는 USB/맥락 분기와 시각 의미를 담당합니다. CLI, 출처 결합, 보고서 모델과 출력기에 역할 플래그, 출처와 스키마 9를 추가합니다.

## 검증과 남은 한계

[테스트와 수동 리뷰](USB_REGISTRY_TESTS.ko.md)는 신규 검사 25개를 대응합니다. EVTX extra가 있으면 Python 148개가 모두 통과하고 없으면 140개를 실행하며 기존 통합 8개를 건너뜁니다. 생성한 하이브로 모든 지원 인덱스, 압축/Unicode 이름, 인라인/외부 값, 속성 시각, dirty/손상/순환 입력, 제한, 출처 보존과 실제 CLI JSON/SQLite를 검사합니다. 독립 python-registry 1.3.1도 합성 인덱스/선택 값을 읽으며 이는 임시 검증 의존성이고 패키지 의존성이나 실제 하이브 동등성 인증이 아닙니다.

여러 Windows 버전의 실제 획득 SYSTEM/SOFTWARE/NTUSER, Windows/Linux, Python 3.10, 대형 사건 성능, 라이브 획득, 독립 실제 하이브 대조와 EnCase 컴파일/실행은 미검증입니다. 기존 브라우저/LNK/Prefetch/EVTX/휴지통의 미지원 구조와 호스트 한계도 문서에 유지합니다. 완전한 USB 연결 이력, 드라이브 매핑, 세션 연계나 증거 완전성을 주장하지 않습니다.

## 참고 자료

[libregf REGF 작업 명세](https://github.com/libyal/libregf/blob/main/documentation/Windows%20NT%20Registry%20File%20%28REGF%29%20format.asciidoc), [Microsoft devpkey.h 속성 ID](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/devpkey.h), [Microsoft FirstInstallDate 의미](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-firstinstalldate), [RegRipper USBSTOR 저장 레이아웃 예시](https://github.com/keydet89/RegRipper3.0/blob/master/plugins/usbstor.pl)를 참고했습니다. 구형 포렌식 예시에서 설치 이름을 바꿔 표기하는 경우 Microsoft 속성 ID를 따릅니다. 의존성 소스를 포함하지 않습니다. [원본 소스 분석](ANALYSIS.ko.md)을 확인하세요.

## RecentDocs 확장

패키지 0.6.0은 도입 당시 스키마 6과 recent_doc_keys/recent_docs를 추가했습니다. 위의 이전 확장 도입은 과거 맥락이며 현재 소비자는 스키마 9을 지원해야 합니다. [RecentDocs 계약](RECENT_DOCS_CLI.ko.md)과 [테스트/리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요. 기존 필드 의미는 유지합니다.
