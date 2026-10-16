# RunMRU 테스트와 코드 리뷰

[English](RUN_MRU_TESTS.md) | **한국어**

2026-10-16에 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX 추가 의존성을 포함한 Python 테스트 376개가 생략 없이 통과했으며 기존 346개와 RunMRU 30개입니다. 추가 의존성이 없으면 368개가 실행되고 기존 EVTX 통합 8개가 생략되므로 완전한 EVTX 검증이 아닙니다. RunMRU 자체는 추가 런타임 의존성이 없습니다. [계약과 제한](RUN_MRU_CLI.ko.md)을 참고하세요. 자체 리뷰이며 외부 승인이나 획득 증거 인증이 아닙니다.

## 재현과 합성 픽스처

기존 독립 REGF 작성기가 정확한 MRUList REG_SZ 제어와 문자 항목 값을 만듭니다. UTF-16 바이트·고정 순위/간격·원시 오프셋·정확한 FILETIME이 독립 기준입니다. 유니코드/이모지·리터럴 접미부와 제어 문자 구분·따옴표/공백·잘못된 제어·미지원 데이터·CLI 전체 단위 실패를 포함합니다. 생성 하이브/출력은 임시 디렉터리만 사용하고 획득 증거는 커밋하지 않습니다. 패치한 예산과 시드 기반 페이로드 변이는 대형 입력 성능 시험이나 전면 퍼징이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 53f0d510b2d06f991394cf5858be22f54416a1f4 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| RUN-01 | test_unicode_literal_commands_and_order | 유니코드 명령과 저장 순서 |
| RUN-02 | test_no_suffix_whitespace_argument_or_environment_normalization | 접미부·공백·인수·환경 토큰 무변환 |
| RUN-03 | test_duplicates_retained_across_slots | 슬롯 간 동일 명령 별도 보존 |
| RUN-04 | test_missing_references_keep_rank_gaps | 없는 참조의 순위 간격 |
| RUN-05 | test_unlisted_entry_has_null_rank | 목록 외 항목 null 순위 |
| RUN-06 | test_missing_control_does_not_guess_alphabetical_rank | 제어 누락 시 알파벳 순위 추측 금지 |
| RUN-07 | test_invalid_controls_never_assign_rank | 잘못된 제어에 순위 없음 |
| RUN-08 | test_mrulistex_and_ambiguous_controls_not_selected | 미지원·모호한 제어 선택 금지 |
| RUN-09 | test_valid_empty_order_distinct_from_missing | 유효한 빈 순서와 누락 구분 |
| RUN-10 | test_ascii_single_letter_names_and_unknown_metadata | ASCII 한 문자 슬롯과 미상 메타데이터 |
| RUN-11 | test_case_insensitive_control_path_and_slots | 경로·제어·슬롯 대소문자 |
| RUN-12 | test_wrong_value_types_kept_raw_without_string_decoding | 다른 형식은 원시 보존 |
| RUN-13 | test_unterminated_and_odd_strings_retained | 미종결·홀수 문자열 |
| RUN-14 | test_invalid_utf16_escaped_and_bytes_preserved | 잘못된 UTF-16 바이트 이스케이프 |
| RUN-15 | test_first_aligned_terminator_and_trailing_bytes | 첫 정렬 종결자와 후행 바이트 |
| RUN-16 | test_empty_command_kept_with_warning | 빈 명령 경고·보존 |
| RUN-17 | test_key_time_and_physical_offsets_not_per_command_times | 키 시각과 물리 오프셋 분리 |
| RUN-18 | test_absent_empty_and_nested_scopes | 루트 누락·빈 키·하위 키 |
| RUN-19 | test_all_regf_versions_and_index_kinds | REGF 버전·인덱스 조합 |
| RUN-20 | test_dirty_corrupt_and_duplicate_aliases_rejected | 더티·손상·중복 별칭 거부 |
| RUN-21 | test_entry_string_and_output_limits | 항목·문자열·출력 제한 |
| RUN-22 | test_json_sqlite_schema_raw_data_and_foreign_keys | JSON·SQLite·원시 값·외래 키 |
| RUN-23 | test_repeated_sources_hashes_and_input_unchanged | 반복 출처·해시·입력 보존 |
| RUN-24 | test_cli_subprocess_json_strict_and_sqlite | 실제 CLI·엄격 모드·SQLite |
| RUN-25 | test_mixed_adapters_preserve_source_groups | 혼합 어댑터 출처 순서 |
| RUN-26 | test_later_failure_publishes_no_partial_report | 나중 입력 실패 시 부분 보고서 없음 |
| RUN-27 | test_input_existing_output_and_sidecar_protection | 입력·기존 출력·사이드카 보호 |
| RUN-28 | test_missing_input_and_sqlite_destination | 누락 입력·SQLite 목적지 |
| RUN-29 | test_no_target_open_and_changed_input_rejected | 대상 미접근·입력 변경 거부 |
| RUN-30 | test_seeded_string_mutations_preserve_full_raw_values | 시드 기반 문자열 변이 원시 보존 |

