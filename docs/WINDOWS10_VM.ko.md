# Windows 10 평가판 VM

[English](WINDOWS10_VM.md) | **한국어**

2026-10-29 · 환경 준비 기록. Windows 10 브라우저 검증은 아직 미완료입니다.

## 확인한 상태

macOS ARM64 호스트에서 QEMU 11.1.2로 실제 Microsoft Windows 10 Enterprise LTSC 2021 Evaluation x64 설치 미디어를 부팅하고 Windows Setup 화면을 확인했습니다. 설치 완료나 Chrome·Edge 통과를 의미하지 않습니다. Windows 약관 동의와 게스트 부트스트랩 실행은 아직 기록되지 않았습니다.

TCG 에뮬레이션, 메모리 8 GiB, 가상 CPU 4개, 희소 QCOW2 디스크 64 GiB를 사용합니다. NAT에 호스트 포트 포워딩이 없고 VNC·웹 콘솔은 루프백에만 연결합니다. 호스트 공유 폴더와 물리 디스크 연결은 없습니다. ISO·디스크·도구·결과는 Git 밖의 전용 VM 폴더에 둡니다. 이 환경은 네이티브 성능이나 모든 Windows 10 버전의 지원을 입증하지 않습니다.

## 설치 미디어

공식 en-US x64 평가판 ISO는 빌드 19044.1288이며 크기는 4,898,582,528바이트입니다. Microsoft 공식 문서와 SHA-256이 일치합니다.

`E4AB2E3535BE5748252A8D5D57539A6E59BE8D6726345EE10E7AFD2CB89FEFB5`

공식 다운로드·해시 링크와 전체 명령 옵션은 [영문 재현 절차](WINDOWS10_VM.md)에 있습니다.

## 재현 절차

1. [VM 도구](../tools/windows10_vm.py)의 `create --directory <external-directory> --iso <ISO>`로 저장소 밖에 VM을 만듭니다. 기존 파일 덮어쓰기를 거부하고 ISO 해시를 검증합니다.
2. [페이로드 도구](../tools/prepare_windows10_payload.py)에 공식 Python 3.14.8 amd64 설치 파일, Node 22.23.4 win-x64 ZIP과 공식 SHASUMS256.txt를 `--directory`, `--python-installer`, `--node-archive`, `--node-shasums`로 전달합니다. 커밋된 HEAD만 내보내며 Node 해시를 확인합니다. Python 서명은 게스트 실행 전 확인합니다.
3. 페이로드를 읽기 전용 ISO로 만들고 VM 도구의 `run --directory <external-directory> --display cocoa --tools-iso <tools.iso>`로 부팅합니다. `--display vnc` 대안과 [콘솔 템플릿](../tools/windows10_vm_console.html)은 로컬 전용입니다. 템플릿 옆에 `node_modules/@novnc/novnc/core/rfb.js`가 필요합니다.
4. 설치 중 실제 평가판 약관을 확인·동의한 뒤 설치를 완료합니다. 무인 약관 수락·인증 우회·시간 조작은 제공하지 않습니다.
5. 게스트에서 [부트스트랩](../tools/windows10_guest_bootstrap.ps1)을 실행합니다. Windows 10 클라이언트 빌드와 QEMU 제조사를 검사하고 전용 작업 폴더, 실제 Chrome·Edge 채널과 브라우저별 기존 9개 시나리오를 실행합니다. 이 스크립트는 아직 Windows에서 실행 검증되지 않았습니다.
6. 정확한 OS·브라우저 버전, 소스 커밋, 결과와 스크린샷을 Git 밖에 보존하고 실패를 수정·재검증한 뒤 [브라우저 검증 기록](WORKBENCH_VENDOR_BROWSERS.ko.md)을 갱신합니다. 초기 페이로드는 `566c0e3b2c2f119638c0443d3e10213516bdc8f3` 기준이며 이후 변경은 새 커밋에서 다시 생성해야 합니다.

## 남은 검증

Windows 설치, 평가판 약관 확인, Chrome·Edge 실행과 문제 수정, 최종 호스트 검증이 남았습니다. 로컬 준비 검사 결과를 Windows 실행 결과로 계산하지 않습니다. [수동 Windows 10 CI](../.github/workflows/windows10-browser.yml)에는 조건에 맞는 자체 호스팅 러너 등록이 별도로 필요하며 VM 도구가 자동 등록하지 않습니다.

## 로컬 준비 검증

2026-10-29 macOS/Python 3.14.8 환경에서 EVTX 추가 의존성을 포함한 Python 500개 테스트, 건너뛰기 없는 엄격한 전체 게이트, Node 모델 테스트 12개, 지원 목록 검사, Python 도구 구문 검사와 아카이브 무결성 검사(소스 13개·재구성 커밋 263개)가 통과했습니다. 첫 샌드박스 실행은 루프백 소켓 바인딩 권한 때문에 실패했으며 필요한 호스트 권한으로 재실행하여 통과했습니다. 문서 검사에서 발견한 한·영 구조 차이도 수정했습니다. 이는 게스트 부트스트랩 실행이나 Windows 10 브라우저 통과를 의미하지 않습니다.
