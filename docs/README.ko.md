# 문서 산출물 목차

[English](README.md) | **한국어**

이 문서의 보존 구현 설명과 검토 결과는 개선 전 태그 `archive/pre-improvements-2026-10-13` 기준입니다. 현재 개선 브랜치의 변경 사항과 남은 검증 항목은 [개선 기록](IMPROVEMENTS.ko.md)을 확인하세요.

2026-10-13 보존된 소스를 기준으로 작성한 사후 문서입니다. 2017년 당시의 원본 산출물이 아닙니다.

## 읽는 순서

- 프로젝트 열람자: 개요 → 요구사항 → 아키텍처 → 결과 보고서.
- 분석자: 설치·사용 가이드 → 데이터 모델 → 검증 계획.
- 유지보수자: 코드 구조 → 상세 설계 → 스키마 참조 → 분석 → 유지보수.
- 아카이브 검토자: 재구성 히스토리 → 검증 보고서 → JSON 매니페스트.

## 산출물 목록

| 문서 | 내용 |
| --- | --- |
| [프로젝트 개요·출처](PROJECT_OVERVIEW.ko.md) | 목적·배경·범위·근거 |
| [요구사항·유스케이스](REQUIREMENTS.ko.md) | 기능·비기능 ID, 사용 흐름, 인수 경계 |
| [아키텍처](ARCHITECTURE.ko.md) | 컨텍스트·구성요소·배포 구조 |
| [시스템 상세 설계](SYSTEM_DESIGN.ko.md) | 선택·수명주기·인터페이스·타임라인 흐름 |
| [코드 구조](CODE_STRUCTURE.ko.md) | 전체 소스 클래스·추출 메서드 위치 |
| [데이터 모델](DATA_MODEL.ko.md) | 저장 경로·테이블·시각·계약 |
| [SQL 선언 참조](SCHEMA_REFERENCE.ko.md) | 소스 리터럴 정의·스키마 변형 |
| [설치·사용 가이드](USER_GUIDE.ko.md) | 사전 조건·모듈 흐름·문제 해결 |
| [검증·테스트 계획](TEST_PLAN.ko.md) | 케이스·기준값·향후 인수 기준 |
| [문서 검증 보고서](VERIFICATION.ko.md) | 수행 검사·검증 한계 |
| [유지보수·위험 목록](MAINTENANCE.ko.md) | 검토 우선순위·변경 원칙·후속 제안 |
| [프로젝트 결과 보고서](PROJECT_REPORT.ko.md) | 산출물 현황·검증 근거·인수인계 |
| [정적 분석](ANALYSIS.ko.md) | 기존 모듈 분석·소스 관찰 |
| [재구성 히스토리](HISTORY.ko.md) | 합성 날짜·재구성·백업 복구 |

## 문서 해석 기준

소스 관찰·작성자의 과거 설명·향후 제안을 구분합니다. 도표는 현존 코드를 설명하며 수행 표시가 없는 테스트는 계획입니다. 원래 EnCase 버전과 HTML/JS 자산은 미확인 또는 누락입니다. Windows 7·버전·날짜 도움말은 소스 근거이며 릴리스 인증이 아닙니다. 양 언어 문서는 기술 ID와 참조를 공유합니다.

기계 판독 기록: [커밋 맵](history-map.json), [소스 매니페스트](source-manifest.json). [프로젝트 README](../README.ko.md)로 돌아갑니다.

## Python 이식

[Python CLI](PYTHON_CLI.ko.md) · [Python tests](PYTHON_TESTS.ko.md)

[Python CLI 리뷰](PYTHON_REVIEW.ko.md)

[Execution CLI](EXECUTION_CLI.ko.md) · [Execution tests and review](EXECUTION_TESTS.ko.md)

[EVTX CLI](EVTX_CLI.ko.md) · [EVTX 테스트와 리뷰](EVTX_TESTS.ko.md)

[휴지통 CLI](RECYCLE_BIN_CLI.ko.md) · [테스트와 리뷰](RECYCLE_BIN_TESTS.ko.md)

[USB 레지스트리 CLI](USB_REGISTRY_CLI.ko.md) · [테스트와 리뷰](USB_REGISTRY_TESTS.ko.md)

