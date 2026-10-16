# 공통 대화상자 MRU 테스트와 코드 리뷰

[English](DIALOG_MRU_TESTS.md) | **한국어**

2026-10-16 macOS/Python 3.14에서 검증하고 자체 코드 리뷰했습니다. EVTX extra 포함 기존 278개와 신규 대화상자 MRU 36개, 전체 314개가 건너뜀 없이 통과합니다. extra가 없으면 306개 실행, 기존 통합 8개 건너뜀입니다. 이 어댑터 자체는 추가 의존성이 없습니다. [계약과 한계](DIALOG_MRU_CLI.ko.md)를 확인하세요. 외부 리뷰 승인이나 실제 획득 자료 인증은 아닙니다.

## 재현과 합성 자료

독립 합성 REGF 작성기로 루트/확장자/와일드카드 범위, MRU 순서와 숫자 바이너리 값을 만듭니다. 애플리케이션 접두사는 Unicode/이모지와 정확한 종결자를 가진 UTF-16로 직접 작성하고 뒤에 길이 기반 PIDL을 붙입니다. 기존 독립 Shell Item 작성기로 GUID/볼륨/폴더/파일/네트워크/확장과 원시 시각을 구성합니다. 고정 예상 문자열/오프셋/순위로 비교하며 실제 증거/출력은 커밋하지 않습니다. 축소 자원 예산과 결정적 변이는 제한된 오류 검증이며 대형 자료 성능이나 포괄적 퍼징 인증이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 2c6a4203770834c6e197e86b9a1888ea5c4c5d68 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | Test method | 검증 내용 |
| --- | --- | --- |
| DM-01 | test_both_lists_categories_application_and_folder_references | 두 목록/범위/애플리케이션과 폴더 참조 |
| DM-02 | test_open_save_root_is_container_without_fabricated_order | OpenSave 루트 컨테이너에 순서 생성 없음 |
| DM-03 | test_open_save_root_numeric_values_are_preserved | OpenSave 루트 숫자 값 보존 |
| DM-04 | test_last_visited_utf16_prefix_and_pidl_offsets_are_exact | UTF-16 접두사와 정확한 PIDL 오프셋 |
| DM-05 | test_application_literal_not_normalized_or_verified_executable | 앱 표지를 정규화/실행 검증하지 않음 |
| DM-06 | test_invalid_application_unicode_does_not_hide_independent_pidl | 잘못된 앱 Unicode와 독립 PIDL 분리 |
| DM-07 | test_empty_application_label_is_not_attributed | 빈 앱 표지에 귀속 추정 없음 |
| DM-08 | test_unterminated_application_never_searches_for_pidl_signature | 미종결 앱 접두사에서 PIDL 검색 없음 |
| DM-09 | test_unterminated_pidl_keeps_components_but_no_path | 미종결 PIDL은 구성 요소만 보존 |
| DM-10 | test_trailing_pidl_and_empty_lists_retained | 후행 PIDL/빈 목록 원시 보존 |
| DM-11 | test_wrong_value_types_do_not_decode_application_or_pidl | 잘못된 타입은 앱/PIDL 해석 없음 |
| DM-12 | test_malformed_pidl_lengths_strings_and_extensions_keep_raw | PIDL 길이/문자열/확장 손상 보존 |
| DM-13 | test_unknown_item_classes_do_not_create_guessed_paths | 미상 항목으로 경로 추정 없음 |
| DM-14 | test_explicit_absolute_anchor_and_namespace_or_relative_bases | 명시 절대 앵커/기호/상대 근거 |
| DM-15 | test_dot_device_and_separator_components_are_not_resolved | 점/장치/구분자 구성 요소 조합 제외 |
| DM-16 | test_mru_sparse_missing_and_unlisted_ranks_keep_gaps | 희소 MRU/누락/미등재 순위 간격 |
| DM-17 | test_invalid_mru_types_sentinels_duplicates_keep_no_ranks | 잘못된 타입/종결자/중복 제어 무순위 |
| DM-18 | test_missing_legacy_and_ambiguous_controls_never_guess_order | 누락/구형/모호한 제어 무순위 |
| DM-19 | test_canonical_names_unknown_metadata_and_raw_offsets | 정규 이름/미상 메타데이터/원시 위치 |
| DM-20 | test_missing_branches_and_valid_empty_key_are_distinct | 분기 부재와 유효 빈 키 구분 |
| DM-21 | test_nested_scopes_diagnosed_not_silently_traversed | 중첩 범위를 진단하고 탐색하지 않음 |
| DM-22 | test_duplicate_paths_across_categories_and_apps_remain_independent | 범위/앱 간 중복 경로 독립 보존 |
| DM-23 | test_key_filetimes_and_item_fat_times_are_not_entry_open_times | 키/FAT 시각을 열람 시각으로 추정하지 않음 |
| DM-24 | test_ansi_codepage_and_unicode_application_are_separate | ANSI 코드페이지와 Unicode 앱 분리 |
| DM-25 | test_invalid_codepage_is_fatal | 잘못된 코드페이지 치명적 오류 |
| DM-26 | test_item_diagnostics_are_adapter_scoped_and_value_identified | 어댑터/숫자 값 범위 진단 ID |
| DM-27 | test_key_entry_application_path_output_budgets_are_fatal | 키/항목/앱/경로/출력 예산 |
| DM-28 | test_shell_item_resource_limits_are_not_downgraded | Shell Item 자원 초과는 치명적 오류 |
| DM-29 | test_regf_versions_indexes_case_and_dirty_inputs | REGF 버전/인덱스/대소문자/dirty 거부 |
| DM-30 | test_cli_repeated_hives_source_hash_and_schema | 실제 CLI 반복 하이브/해시/스키마 |
| DM-31 | test_json_sqlite_schema_raw_unicode_and_foreign_keys | JSON/SQLite 원시/Unicode/외래 키 |
| DM-32 | test_cli_codepage_option_and_sqlite | 실제 CLI 코드페이지와 SQLite |
| DM-33 | test_mixed_adapters_keep_source_order_and_no_automatic_joins | 혼합 어댑터 출처 순서와 자동 조인 없음 |
| DM-34 | test_cli_strict_later_failure_atomic_and_evidence_protection | 엄격/후속 실패 원자성/증거 보호 |
| DM-35 | test_only_supplied_hive_opened_and_changes_rejected | 명시 하이브만 읽고 변경 감지 |
| DM-36 | test_mutated_hives_have_controlled_failures | 변이 하이브의 통제된 오류 |

