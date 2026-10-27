# M0 테스트·검증 결과

[English](M0_TESTS.md) | **한국어**

2026-10-27 · M0 구현·검증 기록. 패키지 0.15.0 / 보고서 스키마 15 유지.

## 검증 방식·테스트 매핑

기존 475개·신규 브라우저/EVTX 회귀 2개·M0 gate 12개로 총 489개입니다. 합성 fixture를 사용하는 유지보수자 자체 검토이며 획득 증거나 독립 호스트 인증이 아닙니다. [구현 계약](M0_BASELINE.ko.md)에 strict gate·설치 wheel 검사를 설명합니다. 신규 gate 테스트는 아래에 매핑하고 브라우저·EVTX 추가 검사는 각 기존 테스트 문서에 매핑했습니다.

| ID | 테스트 메서드 | 검증 항목 |
| --- | --- | --- |
| M0-01 | test_current_registry_and_all_artifact_test_inventory | current registry and all artifact test inventory |
| M0-02 | test_duplicate_missing_and_escaping_references_rejected | duplicate missing and escaping references rejected |
| M0-03 | test_unimplemented_adapter_cannot_claim_synthetic_validation | unimplemented adapter cannot claim synthetic validation |
| M0-04 | test_tested_host_cannot_be_inferred_from_runner_label | tested host cannot be inferred from runner label |
| M0-05 | test_passing_result_claim_requires_zero_skips_and_installed_smoke | passing result claim requires zero skips and installed smoke |
| M0-06 | test_missing_inventory_and_reduced_baseline_rejected | missing inventory and reduced baseline rejected |
| M0-07 | test_package_python_schema_and_lane_drift_rejected | package python schema and lane drift rejected |
| M0-08 | test_skip_expected_failure_and_empty_suite_fail_qualification | skip expected failure and empty suite fail qualification |
| M0-09 | test_passing_suite_qualifies_but_error_and_failure_do_not | passing suite qualifies but error and failure do not |
| M0-10 | test_decoder_absent_or_wrong_version_fails_before_discovery | decoder absent or wrong version fails before discovery |
| M0-11 | test_generated_results_cannot_be_written_into_repository | generated results cannot be written into repository |
| M0-12 | test_environment_uses_allowlist_not_whole_environment | environment uses allowlist not whole environment |

## 최소 인터프리터의 실패·수정 기록

첫 Python 3.10.22/macOS 실행은 486개를 발견해 skip 없이 수행했으나 실패 7개·오류 29개였고 설치 브라우저 smoke도 실패했습니다. 원인은 SQLite URI 해석과 EVTX 소수초 파싱이었습니다. 수정 후 Python 3.10의 브라우저·EVTX 대상 검사가 통과했고 신규 회귀 검사는 읽기 전용 snapshot·정확한 원시 XML 시각 보존을 확인합니다. 아래 최종 전체 실행은 이후 추가한 gate 테스트도 포함합니다. 실패 로그는 Git 밖에 두고 이 요약에 부정 결과를 보존합니다.

## 최종 실행 결과

| 환경 | Python / SQLite | 전체 suite | 설치 wheel |
| --- | --- | --- | --- |
| macOS 26.6.2 / Darwin 25.6.0 / ARM64 | 3.10.22 / 3.53.1 | 489개 통과, skip·실패·오류 없음 | 통과 |
| macOS 26.6.2 / Darwin 25.6.0 / ARM64 | 3.14.8 / 3.53.4 | 489개 통과, skip·실패·오류 없음 | 통과 |
| Debian 13 / LinuxKit 6.10.14 / ARM64 컨테이너 | 3.14.10 / 3.46.1 | 489개 통과, skip·실패·오류 없음 | 통과 |

모든 최종 실행에 python-evtx 0.8.1·hexdump 3.3을 사용했습니다. macOS/Python 3.14.8에서 직접 unittest discovery 명령도 489개 모두 통과했습니다. 일반 unittest가 성공으로 취급하는 skip·expected failure도 gate에서는 검증 실패로 처리합니다. 소스·테스트·도구 해시는 세 환경에서 일치합니다. 테스트 입력의 의도치 않은 변경이나 실패 면제·호스트별 skip은 없었습니다.

