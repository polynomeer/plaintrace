# 시스템 정보 테스트와 코드 리뷰

[English](SYSTEM_INFO_TESTS.md) | **한국어**

2026-10-26에 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX 추가 의존성을 포함한 Python 테스트 440개가 생략 없이 통과했으며 기존 407개와 시스템 정보 33개입니다. 추가 의존성이 없으면 432개가 실행되고 기존 EVTX 통합 8개가 생략되어 완전한 EVTX 검증이 아닙니다. 새 어댑터는 표준 라이브러리만 사용합니다. [계약과 제한](SYSTEM_INFO_CLI.ko.md)을 참고하세요. 자체 리뷰이며 외부 승인이나 획득 증거 인증이 아닙니다.

## 재현과 합성 픽스처

기존 독립 REGF 작성기가 SOFTWARE 버전 값·ControlSet002를 가리키는 SYSTEM Select/Current·충돌하는 설정/활성/TCPIP 레이블·부호 있는 시간대 DWORD·고정 이진 FILETIME을 생성합니다. 명시적 UTC와 부호 없는/2의 보수 바이트 기준으로 변환을 검사하며 ControlSet001 값은 의도적으로 다릅니다. 미상/라이선스 필드는 합성 불투명 바이트로 유지합니다. 실제 증거나 생성 출력은 커밋하지 않고 임시 파일은 삭제합니다. 패치한 예산과 시드 기반 변이는 통제된 검사이며 전면 퍼징이나 대형 입력 성능 검증이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 4638b5101ef3c5ec389d7d77418fe62acd8557c4 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| SYS-01 | test_software_version_owner_and_build_fields_kept_separate | 버전·소유자 레이블·빌드 값 별도 보존 |
| SYS-02 | test_install_date_seconds_and_install_time_exact_filetime | 설치 초 단위와 정확한 FILETIME |
| SYS-03 | test_select_current_not_default_or_controlset001 | Current 선택과 Default/001 대체 금지 |
| SYS-04 | test_control_selection_metadata_and_conflicting_names_remain | 제어 메타데이터·충돌 이름 별도 보존 |
| SYS-05 | test_timezone_signed_biases_are_not_applied_to_timestamps | 시간대 부호·시각 보정 금지 |
| SYS-06 | test_shutdown_binary_filetime_precision_and_no_boot_claim | 종료 FILETIME 정밀도·부팅 추정 금지 |
| SYS-07 | test_key_lastwrite_is_separate_from_embedded_times | 키 마지막 쓰기와 내장 시각 분리 |
| SYS-08 | test_opaque_unknown_and_license_values_never_decoded | 미상/라이선스 값 불투명 유지 |
| SYS-09 | test_strings_expandable_tokens_and_no_normalization | 확장 문자열 토큰 무변환 |
| SYS-10 | test_unsigned_dword_maximum_and_zero | 부호 없는 DWORD 최대/0 |
| SYS-11 | test_zero_and_overflow_filetimes_retained | 0·범위 초과 FILETIME 보존 |
| SYS-12 | test_wrong_types_not_coerced_for_known_fields | 알려진 필드 형식 강제 변환 금지 |
| SYS-13 | test_wrong_numeric_sizes_and_trailing_bytes_not_recovered | 숫자 크기 오류·후행 데이터 복구 금지 |
| SYS-14 | test_unterminated_odd_empty_and_invalid_utf16 | 미종결·홀수·빈 값·잘못된 UTF-16 |
| SYS-15 | test_aligned_terminators_tails_and_invalid_status_precedence | 정렬 종결자·꼬리·오류 우선순위 |
| SYS-16 | test_missing_software_branch_and_optional_fields_diagnosed | SOFTWARE 분기·선택 필드 누락 진단 |
| SYS-17 | test_missing_optional_system_branches_no_invented_rows | 선택 SYSTEM 분기 누락 시 관측 조작 금지 |
| SYS-18 | test_missing_invalid_or_unavailable_control_selection_fatal | 미상/잘못된 제어 선택은 치명적 오류 |
| SYS-19 | test_high_controlset_and_case_insensitive_names | 큰 제어 집합·대소문자 |
| SYS-20 | test_nested_scopes_not_traversed_and_roles_not_auto_detected | 깊은 범위 미순회·역할 자동 추측 금지 |
| SYS-21 | test_physical_key_and_value_offsets_raw_bytes | 물리 키/값 오프셋과 원시 데이터 |
| SYS-22 | test_all_regf_versions_indexes_and_duplicate_names | REGF 버전·인덱스·중복 이름 |
| SYS-23 | test_dirty_and_corrupt_hives_rejected | 더티·손상 하이브 거부 |
| SYS-24 | test_observation_value_string_output_budgets | 관측·값·문자열·출력 예산 |
| SYS-25 | test_json_sqlite_schema_values_and_foreign_keys | JSON·SQLite·중첩 값·외래 키 |
| SYS-26 | test_repeated_hives_source_hashes_and_input_bytes | 반복 하이브·출처 해시·입력 보존 |
| SYS-27 | test_cli_roles_source_order_json_and_sqlite | CLI 역할·출처 순서·JSON·SQLite |
| SYS-28 | test_mixed_adapters_do_not_join_host_or_user | 혼합 어댑터의 호스트/사용자 결합 금지 |
| SYS-29 | test_strict_warning_and_fatal_later_input_atomic | 엄격 경고·나중 입력 실패의 전체 단위 게시 |
| SYS-30 | test_input_existing_output_and_sidecar_protection | 입력·기존 출력·사이드카 보호 |
| SYS-31 | test_missing_input_and_sqlite_destination | 누락 입력·SQLite 목적지 |
| SYS-32 | test_only_supplied_files_opened_and_changes_rejected | 지정 파일만 열기·변경 거부 |
| SYS-33 | test_seeded_shutdown_payload_mutations_are_controlled | 시드 기반 종료 페이로드 변이 통제 |

