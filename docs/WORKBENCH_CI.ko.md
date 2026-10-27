# 작업대 호스팅 CI 검증

**한국어** | [English](WORKBENCH_CI.md)

2026-10-27 · 브랜치 `codex/ui-workbench`; 패키지 0.15.0 / 보고서 스키마 15 유지.

## 결과와 검증 리비전

커밋 `2061db68a08891418790d3ee7cbd14af0ebef020`의 [6개 호스트 워크플로](https://github.com/polynomeer/plaintrace/actions/runs/40513174605)에서 Python 6개 트랙과 static-integrity가 모두 통과했습니다. 각 트랙은 python-evtx 0.8.1/hexdump 3.3으로 테스트 500개를 실행했고 스킵·실패·오류·예상 실패가 없었습니다. 설치된 CLI 스모크와 새 작업대 설치 게이트도 모두 통과했습니다. 같은 커밋의 [모델 워크플로](https://github.com/polynomeer/plaintrace/actions/runs/40513184693)는 Node 22.23.3에서 12개를 스킵·실패 없이 통과했습니다. 이는 합성 데이터와 패키지/서버 검증이며 실제 획득 증거의 정확도, 브라우저 렌더링 또는 모든 OS 버전 검증은 아닙니다.

| CI 트랙 | 실제 Python / SQLite | 실제 OS / CPU | 이미지 빌드 | 결과 |
| --- | --- | --- | --- | --- |
| [macos-14 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903928) | 3.10.11 / 3.40.1 | macOS 14.8.9 / arm64 | 20260831.0302.1 | 500 / CLI / UI pass |
| [macos-14 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903907) | 3.14.7 / 3.50.4 | macOS 14.8.9 / arm64 | 20260831.0302.1 | 500 / CLI / UI pass |
| [ubuntu-24.04 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903941) | 3.10.22 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 20261023.334.3 | 500 / CLI / UI pass |
| [ubuntu-24.04 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219904158) | 3.14.8 / 3.45.1 | Ubuntu 24.04 / 6.17.0-1022-azure / x86_64 | 20261023.334.3 | 500 / CLI / UI pass |
| [windows-2022 / 3.10](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903961) | 3.10.11 / 3.40.1 | Windows Server 2022 / 10.0.20348 / AMD64 | 20261022.344.1 | 500 / CLI / UI pass |
| [windows-2022 / 3.14](https://github.com/polynomeer/plaintrace/actions/runs/40513174605/job/122219903898) | 3.14.9 / 3.50.4 | Windows Server 2022 / 10.0.20348 / AMD64 | 20261022.344.1 | 500 / CLI / UI pass |

Windows Python 3.10의 platform.release는 10으로 표시됩니다. 실제 호스트는 Server 2022 이미지/빌드이며 Windows 10 클라이언트 지원을 의미하지 않습니다. [support.json](../compatibility/support.json)의 원래 M0 검증은 역사적 기록으로 보존합니다. 이번 UI 실행으로 이전 커밋의 결과를 덮어쓰거나 지원 OS 버전을 확장하지 않습니다.

## 변경과 실패 검토

최초 UI 커밋 `66830db58f35d8963eeb025df35f735ff5f398d1`을 푸시했고 [모델 실행](https://github.com/polynomeer/plaintrace/actions/runs/40512909841)이 통과했습니다. 검토 중 기존 설치 CLI 스모크는 Python 모듈만 비교하고 패키지 웹 자산을 실행하지 않는 검증 공백을 확인했습니다. 커밋 `2061db6`에서 모든 Python 트랙에 [verify_workbench_install.py](../tools/verify_workbench_install.py)를 추가했습니다. 체크아웃 밖 격리 가져오기, 모든 wheel 자산 바이트, 콘솔/모듈 도움말, 루프백 HTTP 경로 30개의 내용·MIME·CSP를 확인합니다. 검증 공백을 보완한 것이며 최종 실행에서 파서/UI 실패 수정, 호스트별 스킵 또는 실패 면제는 필요하지 않았습니다.

[호스트 워크플로](../.github/workflows/portability.yml)와 [모델 워크플로](../.github/workflows/ui.yml)는 로컬 actionlint를 통과했습니다. 로컬 strict 전체 테스트도 500개 통과했고, 확장 푸시 전 Python 3.10.22에서 설치 작업대 게이트가 통과했습니다. archive-only 검증은 EnScript 13개와 합성 역사 커밋 263개를 보존했습니다. 정적 CI는 문서/소스 참조, EnScript 계약과 기준 소스/매니페스트 보존을 확인했습니다.

## 보관한 결과 다이제스트

다운로드한 suite 기록의 정확한 커밋/실행, 테스트 500개와 빈 실패/스킵 목록을 확인했습니다. 기록된 Python 소스 다이제스트는 Windows 체크아웃 CRLF를 고려해 검증 커밋과 모두 일치했습니다. 트랙별 CLI/UI 설치 기록은 같은 wheel 다이제스트를 참조합니다. 생성된 원시 결과 JSON·로그·wheel은 Git 밖에 두고 검토한 SHA-256 요약만 표에 기록합니다. Actions 아티팩트는 14일 뒤 만료되며 영구 증거 보관 또는 재현 가능한 빌드 보장은 아닙니다.

| CI 트랙 | Suite 기록 SHA-256 | CLI 스모크 기록 SHA-256 | UI 스모크 기록 SHA-256 | Wheel SHA-256 |
| --- | --- | --- | --- | --- |
| macos-14 / 3.10 | bd59aeff8387123b61ae31300dd6d78cd43fb7d7a0e2d563153c88276d8ee94a | a83b5e812b68279a28acb59462a19adadf9a6668bbd1ed8b5051ed8fc52700a0 | 071438231e693db81b98a5960f576e2ac13b162e71d3e2e6f8aed37b7a4ec6c2 | e83eb3573b6959ed51c444f1bfa78898f9638918ea089457632fa1b1bf87e118 |
| macos-14 / 3.14 | fe2847e07b5b71c2c14aa760137d145b077092623963715ce412f3f31a232688 | 8631ba07bf4fb38af1109bd3fa11dcaeb47f173aca899e6cdece59967e3e531a | 9e0d1a6e05f5828eedcd16c8a6a8b5b84a5c93ddd9aa95ab0ccfa8b42e96157c | 33d2ec78cfc649a3968050f3aca5c8f74b2f51db56b8a70925eca394cae18bb6 |
| ubuntu-24.04 / 3.10 | af5cc9e9b676297e31e0a29bb2664adaa374c4652140e036f99a2465a0349c05 | 164c4e26631606df017fca5a77d8963bd6311cf9ca0b9fbce37f0d6bd63f4f2e | 48dd1fba47930608f7436b54c0880ea9121f5bbff3f17cf59e03882c23bc1f9e | 8954b1dab94bbf76d3369d20fb8422de9a6cd17cf9b0fe0e3776c2fbaf5c8a14 |
| ubuntu-24.04 / 3.14 | 2877f810b1f158adbe2df17cd4e10509c1846667a86abe76d8f51e53fbaf2dc8 | 6bf9931c49f4e3c5aeb75f536eeaf679a2f7efcc09c1579d4f69b499696b175b | f211a3218276d5c08e8a7bddf048204a191d9e40867e79d56517aeeed82df820 | 182fbe155439a501c53717c8314bfc6446467a94c19b805b8bc5258986b02b11 |
| windows-2022 / 3.10 | 94a18224663e41ca28dc82b4c19609758a98483a55fc50d2f4c6de082ad5cd54 | 16e6e49679b5894a537411eafd092cfbcdb9af7d2d234c920b4cecfda3992cd2 | 497ef0e3f762ff979c81e832a6b0386cc0f4d0cb765cddf4da72eaae43239508 | 3d832a22d6c751cef57084b7b0b549f72d9f6a33b6efb3d1ea9be0b5c786b6aa |
| windows-2022 / 3.14 | 4683f25d8f2318e09127c2260f43cf64739821ae47139c222237959169d4e109 | d901d5126046315cab94c887c4330b996c05301e88f3d9e38379c08f1f59fb00 | 6970c7614cebbaa27d0f83c0fe1eced525c37825579a979fc70d4a1864f5f728 | 3c2f9cfca2aa0b084776349664db88ccb5ee88296c28fbb0407761019c935f24 |

## 재현과 한계

[작업대 테스트](WORKBENCH_TESTS.ko.md)와 [M0 기준선](M0_BASELINE.ko.md)의 명령을 사용합니다. CI는 기존 smoke 결과 옆에 `workbench.json`을 쓰고 각 `portability-<runner>-py<minor>` 아티팩트에 보관합니다. 브라우저 DOM/화면 동작, Safari/Firefox, 보조 기술, Windows/Linux UI 렌더링, Windows 클라이언트와 다른 OS 빌드/아키텍처는 별도 검증이 필요합니다. EnCase 컴파일/실행을 주장하지 않습니다. 후속 문서 커밋은 여기 명시한 검증 리비전을 설명하며 별도 CI를 실행합니다. 기록된 결과를 소급 변경하지 않습니다.
