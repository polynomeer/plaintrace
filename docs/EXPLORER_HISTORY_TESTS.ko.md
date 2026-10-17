# 탐색기 이력 테스트와 코드 리뷰

[English](EXPLORER_HISTORY_TESTS.md) | **한국어**

2026-10-17에 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX 추가 의존성을 포함한 Python 테스트 407개가 생략 없이 통과했으며 기존 376개와 탐색기 이력 31개입니다. 추가 의존성이 없으면 399개가 실행되고 기존 EVTX 통합 8개가 생략되므로 완전한 EVTX 검증이 아닙니다. 두 어댑터 자체는 추가 런타임 의존성이 없습니다. [계약과 제한](EXPLORER_HISTORY_CLI.ko.md)을 참고하세요. 자체 리뷰이며 외부 승인이나 획득 증거 인증이 아닙니다.

## 재현과 합성 픽스처

기존 독립 합성 REGF 작성기가 두 루트와 명시적 REG_SZ/REG_BINARY UTF-16 페이로드를 만듭니다. 고정 숫자 슬롯·MRUListEx 순위/간격·유니코드/이모지·원시 셀 오프셋·정확한 FILETIME이 운영 디코더와 독립적인 기준입니다. 명령/검색어는 리터럴 공백·연산자·토큰·URL·접미부를 포함합니다. 획득 형식의 임시 합성 하이브와 출력은 삭제하고 실제 증거는 커밋하지 않습니다. 패치한 예산과 시드 변이는 통제된 검사이며 대형 입력 성능 시험이나 전면 퍼징이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code e94cee173fffdcfdd9b960c29c0e9f81a1067236 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| EH-01 | test_typed_unicode_slots_not_mru_ranks | TypedPaths 유니코드 슬롯과 순위 부재 |
| EH-02 | test_wordwheel_binary_unicode_and_order | WordWheelQuery 이진 유니코드와 순서 |
| EH-03 | test_literals_duplicates_and_no_path_or_query_normalization | 리터럴·중복·경로/검색어 무변환 |
| EH-04 | test_wordwheel_missing_refs_keep_rank_gaps | 누락 참조 순위 간격 |
| EH-05 | test_wordwheel_unlisted_entries_keep_null_rank | 목록 외 항목 null 순위 |
| EH-06 | test_missing_control_no_size_or_slot_rank_guess | 제어 누락 시 슬롯/크기 순위 추측 금지 |
| EH-07 | test_invalid_mrulistex_type_alignment_sentinel_duplicates | MRUListEx 형식·정렬·센티널·중복 오류 |
| EH-08 | test_legacy_and_ambiguous_controls_not_selected | 과거/모호한 제어 선택 금지 |
| EH-09 | test_valid_empty_mru_differs_from_missing | 유효한 빈 MRU와 누락 구분 |
| EH-10 | test_typed_unexpected_controls_never_add_ranks | TypedPaths 예상 밖 제어에 순위 없음 |
| EH-11 | test_noncanonical_names_preserved_as_metadata | 비표준 이름 원시 메타데이터 |
| EH-12 | test_zero_and_maximum_slots_and_case_insensitive_names | 0/최대 슬롯과 대소문자 |
| EH-13 | test_artifact_specific_registry_types_no_coercion | 아티팩트별 형식 강제 변환 금지 |
| EH-14 | test_unterminated_and_odd_text_kept_raw | 미종결·홀수 문자열 원시 보존 |
| EH-15 | test_invalid_utf16_is_byte_escaped | 잘못된 UTF-16 바이트 이스케이프 |
| EH-16 | test_aligned_terminator_tails_padding_and_status_precedence | 정렬 종결자·꼬리·패딩·상태 우선순위 |
| EH-17 | test_empty_strings_retained_with_diagnostic | 빈 문자열 경고·보존 |
| EH-18 | test_key_time_raw_offsets_and_entry_lineage | 키 시각·원시 오프셋·항목 연결 |
| EH-19 | test_absent_empty_roots_and_descendants | 루트 누락·빈 키·하위 키 |
| EH-20 | test_unknown_artifact_rejected | 미상 아티팩트 거부 |
| EH-21 | test_regf_versions_indexes_and_duplicate_names | REGF 버전·인덱스·중복 이름 |
| EH-22 | test_dirty_and_corrupt_regf_rejected | 더티·손상 REGF 거부 |
| EH-23 | test_entry_string_and_output_limits | 항목·문자열·출력 제한 |
| EH-24 | test_json_sqlite_schema_raw_values_and_foreign_keys | JSON·SQLite·원시 값·외래 키 |
| EH-25 | test_repeated_mixed_sources_hashes_and_input_preservation | 반복/혼합 출처·해시·입력 보존 |
| EH-26 | test_cli_flags_source_groups_json_and_sqlite | CLI 플래그·출처 그룹·JSON·SQLite |
| EH-27 | test_strict_warning_and_later_failure_atomic_publication | 엄격 모드·나중 실패·전체 단위 게시 |
| EH-28 | test_input_existing_output_and_sidecar_protection | 입력·기존 출력·사이드카 보호 |
| EH-29 | test_missing_input_and_sqlite_destination | 누락 입력·SQLite 목적지 |
| EH-30 | test_no_stored_target_open_and_changed_input_rejected | 저장 대상 미접근·입력 변경 거부 |
| EH-31 | test_seeded_payload_mutations_keep_raw_values | 시드 기반 페이로드 변이 원시 보존 |

