# M0 멀티 OS 검증 기반

[English](M0_BASELINE.md) | **한국어**

2026-10-27 · M0 구현·검증 기록. 패키지 0.15.0 / 보고서 스키마 15 유지.

## 구현 범위·단계 상태

M0는 감사 가능한 기준 목록·지원 등록부·6개 CI 트랙을 제공합니다. 선언된 최소 인터프리터 실행에서 찾은 호환성 결함 2개도 수정했습니다. 아티팩트 계열·CLI 플래그·출력 스키마·패키지 버전은 유지합니다. 미릴리스 0.15.0 수정본이므로 버전만이 아니라 소스·wheel 해시로 구분합니다.

구현은 준비됐지만 M0 완료 기준은 지정 호스팅 환경 실행을 기다립니다. 로컬 macOS 및 Debian ARM64 컨테이너 테스트는 설정된 macOS 14·Ubuntu 24.04·Windows Server 2022 러너를 인증하지 않으며 Server 검증도 Windows 11 클라이언트 검증을 대신하지 않습니다. M1–M6와 제안 GUI·스키마 16은 이번 범위에 포함하지 않습니다. [검증 결과·남은 기준](M0_TESTS.ko.md)을 참조하세요.

## 기계 판독 지원 등록부

[지원 등록부](../compatibility/support.json)는 구현됐지만 범위가 제한된 어댑터 17개와 계획 어댑터 4개를 목록화합니다. 구현 항목은 모듈·계약·CLI 입력·테스트 파일·포맷 조건·의존성·제외 범위를 연결합니다. 원래 테스트 475개를 모듈별 최소 기준으로 유지하고 신규 검사를 추가합니다. 이는 개발용 목록이며 M1 런타임 플러그인 탐색이나 모든 OS 버전 대응표가 아닙니다.

구현 성숙도·증거 검증·호스트 검증을 분리합니다. 기존 포맷은 합성 검증이며 macOS plist/Safari·Linux metadata/journal export는 계획·미검증입니다. 로컬 검증 조합에는 정확한 OS·kernel·CPU·Python·SQLite·의존성 버전과 검토한 문서 참조를 기록합니다. 러너 이름만으로 검증 상태를 부여할 수 없습니다.

fixture 생성기와 독립 기대값은 소스에 있습니다. 영구 바이너리 fixture·golden 결과 bundle은 없으므로 해당 해시는 null로 둡니다. 대신 생성기·테스트 소스 해시를 기록하고 코드 해시임을 구분합니다. 획득 증거·내보낸 결과·캐시는 커밋하지 않습니다. 구조 검사는 주장 간 일관성을 확인하며 검토자 인증이나 증거 검토를 대신하지 않습니다.

## 검증 도구

[portability.py](../tools/portability.py)는 개발 명령 3개를 제공합니다. validate는 누락·경로 이탈 참조, 중복 ID, 버전·스키마 불일치, 아티팩트 테스트 목록 누락, 근거 없는 검증 표시를 거부합니다. suite는 탐색 전 python-evtx 0.8.1을 요구하며 skip·expected failure·unexpected success·빈 탐색·실패·오류를 모두 실패로 처리합니다. 원래 아티팩트 모듈별 테스트 최소 개수를 유지해야 합니다.

smoke는 격리 Python으로 실행하며 checkout import를 거부하고 설치 모듈 바이트를 지정 wheel과 비교합니다. 임시 디렉터리에서 설치 console·격리 module 진입점을 실행합니다. 별도로 구성한 SQLite fixture로 Unicode·따옴표·개행, 정확한 시각 변환, 소스 해시·보존, JSON/SQLite 스키마 15 동등성, 외래키, 덮어쓰기 방지를 검사합니다. EVTX integration은 전체 suite에서 검증하며 smoke 입력은 브라우저만 사용합니다.

생성 기록에는 허용 목록의 환경 정보, 소스·설정 해시, 검사 결과를 포함하며 전체 환경변수를 출력하지 않습니다. 결과는 checkout 밖 새 디렉터리에 저장합니다. 개발 검증 기록이며 스키마 15 사건 보고서가 아닙니다. 이 도구는 사용자 증거를 획득하거나 처리하지 않습니다.

## CI 호스트 행렬·한계