## 자체 리뷰

원본 범위와 이식 구현·선택 루트/필드·역할 경계·엄격한 Select/Current 해석·ControlSet001/기본값 대체 부재를 검토했습니다. 설정/활성/TCPIP 이름·버전/릴리스 레이블·설치 시각은 추측한 통합 신원 없이 별도로 남깁니다. 선택적/버전별 누락은 필드를 조작하지 않고 경고하며 미상/라이선스 값은 추측한 제품 키 대신 불투명하게 유지합니다.

정확한 레지스트리 형식/길이·정수 기반 에포크와 부호 편차·원시 시각과 키 시각·잘못된 유니코드/꼬리 우선순위·제한·물리 셀 오프셋·반복/혼합 출처·스키마 14·JSON/SQLite 출처 외래 키·전체 단위 출력 보호를 검토했습니다. 편차로 다른 시각을 수정하지 않으며 저장 종료 데이터로 가동/부팅/정상 종료를 증명하지 않습니다. 공유 디코더와 EnScript 바이트는 변경하지 않았고 자체 리뷰에서 남은 차단 문제는 없으며 실제 호스트 검증은 미완료입니다.

## 독립 비교와 검증 결과

합성 SOFTWARE/SYSTEM 키·이름·형식·원시 바이트·물리 nk/vk 오프셋을 python-registry 1.3.1과 비교하고 헤더/페이로드의 4바이트 차이를 명시적으로 반영했습니다. 고정 DWORD/FILETIME과 부호 편차 검사로 선택 값을 독립 확인했습니다. 체크아웃 밖에 설치한 0.14.0 콘솔에서 두 역할 플래그·반복 출처·스키마 14 JSON/SQLite·중첩 원시 값·출처 해시·외래 키·입력 보존을 검증했습니다. 실제 Windows 설정 의미나 획득 하이브를 인증하는 검사는 아닙니다.

EVTX를 포함한 전체 440개 테스트가 통과했습니다. EnScript 정적 회귀 11개·생성 소스 참조 4개·양언어 링크/구조/테스트 매핑·아카이브 검증도 통과했습니다. EnScript 13개와 원본 매니페스트는 기준과 같고 아카이브 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 무결성/정적 검사이며 EnCase 컴파일이나 실행이 아닙니다.

## 남은 검증과 미지원 구조

Windows 버전별 실제 획득 SOFTWARE/SYSTEM·Windows/Linux 실행·Python 3.10·독립 실제 레코드 의미·대형 입력 성능·획득 경쟁은 미검증이고 EnCase 컴파일/실행도 미검증입니다. 파일/볼륨/GUI/차트 API·SAM 계정 분석·제품 키 도출·과거 제어 집합·깊은/다른 목록·네이티브 REGF 1.6/big data/휘발성/링크/삭제/슬랙 구조는 미지원입니다. 로그 재생·복구·과거 이벤트에 시간대 적용·OS/사용자 소유권 추론·부팅/가동/정상 종료 주장·자동 결합을 하지 않습니다. 필드·상태 우선순위·제한은 CLI 문서를 따릅니다.
