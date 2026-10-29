# Windows 클라이언트·정식 브라우저 검증

**한국어** | [English](WORKBENCH_VENDOR_BROWSERS.md)

2026-10-28 · 브랜치 `codex/ui-workbench`; 패키지 0.15.0 / 보고서 스키마 15 유지.

## 결과와 명시적인 미완료 범위

커밋 `1058df858aa6706314ebcd609930af8eec1ba7e5`의 [정식 브라우저 워크플로](https://github.com/polynomeer/plaintrace/actions/runs/40610687294)는 7개 작업을 모두 통과했습니다. Chrome/Edge 6개 트랙에서 각각 9개(54개), 실제 Safari 9개로 총 63개입니다. 테스트 자동 재시도·스킵·실패·flaky 결과는 없습니다. [Python 호스트 워크플로](https://github.com/polynomeer/plaintrace/actions/runs/40610687356)도 6개 트랙(각 500개), 설치 CLI/UI 검사와 static-integrity를 모두 통과했습니다. 이는 측정한 환경의 결과이며 모든 Windows/브라우저 버전 검증은 아닙니다.

**Windows 10은 미검증입니다.** Windows 10 러너/VM이 연결되지 않았고 저장소 러너 목록은 비어 있으며 로컬 호스트는 macOS입니다. 사용자에게 Windows 10 환경을 요청했습니다. Server 2022·Windows 11·Wine/CrossOver·Windows 10 user-agent는 대체 증거가 아닙니다. [Windows 10 수동 게이트](../.github/workflows/windows10-browser.yml)는 준비했지만 실행하지 않았고 통과 결과도 없습니다. 따라서 요청한 Windows 10/11 전체 범위가 완료됐다고 주장하지 않습니다.

## 실제 실행 환경

[Playwright 설정](../playwright.config.mjs)은 관리형 Chromium의 이름을 바꾸지 않고 정식 `chrome`/`msedge` 채널을 사용합니다. Windows 11은 이미지에 사전 설치된 정식 브라우저를, macOS/Linux는 설치 시점의 정식 stable 패키지를 사용합니다. 아래 버전은 실행 중 측정했습니다. Windows 클라이언트는 user-agent와 별도로 Win32_OperatingSystem의 Caption·ProductType=1·빌드 >=22000을 확인했습니다. 두 Windows 11 작업 모두 Microsoft Windows 11 Enterprise / 10.0.26200 / ARM 64-bit Processor를 보고했습니다. Node ARM64로 브라우저 프로세스 아키텍처를 추정하거나 Windows x64 클라이언트를 검증했다고 하지 않습니다.

| 작업 | 실제 OS/커널/CPU | 브라우저 버전 | Node/Python | 이미지 빌드 | 결과 |
| --- | --- | --- | --- | --- | --- |
| [macos-14 / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198445) | darwin / 23.6.0 / arm64 | 156.0.8078.74 | v22.23.2 | 20260831.0302.1 | 9 pass / 4 PNG |
| [macos-14 / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198496) | darwin / 23.6.0 / arm64 | 156.0.4314.50 | v22.23.2 | 20260831.0302.1 | 9 pass / 4 PNG |
| [ubuntu-24.04 / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198395) | linux / 6.17.0-1022-azure / x64 | 156.0.8078.73 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [ubuntu-24.04 / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198629) | linux / 6.17.0-1022-azure / x64 | 156.0.4314.50 | v22.23.3 | 20261023.334.3 | 9 pass / 4 PNG |
| [windows-11-arm / chrome](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198821) | win32 / 10.0.26200 / arm64 | 156.0.8078.48 | v22.23.4 | 20261022.194.1 | 9 pass / 4 PNG |
| [windows-11-arm / msedge](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198328) | win32 / 10.0.26200 / arm64 | 156.0.4314.42 | v22.23.4 | 20261022.194.1 | 9 pass / 4 PNG |
| [macos-14 / Safari](https://github.com/polynomeer/plaintrace/actions/runs/40610687294/job/122561198172) | macOS-14.8.9-arm64-arm-64bit-Mach-O | 26.6 | Python 3.14.7 | 20260831.0302.1 | 9 pass / 2 PNG |

Safari는 `/usr/bin/safaridriver`로 실제 창을 실행하고 browserName=safari를 요청합니다. capabilities에 Safari 26.6·macOS 14.8.9·simulator=false를 기록합니다. Playwright WebKit이나 Safari Technology Preview가 아닌 설치된 Safari 앱입니다. Safari 자동화는 폐기되는 macOS CI 러너에서만 켭니다. 로컬 macOS 26.6.2/빌드 25G83의 Safari 26.6.2에서도 빈 작업대, 키보드 건너뛰기 링크, Escape/포커스 복귀와 네이티브 파일 선택으로 합성 보고서 열기를 확인했습니다. HTML·유니코드가 텍스트로 표시됐습니다. 수동 검토는 CI 검사 수와 별도이며 Safari 다운로드 바이트·반응형 검증을 의미하지 않습니다.

## 테스트 범위와 최초 실패

Chrome/Edge는 [브라우저 검증](WORKBENCH_BROWSER.ko.md)의 B-01–B-09를 재사용합니다. 네이티브 파일 선택, 잘못된 UTF-8/스키마 거부, 원본 다운로드 바이트, 소스/관측 페이지 이동, 화면 폭 6개, 테마/포커스/비우기와 외부 HTTP 요청·페이지 오류 부재를 확인합니다. 각 트랙은 라이트/다크·1440/390 스크린샷 4개를 만듭니다. 합성 데이터만 사용하며 생성 보고서/이미지는 Git 밖에 둡니다.

[Safari 검사](../tests/browser/safari_webdriver.py)는 표준 라이브러리 WebDriver 클라이언트와 설치된 격리 Python 서버를 사용합니다. 검증 범위는 의도적으로 별도이며 더 좁습니다.

| ID | Safari 검사 |
| --- | --- |
| S-01 | empty workspace |
| S-02 | native help modal |
| S-03 | demo source and record rendering |
| S-04 | source format filtering |
| S-05 | explicit-field timeline |
| S-06 | raw values and source references |
| S-07 | theme switching |
| S-08 | clear removes report DOM and raw cache |
| S-09 | no automatic report persistence |

Safari CI는 파일 업로드/다운로드·클립보드·화면 폭 에뮬레이션·네트워크/페이지 오류 계측·스크린리더 감사를 자동화하지 않습니다. 커밋 `889cced`의 [최초 Safari 실행](https://github.com/polynomeer/plaintrace/actions/runs/40610628667)은 Windows 형식 필터 뒤 이벤트 소스 선택이 유지됐는데 테스트가 방문 레코드를 가정해 S-06에서 실패했습니다. 수정 `1058df8`은 레코드를 열기 전 브라우저 소스를 명시적으로 선택하며 같은 원시 값 검사가 통과했습니다. 이는 테스트 준비 오류이며 실제 UI 결함으로 확인된 것은 아닙니다. 테스트를 통과시키려고 제품 코드를 변경하지 않았고 기존 포커스/비우기/표 수정은 계속 검사합니다.

## 보관 기록

결과 JSON의 정확한 커밋/실행·9개 통과·0 스킵/flaky/예상 밖 결과를 확인했습니다. Windows 판정 해시는 클라이언트 OS 기록을 식별하며 Safari 결과에는 capabilities·스크린샷 해시가 포함됩니다. 대표 스크린샷에서 글자/아이콘·테마·선택 소스 배치를 검토했습니다. 전체 픽셀 비교나 접근성 감사는 아닙니다. 원시 기록·trace·다운로드·이미지는 Git 밖에 둡니다. 아티팩트는 14일 뒤 만료되며 아래 다이제스트가 영구 증거 보관을 의미하지 않습니다.

| 작업 | 결과 JSON SHA-256 | Windows 클라이언트 판정 SHA-256 |
| --- | --- | --- |
| macos-14 / chrome | 0cd3c6b9607d480654b53feb91e129ab9bbcceedce52aa0eacdbe7727cd0578a | — |
| macos-14 / msedge | ede80323928bfb867a90522c435c8effeb3d9955d9a50bdb6f8a3e21f797bac2 | — |
| ubuntu-24.04 / chrome | 56abbdf2c0d85b883f686927d3b5cde4ecbc71dbfe9f050bde51b097f556c32d | — |
| ubuntu-24.04 / msedge | f7756e40eac95d418a4dba668242596bb395455c0dd0ca96a294a7fe0a8177a8 | — |
| windows-11-arm / chrome | 704751c9c790925dc070cb4dd0d311c951a618eb4069ad034014ca88b7eaf98a | f82127403f99a7ed60098f4d0b3d42f23cac69223d92a03285165385f0dac676 |
| windows-11-arm / msedge | 738f72a16715d692a23302a5124733532c591d9ea0f5da33211a13f6bc620212 | f82127403f99a7ed60098f4d0b3d42f23cac69223d92a03285165385f0dac676 |
| macos-14 / Safari | 09f7198d722573264661a0ed1a146cc3002bbdbefba2867c690ce466fc1b691f | — |

## Windows 10 사전 조건과 남은 작업

수동 게이트는 소유자가 제공하는 전용 Windows 10 x64 러너, `plaintrace-windows10` 라벨, Node/Python 설치 접근과 사전 설치된 정식 Chrome/Edge가 필요합니다. Server와 19041–21999 밖 빌드는 거부하고 임시 가상 환경에 Plaintrace를 설치하며 호스트 브라우저를 교체하지 않습니다. 준비된 절차이지 검증 결과가 아닙니다. 구형 Windows 10 빌드와 다른 아키텍처는 별도 범위입니다. 적합한 러너가 연결되기 전에는 실행하지 않습니다. GitHub workflow_dispatch는 저장소 기본 브랜치에 워크플로가 등록돼야 하며 이번 기능 브랜치 커밋으로 master 병합이나 러너 등록을 승인한 것은 아닙니다. 승인된 Windows 10 호스트에서 OS 신원을 확인한 뒤 아래 명령을 직접 실행할 수도 있습니다.

```sh
python -m pip install .
npm ci
npm run test:browser -- --project=chrome
npm run test:browser -- --project=msedge
```

생성 결과는 체크아웃 밖에 두고 OS/클라이언트 판정·정확한 브라우저 버전·채널별 테스트 9개 결과를 보관합니다. 해당 기록이 생기기 전에는 Windows 10을 검증 완료 상태로 올릴 수 없습니다.

## 참고 문서와 도구

러너 가용성은 공식 [호스팅 러너 참조](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)와 [Windows 11 이미지](https://github.com/actions/runner-images/blob/main/images/windows/Windows11-Arm64-Readme.md)에서 확인했습니다. 정식 채널은 [Playwright 안내](https://playwright.dev/docs/browsers), Safari는 [Apple WebDriver 안내](https://developer.apple.com/documentation/webkit/testing-with-webdriver-in-safari)를 따릅니다. 로컬 actionlint 1.7.7은 Windows 11 호스팅 라벨보다 오래돼 [lint 설정](../.github/actionlint.yaml)에 해당 라벨과 수동 Windows 10 라벨을 명시했습니다. lint 라벨은 러너 등록이나 지원 검증이 아닙니다. 이 설정으로 모든 워크플로가 lint를 통과합니다. EnScript/보관 참조·재구성 역사는 보존하며 EnCase 또는 획득 증거 정확도에 대한 새 주장은 없습니다.

Windows 10 VM 준비 상태와 남은 실행 검증은 [VM 기록](WINDOWS10_VM.ko.md)에서 관리합니다.
