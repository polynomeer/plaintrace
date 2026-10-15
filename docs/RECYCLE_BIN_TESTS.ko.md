# 휴지통 테스트와 코드 리뷰

**한국어** | [English](RECYCLE_BIN_TESTS.md)

2026-10-15 macOS/Python 3.14에서 검증하고 수동 리뷰했습니다. python-evtx 0.8.1이 있는 환경에서 브라우저 33개, LNK/Prefetch 30개, EVTX 32개, 휴지통 28개로 실제 Python 검사 123개 모두 건너뛰기 없이 통과했습니다. 자체 리뷰와 합성 검증이며 외부 리뷰나 실제 획득 파일 인증이 아닙니다. [사용법과 스키마 계약](RECYCLE_BIN_CLI.ko.md)을 확인하세요.

## 재현과 독립 픽스처

픽스처는 알려진 리틀 엔디언 버전/크기/FILETIME 필드와 UTF-16 경로 바이트를 임시 디렉터리에 만듭니다. UTC 오라클에는 알려진 100 ns 나머지가 있으며 운영 파서에서 기대 값을 계산하지 않습니다. 획득 증거나 생성 출력을 커밋하지 않습니다. 실제 어댑터, JSON/SQLite 출력과 CLI 프로세스를 실행합니다. 신규 검사 중 다섯 출처 통합 하나만 EVTX가 필요하므로 전체 discovery에는 선택 extra를 설치하세요. 없으면 기존 EVTX 검사 7개를 포함해 통합 8개를 명시적으로 건너뛰고 115개를 실행합니다. 휴지통 파싱 자체에는 추가 의존성이 없습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code e0d0145cfb7b649c1713d66776ea140a43f891a3 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 검사

| ID | 테스트 메서드 | 오라클 / 동작 |
| --- | --- | --- |
| RB-01 | test_version_one_fixed_layout_and_raw_fields | 버전 1 고정 필드, 크기, UTC/원시 FILETIME과 경고 없음 |
| RB-02 | test_version_two_counted_layout_and_utf16_units | 버전 2 개수에 보조 평면 문자와 NUL의 UTF-16 단위 반영 |
| RB-03 | test_literal_unc_extended_relative_and_special_paths | UNC/확장/상대/환경 변수/특수 경로를 그대로 보존 |
| RB-04 | test_unsigned_sizes_and_zero_size_preserved | 0과 부호 없는 64비트 최대 크기를 십진 텍스트로 보존 |
| RB-05 | test_zero_and_overflow_deletion_times_are_diagnostic | 0/범위 초과 FILETIME을 null/경고와 정확한 틱으로 보존 |
| RB-06 | test_empty_paths_are_retained_with_warning | 두 레이아웃의 빈 경로를 보존하고 경고 |
| RB-07 | test_malformed_utf16_preserves_bytes_and_escapes | 잘못된 UTF-16 바이트를 이스케이프하고 정확한 필드 보존 |
| RB-08 | test_version_one_nonzero_padding_retained_and_diagnosed | 버전 1 NUL 이후 필드의 0 아닌 바이트 보존/경고 |
| RB-09 | test_version_two_early_terminator_and_padding_warn | 버전 2 조기 NUL과 추가 필드 패딩 경고 |
| RB-10 | test_trailing_bytes_are_opaque_and_diagnosed | 0을 포함한 후미 바이트를 미해석 hex로 보존 |
| RB-11 | test_unknown_versions_and_short_headers_rejected | 미지 버전과 불완전 헤더 실패 |
| RB-12 | test_invalid_lengths_counts_and_missing_terminators_rejected | 0/과도한/경계 밖 개수와 미종결 필드 실패 |
| RB-13 | test_every_truncated_prefix_of_both_layouts_fails | 대표 버전 1/2 파일의 모든 절단 접두부 실패 |
| RB-14 | test_path_and_input_limits_cover_direct_parser_and_cli | 32768 단위 경계와 128 KiB 입력/파서 직접 호출 상한 |
| RB-15 | test_renamed_and_repeated_sources_have_stable_hash_and_lineage | 이름 변경/반복 입력의 별도 출처 ID와 해시/바이트 보존 |
| RB-16 | test_changed_input_fails_without_publication | 변경 파일은 출력 게시 방지 |
| RB-17 | test_json_sqlite_schema_four_and_unsigned_size_roundtrip | JSON/SQLite 버전 6, 부호 없는 크기, Unicode와 출처 외래 키 |
| RB-18 | test_cli_stdout_strict_and_real_subprocess | strict 경고 stdout과 실제 프로세스 성공 |
| RB-19 | test_cli_all_or_nothing_when_later_input_fails | 후속 입력 오류는 전체 출력 중단과 임시 출력 정리 |
| RB-20 | test_existing_output_sidecar_and_evidence_collision_preserved | 기존 출력/사이드카와 출처 충돌에서 바이트 덮어쓰기 방지 |
| RB-21 | test_no_payload_sid_owner_or_target_filesystem_inference | 실제 파일 열기는 $I 출처만 접근하며 소유자/$R 추정 없음 |
| RB-22 | test_mixed_browser_link_prefetch_and_recycle_sources | 브라우저/LNK/Prefetch/휴지통 출처 순서와 스키마 6 |
| RB-23 | test_mixed_five_source_cli_with_actual_evtx_decoder | 실제 EVTX 디코더와 다섯 입력 유형의 JSON/SQLite |
| RB-24 | test_mutated_inputs_only_raise_contract_errors | 고정 시드 변형 200개는 계약 오류 또는 메타데이터 보존 |
| RB-25 | test_review_utf16_terminator_is_aligned_not_byte_substring | NUL 검색을 임의 바이트가 아닌 UTF-16 단위에 정렬 |
| RB-26 | test_review_version_one_543_byte_anomaly_is_not_guessed | 543바이트 밀린 버전 1 변형을 추정 없이 거부 |
| RB-27 | test_review_directory_and_unknown_files_fail_without_report | 디렉터리/누락/$R/INFO2 입력은 보고서 없이 실패 |
| RB-28 | test_review_other_artifact_options_do_not_change_recycle_parsing | 브라우저 표기/LNK 코드페이지는 $I 파싱에 영향 없음 |

