# Python CLI 테스트 계획과 결과

[English](PYTHON_TESTS.md) | **한국어**

2026-10-14 macOS와 Python 3.14에서 검증했습니다. 실제 Python 어댑터/CLI와 생성한 합성 SQLite 픽스처를 실행하며 EnScript 검증은 아닙니다. 실제 증거나 생성 DB는 커밋하지 않습니다. [구현 계약](PYTHON_CLI.ko.md)을 확인하세요.

## 재현

체크아웃 루트에서 실행합니다. 외부 런타임/테스트 라이브러리는 필요하지 않습니다. 아카이브 검사에는 원본 로컬 백업 ref가 추가로 필요하며 휴대 가능한 Python 테스트와 별개입니다. 마지막 비교는 브랜치 기준과 모든 EnScript 및 과거 매니페스트를 대조합니다.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code bb476180453c76f7d38e5b6a9f1f025ad2273ce0 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 가능한 사례

33개 모두 통과했습니다. 기대 UTC 시각과 문자열을 독립적으로 명시했으며 Firefox 주석 ID/순서는 EnScript 가정과 의도적으로 다릅니다. 각 사례의 임시 테스트 자료는 검사 후 제거합니다.

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| PY-01 | test_chromium_visits_keywords_and_downloads | 개별 시각, 반복 UTF-8 쿼리, 저장 검색어와 리디렉션 체인 |
| PY-02 | test_firefox_correlates_annotation_names_and_place | 임의 주석 ID/순서, JSON 메타데이터와 다운로드 이벤트 시각 |
| PY-03 | test_url_summary_is_not_a_visit | 요약 폴백과 개별 방문을 명시적으로 구분 |
| PY-04 | test_missing_downloads_are_diagnosed | 다운로드 미지원 시 진단 생성 |
| PY-05 | test_firefox_malformed_metadata_and_duplicate_annotations | 잘못된 최신 메타데이터 보존과 중복 주석 경고 |
| PY-06 | test_iso_firefox_endtime_and_invalid_numeric_metadata | 시간대 포함 ISO 변환과 잘못된 숫자 메타데이터 거부 |
| PY-07 | test_invalid_timestamp_and_query_preserve_records | 범위 초과 시각과 잘못된 UTF-8 쿼리에도 방문 보존 |
| PY-08 | test_unknown_empty_and_corrupt_databases_fail_without_output | 알 수 없는/손상/누락 입력은 보고서 게시하지 않음 |
| PY-09 | test_multiple_profiles_and_browser_label_conflict | 혼합 계열 출처와 잘못된 명시 표기 거부 |
| PY-10 | test_json_and_sqlite_roundtrip_and_no_overwrite | Unicode/문자열, 외래 키, 출력 거부와 증거 바이트 |
| PY-11 | test_wal_committed_records_and_input_bytes_unchanged | DB/WAL/SHM 변경 없이 커밋된 WAL 자료 읽기 |
| PY-12 | test_changed_snapshot_and_rollback_journal_rejected | 복사 불일치와 비어 있지 않은 롤백 저널 거부 |
| PY-13 | test_cli_stdout_strict_and_sqlite_output | stdout JSON, strict 경고 종료와 SQLite 출력; 서브프로세스 실행 |
| PY-14 | test_minimal_chromium_schema_without_optional_fields | 선택 열 누락, Opera 표기와 리터럴 파일 경로 |
| PY-15 | test_firefox_summary_missing_downloads_and_incomplete_annotation | Firefox 요약, 주석 대리 시각과 메타데이터/테이블 누락 |
| PY-16 | test_orphan_visits_and_annotation_urls_are_not_silently_dropped | 대응 URL 없는 행과 원시 Firefox transition 보존 |
| PY-17 | test_empty_supported_database_is_successful | 지원하는 빈 스키마는 행을 만들어내지 않고 성공 |
| PY-18 | test_malformed_required_and_ambiguous_schemas_are_rejected | 잘못된 필수 열과 스키마 혼재 모호성 거부 |
| PY-19 | test_fragment_and_literal_bad_escape_query | 프래그먼트 제외, 빈 검색어와 잘못된 이스케이프 리터럴 |
| PY-20 | test_sqlite_cli_requires_destination | SQLite 출력 경로를 입력 열기 전에 요구 |
| PY-21 | test_output_race_preserves_other_writer | 다른 작성자가 먼저 게시한 출력을 덮어쓰지 않음 |
| PY-22 | test_all_or_nothing_multiple_inputs | 후속 입력 실패 시 부분 보고서 게시하지 않음 |
| PY-23 | test_output_publication_failure_leaves_no_report_or_temp | 하드 링크 미지원 시 임시 출력 정리 |
| PY-24 | test_epoch_precision_and_unknown_values | 에포크 오프셋, 마이크로초 정밀도, 미상 및 잘못된 시각 |
| PY-25 | test_invalid_unrelated_query_does_not_drop_valid_terms | 잘못된 비검색/검색 필드 때문에 정상 인접 검색어가 누락되지 않음 |
| PY-26 | test_dangling_output_symlink_is_not_followed | 최종 출력의 dangling symlink을 따라가지 않고 유지 |
| PY-27 | test_existing_output_sqlite_sidecars_are_preserved | 기존 출력 WAL/SHM/저널이 있으면 게시 거부 |
| PY-28 | test_stdout_serialization_failure_has_no_partial_json | 바이너리/비유한 JSON 값은 stdout 쓰기 전에 실패 |
| PY-29 | test_browser_views_are_not_accepted_as_native_tables | 브라우저 표준 이름은 실제 테이블이어야 함 |
| PY-30 | test_orphan_stored_keyword_is_diagnosed | URL 대응이 없는 저장 검색어를 진단하고 보존 |
| PY-31 | test_download_lineage_and_inconsistent_times | 선택된 주석/이벤트 ID를 출력하고 역전 시각 진단 |
| PY-32 | test_unsupported_export_format_fails_explicitly | API 출력 형식 미지원 시 조용히 JSON을 선택하지 않음 |
| PY-33 | test_iso_timezone_overflow_is_diagnostic_not_exception | ISO 시간대 정규화 범위 초과를 예외 대신 진단 처리 |

