# SAM 계정 테스트와 코드 리뷰

[English](SAM_ACCOUNTS_TESTS.md) | **한국어**

2026-10-26에 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX 추가 의존성을 포함한 Python 테스트 475개가 생략 없이 통과했으며 기존 440개와 SAM 메타데이터 35개입니다. 추가 의존성이 없으면 467개가 실행되고 기존 EVTX 통합 8개가 생략되어 완전한 EVTX 검증이 아닙니다. SAM 메타데이터는 표준 라이브러리만 사용합니다. [계약과 제한](SAM_ACCOUNTS_CLI.ko.md)을 참고하세요. 자체 리뷰이며 외부 승인이나 획득 증거 인증이 아닙니다.

## 재현과 합성 픽스처

독립 합성 REGF 작성기가 표준 RID/Names 키를 만듭니다. 고정 80바이트 F 작성기는 알려진 명시적 오프셋·원시 플래그/카운터·고정 100 ns/UTC 기준을 사용합니다. 별도 204바이트 V 헤더 작성기가 UTF-16 설명자 필드 9개·유니코드/이모지·리터럴 경로를 직접 구성합니다. 자격 증명 레코드·부트 키·암호화 픽스처·실제 획득 증거는 포함하지 않습니다. 임시 하이브/출력은 삭제하고 패치 예산/시드 변이는 통제 검사이며 전면 퍼징이나 대형 입력 성능 인증이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code def0c228b0ef2721470d63e3adbf14719311428c -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| SAM-01 | test_account_unicode_name_mapping_and_rid | 유니코드 계정·이름 참조·RID |
| SAM-02 | test_fixed_offsets_unsigned_counts_country_and_flags | 고정 오프셋·부호 없는 카운터·국가·플래그 |
| SAM-03 | test_exact_filetimes_three_fields_and_separate_key_time | 정확한 시각 3개와 키 시각 분리 |
| SAM-04 | test_zero_and_sentinel_times_not_calendar_dates | 0·센티널은 달력 시각 아님 |
| SAM-05 | test_out_of_range_time_warns_without_losing_raw_ticks | 범위 초과와 원시 틱 보존 |
| SAM-06 | test_unknown_flags_and_maximum_counters_preserved | 미상 비트·최대 카운터 |
| SAM-07 | test_f_rid_mismatch_retained_and_not_overwritten | F RID 불일치 보존 |
| SAM-08 | test_f_wrong_type_size_missing_do_not_guess_layout | F 형식·크기·누락 시 추측 금지 |
| SAM-09 | test_missing_v_still_retains_f_metadata | V 누락에도 F 보존 |
| SAM-10 | test_v_wrong_type_and_short_header_retained_as_summary | V 형식·짧은 헤더 요약 |
| SAM-11 | test_v_relative_offsets_descriptor_bytes_and_literals | V 상대 오프셋·설명자·리터럴 |
| SAM-12 | test_v_empty_length_is_not_missing | V 빈 길이와 누락 구분 |
| SAM-13 | test_v_invalid_bounds_keep_descriptors_without_repair | V 범위 오류 설명자 보존·복구 금지 |
| SAM-14 | test_v_odd_offset_or_length_not_shifted | V 홀수 오프셋/길이 이동 금지 |
| SAM-15 | test_v_invalid_unicode_and_embedded_nul_preserved | V 유니코드 오류·중간 NUL |
| SAM-16 | test_v_overlapping_ranges_diagnosed_without_silent_repair | V 겹침 진단·묵시적 복구 금지 |
| SAM-17 | test_unselected_v_payload_and_other_values_not_exported | 미선택 V·기타 값 콘텐츠 미출력 |
| SAM-18 | test_names_default_type_is_rid_not_data_integer | Names 기본 형식이 RID이며 데이터 정수 아님 |
| SAM-19 | test_orphan_invalid_and_duplicate_name_mappings_retained | 고아·잘못됨·중복 매핑 보존 |
| SAM-20 | test_missing_names_unmapped_rid_no_invented_username | Names 누락 시 사용자 이름 조작 금지 |
| SAM-21 | test_missing_empty_users_and_noncanonical_children | 루트 누락·빈 Users·비표준 자식 |
| SAM-22 | test_descendants_and_container_values_not_traversed | 하위·컨테이너 값 미순회 |
| SAM-23 | test_physical_cell_offsets_and_key_filetimes | 물리 셀 오프셋·키 FILETIME |
| SAM-24 | test_case_insensitive_paths_and_record_names | 경로·레코드 이름 대소문자 |
| SAM-25 | test_regf_versions_indexes_and_duplicate_values | REGF 버전·인덱스·중복 값 |
| SAM-26 | test_dirty_and_corrupt_hive_rejected | 더티·손상 하이브 거부 |
| SAM-27 | test_account_mapping_value_string_and_output_budgets | 계정·매핑·값·문자열·출력 예산 |
| SAM-28 | test_json_sqlite_schema_raw_strings_and_foreign_keys | JSON·SQLite·원시 문자열·외래 키 |
| SAM-29 | test_repeated_sources_hashes_and_unchanged_input | 반복 출처·해시·입력 보존 |
| SAM-30 | test_cli_json_strict_and_sqlite | 실제 CLI·엄격 모드·SQLite |
| SAM-31 | test_mixed_sources_do_not_attribute_machine_or_sid | 혼합 출처의 장비/SID 귀속 금지 |
| SAM-32 | test_later_failure_no_partial_report | 나중 입력 실패 시 부분 보고서 없음 |
| SAM-33 | test_input_existing_output_and_sidecar_protected | 입력·기존 출력·사이드카 보존 |
| SAM-34 | test_missing_input_sqlite_destination_and_only_hive_reads | 누락 입력·SQLite 목적지·지정 하이브만 읽기 |
| SAM-35 | test_seeded_f_payload_mutations_keep_controlled_status | 시드 기반 F 변이 상태 통제 |