## 자체 리뷰와 수정

단일 키 범위·ASCII 슬롯·엄격한 제어 검증·누락/잘못됨/모호함 순서·순위 간격/목록 외 관측·유니코드 경계·원시 출처를 검토했습니다. 접미부 제거 추측 대신 리터럴 접미부와 공백을 유지합니다. 문자열 경계는 임의 바이트 검색이 아닌 정렬 NUL이며 다른 레지스트리 형식을 강제 변환하지 않습니다. 잘못된 유니코드 표시는 바이트 역슬래시 이스케이프이므로 테스트 기준을 해독된 서로게이트 표기 대신 정확한 바이트 이스케이프로 수정했습니다. 원시 바이트가 기준입니다.

출처 순서·반복/혼합 입력·모든 어댑터의 스키마 증가·JSON/SQLite 값과 외래 키·정확한 키 시각과 명령별 시각 부재·예산·입출력 실패 처리를 검토했습니다. 공유 디코더는 변경하지 않았습니다. 자체 리뷰에서 남은 차단 문제는 없으며 실제 호스트 검증은 미완료입니다.

## 독립 비교와 검증 결과

합성 키/값 이름·형식·전체 원시 바이트·물리적 nk/vk 오프셋을 python-registry 1.3.1과 비교하며 셀 헤더와 페이로드의 4바이트 차이를 반영했습니다. 명시적 UTF-16/제어 검사로 저장 명령 접미부와 MRU 순서를 독립 확인했습니다. 체크아웃 밖의 설치된 0.12.0 콘솔에서 JSON/SQLite 스키마 12·반복 출처 해시·외래 키·입력 보존을 확인했습니다. Windows 실행 대화상자 동작이나 실제 획득 NTUSER 데이터를 독립 인증하는 검증은 아닙니다.

EVTX를 포함한 Python 테스트 376개가 모두 통과했습니다. EnScript 정적 회귀 11개·생성 소스 참조 4개·양언어 문서/링크/테스트 매핑·아카이브 검증도 통과했습니다. EnScript 13개와 원본 매니페스트는 기준과 같으며 아카이브 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 정적 무결성 테스트는 EnCase 컴파일/실행을 입증하지 않습니다.

## 남은 검증과 미지원 구조

Windows 버전별 실제 획득 NTUSER RunMRU·Windows/Linux 실행·Python 3.10·독립 실제 레코드 해석·대형 입력 성능·획득 경쟁은 미검증입니다. 다른 범위·미지원 값/제어 형식·비표준 슬롯·잘못되거나 모호한 순서·기존 REGF 제한을 명시합니다. 더티 하이브 재생·삭제/슬랙 복구·대상 실행/확장·소유권/세션/성공 추론·키 시각의 항목 할당·아티팩트 간 결합을 하지 않습니다. 키 마지막 쓰기와 MRU 순위는 명령 실행 시각이 아닙니다. EnCase 컴파일/실행은 여전히 미검증입니다. 정확한 상태 우선순위와 제한은 CLI 문서에 있습니다.
