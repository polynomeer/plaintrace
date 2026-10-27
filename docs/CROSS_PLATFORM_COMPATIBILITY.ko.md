# 호환성·버전 지원 정책

[English](CROSS_PLATFORM_COMPATIBILITY.md) | **한국어**

2026-10-27 · 향후 확장 설계. 구현·호환 인증 결과가 아닙니다. 현재 패키지 0.15.0 / 보고서 스키마 15는 변경하지 않습니다.

## 모든 버전의 의미

목표는 과거·현재·미래의 증거 포맷을 지속적으로 확장하는 것입니다. 런타임·CPU·보안 정책·미공개 레이아웃이 달라 모든 OS 릴리스에서의 직접 실행은 보장할 수 없습니다. 구형 OS에 Plaintrace를 설치하지 않아도 지원되는 현대 호스트에서 그 증거를 분석할 수 있습니다. 미래의 미확인 리비전에 검증 표시를 자동 상속하지 않습니다.

호환성은 호스트 OS/build + CPU + Python + 선택 의존성 + 입력 계열/리비전 + 출력 스키마 + 테스트 근거의 조합으로 기록합니다. 공급사 지원 수명과 Plaintrace 검증은 별도 축입니다.

## 분석 실행 환경 목표

| 호스트 계열 | 첫 검증 대상 | 추가 검증 트랙 | 현재 근거 |
| --- | --- | --- | --- |
| Windows | Windows 11 x86-64, build 명시 | Windows 10/Server·ARM64 각각 별도 검증 | 저장소 기록상 미검증 |
| macOS | macOS 14+ ARM64 중 선정 릴리스 각각 | Intel·구형 macOS 별도 러너 | macOS/Python 3.14 기록만 존재, 전체 버전·CPU 인증 없음 |
| Linux | Ubuntu 24.04 LTS x86-64, 이미지 고정 | Debian/Fedora·ARM64·musl 별도 | 저장소 기록상 미검증 |
| 구형 실행 환경 | 일괄 native 런타임 보장 없음 | 현대 호스트에서 내보낸 증거 분석 | 포맷별 검증 필요 |

이는 테스트 대상 제안이며 공급사 지원이나 완료된 테스트를 뜻하지 않습니다. 별도 호환성 결정까지 Python 3.10+ 선언을 유지합니다. 최소 버전과 지원 선언한 각 인터프리터 minor를 실행 검증하며 구형 증거 OS 실행만을 위해 수명 종료 런타임을 유지하지 않습니다. CPU별 wheel/native 의존성 제공 여부도 확인합니다.

## 증거 OS·포맷 확장 지도

| 증거 계열 | 현재 또는 계획된 포맷 범위 | 버전 식별 규칙 |
| --- | --- | --- |
| Windows NT 클라이언트·서버 | 기존 제한 REGF/LNK/Prefetch/EVTX/CFB·선택 메타데이터, 구형 EVT/IE·신규 레이아웃은 후속 | 헤더·리비전·스키마 판정, Windows 버전은 문맥 정보 |
| Windows 9x/DOS 시대 | 별도 미래 어댑터, REGF/EVTX 대체 해석 금지 | 개별 명세·검증된 포맷만 허용 |
| Mac OS X / OS X / macOS | XML/binary plist·시스템 메타데이터·선별 Safari SQLite 계획 | 컨테이너 시그니처·스키마·별도 획득 build 출처 |
| Classic Mac OS | 조사 백로그, macOS plist 지원에 포함하지 않음 | 별도 파일시스템·아티팩트 조사 |
| Linux 배포판 | os-release·passwd/group 메타데이터·journal export·선별 텍스트 로그 계획 | 배포판 설정·생성 프로그램 버전·포맷 기능 |
| 비 systemd Linux | 텍스트 로그·지원 앱 아티팩트 | journald 강제 또는 없는 boot ID 생성 금지 |
| OS 공통 브라우저 | 기존 Chromium/Firefox 스키마 파싱, Safari 계획 | 호스트·파일명 대신 앱 스키마 |
| 미래·미확인 릴리스 | 원시 출처와 명시적 미지원 진단 | 새 fixture·검토 후 승격 |

유한 표본으로 모든 패치·배포판·설정을 인증할 수 없습니다. 테스트 build·생성 프로그램 리비전·제외 범위를 공개합니다. 브라우저 앱 버전은 증거 OS와 독립적으로 바뀔 수 있습니다.

## 지원 상태와 등록부

세 필드를 구분합니다. 구현 성숙도는 계획·구현·부분·미지원, 호스트 검증은 미검증·검증·회귀, 증거 검증은 합성·획득·독립 비교로 기록합니다. 합성 테스트 통과로 획득 증거 검증 표시를 부여하지 않습니다. 파서는 구현됐어도 특정 호스트는 미검증일 수 있습니다.

향후 기계 판독 지원 등록부에는 어댑터 ID/버전, 정확한 포맷 판정 조건, 검증 호스트 조합, fixture 해시·라이선스, 기대 결과 해시, 명령·날짜·결과, 제약, 검토자를 기록합니다. 초기에는 기존 기록만 옮기고 모르는 값은 미상으로 둡니다. 필수 트랙이 예상 밖 skip 없이 통과하고 제외 범위를 공개해야 지원을 선언합니다. 회귀 시 해당 선언을 철회하고 신규 OS는 미검증에서 시작합니다.

## 외부 제약과 근거

2026-10-27 확인. Python 배포·런타임 요구사항은 달라질 수 있으므로 패키징 대상을 확정할 때 [CPython Windows 문서](https://docs.python.org/3/using/windows.html)를 확인합니다. 따라서 구형 증거 지원과 호스트 런타임 지원을 분리합니다.

[Microsoft Shell Link 명세](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943)는 리비전을 공개하므로 포맷별 판정을 적용합니다. [systemd journal export](https://systemd.io/JOURNAL_EXPORT_FORMATS/)는 중복·바이너리 필드를 허용하므로 순서 있는 값 보존을 요구합니다. Apple [파일 접근 안내](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox)는 사용자 Full Disk Access 부여를 설명합니다. 오프라인 코어가 보호된 호스트 자료를 직접 획득할 수 있다고 가정하지 않습니다. 이 근거는 설계 제약을 뒷받침하며 Plaintrace 검증 결과가 아닙니다.

## M0 구현 후속 기록

2026-10-27 M0의 지원 등록부·검증 도구·CI를 구현했습니다. [구현 계약](M0_BASELINE.ko.md)과 [실제 검증·남은 기준](M0_TESTS.ko.md)을 참조하세요. 지정 6개 트랙의 [원격 CI 결과](M0_CI.ko.md)로 M0 호스트 기준을 완료했습니다. 검증한 조합을 넘어 모든 OS 버전 지원을 선언하지 않습니다.
