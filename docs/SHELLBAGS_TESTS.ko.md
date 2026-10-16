# ShellBags 테스트와 코드 리뷰

[English](SHELLBAGS_TESTS.md) | **한국어**

2026-10-15 macOS/Python 3.14에서 검증하고 자체 코드 리뷰했습니다. EVTX extra 포함 기존 236개와 신규 ShellBags 42개, 전체 278개가 건너뜀 없이 통과합니다. extra가 없으면 270개 실행, 기존 통합 8개 건너뜀입니다. ShellBags 자체는 추가 의존성이 없습니다. [계약과 한계](SHELLBAGS_CLI.ko.md)를 확인하세요. 외부 리뷰 승인이나 실제 획득 자료 인증은 아닙니다.

## 재현과 합성 자료

임시 디렉터리에 독립 합성 REGF 생성기로 NTUSER/UsrClass 경로, 희소 MRU, NodeSlot과 보기 트리를 작성합니다. Shell Item 작성기는 GUID, 드라이브, 네트워크, 파일/폴더, 버전별 확장과 알려진 FAT 시각을 구성합니다. 예상 이름/계층/시각은 고정값으로 검증하며 어댑터로 계산하지 않습니다. 잘못된 포인터/이름/길이와 축소 자원 예산을 확인합니다. 결정적 변이는 제한된 통제 오류 표본이며 포괄적 퍼징이 아닙니다. 실제 증거나 생성 출력을 커밋하지 않습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 9bc15c8f765ea2c10d2259049a39222375f5d61c -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | Test method | 검증 내용 |
| --- | --- | --- |
| SB-01 | test_hierarchy_guid_volume_long_names_and_same_hive_views | 계층/GUID/볼륨/긴 이름과 같은 하이브 보기 |
| SB-02 | test_ntuser_and_usrclass_root_layouts_are_role_explicit | 명시 역할별 NTUSER/UsrClass 루트 |
| SB-03 | test_mru_sparse_order_is_rank_not_timestamp | 희소 MRU 순위와 별도 키 시각 |
| SB-04 | test_invalid_ambiguous_and_missing_mru_keep_raw_no_ranks | 잘못된/모호한/누락 MRU의 원시 보존 |
| SB-05 | test_unlisted_and_noncanonical_values_are_not_dropped | 미등재/비정규 값 보존 |
| SB-06 | test_valid_empty_mru_and_absent_roots | 유효 빈 순서와 루트 부재 |
| SB-07 | test_node_slot_type_missing_bag_and_raw_controls | NodeSlot 타입/누락 Bags/원시 제어 |
| SB-08 | test_node_slot_belongs_to_key_not_child_value | NodeSlot은 현재 키에 귀속 |
| SB-09 | test_missing_parent_value_propagates_unresolved_ancestry | 부모 값 누락 시 미해결 조상 전파 |
| SB-10 | test_unknown_ancestor_is_not_guessed_and_explicit_volume_can_anchor | 미상 조상과 명시 볼륨 앵커 |
| SB-11 | test_noncanonical_child_is_diagnosed_and_not_traversed | 비정규 자식 진단 후 제외 |
| SB-12 | test_duplicate_paths_and_separate_roots_are_preserved | 중복 경로/루트 보존 |
| SB-13 | test_file_entry_extension_versions_and_exact_fat_bytes | 확장 버전과 정확한 FAT 바이트 |
| SB-14 | test_unknown_extension_version_retains_primary_without_guess | 미상 확장은 기본 이름만 사용 |
| SB-15 | test_malformed_extension_offsets_sizes_and_backlinks_keep_whole_raw | 확장 오프셋/크기/역참조 원시 보존 |
| SB-16 | test_ansi_codepage_and_unicode_names | ANSI 코드페이지와 Unicode 이름 |
| SB-17 | test_invalid_unicode_does_not_become_path | 잘못된 Unicode는 경로로 사용하지 않음 |
| SB-18 | test_network_unc_and_folder_hierarchy_literal | UNC와 폴더의 원문 계층 |
| SB-19 | test_unsupported_volume_network_and_namespace_variants_stay_opaque | 미지원 볼륨/네트워크/네임스페이스 변형 |
| SB-20 | test_root_guid_not_mapped_and_opaque_tail_retained | GUID 매핑 없이 원문/후행 보존 |
| SB-21 | test_dot_and_separator_names_not_composed_or_normalized | 점/구분자 이름 조합 제외 |
| SB-22 | test_item_list_multiple_components_and_optional_terminal | 다중 항목과 선택적 종결자 |
| SB-23 | test_trailing_bytes_empty_and_wrong_type_keep_raw | 후행/빈/잘못된 타입의 원시 보존 |
| SB-24 | test_malformed_list_bounds_and_strings_are_observations | 잘못된 경계/문자열은 관찰로 남음 |
| SB-25 | test_zero_invalid_fat_times_keep_raw_no_epoch_guess | 0/잘못된 FAT 시각의 원시 보존 |
| SB-26 | test_item_and_extension_budgets_are_fatal_not_malformed_rows | 항목/확장 자원 예산은 치명적 오류 |
| SB-27 | test_key_view_entry_output_and_path_budgets | 키/보기/항목/출력/경로 예산 |
| SB-28 | test_hierarchy_and_view_depth_are_bounded | 계층과 보기 깊이 제한 |
| SB-29 | test_regf_versions_indexes_case_paths_and_dirty_hives | REGF 버전/인덱스와 dirty 거부 |
| SB-30 | test_role_and_encoding_validation_are_fatal | 역할/인코딩 검증 |
| SB-31 | test_cli_repeated_roles_hashes_and_schema | 실제 CLI 역할/해시/스키마 |
| SB-32 | test_json_sqlite_raw_roundtrip_and_composite_relationships | JSON/SQLite 원시 왕복과 복합 관계 |
| SB-33 | test_deferred_orphan_parent_fails_without_publishing_output | 지연 참조 오류 시 출력 게시 없음 |
| SB-34 | test_mixed_adapters_do_not_join_users_or_duplicate_sources | 혼합 어댑터의 사용자 자동 조인 없음 |
| SB-35 | test_cli_strict_fatal_atomic_and_evidence_protection | 엄격/치명적 오류/원자적 출력/증거 보호 |
| SB-36 | test_only_supplied_hive_opened_and_changing_read_rejected | 명시 하이브만 읽고 변경 감지 |
| SB-37 | test_deterministic_mutations_raise_only_controlled_errors | 결정적 변이의 통제된 오류 |
| SB-38 | test_view_metadata_offsets_raw_values_and_slot_reuse | 보기 메타데이터 오프셋/원시/슬롯 재사용 |
| SB-39 | test_mru_sentinel_missing_embedded_and_trailing_are_invalid | MRU 종결자 누락/중간/후행은 무효 |
| SB-40 | test_invalid_long_name_falls_back_to_explicit_primary | 잘못된 긴 이름은 유효 기본 이름으로 대체 |
| SB-41 | test_cli_shellbag_codepage_option_and_sqlite | 실제 CLI 코드페이지와 SQLite |
| SB-42 | test_network_description_comments_and_non_unc_remain_literal | 네트워크 설명/주석/비UNC 원문 |

