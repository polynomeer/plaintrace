# Jump Lists 테스트와 코드 리뷰

[English](JUMP_LISTS_TESTS.md) | **한국어**

2026-10-15 macOS/Python 3.14에서 검증하고 자체 코드 리뷰했습니다. EVTX extra 포함 기존 200개와 신규 Jump Lists 36개, 전체 236개가 건너뜀 없이 통과합니다. extra가 없으면 228개를 실행하고 기존 통합 8개를 건너뜁니다. Jump Lists는 추가 의존성이 없습니다. [계약과 한계](JUMP_LISTS_CLI.ko.md)를 확인하세요. 외부 리뷰 승인이나 획득 증거 인증은 아닙니다.

## 재현과 합성 자료

독립 합성 생성기로 CFB v3/v4, 일반/미니/단편화 체인, 확장 DIFAT, DestList와 사용자 지정 범주를 임시 디렉터리에 작성합니다. 원시 GUID, FILETIME, 경로와 물리 블록 시작을 검증합니다. 잘못된 체인/포인터/레코드는 명시적으로 변조하며 결정적 변이 검사는 통제된 오류만 확인하는 제한적 표본으로 포괄적 퍼징이 아닙니다. 실제 증거, 공개 샘플이나 생성 출력은 커밋하지 않습니다. 축소 예산 테스트는 대용량 성능 인증이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 285f7f5020213042372e4d791fd001626a04231e -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | Test method | 검증 내용 |
| --- | --- | --- |
| JL-01 | test_automatic_v1_raw_time_guid_and_link_association | 자동 v1 원시 시각/GUID와 링크 연결 |
| JL-02 | test_v3_v4_extensions_and_pinned_state | v3/v4 불투명 확장과 고정 상태 |
| JL-03 | test_destlist_version_two_and_future_rejected | DestList 2/향후 버전 거부 |
| JL-04 | test_mini_and_regular_streams_cfb_v3_v4_fragmented | CFB v3/v4 일반/미니 스트림과 단편화 |
| JL-05 | test_ministream_many_mini_sectors_and_physical_offsets | 여러 미니 섹터와 물리 시작 오프셋 |
| JL-06 | test_missing_empty_destlist_and_unassociated_links | 누락/빈 DestList와 미연결 링크 |
| JL-07 | test_missing_links_and_orphans_are_not_discarded | 누락 링크와 잔여 스트림 보존 |
| JL-08 | test_duplicate_ids_ambiguous_no_silent_join | 중복 ID는 모호하며 연결 추정 없음 |
| JL-09 | test_numbered_stream_case_and_unknown_metadata_retained | 대문자 번호 스트림과 미상 메타데이터 |
| JL-10 | test_declared_count_trailing_bytes_retained_not_carved | 미선언 바이트 보존 및 카빙 제외 |
| JL-11 | test_invalid_utf16_nul_and_unknown_pin_retained | 잘못된 UTF-16/NUL/음수 고정 보존 |
| JL-12 | test_zero_overflow_and_pinned_count_diagnostic | 0/범위 초과 시각과 고정 개수 불일치 |
| JL-13 | test_invalid_embedded_lnk_raw_retained | 잘못된 내장 LNK의 원시 바이트 |
| JL-14 | test_lnk_diagnostics_use_unique_entry_identity | LNK 진단의 고유 항목 ID |
| JL-15 | test_cfb_fat_cycle_overlap_and_truncation_rejected | FAT 순환/겹침/잘림 거부 |
| JL-16 | test_cfb_minifat_cycle_and_duplicate_ownership_rejected | miniFAT 순환과 중복 소유권 거부 |
| JL-17 | test_cfb_directory_cycle_nested_unreachable_and_duplicate_names | 디렉터리 순환/중첩/미도달/이름 중복 |
| JL-18 | test_cfb_header_counts_format_and_stream_size_limits | 헤더 개수/형식/스트림 제한 |
| JL-19 | test_cfb_extended_difat_and_large_regular_stream | 확장 DIFAT와 대형 일반 스트림 |
| JL-20 | test_destlist_truncated_path_and_extension_are_fatal | DestList 경로/확장 잘림 거부 |
| JL-21 | test_custom_named_tasks_known_categories_and_full_lnk | 이름/작업/알려진 범주와 전체 LNK |
| JL-22 | test_custom_clsid_body_preserves_original_and_normalized_lnk | CLSID-body 원본과 정규화 링크 구분 |
| JL-23 | test_custom_does_not_split_embedded_signatures | 내부 footer 시그니처로 분할하지 않음 |
| JL-24 | test_custom_lnk_sections_codepage_and_extra_blocks | LNK 구간/코드페이지/추가 블록 |
| JL-25 | test_custom_empty_file_and_empty_category | 빈 사용자 지정 파일과 범주 |
| JL-26 | test_custom_unsupported_version_category_footer_trailing_rejected | 미지원 버전/범주/footer/후행 거부 |
| JL-27 | test_custom_declared_count_and_lnk_length_are_bounded | 선언 개수와 LNK 길이 경계 |
| JL-28 | test_input_entry_category_path_link_output_budgets | 입력/항목/범주/경로/링크/출력 예산 |
| JL-29 | test_cli_repeated_inputs_renamed_detection_hash_and_app_hint | 실제 CLI 반복 입력/이름 변경/해시/힌트 |
| JL-30 | test_json_sqlite_schema_lineage_raw_roundtrip | JSON/SQLite 스키마/외래 키/원시 왕복 |
| JL-31 | test_mixed_inputs_preserve_previous_ids_and_no_link_duplication | 혼합 출처와 독립 LNK 중복 없음 |
| JL-32 | test_cli_strict_fatal_atomic_and_output_protection | 엄격/치명적 오류와 원자적 출력 보호 |
| JL-33 | test_only_supplied_input_opened_and_changing_read_rejected | 명시 입력만 읽고 변경 감지 |
| JL-34 | test_invalid_codepage_is_fatal_not_a_bad_link | 잘못된 코드페이지는 치명적 설정 오류 |
| JL-35 | test_mutated_containers_fail_with_controlled_errors | 결정적 변이 입력의 통제된 실패 |
| JL-36 | test_cfb_surplus_difat_rejected_before_table_expansion | 섹터 읽기/테이블 확장 전 과도한 DIFAT 개수 거부 |

