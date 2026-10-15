# USB 레지스트리 테스트와 코드 리뷰

**한국어** | [English](USB_REGISTRY_TESTS.md)

2026-10-15 macOS/Python 3.14에서 검증하고 수동 리뷰했습니다. EVTX extra가 있으면 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개, USB 레지스트리 25개로 Python 148개가 통과합니다. 없으면 140개를 실행하고 기존 통합 8개를 건너뜁니다. 레지스트리 검사에는 새 런타임/테스트 의존성이 필요하지 않습니다. [사용법과 계약](USB_REGISTRY_CLI.ko.md)을 확인하세요. 자체 리뷰이며 외부 승인이 아닙니다.

## 재현과 픽스처

합성 REGF 헤더, hbin, 할당/비할당 셀, nk/vk, li/lf/lh/ri 인덱스와 인라인/외부 값을 임시 디렉터리에 독립적으로 조립합니다. 알려진 Unicode 문자열, Select Current=2와 100 ns 나머지가 알려진 원시 FILETIME을 오라클로 사용합니다. 획득 하이브/증거나 출력을 커밋하지 않습니다. 네이티브 리더, 실제 CLI 프로세스와 JSON/SQLite 출력을 실행합니다. 자원 상한 검사는 작은 예산을 패치하며 대형 사건 성능을 주장하지 않습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d174bc8c7f57aa5f91e0e3c87113e4af78ce3eb1 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 검사

| ID | 테스트 메서드 | 오라클 / 동작 |
| --- | --- | --- |
| USB-01 | test_active_controlset_and_device_identity | Select Current=2, 식별자와 키 수정 시각 근거 |
| USB-02 | test_property_filetime_meanings_raw_values_and_offsets | 속성 네 의미, 정확한 틱과 물리 출처 |
| USB-03 | test_usb_vid_pid_and_instance_not_physical_serial_claim | VID/PID와 그대로의 instance ID, 일련번호 주장 없음 |
| USB-04 | test_mounteddevices_kept_raw_without_drive_inference | 드라이브 연결 없이 MountedDevices 원시 바이트 보존 |
| USB-05 | test_software_and_ntuser_context_is_not_automatically_joined | 하이브 간 식별 결합 없는 SOFTWARE/NTUSER 맥락 |
| USB-06 | test_deviceclasses_context_not_usb_proof | DeviceClasses 맥락을 입증된 USB 연결로 해석하지 않음 |
| USB-07 | test_all_supported_index_layouts_and_regf_versions | li/lf/lh/ri 인덱스와 REGF 1.3/1.4/1.5 |
| USB-08 | test_inline_dword_bigendian_qword_multisz_unknown | 인라인 DWORD, 빅 엔디언, QWORD, MULTI_SZ와 미해석 타입 |
| USB-09 | test_missing_select_or_bad_current_never_falls_back | 누락/잘못된 Select에서 ControlSet 추정 없음 |
| USB-10 | test_empty_branches_and_absent_properties_diagnosed | 빈/누락 분기와 속성 부재 경고 |
| USB-11 | test_malformed_property_type_size_and_ambiguity_retained | 모호/타입 오류/크기 오류 속성 원시 보존 |
| USB-12 | test_zero_overflow_property_and_invalid_text_preserved | 0/범위 초과 시각과 해독 불가능 UTF-16 |
| USB-13 | test_dirty_checksum_version_and_extent_fail | dirty/체크섬/버전/타입/형식/범위 거부 |
| USB-14 | test_cell_reference_free_interior_bad_size_and_index_cycle | 할당 경계, 잘못된 셀과 RI 순환 |
| USB-15 | test_duplicate_names_parent_alias_and_wrong_record_rejected | 중복 이름, 부모 불일치와 별칭 거부 |
| USB-16 | test_counts_value_size_and_output_limits | 셀/항목/값/행/출력 예산과 분할 값 상한 |
| USB-17 | test_truncations_and_seeded_mutations_are_contract_errors | 경계 절단과 고정 시드 변형 100개 |
| USB-18 | test_unicode_keys_case_insensitive_paths_and_value_names | Unicode 키와 대소문자 무관 조회 |
| USB-19 | test_source_hashes_roles_and_json_sqlite_schema_five | 반복 출처 해시, JSON/SQLite 스키마 6와 외래 키 |
| USB-20 | test_cli_subprocess_strict_and_multiple_roles | 역할 출처와 strict 경고를 포함한 실제 CLI 프로세스 |
| USB-21 | test_later_bad_input_atomic_and_existing_output_protected | 후속 치명적 하이브의 원자성과 출처 덮어쓰기 방지 |
| USB-22 | test_stable_read_and_no_logs_or_live_registry_access | 획득 하이브만 열며 변경 입력 거부 |
| USB-23 | test_review_inline_length_key_flags_and_name_corruption | 인라인 크기/키 플래그/이름/중복 참조와 잘못된 값 |
| USB-24 | test_review_header_size_cap_multibin_and_unknown_role | 입력 상한, 여러 hbin과 미지 역할 거부 |
| USB-25 | test_review_mixed_existing_artifacts_and_usb_source_order | 기존 브라우저/휴지통 입력과 USB 출처 결합 |