[RecentDocs CLI](RECENT_DOCS_CLI.ko.md) · [테스트와 리뷰](RECENT_DOCS_TESTS.ko.md)

## 애플리케이션 MRU 확장

Office·HWP·Adobe MRU와 스키마 7을 패키지 0.7.0에서 추가했습니다.

[CLI](APPLICATION_MRU_CLI.ko.md) · [테스트와 리뷰](APPLICATION_MRU_TESTS.ko.md)

## Jump Lists 확장

패키지 0.8.0은 자동/사용자 지정 Jump Lists와 스키마 8을 추가합니다.

[CLI](JUMP_LISTS_CLI.ko.md) · [테스트와 리뷰](JUMP_LISTS_TESTS.ko.md)

## ShellBags 확장

패키지 0.9.0은 ShellBags 계층·Shell Item·참조 Bags 메타데이터와 스키마 9를 추가합니다.

[CLI](SHELLBAGS_CLI.ko.md) · [테스트와 리뷰](SHELLBAGS_TESTS.ko.md)

## 공통 파일 대화상자 MRU 확장

패키지 0.10.0은 OpenSavePidlMRU·LastVisitedPidlMRU와 스키마 10을 추가합니다.

[CLI](DIALOG_MRU_CLI.ko.md) · [테스트와 리뷰](DIALOG_MRU_TESTS.ko.md)

## UserAssist 확장

패키지 0.11.0은 획득 UserAssist 관측과 스키마 11을 추가합니다.

[CLI](USERASSIST_CLI.ko.md) · [테스트와 리뷰](USERASSIST_TESTS.ko.md)

## RunMRU 확장

패키지 0.12.0은 리터럴 실행 대화상자 MRU 문자열과 스키마 12를 추가합니다.

[CLI](RUN_MRU_CLI.ko.md) · [테스트와 리뷰](RUN_MRU_TESTS.ko.md)

## 탐색기 주소·검색 이력

패키지 0.13.0은 TypedPaths/WordWheelQuery 관측과 스키마 13을 추가합니다.

[CLI](EXPLORER_HISTORY_CLI.ko.md) · [테스트와 리뷰](EXPLORER_HISTORY_TESTS.ko.md)

## Windows 시스템 정보

패키지 0.14.0은 스키마 14와 획득 SOFTWARE/SYSTEM의 OS·이름·시간대·저장 시각 관측을 추가합니다.

[CLI](SYSTEM_INFO_CLI.ko.md) · [테스트와 리뷰](SYSTEM_INFO_TESTS.ko.md)

## SAM 계정 메타데이터

패키지 0.15.0은 획득 SAM 계정/이름 메타데이터와 스키마 15를 추가합니다.

[CLI](SAM_ACCOUNTS_CLI.ko.md) · [테스트와 리뷰](SAM_ACCOUNTS_TESTS.ko.md)

## 멀티 OS 확장 설계

2026-10-27 작성한 향후 확장 계획입니다. 현재 구현·검증 범위와 구분합니다.

[기획](CROSS_PLATFORM_PLAN.ko.md) · [호환성 정책](CROSS_PLATFORM_COMPATIBILITY.ko.md) · [아키텍처·데이터 계약](CROSS_PLATFORM_ARCHITECTURE.ko.md) · [로드맵·검증](CROSS_PLATFORM_ROADMAP.ko.md)

## M0 구현

지원 등록부·strict 검증 실행기·3개 OS CI와 Python 3.10 호환성 수정을 추가했습니다. 지정 CI 호스트 검증은 별도 완료 기준입니다.

[구현·재현 절차](M0_BASELINE.ko.md) · [테스트·검증 결과](M0_TESTS.ko.md)

[6개 트랙의 원격 CI 결과](M0_CI.ko.md)에서 검증 커밋·환경·수정 이력을 확인할 수 있습니다.

## 로컬 보고서 작업대

화면 디자인을 읽기 전용 JSON 보고서 작업대로 적용했습니다.

[실행·사용 가이드](WORKBENCH.ko.md) · [테스트·검증 범위](WORKBENCH_TESTS.ko.md)

- [작업대 호스팅 CI](WORKBENCH_CI.ko.md)

[Windows/Linux 브라우저 검증과 수정 기록](WORKBENCH_BROWSER.ko.md)