## 자체 리뷰와 수정

표준 RID 탐색·Names 기본 형식 참조·고아/잘못됨/중복 매핑·F/V 누락·RID/이름 불일치·출처 내 연결을 검토했습니다. 선호 이름·전체 SID·관리자 소속·실효 로그인 정책을 만들어내지 않습니다. 정확한 F 구조와 부분 V 설명자 해독을 구분하고 원시 비트 레이블/카운터의 제한을 유지합니다. 0/센티널/범위 초과 시각을 키 마지막 쓰기와 구분하며 고정 암호 만료 기간을 계산하지 않습니다.

V 오프셋/길이 범위·정렬·리터럴/유니코드 오류·중간 NUL·문자열 겹침·원시 선택 필드 출처·출력 콘텐츠 경계를 검토했습니다. 전체 V/미선택 페이로드와 다른 값 콘텐츠는 내보내지 않고 크기/다이제스트를 유지합니다. 자격 증명 포인터·해시 추출/복호화·부트 키 파서는 추가하지 않습니다. 콘텐츠 선택은 임의 텍스트의 비식별 처리 보장이 아닙니다. 불필요한 제곱 시간 작업을 줄이기 위해 후보 목록 반복 검색과 중복 매핑 스캔을 오프셋 집합/카운터로 바꿨습니다. 기존 디코더 의미와 EnScript 바이트는 유지합니다.

입력 해시·출처 순서·스키마 15·JSON/SQLite 복합 매핑 외래 키·제한·엄격 종료·전체 단위 출력 게시를 검토했습니다. 자체 리뷰에서 남은 차단 문제는 없으며 획득 데이터/호스트 검증은 미완료입니다.

## 독립 비교와 검증 결과

합성 계정/매핑 키·값 이름·형식·원시 선택 F/V 문자열 바이트·물리 nk/vk 오프셋을 python-registry 1.3.1과 비교하고 셀 헤더/페이로드의 4바이트 차이를 반영했습니다. 고정 오프셋 정수/FILETIME·길이 경계 UTF-16 검사로 예상 메타데이터를 독립 확인했습니다. 체크아웃 밖에 설치한 0.15.0 콘솔에서 반복 SAM 입력·스키마 15 JSON/SQLite·출처 해시·원시 문자열·매핑 외래 키·입력 보존을 검증했습니다. 실제 Windows SAM 구조나 신원 의미를 인증하는 검사는 아닙니다.

독립 판독기의 raw_data API는 이 픽스처의 길이 0·비표준 형식 Names 기본 값에서 포인터 4바이트를 반환합니다. 페이로드가 아니므로 선언된 raw_data_length 0·RID 형식·물리 vk 오프셋을 직접 확인했습니다. Plaintrace는 선언 길이를 따라 빈 값을 유지하며 이 특수 사례의 raw_data API 동작까지 같다고 주장하지 않습니다.

EVTX를 포함한 전체 테스트 475개가 통과했습니다. EnScript 정적 회귀 11개·생성 소스 참조 4개·양언어 문서/링크/테스트 매핑·아카이브 검증도 통과했습니다. EnScript 13개와 원본 매니페스트는 기준과 같으며 원본 아카이브 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 무결성/정적 검사이며 EnCase 컴파일/실행이 아닙니다.

## 남은 검증과 미지원 구조

Windows 버전/F/V 리비전별 실제 획득 SAM·Windows/Linux 실행·Python 3.10·독립 실제 레코드 해석·대형 컬렉션·획득 경쟁은 미검증입니다. 대체 루트/구조·미할당 필드·그룹/별칭/도메인 정책/전체 SID·자격 증명 추출/복호화·네이티브 REGF 1.6/big data/휘발성/링크/삭제/슬랙 구조는 미지원입니다. 로그 재생·복구·권한/만료/소유권 추론·자동 하이브 간 결합은 없고 EnCase 컴파일/실행은 여전히 미검증입니다. 정확한 필드·상태·출력 제한은 CLI 문서를 따릅니다.
