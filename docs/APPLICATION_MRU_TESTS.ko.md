# 애플리케이션 MRU 테스트와 코드 리뷰

[English](APPLICATION_MRU_TESTS.md) | **한국어**

2026-10-15 macOS/Python 3.14에서 검증하고 자체 코드 리뷰했습니다. EVTX extra 포함 200개가 건너뜀 없이 통과합니다: 기존 175개와 신규 애플리케이션 MRU 25개입니다. extra가 없으면 192개 실행, 기존 통합 8개 건너뜀입니다. 애플리케이션 MRU 자체는 추가 의존성이 없습니다. [어댑터 계약](APPLICATION_MRU_CLI.ko.md)을 확인하세요. 외부 리뷰 승인이나 실제 획득 자료 검증은 아닙니다.

## 재현과 합성 자료

임시 디렉터리에 독립 REGF 생성기로 세 제품군, 희소 슬롯과 원시 문자열을 구성합니다. 예상 경로와 FILETIME은 어댑터로 계산하지 않고 고정값과 대조합니다. 실제 증거나 출력은 커밋하지 않습니다. 기존 읽기/출력 보호를 재사용하며 실제 CLI와 두 출력 형식을 실행합니다. 축소 예산 검증은 대용량 성능 검증이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 4b88c0a8d8699920ecdd5622400484bbef956c89 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | Test method | 검증 내용 |
| --- | --- | --- |
| APP-01 | test_three_families_sparse_slots_and_raw_time | 세 제품군, 빈 슬롯 뒤 항목과 원시 시각 |
| APP-02 | test_office_versions_apps_places_and_user_scopes | Office 버전/앱/폴더/계정 범위 |
| APP-03 | test_office_prefix_delimiter_and_opaque_flags | 첫 구분자 뒤 별표와 불투명 플래그 |
| APP-04 | test_invalid_and_duplicate_office_times_do_not_guess | 잘못된/중복 T는 시각 미선택 |
| APP-05 | test_office_zero_and_overflow_filetime | 0/범위 초과 FILETIME의 원시 값 보존 |
| APP-06 | test_unrecognized_prefix_retains_raw_without_path | 잘못된 접두사는 원문만 보존 |
| APP-07 | test_plain_office_path_no_time_or_normalization | 환경변수와 경로를 그대로 보존 |
| APP-08 | test_hwp_frames_versions_binary_bom_and_regsz | HWP 프레임/버전/BOM/문자열 |
| APP-09 | test_hwp_big_endian_not_interpreted | 빅엔디언 바이너리 해석 제외 |
| APP-10 | test_adobe_products_versions_and_literal_paths | Adobe 제품/버전과 원문 경로 |
| APP-11 | test_adobe_missing_path_unknown_slot_and_metadata | 누락 경로/알 수 없는 슬롯 진단 |
| APP-12 | test_noncanonical_names_retained_as_metadata | 비정규 이름은 메타데이터 |
| APP-13 | test_case_insensitive_canonical_names | 정규 이름의 대소문자 처리 |
| APP-14 | test_wrong_type_and_invalid_unicode_keep_bytes | 잘못된 타입/유니코드의 바이트 보존 |
| APP-15 | test_embedded_nul_unterminated_and_empty_text | 내부 NUL/미종결/빈 문자열 |
| APP-16 | test_duplicates_key_time_and_offsets_are_scoped | 중복 보존, 키 시각과 오프셋 |
| APP-17 | test_missing_families_and_existing_empty_key | 제품군 부재와 기존 빈 목록 구분 |
| APP-18 | test_regf_supported_indexes_and_dirty_header | REGF 인덱스와 dirty 헤더 거부 |
| APP-19 | test_adapter_budgets_reject_without_partial_output | 키/항목/출력 예산 거부 |
| APP-20 | test_cli_repeated_sources_hashes_and_schema | 실제 CLI 반복 입력과 해시/스키마 |
| APP-21 | test_json_sqlite_roundtrip_and_parent_foreign_key | JSON/SQLite 왕복과 부모 외래 키 |
| APP-22 | test_mixed_registry_sources_no_automatic_joins | 레지스트리 어댑터 간 자동 조인 없음 |
| APP-23 | test_cli_strict_fatal_output_and_evidence_collision | 엄격/치명적 오류와 입력 충돌 보호 |
| APP-24 | test_nested_list_keys_are_diagnosed | 중첩 목록 키 진단 |
| APP-25 | test_deterministic_mutations_have_controlled_failures | 결정적 변이 입력의 통제된 실패 |

## 자체 리뷰와 보완

원본 모듈과 별도로 판독기 경계, 출처 조립, 문자열/메타데이터 분리, 시각 의미와 출력 계약을 검토했습니다. 빈 슬롯에서 중단하거나 Adobe 자식 경로를 누적하지 않도록 형제 열거를 구현했습니다. 모호한 Office T와 잘못된 UTF-16은 해석을 거부하고 원시 바이트를 보존합니다. 중첩 키를 묵시적으로 무시하지 않고 경고하도록 보완했습니다. 슬롯 번호를 순위로, 키 시각을 문서별 열람 시각으로 승격하지 않습니다. 복합 외래 키와 기존 아티팩트 전용 보고서의 스키마 7도 검증합니다.

python-registry 1.3.1로 합성 Office/HWP/Adobe 값 이름/타입/바이트를 독립 대조했습니다. 패키지를 재설치한 뒤 저장소 밖에서 설치된 콘솔의 JSON/SQLite 스키마와 원본 해시를 확인했습니다. EnScript 정적 회귀 11개, 소스 참조, 영문/국문 링크/구조/테스트 매핑과 아카이브 검증도 실행했습니다. 이는 아래 실행 환경 한계를 해소하지 않습니다.

## 남은 검증

실제 애플리케이션 NTUSER 하이브, Windows/Linux, Python 3.10, 실제 자료의 독립 파서 대조, 대규모 성능과 획득 경합은 미검증입니다. 버전별 미지원 레이아웃, 다른 제품/앱과 중첩 슬롯, Adobe 구형 REG_BINARY 경로, dirty 하이브/로그 재생, REGF 1.6/big data/volatile/link/삭제/slack 구조는 지원하지 않습니다. 경로 존재/사용자 소유권/문서 열람을 증명하지 않으며 자동 상관분석도 없습니다. EnCase 컴파일/실행은 계속 미검증이고 원본 EnScript와 아카이브는 보존합니다.