## 추가 검사

독립된 임시 가상환경에서 wheel을 빌드/설치했으며 설치한 콘솔 명령은 버전 0.2.0을 출력하고 체크아웃 밖에서 스모크 검증합니다. 기존 EnScript 계약 검사 11개, 자동 생성 참조, 영문·국문 문서 검사와 과거 아카이브 전용 검증은 별도로 수행합니다. Python 패키지 빌드 산출물은 Git에서 제외합니다.

## 남은 검증

사건 분석 결과에 의존하기 전에 여러 버전/플랫폼의 실제 획득 Chrome/Opera/Firefox 프로필, 매우 큰 프로필, 브라우저 종료/획득 절차와 특이한 Unicode/메타데이터/스키마 변형을 검사해야 합니다. 해시 기반 복사 안정성은 원자적인 획득이 아니며 테스트가 증거 완전성이나 모든 라이브 작성자 경합 탐지를 입증하지는 않습니다. EnCase 컴파일/실행은 아직 남아 있습니다. Python 테스트는 원본 EnScript를 실행하지 않으며 호스트 API 동작과의 동등성을 입증하지 않습니다.

후속 수정과 남은 한계는 [코드 리뷰](PYTHON_REVIEW.ko.md)를 확인하세요.

## EVTX 회귀 실행 (2026-10-15)

EVTX 도입 검증에서는 브라우저 33개, 실행 30개, EVTX 32개로 총 95개를 실행했습니다. 전체 통합 검사를 실행하려면 선택 extra를 설치하며 없으면 EVTX 7개를 명시적으로 건너뜁니다. 기존 출력 회귀 검사도 이제 스키마 버전 3을 확인합니다. [EVTX 재현과 리뷰](EVTX_TESTS.ko.md)를 확인하세요. 위의 기존 검증 날짜는 과거 기록으로 유지합니다.

## 휴지통 회귀 실행 (2026-10-15)

현재 선택 EVTX extra를 포함하면 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개로 123개가 통과합니다. 없으면 115개를 실행하고 8개를 명시적으로 건너뜁니다. 기존 출력 검사는 이제 스키마 4를 확인합니다. [재현과 리뷰](RECYCLE_BIN_TESTS.ko.md)를 확인하세요. 기존 날짜/개수는 과거 검증 기록으로 유지합니다.

## USB 레지스트리 회귀 실행 (2026-10-15)

현재 전체 discovery는 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개, USB 레지스트리 25개로 148개가 통과합니다. EVTX extra가 없으면 140개를 실행하고 8개를 건너뜁니다. 현재 출력 검사는 스키마 5이며 이전 개수/스키마 도입은 과거 기록입니다. [USB 재현과 리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 회귀 실행 (2026-10-15)

현재 전체 discovery는 기존 148개와 RecentDocs 27개로 175개가 통과합니다. EVTX extra가 없으면 167개를 실행하고 기존 통합 8개를 건너뜁니다. 현재 출력 검사는 스키마 6이며 이전 검증 개수/스키마 도입은 과거 기록입니다. [RecentDocs 재현과 리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요.
