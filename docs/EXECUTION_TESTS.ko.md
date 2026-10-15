# 실행 아티팩트 테스트와 코드 리뷰

[English](EXECUTION_TESTS.md) | **한국어**

2026-10-14 macOS/Python 3.14에서 검증하고 수동 리뷰했습니다. 브라우저 회귀 33개와 실행 검사 30개, 실제 Python 사례 총 63개가 통과합니다. 외부 리뷰나 실제 획득 파일 인증이 아니며 EnScript와 아카이브 보존은 별도로 확인합니다.

## 재현과 픽스처

저장소 루트에서 unittest discovery를 실행합니다. 독립적으로 명시한 필드 값으로 임시 디렉터리에 픽스처를 생성합니다. XPRESS 픽스처 인코더는 완전한 고정 코드 테이블과 알려진 리터럴/매치를 생성하며 실제 증거나 라이브러리 소스를 커밋하지 않습니다. FILETIME 기대값은 알려진 100 ns 나머지와 UTC 값을 유지합니다.

```sh
python3 -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code d1830099999cb1669f8f868506d5c323acdb8ca5 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 가능한 사례

| ID | 테스트 메서드 | 기대 동작 |
| --- | --- | --- |
| EX-01 | test_lnk_unicode_strings_and_correct_time_order | UTF-16 문자열과 대상 생성/접근/쓰기 순서 |
| EX-02 | test_lnk_ansi_codepage | 명시적 cp949와 ANSI 비호환 인코딩 거부 |
| EX-03 | test_lnk_local_volume_no_duplicate_suffix | 볼륨 필드와 대상 파일명 중복 방지 |
| EX-04 | test_lnk_unicode_link_info_preferred | Unicode 경로를 ANSI LinkInfo보다 우선 |
| EX-05 | test_lnk_network_path | UNC 공유와 공통 접미사 후보 |
| EX-06 | test_lnk_tracker_environment_and_opaque_items | 머신/GUID, 리터럴 환경 대상과 불투명 PIDL |
| EX-07 | test_lnk_unknown_extra_and_unresolved_are_diagnosed | 미지원 블록 메타데이터와 미해결 대상 진단 |
| EX-08 | test_lnk_invalid_sizes_offsets_and_missing_terminal | 잘못된 오프셋/크기 및 종료 누락 거부 |
| EX-09 | test_every_lnk_truncated_prefix_fails | 구조화 LNK 픽스처의 잘린 모든 길이 거부 |
| EX-10 | test_lnk_invalid_utf16_and_filetime_preserved | 잘못된 텍스트 이스케이프와 범위 초과 원시 시각 유지 |
| EX-11 | test_prefetch_versions_and_v30_variants | 버전별 카운터, 시각 슬롯, 참조와 볼륨 |
| EX-12 | test_prefetch_version_and_size_rejection | 알 수 없는 버전/레이아웃과 크기 불일치 |
| EX-13 | test_prefetch_section_bounds_and_unterminated_strings | 범위 초과 영역/개수와 문자열 종료 누락 |
| EX-14 | test_every_prefetch_truncated_prefix_fails | Prefetch 픽스처의 잘린 모든 길이 거부 |
| EX-15 | test_mam_prefetch_portable_decompression | 표준 라이브러리로 MAM04 픽스처 디코딩 및 파싱 |
| EX-16 | test_xpress_overlapping_match_and_extended_length | 겹치는 매치와 바이트/16비트 확장 길이 |
| EX-17 | test_xpress_multiple_blocks | 여러 Huffman 블록으로 64 KiB 초과 디코딩 |
| EX-18 | test_xpress_invalid_table_match_and_truncation | 잘못된 트리, 역참조, 확장 초과와 잘린 입력 |
| EX-19 | test_mam_checksum_and_size_limits_fail | MAM84 및 과도하거나 짧은 선언 크기 거부 |
| EX-20 | test_mixed_browser_execution_json_sqlite_and_source_hashes | 혼합 출처, 현재 버전 6, JSON/SQLite 값과 바이트 보존 |
| EX-21 | test_execution_cli_strict_and_fatal_atomicity | strict 경고 출력과 후속 실패 시 부분 파일 방지 |
| EX-22 | test_execution_file_size_limit_and_changing_input | 입력 읽기 제한과 출처 변경 탐지 |
| EX-23 | test_mutated_binary_inputs_never_escape_contract_errors | 결정적 바이트 변형이 결과 또는 계약 오류만 생성 |
| EX-24 | test_review_xpress_direct_api_limits | 직접 디코더 호출의 출력 크기와 정수 타입 제한 |
| EX-25 | test_review_unicode_volume_and_network | Unicode 볼륨 레이블과 네트워크 공유 오프셋 |
| EX-26 | test_review_prefetch_volume_bounds_and_overflow_time | 볼륨 경로 겹침과 FILETIME 범위 초과 |
| EX-27 | test_review_terminal_trailing_bytes_and_source_collision | 종료 이후 바이트 진단과 출처 덮어쓰기 거부 |
| EX-28 | test_review_prefetch_overlapping_sections_are_rejected | 알려진 Prefetch 영역 겹침 거부 |
| EX-29 | test_review_lnk_suffix_with_leading_separator | 선행 구분자 때문에 기존 접미사를 중복하지 않음 |
| EX-30 | test_review_empty_target_candidates_are_unresolved | 빈 텍스트 후보는 미해결 진단 생성 |

## 코드 리뷰 발견 사항

| 우선순위 | 발견 사항 | 수정 / 근거 |
| --- | --- | --- |
| 높음 | 해시를 읽는 동안 입력이 읽기 제한보다 커질 수 있음 | 제한된 해시와 본문 읽기, 전/본문/후 해시 검사; EX-22 |
| 높음 | 직접 디코더 호출의 출력 크기 검증 누락 | 디코딩 전 정수 크기와 8 MiB 제한; EX-24 |
| 높음 | 개별 범위는 맞아도 Prefetch 영역이 겹칠 수 있음 | 접근한 상위 영역과 볼륨 경로 겹침 거부; EX-26/EX-28 |
| 중간 | 공통 접미사의 선행 구분자가 완전한 대상 경로를 중복할 수 있음 | 후보 비교에서 선행 구분자를 제거하고 원시 접미사는 유지; EX-29 |
| 중간 | Unicode 볼륨/네트워크 변형과 잘못된 시각에 검사 필요 | Unicode 오프셋 픽스처와 범위 초과 원시 값 검사; EX-25/EX-26 |
| 중간 | 브라우저 전용 소비자가 확장 테이블을 조용히 받을 수 있음 | 명시적 보고서/SQLite 버전 2와 출처 유형 및 마이그레이션 안내; EX-20 |

## 검증과 남은 한계

기존 EnScript 계약 검사 11개, 자동 생성 참조 4개, 양언어 링크/기술 리터럴/테스트 매핑, 소스 대조와 아카이브 전용 검증을 별도로 통과합니다. 패키지를 빌드/설치하고 체크아웃 밖에서 콘솔 명령을 스모크 검증합니다. 아카이브 검사에는 원본 로컬 백업 ref가 필요하고 합성 실행 테스트에는 필요하지 않습니다.

지원하는 SCCA 레이아웃은 합성 검사이며 실제 OS/프로필 검증은 아닙니다. MAM04 리터럴/매치/여러 블록 검사가 모든 압축기 호환을 입증하지는 않습니다. MAM84/체크섬, 불투명 PIDL/ExtraData와 상세 Prefetch 내부 구조는 미지원입니다. Windows/Linux, Python 3.10 실행, 실제 획득 픽스처, 독립 파서 비교와 성능은 추가 검증이 필요합니다. LNK 후보를 실행하거나 해석하지 않으며 실행 흔적이 모든 실행을 입증하지도 않습니다. EnCase 컴파일/실행은 미검증입니다.

[사용법, 필드와 형식 참조](EXECUTION_CLI.ko.md), [브라우저 회귀 계획](PYTHON_TESTS.ko.md)을 확인하세요.

## EVTX 회귀 실행 (2026-10-15)

EVTX 도입 검증에서는 브라우저 33개, 실행 30개, EVTX 32개로 총 95개를 실행했습니다. 전체 통합 검사를 실행하려면 선택 extra를 설치하며 없으면 EVTX 7개를 명시적으로 건너뜁니다. 기존 출력 회귀 검사도 이제 스키마 버전 3을 확인합니다. [EVTX 재현과 리뷰](EVTX_TESTS.ko.md)를 확인하세요. 위의 기존 검증 날짜는 과거 기록으로 유지합니다.

## 휴지통 회귀 실행 (2026-10-15)

현재 선택 EVTX extra를 포함하면 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개로 123개가 통과합니다. 없으면 115개를 실행하고 8개를 명시적으로 건너뜁니다. 기존 출력 검사는 이제 스키마 4를 확인합니다. [재현과 리뷰](RECYCLE_BIN_TESTS.ko.md)를 확인하세요. 기존 날짜/개수는 과거 검증 기록으로 유지합니다.

## USB 레지스트리 회귀 실행 (2026-10-15)

현재 전체 discovery는 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개, USB 레지스트리 25개로 148개가 통과합니다. EVTX extra가 없으면 140개를 실행하고 8개를 건너뜁니다. 현재 출력 검사는 스키마 5이며 이전 개수/스키마 도입은 과거 기록입니다. [USB 재현과 리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 회귀 실행 (2026-10-15)

현재 전체 discovery는 기존 148개와 RecentDocs 27개로 175개가 통과합니다. EVTX extra가 없으면 167개를 실행하고 기존 통합 8개를 건너뜁니다. 현재 출력 검사는 스키마 6이며 이전 검증 개수/스키마 도입은 과거 기록입니다. [RecentDocs 재현과 리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요.
