# UserAssist 테스트와 코드 리뷰

[English](USERASSIST_TESTS.md) | **한국어**

2026-10-16에 macOS/Python 3.14에서 검증하고 자체 리뷰했습니다. EVTX 추가 의존성을 포함한 Python 사례 346개가 생략 없이 통과했으며 기존 314개와 UserAssist 32개입니다. 추가 의존성이 없으면 338개가 실행되고 기존 EVTX 통합 8개가 생략되므로 완전한 EVTX 검증이 아닙니다. UserAssist 자체는 추가 런타임 의존성이 없습니다. [계약과 제한](USERASSIST_CLI.ko.md)을 참고하세요. 자체 리뷰이며 외부 승인이나 획득 증거 인증이 아닙니다.

## 재현과 합성 픽스처

기존 독립 합성 REGF 작성기가 정확한 Version DWORD를 갖는 GUID/Count/Settings 범위를 만듭니다. 페이로드는 운영 인코더가 아니라 독립적으로 지정한 리틀 엔디언 오프셋과 고정 UTC/100 ns 기준으로 직접 구성합니다. 두 구조·유니코드/이모지·ROT13/평문/미상 정책·원시 메타데이터·잘못된 제어를 포함합니다. 임시 하이브와 출력은 삭제하고 실제 증거는 커밋하지 않습니다. 패치한 예산과 시드 기반 페이로드 변이는 통제된 검사이며 성능 시험이나 전면 퍼징이 아닙니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[evtx]'
.venv/bin/python -m unittest discover -s tests -v
python3 tools/test_improvements.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py --archive-only
git diff --check
git diff --exit-code caa66102c4c46ebc7ab0e81153c36801bdfc8d67 -- '*.EnScript' docs/source-manifest.json docs/history-map.json
```

## 실행 사례

| ID | 테스트 메서드 | 기준 / 동작 |
| --- | --- | --- |
| UA-01 | test_v3_offsets_unicode_and_unadjusted_count | 버전 3 오프셋·유니코드·원시 카운터 |
| UA-02 | test_v5_metrics_and_opaque_ranges_are_exact | 버전 5 지표와 불투명 구간 |
| UA-03 | test_session_control_never_becomes_run_record | 세션 제어에는 실행 지표 없음 |
| UA-04 | test_session_control_name_case_and_entry_sized_payload | 소문자 제어 이름과 정상 크기 페이로드 |
| UA-05 | test_zero_and_out_of_range_filetimes | 0·범위 초과 FILETIME |
| UA-06 | test_unsigned_counts_and_no_legacy_bias_correction | 부호 없는 카운터와 레거시 무보정 |
| UA-07 | test_noencrypt_one_preserves_plain_names_and_control | 평문 설정과 세션 제어 |
| UA-08 | test_noencrypt_zero_default_and_nonascii_names | 기본 ROT13과 비 ASCII 보존 |
| UA-09 | test_invalid_noencrypt_does_not_guess_names_or_controls | 잘못된 설정은 이름·제어를 추측하지 않음 |
| UA-10 | test_missing_version_retains_values_without_size_guessing | 버전 누락 시 크기 추측 금지 |
| UA-11 | test_unsupported_version_and_wrong_version_type | 미지원 버전과 버전 형식 오류 |
| UA-12 | test_wrong_size_truncation_tail_and_cross_version_rejected | 절단·후행·다른 버전 길이 거부 |
| UA-13 | test_wrong_registry_type_not_parsed | 잘못된 레지스트리 형식 미해석 |
| UA-14 | test_keys_raw_metadata_parent_links_and_physical_offsets | 키 원시 메타데이터·부모·물리 오프셋 |
| UA-15 | test_absent_and_empty_supported_roots | 누락 루트와 유효한 빈 루트 구분 |
| UA-16 | test_unknown_guid_version_supported_without_identity_mapping | 미상 GUID도 앱 신원 추정 없이 처리 |
| UA-17 | test_non_guid_children_missing_count_and_nested_scopes | 미지원 이름·Count 누락·깊은 범위 진단 |
| UA-18 | test_case_insensitive_paths_versions_settings | 경로·버전·설정의 대소문자 |
| UA-19 | test_all_regf_index_and_version_layouts | REGF 인덱스와 버전 조합 |
| UA-20 | test_dirty_and_corrupt_hives_rejected | 더티·손상 하이브 거부 |
| UA-21 | test_key_entry_and_output_budgets | 키·항목·출력 예산 |
| UA-22 | test_duplicate_values_and_aliases_rejected | 중복 값과 대소문자 별칭 거부 |
| UA-23 | test_json_sqlite_schema_and_foreign_keys | JSON·SQLite 스키마와 외래 키 |
| UA-24 | test_repeated_sources_hashes_and_input_unchanged | 반복 출처·해시·입력 보존 |
| UA-25 | test_cli_subprocess_json_strict_and_sqlite | 실제 CLI JSON·엄격 모드·SQLite |
| UA-26 | test_mixed_dialog_and_userassist_sources | 대화상자와 UserAssist 별도 출처 |
| UA-27 | test_fatal_later_input_publishes_no_partial_output | 나중 입력 실패 시 부분 출력 없음 |
| UA-28 | test_evidence_and_existing_outputs_protected | 증거·기존 출력 보존 |
| UA-29 | test_missing_input_and_sqlite_destination_rejected | 누락 입력·SQLite 목적지 거부 |
| UA-30 | test_no_decoded_target_is_opened | 해독 대상은 열지 않음 |
| UA-31 | test_changed_input_hash_rejected | 입력 해시 변경 거부 |
| UA-32 | test_seeded_binary_payload_mutations_are_bounded | 결정적 페이로드 변이와 제한 |

## 자체 리뷰와 수정

범위 탐색·그룹별 Version·설정에 따른 이름 해독·세션 제어 제외·정확한 이진 길이·정수 시각/카운터·제한·출처/출력 결합을 검토했습니다. 제어 이름 비교를 대소문자 구분 없이 수정하고 정상 항목 길이 페이로드라도 제어는 불투명해야 한다는 회귀 검사를 추가했습니다. 잘못된 NoEncrypt에서는 암호를 추측하거나 제어 가능성이 있는 값의 지표를 노출하지 않습니다. 길이만으로 버전을 고르지 않고 과거 카운터를 묵시적으로 보정하거나 미지원 값을 버리지 않습니다. 미상 GUID는 앱 신원을 부여하지 않고 리터럴 식별자로 남기며 해독 이름을 열거나 확장하지 않습니다.

모든 기존 어댑터는 스키마 11을 사용하고 기존 필드 의미와 디코더 동작은 유지합니다. 원시 키/값 오프셋·키와 실행 시각 분리·부모 연결·반복/혼합 출처·SQLite 외래 키·엄격 모드 경고 종료·전체 단위 게시·입출력 보호를 검토했습니다. 원본 EnScript와 역사 데이터는 변경하지 않았습니다.

## 독립 비교와 검증 결과

합성 REGF 키/값 이름·형식·전체 원시 데이터·물리 오프셋을 python-registry 1.3.1과 비교하고 그 도구의 페이로드 오프셋이 셀 헤더보다 4바이트 뒤임을 반영했습니다. 명시적 고정 오프셋 언패킹으로 버전 3/5 DWORD와 FILETIME을 독립 확인했습니다. 체크아웃 밖에서 설치한 0.11.0 콘솔로 반복 출처 해시·JSON/SQLite 스키마 11·외래 키·입력 보존을 확인했습니다. Windows 의미나 실제 획득 NTUSER 데이터를 독립 인증하는 검증은 아닙니다.

EVTX를 포함한 전체 테스트 346개가 통과했습니다. EnScript 정적 회귀 11개·생성 소스 참조 4개·양언어 문서/링크/테스트 매핑·아카이브 검증도 통과했습니다. EnScript 13개와 원본 매니페스트는 기준과 동일하며 아카이브 트리/README와 재구성된 2017년 커밋 263개를 보존합니다. 정적 검사는 EnCase 컴파일이나 실행을 입증하지 않습니다.

## 남은 검증과 미지원 구조

Windows/GUID/버전/설정 변형별 실제 획득 NTUSER UserAssist·Windows/Linux 실행·Python 3.10·독립 실제 레코드 해석·대형 컬렉션·획득 경쟁은 미검증입니다. 미상 버전·베타 Vigenère/혼합 인코딩·깊은 범위·네이티브 REGF 제한은 미지원입니다. 더티 하이브 로그 재생·삭제/슬랙 복구·경로 확장·소유권/세션 추론·실행 성공 단정·아티팩트 간 결합을 하지 않습니다. 키 시각은 항목 실행 시각이 아니며 원시 카운터/포커스 필드는 검증된 빈도나 활성 사용 시간이 아닙니다. EnCase 컴파일/실행은 여전히 미검증입니다. 정확한 제한과 상태 우선순위는 CLI 문서를 참고하세요.