[워크플로](../.github/workflows/portability.yml)는 Ubuntu 24.04·macOS 14·Windows Server 2022 각각에 Python 3.10/3.14를 배치합니다. wheel 빌드·EVTX extra 설치·의존성 검사·등록부 검사·strict 전체 suite·checkout 밖 설치 검증을 수행합니다. 각 트랙은 실패를 포함한 환경·결과 artifact를 14일 보관합니다. Actions는 공식 저장소 커밋 SHA로 고정하고 권한은 읽기 전용이며 비밀 값·배포가 필요하지 않습니다. 이번 로컬 작업에서 push나 호스팅 workflow 실행은 수행하지 않았습니다.

호스트 기본 셸에서 Python으로 wheel 탐색·subprocess 실행을 처리해 Windows에 Bash 경로 가정을 적용하지 않습니다. OS 버전 라벨도 이미지가 갱신되므로 실행 시 정확 build·CPU를 기록합니다. 인터프리터 minor 선택은 patch 버전을 해석하므로 고정이라고 주장하지 않고 실제 버전을 기록합니다. 격리 빌드는 setuptools·전이 의존성을 해석하며 완전한 lock이나 바이트 단위 재현 빌드를 주장하지 않습니다. 완전한 잠금·릴리스 재현성은 M6 작업입니다.

별도 Linux job은 EnScript 정적 계약·소스 참조·양언어 문서·기준 소스/매니페스트를 검사합니다. 원본 로컬 backup ref가 원격에 없으므로 전체 archive-only 검증은 로컬에서 수행합니다. CI가 이 ref를 만들어내지 않습니다. Windows symlink 기능 부재는 strict gate에서 조용히 skip하지 않으며 해당 트랙 실패 후 지원 범위를 명시적으로 결정해야 합니다.

러너 선택·설정 동작은 2026-10-27 공식 [runner images](https://github.com/actions/runner-images)·[setup-python 문서](https://github.com/actions/setup-python)로 확인했습니다. 이는 CI 동작 근거이며 Plaintrace 실행 결과가 아닙니다.

## 발견한 호환성 수정

SQLite snapshot 연결에서 읽기 전용 모드를 유지하며 URI 해석을 명시했습니다. 이전에는 기본 URI 해석이 없는 빌드에서 URI를 파일명으로 열려다 브라우저·혼합 입력 처리가 실패했습니다. 새 회귀 검사는 인코딩된 Unicode staging 경로, 읽기 전용 동작, 입력 바이트 보존을 확인합니다.

EVTX 표시 변환은 허용된 소수초를 여섯 자리로 채우거나 잘라 datetime에 전달해 Python 3.10과 이후 버전에서 같은 동작을 제공합니다. 원본 XML·정확한 envelope FILETIME·원시 SystemTime 텍스트는 유지합니다. UTC·명시 offset에서 소수초 1–7자리를 회귀 검증합니다. 신규 포맷·정밀도 주장·스키마 필드는 추가하지 않습니다.

## 재현 절차

대상 인터프리터의 격리 가상환경에서 저장소 루트를 기준으로 아래 공통 명령을 실행합니다. 결과·wheel 경로는 checkout 밖 예시이며 실행마다 새 결과 디렉터리를 선택합니다. 설치는 패키지 인덱스에 접근할 수 있고 파서 테스트는 임시 합성 데이터만 사용합니다. 컨테이너 오프라인 재현 시 wheelhouse를 먼저 준비하고 소스를 읽기 전용으로 연결한 뒤 결과 문서의 digest를 사용합니다.

```sh
python -m pip install ".[evtx]" build==1.6.1
python tools/portability.py validate
python -m unittest discover -s tests -v
python tools/portability.py suite --output ../plaintrace-validation/suite
python -m build --wheel --outdir ../plaintrace-validation/wheel
python -m pip install --force-reinstall --no-deps ../plaintrace-validation/wheel/plaintrace-0.15.0-py3-none-any.whl
python -I tools/portability.py smoke --wheel ../plaintrace-validation/wheel/plaintrace-0.15.0-py3-none-any.whl --output ../plaintrace-validation/smoke
python tools/verify_documentation.py
python tools/verify_archive.py --archive-only
git diff --check
```

아카이브 명령에는 원본 로컬 backup ref가 필요합니다. 소스 참조·정적 검사는 EnCase 컴파일·실행 검증과 별개입니다.