## 독립 대조와 공개 자료

olefile 0.47로 합성 CFB v3/v4/단편화/DIFAT 스트림 바이트를 독립 대조했습니다. 설치된 0.8.0 콘솔을 저장소 밖에서 JSON/SQLite 형식으로 실행하여 스키마 8, 출처 해시, 부모 외래 키와 입력 불변을 확인했습니다. olefile은 비교 전용이며 런타임/테스트 의존성이 아닙니다.

원저자 저장소의 공개 자동 목록 두 개도 임시 공간에서만 읽었습니다. Windows 7 표본은 DestList 1/링크 4개, Windows 10 표본은 DestList 3/링크 9개가 해석됐으며 활성 스트림 바이트는 모두 olefile과 일치했습니다. 경고는 기록됐고, PIDL/불투명 추가 블록을 완전 해석했다고 주장하지 않습니다. 표본 이름은 배포자가 붙인 환경 표지이며 로컬에서 해당 OS를 실행한 것은 아닙니다.

| Upstream sample | SHA-256 |
| --- | --- |
| [Win7/1b4dd67f29cb1962](https://github.com/EricZimmerman/JumpList/blob/master/JumpList.Test/TestFiles/Win7/1b4dd67f29cb1962.automaticDestinations-ms) | efb95b8477f4ed4968fb16c724845a52bcfc0ab671f4769a33ca05a25eef5379 |
| [Win10/f01b4d95cf55d32a](https://github.com/EricZimmerman/JumpList/blob/master/JumpList.Test/TestFiles/Win10/f01b4d95cf55d32a.automaticDestinations-ms) | a724713d2ff51d32e3f028c57ab906339f882de0c93dc9903f0f8b241c53fd56 |

## 자체 코드 리뷰와 수정

CFB 할당/순환/별칭, 디렉터리 탐색, 미니 스트림의 논리-물리 매핑, DestList 경계, 중복/누락 ID, 사용자 지정 프레임과 출력 외래 키를 검토했습니다. DestList 출처와 연결 LNK 스트림을 별도 필드로 분리했고, 잘못된 코드페이지는 손상 링크로 삼키지 않고 치명적 설정 오류로 처리합니다. CLSID-body 합성 HeaderSize와 원본 바이트를 구분하고, 텍스트/LNK 진단에는 항목/범주 ID를 연결했습니다. 최종 리뷰에서 섹터 읽기/테이블 확장 전에 선언 FAT 용량으로 DIFAT 개수를 제한하도록 보완했습니다(JL-36). 할당 테이블 확장 크기를 제한하고 CLSID-body 프레임에서 잔여 버퍼 반복 복사를 피했습니다. 시그니처로 항목을 쪼개거나 중복 번호를 임의 연결하지 않습니다.

전체 회귀, EnScript 정적 회귀 11개, 소스 참조 4개와 문서/언어/테스트 매핑을 확인했습니다. 아카이브 검증으로 소스 13개, 원래 트리/README와 2017년 재구성 커밋 263개를 확인했으며 기준 이후 EnScript/매니페스트 변경은 없습니다. 이 검사는 EnCase 실행 검증이 아닙니다.

## 남은 검증과 미지원 구조

사용자 획득 Jump Lists, 공개/실제 CustomDestinations, 다양한 Windows/앱 버전, Windows/Linux 실행, Python 3.10, 실제 자료의 광범위한 독립 해석 대조, 대규모 성능과 획득 경합은 미검증입니다. 공개 자동 샘플 두 개는 이 범위를 대체하지 않습니다. 중첩/미도달 활성 CFB 구조, DestList 2/향후 버전, 속성 확장 해석, LNK 외 객체, 비정규 사용자 지정 개수/봉투, 삭제/slack 카빙과 ProgramsCache는 미지원입니다. CFB 적흑 트리/비활성 할당 의미나 DestList 체크섬을 인증하지 않습니다. 기존 LNK 한계를 유지하고 실행/열람/사용자 귀속을 추정하지 않습니다. EnCase 컴파일/실행은 계속 미검증이며 원본과 아카이브를 보존합니다.