## 리뷰 발견 사항과 독립 대조

| 우선순위 | 검토 위험 / 수정 | 근거 |
| --- | --- | --- |
| 높음 | ControlSet001 가정으로 오래된 장치 선택 가능 | Select/Current와 선택 ControlSet 검증; USB-01/09 |
| 높음 | 키 수정 시각을 연결 이력으로 바꾸면 잘못된 시각 생성 | 키 메타데이터와 타입을 확인한 속성 FILETIME 분리; USB-02/11/12 |
| 높음 | 손상 개수/참조, RI 순환과 공유 대형 값의 통제되지 않는 파싱 | 할당 셀 경계, view 버퍼, 순환/개수/이름/데이터 예산, 중복 참조 조기 거부; USB-14/15/16/23 |
| 중간 | 반복 경로 검색이 장치 속성마다 작업량 증폭 | 대소문자 무관 하위 키 맵 캐시; 인덱스/속성 검사 통과 |
| 중간 | 맥락 키 이름을 장치 ID로 오해 가능 | Enum 외의 관찰에서 device/instance ID를 null로 유지; USB-04/05/06 |
| 중간 | 하이브 간 부분 문자열 결합으로 드라이브/사용자/일련번호 관계 생성 | 별도 관찰과 명시적 출처 역할 유지; USB-03/05/19/20 |
| 중간 | 스키마 확장이 소비자를 조용히 깨뜨릴 수 있음 | JSON/SQLite 버전 5와 영문·국문 변경 안내; USB-19/25 |

별도 수동 검사에서 python-registry 1.3.1이 네 합성 인덱스를 독립적으로 열고 Select Current=2, Unicode FriendlyName과 정확한 원시 도착 FILETIME을 확인했습니다. 해당 라이브러리 datetime은 100 ns 나머지를 마이크로초로 반올림하지만 이 구현은 정수로 절삭하고 원시 틱을 남깁니다. 라이브러리는 임시 검증 환경에만 설치했으며 패키지/테스트 의존성이나 독립 실제 하이브 동등성 검증이 아닙니다. 구형 예시의 0064 설치/0065 최초 설치 이름 뒤바뀜을 피하도록 Microsoft devpkey.h를 확인했습니다.

## 검증과 남은 한계

설치한 plaintrace 0.5.0을 체크아웃 밖에서 SYSTEM/SOFTWARE/NTUSER, JSON/SQLite 스키마 5, 속성 값, 출처 오프셋과 입력 해시 보존으로 스모크 검증합니다. EnScript 이식 가능한 검사 11개, 자동 생성 소스 참조 4개, 영문·국문 문서/테스트 대응, 공백/소스 비교와 아카이브 전용 검증은 별도로 통과합니다. 아카이브 ref, 원본 EnScript 13개, 원래 README/트리와 2017년 합성 커밋 263개를 보존하며 아카이브 검사에는 로컬 원래 백업 ref가 필요하고 컴파일 검증이 아닙니다.

실제 획득 하이브, Windows/Linux, Python 3.10, 독립 실제 하이브 비교, 대형 사건 벤치마크나 라이브 획득 검증은 수행하지 않았습니다. dirty/로그 재생, 분할 big data, 미지원 REGF 버전, 휘발성/링크/삭제/슬랙 구조와 대체 장치 속성 저장은 미지원입니다. 자동 드라이브/볼륨/장치/사용자 결합이나 완전한 USB 세션 타임라인을 주장하지 않습니다. 키 메타데이터는 연결 시각이 아니며 저장된 최근 도착/제거 값도 전체 이력이 아닙니다. 기존 브라우저/LNK/Prefetch/EVTX/휴지통 한계와 EnCase 컴파일/실행 미검증도 문서에 유지합니다.

## RecentDocs 회귀 실행 (2026-10-15)

현재 전체 discovery는 기존 148개와 RecentDocs 27개로 175개가 통과합니다. EVTX extra가 없으면 167개를 실행하고 기존 통합 8개를 건너뜁니다. 현재 출력 검사는 스키마 6이며 이전 검증 개수/스키마 도입은 과거 기록입니다. [RecentDocs 재현과 리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요.
