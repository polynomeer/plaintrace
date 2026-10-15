# RecentDocs 테스트와 코드 리뷰

**한국어** | [English](RECENT_DOCS_TESTS.md)

2026-10-15 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX extra가 있으면 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개, USB 레지스트리 25개, RecentDocs 27개로 Python 175개가 건너뛰기 없이 통과합니다. 없으면 167개를 실행하고 기존 통합 8개를 건너뜁니다. RecentDocs 자체에는 추가 의존성이 없습니다. [어댑터 계약](RECENT_DOCS_CLI.ko.md)을 확인하세요. 외부 리뷰어 승인이나 획득 파일 인증이 아닙니다.

## 재현과 픽스처

합성 REGF 하이브에 루트/확장자/Folder 범위, 알려진 원시 제어 바이트, 희소 ID, 그대로의 Unicode 이름과 미해석 후미 바이트를 임시 디렉터리에 만듭니다. 어댑터로 계산하지 않은 독립 순서/문자열/FILETIME 틱을 오라클로 사용합니다. 획득 증거나 출력을 커밋하지 않습니다. 네이티브 리더, 실제 CLI 프로세스와 두 출력기를 실행하며 상한은 작은 예산 패치로 확인하고 대형 프로필 성능을 주장하지 않습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 0f3e9e4fec930332310c172df6b1e599249c8924 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 검사

| ID | 테스트 메서드 | 오라클 / 동작 |
| --- | --- | --- |
| RD-01 | test_modern_sparse_order_unicode_and_key_time | 희소 MRU 순위, 보조 평면 Unicode와 별도 키 수정 시각 |
| RD-02 | test_scopes_folder_and_duplicates_are_not_deduplicated | 루트/확장자/Folder 범위의 중복 문서 관찰 보존 |
| RD-03 | test_legacy_mrulist_letters_and_regsz | 구형 문자 순서와 REG_SZ 항목 |
| RD-04 | test_both_controls_are_ambiguous_no_ranks | 두 제어 값 보존, 모호 상태와 null 순위 |
| RD-05 | test_missing_control_and_empty_key_preserved | 누락 순서와 빈 키 메타데이터 보존 |
| RD-06 | test_valid_empty_control_is_not_missing | 정상 빈 순서와 누락 제어 값 구분 |
| RD-07 | test_invalid_modern_sentinel_length_type_and_duplicates | 잘못된 DWORD 길이/타입/종료자/중복은 전체 순위 무효 |
| RD-08 | test_invalid_legacy_mru_keeps_raw | 구형 ASCII 오류/Unicode 유사 문자/타입/종료 오류 원시 보존 |
| RD-09 | test_missing_and_unlisted_entries_keep_rank_gaps | 누락 참조 순위 간격과 목록 밖 값 유지 |
| RD-10 | test_noncanonical_numeric_and_unknown_values_are_key_metadata | 미지/비표준 이름을 키 메타데이터로 보존 |
| RD-11 | test_opaque_shell_tail_and_literal_names_are_preserved | 그대로의 이름과 미해석 Shell Item 후미 바이트 보존 |
| RD-12 | test_missing_terminator_wrong_type_and_empty_name_retained | 타입 오류/NUL 누락/빈 이름에서도 원시 레코드 보존 |
| RD-13 | test_unpaired_surrogate_and_aligned_nul | 잘못된 surrogate 이스케이프 진단과 정렬 NUL 해독 |
| RD-14 | test_nested_scopes_are_diagnosed_not_traversed | 더 깊은 범위는 경고와 제외 |
| RD-15 | test_missing_branch_and_wrong_hive_do_not_invent_documents | RecentDocs 누락을 명시적 빈 결과로 처리 |
| RD-16 | test_regf_versions_indexes_and_case_insensitive_path | 네이티브 REGF 버전/인덱스와 대소문자 무관 경로 |
| RD-17 | test_key_document_and_output_budgets | 키/문서/출력과 기존 값 바이트 예산 |
| RD-18 | test_dirty_corrupt_truncated_hives_fail | dirty/손상/절단 하이브 실패 |
| RD-19 | test_repeated_renamed_sources_hashes_and_offsets | 이름 변경/반복 출처 해시와 물리 nk/vk 출처 |
| RD-20 | test_json_sqlite_current_schema_and_raw_metadata_roundtrip | JSON/SQLite 현재 스키마, 원시 MRU 객체와 Unicode 왕복 |
| RD-21 | test_cli_real_subprocess_strict_and_sqlite | 실제 CLI 프로세스, SQLite 출력과 strict 경고 |
| RD-22 | test_later_failure_atomic_and_outputs_protected | 후속 실패 시 게시 없음과 기존 증거/출력 보호 |
| RD-23 | test_only_acquired_hive_opened_and_changing_input_rejected | 획득 하이브만 열며 변경 입력 거부 |
| RD-24 | test_mixed_browser_usb_recycle_and_recent_lineage | 브라우저/USB/휴지통과 RecentDocs 출처 순서 |
| RD-25 | test_review_mru_mutations_do_not_escape_contract | 고정 시드 MRU 변형 100개에서 상태와 레코드 보존 |
| RD-26 | test_review_large_unsigned_slot_and_case_insensitive_legacy | 최대 부호 없는 슬롯과 구형 대소문자 무관 참조 |
| RD-27 | test_review_sqlite_key_lineage_foreign_key_rejects_orphan | SQLite 복합 키 출처가 고아를 거부하고 파일을 남기지 않음 |

