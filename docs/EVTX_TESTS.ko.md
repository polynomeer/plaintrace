# EVTX 테스트와 코드 리뷰

**한국어** | [English](EVTX_TESTS.md)

2026-10-15 macOS/Python 3.14와 python-evtx 0.8.1에서 검증하고 수동 리뷰했습니다. Python 95개 모두 건너뛰기 없이 통과했습니다: 브라우저 33개, LNK/Prefetch 30개, EVTX 32개입니다. 자체 리뷰와 합성 검사를 기록하며 외부 리뷰나 획득 파일 인증이 아닙니다. [EVTX 계약](EVTX_CLI.ko.md)을 확인하세요.

## 재현과 픽스처 범위

discovery 전에 선택 extra를 설치합니다. 표준 라이브러리만 있는 환경에서는 통합 검사 7개를 명시적으로 건너뛰고 통과하며 완전한 EVTX 결과가 아닙니다. 픽스처는 독립적으로 조립한 파일/청크/레코드 헤더, CRC, 리터럴 BinXML 템플릿 노드, 공유 템플릿과 Unicode WSTRING 치환을 임시 디렉터리에 만듭니다. XML 오라클에는 알려진 필드 값과 100 ns 틱을 사용합니다. 실제 증거나 의존성 소스를 커밋하지 않습니다. 전체 검사는 mock XML 제공자만이 아니라 실제 디코더 프로세스와 CLI도 실행합니다. 실패/시간 초과/IPC 경계 검사는 집중 mock과 작은 제한도 사용하며 시간 초과 실패 경로는 mock으로 확인한 것이고 대형 로그 실측 벤치마크가 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code 9f32324141810b257d4f680e84c849c013543900 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 검사

| ID | 테스트 메서드 | 오라클 / 동작 |
| --- | --- | --- |
| EV-01 | test_common_fields_and_logon_details | System 필드, UTC, 원시 100 ns 틱과 로그온 details |
| EV-02 | test_security_logoff_variants_and_system_accounts_preserved | 4634/4647 action과 시스템 계정 보존 |
| EV-03 | test_provider_and_channel_qualify_classification | 공급자/채널을 확인한 로그온·전원 분류 |
| EV-04 | test_driver_frameworks_never_infers_usb_state | DriverFrameworks에서 USB 상태를 주장하지 않음 |
| EV-05 | test_repeated_unnamed_nested_data_and_user_data_preserved | 중복/무명/빈 EventData와 네임스페이스 UserData 보존 |
| EV-06 | test_unknown_and_namespace_free_events_retained | 미지 ID와 네임스페이스 없는 Event 허용 |
| EV-07 | test_invalid_and_missing_time_and_numeric_fields | 잘못된/누락 시각과 숫자 경고 |
| EV-08 | test_time_zone_precision_overflow_and_mismatch | 시간대/7자리 정밀도, 범위 초과와 XML/컨테이너 불일치 |
| EV-09 | test_unsigned_record_ids_remain_text_in_sqlite | 부호 없는 64비트 ID를 SQLite 텍스트로 보존; 버전 3과 외래 키 |
| EV-10 | test_xml_dtd_entities_roots_and_duplicate_system_rejected | DTD/entity, 외부 루트와 누락/중복 단일 필드 거부 |
| EV-11 | test_xml_size_depth_and_node_limits | 레코드 XML 바이트와 깊이 제한 |
| EV-12 | test_container_versions_empty_and_dirty | 3.1/3.2 컨테이너, 빈 청크와 dirty 경고 |
| EV-13 | test_container_header_checksums_count_version_and_alignment | 파일 서명/레이아웃/버전/플래그/개수/체크섬/정렬 실패 |
| EV-14 | test_chunk_and_record_envelope_corruption_rejected | 청크 경계/CRC, 레코드 서명/크기/후미/마지막 오프셋 실패 |
| EV-15 | test_inactive_chunks_diagnosed_without_carving | 추가 물리 청크를 경고와 함께 제외 |
| EV-16 | test_record_and_input_limits_and_changing_file | 개수/읽기 상한과 변경 파일 거부 |
| EV-17 | test_missing_or_wrong_dependency_is_actionable | 누락/다른 버전 선택 디코더 명시적 거부 |
| EV-18 | test_worker_timeout_and_exit_failure_abort | 시간 초과/프로세스 실패를 치명적 계약 오류로 처리 |
| EV-19 | test_decoder_lineage_counts_and_output_caps | 출력 수용 전 디코더 오프셋/개수/JSON 검사 |
| EV-20 | test_mutated_and_truncated_envelopes_only_raise_contract_errors | 경계 절단과 고정 시드 변형 100개에서 계약 오류 처리 |
| EV-21 | test_real_decoder_synthetic_binxml_end_to_end | 실제 디코더/어댑터: 합성 레코드 2개와 출처 바이트/해시 유지 |
| EV-22 | test_cli_subprocess_mixed_inputs_json_sqlite_and_no_overwrite | 실제 CLI 프로세스: 네 입력 종류, JSON/SQLite와 덮어쓰기 방지 |
| EV-23 | test_multiple_logs_duplicate_ids_and_dirty_strict | 여러 로그의 중복 ID를 별도 source ID로 유지; strict 경고 |
| EV-24 | test_empty_evtx_and_corrupt_binxml_fatal_atomicity | 실제 디코더: 빈 출처 성공, 잘못된 BinXML이 전체 출력 중단 |
| EV-25 | test_review_shared_template_and_unicode_substitutions | 공유 템플릿과 Unicode WSTRING 치환; 중복 ID 경고 |
| EV-26 | test_review_multiple_chunks_and_container_32 | 실제 디코더: 여러 물리 청크와 버전 3.2 컨테이너 |
| EV-27 | test_review_non_data_nodes_cannot_supply_normalized_identity | Binary/외부 네임스페이스 요소가 정규화 사용자를 위장하지 못함 |
| EV-28 | test_review_missing_ids_and_overflow_filetime | 누락 XML ID와 범위 초과 컨테이너 시각 경고; 원시 틱 보존 |
| EV-29 | test_review_worker_and_parent_decoded_size_limits | 프로세스/부모가 게시 전 과도한 IPC/XML 거부 |
| EV-30 | test_review_xml_node_limit_and_integer_lexical_bounds | XML 노드 상한과 잘못된/거대한 부호 없는 ID 텍스트 거부 |
| EV-31 | test_review_missing_dependency_cli_publishes_nothing | CLI에서 extra 누락 시 파일/stdout 출력 없음 |
| EV-32 | test_review_binxml_invalid_chunk_reference_is_fatal | 실제 디코더가 청크 밖 템플릿 참조 거부 |