setuptools 84.2.1로 만든 동일한 순수 Python wheel을 각 환경에 설치하고 설치 모듈 바이트를 wheel과 비교했습니다. smoke는 console·격리 module 진입점, 합성 Unicode·시각 해석, 스키마 15 JSON/SQLite 동등성, 소스 보존, 외래키, 덮어쓰기 방지를 검증했습니다. 모든 설치 아티팩트 어댑터를 인증하는 검사는 아니며 각 어댑터는 전체 소스 suite에서 검증합니다.

Linux는 네트워크를 끈 임시 Docker 컨테이너에서 실행했습니다. root·소스·wheelhouse는 읽기 전용이며 임시 파일시스템·별도 결과 mount만 쓰기를 허용했습니다. CPU·메모리·PID 한도를 적용했고 종료 후 컨테이너를 제거했습니다. 기록한 컨테이너 조합에만 해당하며 Ubuntu/x86-64·native Linux 호스트·Windows 동작을 인증하지 않습니다.

## 재현 정보·보존 근거

[지원 등록부](../compatibility/support.json)에 정확한 환경·결과·wheel/소스 매니페스트 해시·원시 결과 기록 해시를 보존합니다. 생성한 상세 로그·바이너리·export·가상환경·wheelhouse는 Git 밖에 둡니다. 소스 매니페스트 해시는 plaintrace·tests·tools의 Python 파일 경로와 SHA-256 값을 정렬한 compact JSON map의 해시입니다. 포렌식 증거 해시나 영구 golden 결과 bundle 해시가 아닙니다.

| 항목 | SHA-256 / 식별자 |
| --- | --- |
| Python source manifest | ce3fbaa2813fcf16078200b8b9176d6a78e7833c74a1286a48ea65f1d4225109 |
| Installed wheel | 99ed030f391b1c7681efc28fe6c00ebff6886b820225ef06b24fa20ed0a7117c |
| Docker image manifest | sha256:82abc9f53600280b0757126f83c5a7d47088592d2acb6b4c0b9e97f76865508c |


3개 호스트 CI workflow를 로컬에서 YAML로 파싱했고 공식 저장소에서 action SHA를 확인했습니다. GitHub에 dispatch하거나 실행하지 않았습니다. 각 트랙 실행 시 이미지 ID·의존 버전을 기록하며 변하는 러너 라벨을 불변 이미지라고 주장하지 않습니다.

## 무결성·남은 완료 기준

EnScript 정적 회귀 11개 통과, 생성 소스 참조 문서 4개 일치를 확인했습니다. archive-only 검증은 원본 소스 13개·보존 README·합성 역사 커밋 263개·원본 트리를 확인했습니다. 작업 EnScript·원본 매니페스트는 bb476180453c76f7d38e5b6a9f1f025ad2273ce0과 일치합니다. 최종 문서 검사도 110개 문서·1,608개 로컬 링크와 양언어 테스트 매핑을 포함해 통과했고 공백 검사도 통과했습니다. 이는 무결성·정적 결과이며 EnCase 컴파일·실행 검증이 아닙니다.

M0 호스트 인수는 지정 CI 6개 트랙 전체 실행을 기다립니다. Windows 11 클라이언트는 별도 실제 호스트 테스트 환경이 필요하며 Server 2022가 대신하지 않습니다. macOS 14·Ubuntu 24.04/x86-64·Windows·추가 Python minor·CPU·획득 버전 fixture·파일시스템 변형은 이번 작업에서 미검증입니다. Linux 컨테이너 통과로 지정 호스팅 트랙을 승격하지 않습니다. Apple/Linux 고유 파서·라이브 획득·이미지 리더·스키마 16·GUI backend는 추가하지 않았습니다.
