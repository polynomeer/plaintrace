# M0 원격 CI 검증 결과

[English](M0_CI.md) | **한국어**

2026-10-27 · 검증한 실행·커밋과 실제 환경을 기준으로 한 결과입니다.

## 결과·검증 범위

[검증 실행](https://github.com/polynomeer/plaintrace/actions/runs/40446197093)의 호스트 6개 트랙과 정적 무결성 job이 모두 통과했습니다. 검증 커밋은 a8943e4fc58e6b7924bb20a9eea7e6d2542e8a60이며 각 트랙은 EVTX extra를 포함한 489개 테스트를 skip·실패·오류 없이 수행하고 설치 wheel 검사도 통과했습니다. 이는 지정 환경의 M0 완료 근거이며 모든 OS 버전이나 실제 획득 증거의 정확성을 인증하지 않습니다.

| CI 트랙 | 실제 Python / SQLite | 실제 OS·CPU | 결과 |
| --- | --- | --- | --- |
| [windows-2022 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963992) | 3.10.11 / 3.40.1 | Windows Server 2022 / 10.0.20348 / AMD64 | 489 통과, 설치 통과 |
| [windows-2022 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997964093) | 3.14.9 / 3.50.4 | Windows Server 2022 / 10.0.20348 / AMD64 | 489 통과, 설치 통과 |
| [macos-14 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963902) | 3.10.11 / 3.40.1 | macOS 14.8.9 / arm64 | 489 통과, 설치 통과 |
| [macos-14 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963993) | 3.14.7 / 3.50.4 | macOS 14.8.9 / arm64 | 489 통과, 설치 통과 |
| [ubuntu-24.04 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997964000) | 3.10.22 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 489 통과, 설치 통과 |
| [ubuntu-24.04 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40446197093/job/121997963936) | 3.14.8 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 489 통과, 설치 통과 |

macOS 이미지·Windows Server build·CPU와 Python patch 버전은 실측값입니다. Python 3.10의 Windows platform.release 값이 10이어도 Windows 10 클라이언트를 검증한 것은 아니며 러너와 실제 build는 Server 2022입니다. Windows 11·다른 배포판·다른 CPU·구형/미래 버전은 별도 검증이 필요합니다.

## 최초 실패·수정·재검증

첫 커밋 f823c64의 [실행](https://github.com/polynomeer/plaintrace/actions/runs/40446042052)은 job 생성 전에 workflow 검증 오류로 실패했습니다. job 수준 env에서 runner.temp 문맥을 참조한 것이 원인이었습니다. YAML 파싱만으로는 이 제약을 검출하지 못합니다.

수정 커밋 a8943e4는 RUNNER_TEMP·GITHUB_WORKSPACE 기본 환경변수로 경로를 읽습니다. actionlint 1.7.7로 원본 오류를 재현했고 수정 workflow의 의미 검사가 통과했습니다. 해당 [재실행](https://github.com/polynomeer/plaintrace/actions/runs/40446197093)은 6개 트랙에서 각각 489개 테스트와 설치 검사를 통과했습니다. Windows 전용 파서 수정이나 skip·실패 면제는 필요하지 않았습니다.

등록부가 검증 표시를 부여할 때 두 Python minor·일치하는 OS/러너·정확한 커밋·실행 URL·skip 없는 결과가 모두 필요하도록 검사를 보강했습니다. 관련 회귀 2개를 추가해 전체 테스트가 491개가 됐습니다. 본 문서 첫 표는 링크된 실행에서 실제 수행한 개수를 표시합니다.

## 기록 보존·재현성

기계 판독 [지원 등록부](../compatibility/support.json)에 6개 호스팅 검증 조합, 이미지 build, 의존성 버전, job URL, source/configuration/wheel/result/artifact 해시를 보존했습니다. 각 호스트는 검증 조합 2개를 참조합니다. [로컬 결과](M0_TESTS.ko.md)는 당시 기록으로 유지하고 호스팅 결과와 혼동하지 않습니다.

Windows checkout의 Python 파일은 CRLF이므로 원시 소스 해시는 Unix 호스트와 다를 수 있습니다. 첫 성공 실행에서 모든 Python 파일의 Windows 해시를 커밋 내용의 CRLF 표현과 비교해 일치를 확인했습니다. 해시를 같게 만들기 위한 인코딩 변환은 하지 않았으며 EnScript 바이트·BOM·CRLF는 보존했습니다. wheel 해시도 빌드 메타데이터 때문에 트랙별로 다를 수 있어 각 설치본을 해당 wheel과 비교했습니다.

원시 로그·result JSON·wheel·캐시는 Git 밖에 두고 검토한 요약과 해시만 커밋합니다. Actions artifact는 14일 후 만료되므로 영구 증거 보관이나 바이트 단위 재현 빌드를 주장하지 않습니다. 문서·정적 검사와 원본 소스·매니페스트 비교는 별도 정적 job에서 통과했으며, 로컬 archive-only 검사는 263개 합성 역사 커밋 보존을 확인합니다. EnCase 실행·컴파일 인증은 아닙니다.

## 문맥 규칙 근거

2026-10-27 [GitHub 문맥 가용성 표](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)를 확인했습니다. job env에는 runner 문맥이 없고 step env/run에는 허용됩니다. 이 근거와 actionlint 검사를 함께 사용해 오류를 수정했습니다.