## 코드 리뷰 발견 사항

| 우선순위 | 발견 사항 | 해결 / 근거 |
| --- | --- | --- |
| 높음 | 이벤트 ID만 확인하면 다른 공급자의 이벤트를 오분류 | 로그온/전원은 공급자와 채널을 요구; EV-03 |
| 높음 | BinXML 공유 포인터, 순환과 확장에 제한된 실패 경로 필요 | 컨테이너 엄격 검사, 청크 내 디코더 버퍼, 시간 제한 프로세스, IPC/XML 상한과 치명적 예외; EV-13/14/18/19/29/32 |
| 높음 | 비 Data/외부 네임스페이스 요소가 정규화 신원을 위장 가능 | 허용한 네임스페이스의 Data만 정규화하고 나머지 XML 보존; EV-27 |
| 중간 | 부호 없는 64비트 레코드 ID가 SQLite 부호 있는 정수 초과 | 십진 텍스트와 독립 출처 오프셋; EV-09/23/25 |
| 중간 | 컨테이너 FILETIME을 쓰기 시각으로 부르면 의미 과장 | container_time과 XML TimeCreated 분리, 원시 값/불일치 경고; EV-01/08/28 |
| 중간 | 중복 데이터/세션 ID와 USB 개수 추정이 결론을 만들어낼 수 있음 | 모호한 정규화 필드 null, 모든 오프셋/계정 보존, 세션 연결/USB 상태 추론 없음; EV-02/04/05/25 |
| 중간 | 선택 의존성 때문에 중요한 검사가 조용히 건너뛰어질 수 있음 | 정확한 버전 고정, 설치 안내와 extra 전체 실행/7개 skip 구분 문서화; EV-17/31 |
| 중간 | events 추가가 소비자의 기대를 조용히 변경 | 모든 보고서에 명시적 스키마 버전 3과 변경 안내; EV-09/22 |

## 검증과 남은 한계

실제 선택 디코더가 있는 격리 환경에서 전체 검사를 실행합니다. 디코더가 없는 두 번째 실행에서는 88개를 실행하고 7개를 명시적으로 건너뜁니다. 패키지 설치/콘솔 실행도 체크아웃 밖에서 스모크 검증합니다. 기존 EnScript 이식 가능한 검사 11개, 자동 생성 참조 4개, 영문·국문 문서/테스트 대응, 바이트 비교와 아카이브 전용 검증은 별도로 통과하며 EnCase 런타임 검증이 아닙니다. 아카이브 검사에는 원래 로컬 백업 ref가 필요합니다.

생성한 리터럴/공유 템플릿/문자열 치환 픽스처는 디코더를 실행하지만 실제 Windows 템플릿 캐시, 조건부 치환, 타입/배열 치환, 드문 BinXML 토큰이나 모든 공급자 호환을 입증하지 않습니다. 획득 EVTX, Windows/Linux, Python 3.10, 독립 파서 동등성, 대형 로그 성능이나 라이브 획득 검사를 수행하지 않았습니다. CRC 검사는 손상/체크섬 없는 변형을 복구하지 않고 의도적으로 거부합니다. 입력별 제한이 정상 대형 로그도 거부할 수 있으며 시간 제한 프로세스는 메모리 샌드박스가 아닙니다. 삭제/슬랙 복구, 메시지 DLL 렌더링, EVT, 세션 연계와 USB 레지스트리/상태 연계는 미지원입니다. 기존 브라우저/LNK/Prefetch 한계와 Windows/EnCase 실행 미검증을 문서에 유지합니다. 합성 검사는 사건 분석 수용 기준이 아닙니다.