## 자체 리뷰

아티팩트별 레지스트리 형식/범위·표준 슬롯·TypedPaths 레이블과 WordWheelQuery MRU 순위의 구분·엄격한 센티널/중복 처리·누락 참조·목록 외 값을 검토했습니다. TypedPaths는 슬롯이나 예상 밖 제어에서 순위를 만들지 않고 WordWheelQuery 순서는 텍스트 유효성과 별개입니다. 레이블은 선행 0 없는 제한된 부호 없는 십진수이며 미상 이름은 원시 메타데이터로 남깁니다. 열거 순서와 중복 관측은 정렬/중복 제거 없이 유지합니다.

정렬 UTF-16 경계·잘못된 텍스트/꼬리 상태 우선순위·리터럴 보존·정확한 키 시각과 항목별 시각 부재·바이트/항목/출력 제한·nk/vk 원시 출처·혼합/반복 출처 그룹·스키마 13·외래 키·배타적 전체 단위 출력을 검토했습니다. 기존 디코더는 변경하지 않았고 자체 리뷰에 남은 차단 문제는 없으며 실제 호스트/획득 데이터 검증은 미완료입니다.

## 독립 비교와 결과

두 합성 범위의 키/값 이름·형식·전체 원시 바이트·물리적 nk/vk 오프셋을 python-registry 1.3.1과 비교하고 셀 헤더와 페이로드의 4바이트 차이를 반영했습니다. 명시적 UTF-16/DWORD 배열 검사로 리터럴 텍스트·슬롯 레이블·MRU 순서를 독립 확인했습니다. 체크아웃 밖에 설치한 0.13.0 콘솔에서 두 플래그·반복 출처·스키마 13 JSON/SQLite·출처 해시·외래 키·입력 보존을 검증했습니다. Windows 탐색/검색 의미나 실제 획득 NTUSER 데이터를 인증하는 검증은 아닙니다.

EVTX를 포함한 테스트 407개가 통과했습니다. EnScript 정적 회귀 11개·소스 참조 문서 4개·양언어 문서/링크/테스트 매핑·아카이브 검증도 통과했습니다. EnScript 13개와 원본 매니페스트는 기준과 같으며 원본 아카이브 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 정적 검사는 EnCase 컴파일/실행을 입증하지 않습니다.

## 남은 검증과 미지원 구조

Windows 버전별 실제 획득 NTUSER TypedPaths/WordWheelQuery·Windows/Linux 실행·Python 3.10·독립 실제 레코드 의미·대형 입력 성능·획득 경쟁은 미검증입니다. 다른 범위/입력 이력·미지원 레지스트리/제어 형식·비표준 이름·모호하거나 잘못된 순서·네이티브 REGF 제한을 명시합니다. 더티 하이브 재생·삭제/슬랙 복구·대상 접근/실행·사용자/세션 귀속·항목별 키 시각·탐색/검색 성공 추론·아티팩트 결합을 하지 않습니다. EnCase 컴파일/실행은 여전히 미검증이며 정확한 제한과 상태 우선순위는 CLI 문서에 있습니다.