## 수동 코드 리뷰

| 우선순위 | 검토한 위험 | 처리 / 근거 |
| --- | --- | --- |
| 높음 | 버전 2 문자 개수를 Python 문자 개수나 바이트로 오해 가능 | NUL 포함 UTF-16 단위로 계산하며 디코딩 전 상한/경계 확인; RB-02/12/14 |
| 높음 | 임의 바이트 부분 문자열로 NUL을 찾으면 정상 UTF-16 절단 가능 | 정렬된 2바이트 단위로만 검색; RB-25 |
| 높음 | 절단/밀린 메타데이터에서 크기/시각/경로를 만들어낼 수 있음 | 지원 필드 전체 요구, 미지 버전/543바이트 변형 거부; RB-11/13/26 |
| 중간 | 부호 없는 크기가 SQLite 부호 있는 정수/JavaScript 정확한 정수 초과 | JSON과 SQLite에 십진 텍스트; RB-04/17 |
| 중간 | 패딩/조기 NUL/후미 바이트에 미해석 자료가 숨겨질 수 있음 | 전체 원시 필드와 후미 바이트 보존 및 명시적 경고; RB-08/09/10 |
| 중간 | 출처 디렉터리 이름이나 가까운 $R을 입증된 소유자/내용으로 오해 가능 | 명시한 $I 출처만 여는지 직접 관찰, SID/내용 추론 없음; RB-21 |
| 중간 | 컬렉션 추가가 소비자의 기대를 조용히 변경 | 보고서/SQLite 스키마 4와 기존 출력 회귀 검사 갱신; RB-17/22/23 |

파서, 제한된 읽기 연계, 인자 범위, 출력 게시, 스키마 변경과 영문·국문 문서를 검토했습니다. 검토한 위험과 구현한 방어이며 외부 리뷰어 승인을 주장하지 않습니다. 비정상 버전 1 레이아웃은 휴리스틱 복구 대신 의도적으로 미지원입니다.

## 검증과 남은 한계

설치한 0.4.0 콘솔 명령을 체크아웃 밖에서 다섯 아티팩트 유형, JSON/SQLite 스키마 4와 입력 해시 보존으로 스모크 검증합니다. 기존 EnScript 이식 가능한 검사 11개, 소스 참조 4개, 영문·국문 문서/테스트 대응, 공백과 소스/아카이브 비교는 별도로 통과합니다. 아카이브 검사는 원본 소스 13개, 원래 README, 원래 트리와 2017년 합성 커밋 263개를 보존하지만 EnScript 컴파일이 아니며 원래 로컬 백업 ref가 필요합니다.

실제 획득 $I, Windows/Linux, Python 3.10, 독립 파서 대조, 대형 컬렉션과 획득 경합은 미검증입니다. 지원 레이아웃은 합성 검사만 수행했습니다. INFO/INFO2, 543바이트 버전 1 변형, 절단/손상 필드 복구, 디렉터리 검색, $R 추출/복구/상태 분석과 계정 식별은 미지원입니다. 메타데이터/CRC 없는 레이아웃 인식은 진위나 완전성 인증이 아닙니다. 기존 브라우저/LNK/Prefetch/EVTX 한계, 선택 디코더 요구, 입력별 자원 제한과 EnCase 컴파일/실행 미검증도 문서에 유지합니다.

## USB 레지스트리 회귀 실행 (2026-10-15)

현재 전체 discovery는 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개, USB 레지스트리 25개로 148개가 통과합니다. EVTX extra가 없으면 140개를 실행하고 8개를 건너뜁니다. 현재 출력 검사는 스키마 5이며 이전 개수/스키마 도입은 과거 기록입니다. [USB 재현과 리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 회귀 실행 (2026-10-15)

현재 전체 discovery는 기존 148개와 RecentDocs 27개로 175개가 통과합니다. EVTX extra가 없으면 167개를 실행하고 기존 통합 8개를 건너뜁니다. 현재 출력 검사는 스키마 6이며 이전 검증 개수/스키마 도입은 과거 기록입니다. [RecentDocs 재현과 리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요.