## 자체 코드 리뷰와 보완

키 범위/열거, 루트 컨테이너와 실제 목록 구분, MRU 제어 검증, 앱 접두사/PIDL 논리 위치, 공유 디코더의 부분 지원과 자원 제한, 원시 출처 및 출력 외래 키를 검토했습니다. ShellBags의 선택적 항목 종결과 구분하여 PIDL 경로에는 0 종결자를 요구합니다. 잘못된 앱 텍스트를 실행 파일 정체성으로 취급하지 않고 독립 경계의 PIDL은 별도 보존합니다. 접두사가 미종결이면 시그니처를 검색하거나 읽을 만한 문자열로 경로를 추측하지 않습니다.

OpenSave 루트에 제어/숫자가 없으면 정상 컨테이너로 남겨 순서 부재를 허위 경고하지 않습니다. 순위 간격과 중복 관찰을 유지하고 OpenSave와 LastVisited를 임의 연결하지 않습니다. 공유 판독기 진단 코드를 어댑터 범위로 바꾸고 숫자 값 ID를 유지하며 자원 초과를 손상 관찰로 낮추지 않습니다. 기존 디코더 동작을 변경하지 않고 전체 어댑터의 스키마 10 회귀를 검증합니다.

## 독립 대조와 검증 결과

python-registry 1.3.1로 합성 키/값 이름, 타입, 전체 원시 바이트와 nk/vk 오프셋을 독립 대조했습니다. 비교기 페이로드 위치와 셀 헤더 사이 4바이트 차이를 명시적으로 확인했습니다. 전체 PIDL 의미나 실제 하이브를 독립 인증한 것은 아닙니다. 설치된 0.10.0 콘솔을 저장소 밖에서 JSON/SQLite로 실행해 스키마 10, 반복 출처 해시, 부모 외래 키와 원본 불변을 확인했습니다.

EnScript 정적 회귀 11개, 생성 소스 참조 4개, 문서/언어/테스트 매핑과 아카이브 검증도 실행했습니다. EnScript 13개와 매니페스트는 기준과 같으며 아카이브 원래 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 이 검사는 EnCase 실행 검증이 아닙니다.

## 남은 검증과 미지원 구조

실제 Windows/앱 버전별 NTUSER 대화상자 MRU, Windows/Linux 실행, Python 3.10, 독립 실제 PIDL 의미 대조, 대규모 성능과 획득 경합은 미검증입니다. 기존/다른 대화상자 키, 깊은 범위, 미지원 Shell Item/확장/네임스페이스와 네이티브 REGF 미지원 구조는 제외합니다. 로그 재생, 삭제/slack 카빙, 시그니처/문자열 휴리스틱 복구나 자동 사용자/아티팩트 조인은 없습니다. 키 수정/MRU/항목 FAT 시각은 성공한 파일 열기/저장이나 실행을 증명하지 않습니다. EnCase 컴파일/실행은 계속 미검증이며 원본과 아카이브를 보존합니다.