## 자체 리뷰와 보완

계층과 값의 관계, NodeSlot의 귀속, 지원 형식/미상 변형, 문자열과 확장 경계, 자원 제한, 상대/네임스페이스/절대 후보와 시각 의미를 검토했습니다. 부모 값이 없는 하위 키도 탐색하지만 조상을 만들어내지 않습니다. 장치 네임스페이스를 서버/공유 UNC 앵커로 오인하지 않도록 보완했습니다. 파일 이름의 점/구분자를 정규화해 실제 경로처럼 만들지 않으며 미지원 Shell Item은 바이트로 보존합니다. 잘못된 문자열은 표시만 이스케이프하고 경로 조합에서 제외하며 유효한 기본 이름 대체는 별도로 검증합니다. 자원 제한과 손상 관찰을 별도 예외로 구분했습니다.

SQLite의 키-항목 상호 참조를 위해 모든 테이블을 먼저 만들고 부모 항목 제약을 커밋까지 지연합니다. 누락 부모/보기/자식 관계는 실패하며 부분 파일을 게시하지 않습니다. MRU 순위가 파일 시각이나 키 수정으로 바뀌지 않고 NodeSlot이 자식 값에 복사되지 않는지 검증했습니다. 전체 기존 어댑터 회귀도 스키마 9로 실행했습니다.

## 독립 대조와 검증 결과

python-registry 1.3.1로 합성 하이브 키/값의 이름, 타입, 원시 바이트와 nk/vk 위치를 독립 대조했습니다. 비교기의 레코드 오프셋은 셀 페이로드 위치이므로 4바이트 셀 헤더 차이를 명시적으로 검증했습니다. Shell Item 의미 전체를 독립 인증한 것은 아니며 실제 획득 하이브 대조도 아닙니다. 설치된 0.9.0 콘솔을 저장소 밖에서 두 역할의 JSON/SQLite로 실행해 스키마 9, 출처 해시, 관계 무결성과 입력 불변을 확인했습니다.

EnScript 정적 회귀 11개, 생성 소스 참조 4개, 문서/언어/테스트 매핑과 아카이브 무결성도 확인했습니다. EnScript 13개와 기존 매니페스트는 기준과 동일하며 아카이브의 원래 트리/README와 재구성 2017년 커밋 263개를 보존합니다. 이러한 검사는 EnCase 실행 검증이 아닙니다.

## 남은 검증과 미지원 구조

실제 NTUSER/UsrClass ShellBags, Windows/앱 버전별 획득 자료, Windows/Linux 실행, Python 3.10, 독립 실제 Shell Item 의미 대조, 대규모 성능과 획득 경합은 미검증입니다. Dirty 하이브/로그 재생, REGF 1.6/big data/volatile/link/삭제/slack, 미참조 Bags, 구형 MRUList 순위, 미지원 Shell Item/확장/속성/네임스페이스는 제외합니다. FAT 시각에 시간대를 부여하지 않으며 키 수정/MRU/NodeSlot으로 폴더 보기, 접근, 실행이나 사용자 소유권을 증명하지 않습니다. EnCase 컴파일/실행은 계속 미검증이고 원본/아카이브는 보존합니다.