## 수동 리뷰와 독립 확인

| 우선순위 | 검토 위험 / 수정 | 근거 |
| --- | --- | --- |
| 높음 | 키 수정 시각을 모든 문서의 열람 시각으로 오해 가능 | 키/문서 컬렉션 분리와 문서별 시각 없음; RD-01 |
| 높음 | 손상/모호 MRU로 잘못된 시간순 이력 생성 가능 | 누락/오류/두 제어 값에서 순위 없음, 원시 제어와 참조 보존; RD-04/07/08/09 |
| 높음 | 미해석 Shell Item을 검증된 경로로 오해 가능 | 후미 원시 보존/진단과 대상 접근 없음; RD-11/23 |
| 중간 | 잘못된 텍스트 진단에 값별 출처가 빠짐 | 물리 값 오프셋으로 진단하고 이스케이프; RD-13 |
| 중간 | Unicode 대소문자 무관 정규식이 비 ASCII 유사 문자 허용 | 구형 문자 일치를 ASCII로 제한; RD-08/26 |
| 중간 | SQLite 출력에서 문서의 부모 키 출처 유실 가능 | 출처/키 복합 외래 키와 부모 ID 고유성; RD-20/27 |
| 중간 | 스키마 확장이 소비자 기대를 조용히 변경 | 보고서/SQLite 버전 7과 영문·국문 변경 안내; RD-20/24 |

별도 python-registry 1.3.1 검사는 생성한 네 인덱스, 정확한 MRUListEx 슬롯/종료자, 보조 평면 Unicode 항목과 확장자 범위를 읽습니다. 임시 검증 의존성이며 패키지/테스트 요구나 독립 실제 하이브 동등성 결과가 아닙니다. 제한된 출처 읽기, REGF 재사용, 순위 의미, 해독, 출력 원자성, 스키마 변경과 문서를 리뷰했습니다.

## 검증과 남은 한계

설치한 plaintrace 0.6.0을 체크아웃 밖에서 현대식/구형 RecentDocs, JSON/SQLite 현재 스키마, 복합 키 출처와 입력 해시 보존으로 스모크 검증합니다. EnScript 이식 가능한 검사 11개, 자동 생성 참조 4개, 영문·국문 문서/테스트 대응, 공백/소스 비교와 아카이브 전용 검사는 별도로 통과합니다. 원본 EnScript/아카이브 ref/매니페스트/트리/README와 2017년 합성 커밋 263개를 보존합니다. 아카이브 전용 검사에는 로컬 원래 백업 ref가 필요하며 컴파일/실행 검사가 아닙니다.

실제 획득 NTUSER, Windows/Linux, Python 3.10, 독립 실제 하이브 비교, 대형 사건 성능이나 라이브 획득 검증은 수행하지 않았습니다. Shell Item/PIDL 해석, 깊은 범위, Office/HWP/Adobe 애플리케이션 MRU, Recent 폴더/LNK 연계, Jump Lists, 삭제 레코드, 사용자 식별과 세션은 미지원입니다. 네이티브 REGF 제약과 기존 아티팩트 한계도 유지합니다. 키 수정과 상대 순서는 정확한 문서 열람 시각이나 사용 증거가 아닙니다. EnCase 컴파일/실행은 여전히 미검증입니다.
