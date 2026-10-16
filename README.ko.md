# Plain View of Multi Artifacts (PVMA)

[English](README.md) | **한국어**

이 문서의 보존 구현 설명과 검토 결과는 개선 전 태그 `archive/pre-improvements-2026-10-13` 기준입니다. 현재 개선 브랜치의 변경 사항과 남은 검증 항목은 [개선 기록](docs/IMPROVEMENTS.ko.md)을 확인하세요.

Windows의 여러 디지털포렌식 아티팩트를 수집·분석하고, 시간 흐름에 따라 사용자의 행위를 살펴보기 위해 개발한 **EnCase용 EnScript 플러그인**입니다. 현재 저장소 이름은 `plaintrace`이며, 프로젝트의 원래 이름은 **Plain View of Multi Artifacts**입니다.

## 개발 배경

대학교 학부 재학 중 **차세대보안리더양성프로그램(Best of the Best, BoB) 디지털포렌식 트랙**의 프로젝트로 **2017년 7월부터 11월까지** 개발했습니다. 서로 다른 Windows 아티팩트를 하나의 인터페이스에서 조회하고 타임라인으로 연결해, 사용자 행위 분석을 돕는 것을 목표로 했습니다.

당시 작업에는 UI 개발과 EnScript를 이용한 Windows 아티팩트 추출·파싱이 포함됩니다. 사용 기술과 도구는 EnCase, EnScript, SQLite, JavaScript, StarUML입니다. 기존 프로젝트 소개에는 에이콘 출판사 집필 계약, 그랑프리 도전 자격, 더존비즈온 초청 발표가 성과로 기록되어 있습니다.

## 주요 기능

| 영역 | 기능 |
| --- | --- |
| 시스템·계정 | 운영체제·볼륨·컴퓨터 정보, 사용자 계정과 로그인 관련 정보 조회 |
| 파일 | 일반·숨김·삭제 파일의 메타데이터, 휴지통의 삭제 시각과 원래 경로 분석 |
| 실행·파일 사용 흔적 | Prefetch 실행 흔적과 LNK 대상 경로·시각 등을 추출 |
| 최근 문서 | Office, HWP, Adobe 등의 최근 문서 기록과 LNK 대조 |
| 로그인·전원 | 이벤트 로그 기반 로그인·로그오프 및 전원 켜짐·꺼짐 기록 분석 |
| USB | 레지스트리와 이벤트 로그 기반 장치 식별·연결 흔적 분석 |
| 웹 | Chrome·Firefox·Opera·Internet Explorer의 방문·검색어·다운로드 기록 분석 |
| 조회·내보내기 | 탭별 목록, 검색, 일부 빈도 차트, 북마크, CSV·SQLite 내보내기 |
| 타임라인 | 여러 아티팩트를 SQLite에 통합하고 외부 HTML 시각화를 실행하는 연계 기능 |

## 실행 환경

- **Windows와 EnCase의 EnScript 실행 환경**이 필요합니다. 독립 실행 프로그램이 아니며 EnCase의 케이스·파일·레지스트리·이벤트 로그 API에 의존합니다.
- 진입 파일은 [`Plain View of Multi Artifacts.EnScript`](<Plain View of Multi Artifacts.EnScript>)입니다. 나머지 12개 `Win_*.EnScript` 모듈을 함께 배치하고, EnCase에서 Windows 증거가 포함된 케이스를 대상으로 실행하도록 작성되어 있습니다.
- 정확한 EnCase 버전, SDK, 테스트 증거와 빌드 설정은 이 저장소에 포함되어 있지 않습니다. 현재 환경에서의 호환성과 실행 결과는 별도 검증이 필요합니다.
- 소스에는 `C:\` 아래의 데이터베이스·브라우저·HTML 경로가 고정되어 있습니다. 실행 전 실제 환경과 경로를 확인해야 합니다.
- **웹 타임라인의 HTML/JavaScript 자산은 현재 저장소에 없습니다.** 이 소스만으로 당시의 시각화 기능 전체를 실행할 수는 없습니다.

이 저장소는 당시 남아 있는 소스를 보존하는 아카이브입니다. Windows 버전별 아티팩트 포맷 차이와 기존 구현의 제약은 [정적 분석 문서](docs/ANALYSIS.ko.md)에 정리되어 있습니다.

## 커밋 히스토리 안내

**2017년 7–11월 날짜의 커밋은 실제 당시 Git 기록이 아니라, 2026년 10월에 최종 소스를 기준으로 만든 기록용 사후 재구성입니다.**

코드를 클래스·메서드 단위의 263개 커밋으로 나누었으며, 날짜·작업 순서·간격은 임의로 배치했습니다. 모든 재구성 커밋에는 `archive:` 제목과 재구성 사실을 알리는 본문이 있습니다. 이 기록은 실제 개발 일정이나 개인별 기여를 입증하지 않으며, 각 중간 커밋의 실행 가능성을 보장하지 않습니다.

재구성의 마지막 소스 스냅샷은 기존 소스와 바이트 단위로 동일하게 보존했습니다. 이후 README 정리, Codex 환경 설정과 분석·검증 도구는 실제 작업 날짜의 후속 커밋으로 기록합니다.

- [재구성 방식과 원본 백업 안내](docs/HISTORY.ko.md)
- [커밋별 날짜·파일·작업 단위](docs/history-map.json)
- [원본 파일 크기·SHA-256](docs/source-manifest.json)

## 소스 살펴보기

EnScript 파일에는 UTF-8과 UTF-16LE가 혼재되어 있습니다. 원본 인코딩과 줄바꿈을 보존하면서 읽으려면 Python 3 도구를 사용할 수 있습니다.

```sh
python3 tools/inspect_sources.py
python3 tools/inspect_sources.py Win_TimeLine.EnScript --start 2006 --end 2120
python3 tools/verify_archive.py --archive-only
```

전체 아카이브 검증에는 재구성 작업 공간의 로컬 백업 ref가 필요합니다. [검증 사전 조건](docs/USER_GUIDE.ko.md)을 참조하세요.

검증 도구는 현재 EnScript 소스, 재구성 당시 README 스냅샷과 커밋의 무결성을 확인합니다. EnCase 컴파일이나 실행 검증을 수행하는 도구는 아닙니다.

## 문서 산출물

프로젝트 개요부터 요구사항, 아키텍처, 상세 설계, 코드·데이터 구조, 사용 가이드, 테스트 계획, 유지보수, 결과 보고서까지 [전체 문서 목차](docs/README.ko.md)에서 확인할 수 있습니다. 문서는 보존된 구현을 기준으로 현재 작성했으며 2017년 당시 원본 산출물이 아닙니다.

## 관련 기록

- [현재 GitHub 저장소](https://github.com/polynomeer/plaintrace)
- [기존 프로젝트 GitHub 주소](https://github.com/Polynomeer/PVMA)
- [당시 프로젝트 Trello 주소](https://trello.com/b/xIo5E0Ez/bobenscriptwork)

## Python CLI (2026)

독립 실행 가능한 Python 이식 버전으로 EnCase 없이 획득한 Chromium/Firefox SQLite의 방문, 검색어 후보와 다운로드를 분석합니다. 이 브랜치의 EnScript 파일과 아카이브는 변경하지 않습니다. [사용법과 구조](docs/PYTHON_CLI.ko.md), [실행 가능한 테스트 계획](docs/PYTHON_TESTS.ko.md)을 확인하세요. Python 테스트가 EnCase 런타임 정확성을 입증하지는 않습니다.

```sh
python3 -m plaintrace --input /path/to/History --browser chrome --output report.json
python3 -m unittest discover -s tests -v
```

## LNK와 Prefetch CLI

[사용법과 현재 스키마](docs/EXECUTION_CLI.ko.md) · [테스트와 리뷰](docs/EXECUTION_TESTS.ko.md)

## EVTX CLI

[설치, 이벤트 필드와 현재 스키마](docs/EVTX_CLI.ko.md) · [테스트와 리뷰](docs/EVTX_TESTS.ko.md)

## 휴지통 $I CLI

[사용법과 현재 스키마](docs/RECYCLE_BIN_CLI.ko.md) · [테스트와 리뷰](docs/RECYCLE_BIN_TESTS.ko.md)

## USB 레지스트리 CLI

[사용법과 현재 스키마](docs/USB_REGISTRY_CLI.ko.md) · [테스트와 리뷰](docs/USB_REGISTRY_TESTS.ko.md)

## RecentDocs CLI

[Explorer RecentDocs와 스키마 6](docs/RECENT_DOCS_CLI.ko.md) · [테스트와 리뷰](docs/RECENT_DOCS_TESTS.ko.md)

## 애플리케이션 MRU 확장

Office·HWP·Adobe MRU와 스키마 7을 패키지 0.7.0에서 추가했습니다.

[CLI](docs/APPLICATION_MRU_CLI.ko.md) · [테스트와 리뷰](docs/APPLICATION_MRU_TESTS.ko.md)

## Jump Lists 확장

패키지 0.8.0은 자동/사용자 지정 Jump Lists와 스키마 8을 추가합니다.

[CLI](docs/JUMP_LISTS_CLI.ko.md) · [테스트와 리뷰](docs/JUMP_LISTS_TESTS.ko.md)

## ShellBags 확장

패키지 0.9.0은 ShellBags 계층·Shell Item·참조 Bags 메타데이터와 스키마 9를 추가합니다.

[CLI](docs/SHELLBAGS_CLI.ko.md) · [테스트와 리뷰](docs/SHELLBAGS_TESTS.ko.md)

## 공통 파일 대화상자 MRU 확장

패키지 0.10.0은 OpenSavePidlMRU·LastVisitedPidlMRU와 스키마 10을 추가합니다.

[CLI](docs/DIALOG_MRU_CLI.ko.md) · [테스트와 리뷰](docs/DIALOG_MRU_TESTS.ko.md)
