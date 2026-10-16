# 휴지통 $I Python CLI

**한국어** | [English](RECYCLE_BIN_CLI.md)

현재 패키지는 0.10.0이며 모든 출력은 스키마 10입니다. 아래 이전 버전 도입/테스트 결과는 당시 기록이며 현재 계약은 [공통 대화상자 MRU 확장](DIALOG_MRU_CLI.ko.md)을 따릅니다.

2026-10-15 병합 커밋 `e0d0145cfb7b649c1713d66776ea140a43f891a3`을 기준으로 `codex/python-recycle-bin`에서 구현했습니다. EnScript 파일 13개와 과거 매니페스트는 기준 커밋과 바이트가 같습니다. 원본 아카이브 태그와 재구성된 2017년 커밋 263개를 보존합니다. 패키지 버전 `0.4.0`은 독립 Python 확장입니다.

## 실행과 설치

sqlite3이 있는 Python 3.10 이상을 선언하며 여기서는 macOS/Python 3.14로 검증합니다. 휴지통 파싱은 표준 라이브러리만 사용합니다. 선택 EVTX extra는 EVTX를 분석할 때만 필요합니다. 안정적으로 획득한 메타데이터 파일을 사용하고 여러 파일에는 `--recycle-bin`을 반복합니다. 이름을 바꾼 획득 파일도 명시적으로 입력할 수 있으며 디렉터리를 검색하거나 특정 파일명을 요구하지 않습니다. 달러 기호가 있는 경로는 셸에서 확장되지 않도록 따옴표로 감싸세요.

```sh
python3 -m plaintrace --recycle-bin '/path/to/$IABC123.txt' --output recycle.json
python3 -m plaintrace --recycle-bin '/path/to/$IFIRST' --recycle-bin '/path/to/$ISECOND' --format sqlite --output recycle.sqlite
python3 -m plaintrace --input /path/to/History --lnk /path/to/example.lnk --prefetch /path/to/APP.pf --recycle-bin '/path/to/$IABC123.txt' --strict
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/plaintrace --recycle-bin '/path/to/$IABC123.txt'
```

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\plaintrace.exe --recycle-bin 'C:\acquired\$IABC123.txt' --output recycle.json
```

`--input`, `--lnk`, `--prefetch`, `--evtx`, `--recycle-bin` 중 하나 이상이 필요합니다. 브라우저/LNK 옵션은 해당 입력 유형에만 적용합니다. JSON은 기본 stdout이며 SQLite는 `--output`이 필요합니다. 기존 독점 게시 계약으로 출력, 출처 경로와 예약 SQLite 사이드카 덮어쓰기를 방지합니다. 치명적 입력 오류는 게시 전에 전체 명령을 중단합니다. 경고는 diagnostics와 stderr에 포함하며 `--strict`는 보고서를 만든 뒤 경고가 있으면 1을 반환합니다. [공통 CLI 동작](PYTHON_CLI.ko.md)과 [EVTX 설치](EVTX_CLI.ko.md)를 확인하세요.

## 지원 레이아웃과 경계

리틀 엔디언 헤더에는 오프셋 0의 8바이트 형식 버전, 오프셋 8의 부호 없는 8바이트 원래 크기, 오프셋 16의 8바이트 삭제 FILETIME이 있습니다. 파일명이나 추정 Windows 릴리스가 아닌 내용의 버전으로 분기합니다.

| 버전 | 경로 레이아웃과 계약 |
| --- | --- |
| 1 | 오프셋 24: 260 코드 단위에 해당하는 완전한 520바이트 UTF-16LE 필드; 표준 전체 크기 544바이트 |
| 2 | 오프셋 24: 부호 없는 4바이트 코드 단위 개수; 오프셋 28: 개수 × 2 UTF-16LE 바이트; 개수에 종료 NUL 포함 |

두 레이아웃 모두 지원 경로 필드의 2바이트 경계에 NUL이 있어야 합니다. 버전 2 개수는 종료 문자를 포함하여 UTF-16 코드 단위 1..32768입니다. 보조 평면 Unicode 문자는 두 단위를 차지합니다. 원래 파일 크기는 경로 길이와 독립적이며 데이터 할당에 사용하지 않습니다. 각 입력과 파서 직접 호출은 128 KiB로 제한합니다. 공통 읽기는 제한된 읽기 전/본문/후 해시를 비교하며 오프셋과 선언 길이가 캡처 바이트 안에 있어야 합니다.

미지원 버전, 불완전 헤더/필드, 과도한 개수와 미종결 경로는 치명적 오류입니다. 필드가 밀린 드문 543바이트 버전 1 변형, 절단/복구 변형, INFO/INFO2, 다른 휴지통 형식과 디렉터리 검색은 미지원입니다. 밀린 필드를 추정해 복구하지 않습니다. 형식 인식은 진위 검증이 아니며 임의 바이트나 의도적으로 수정한 바이트도 지원 헤더처럼 보일 수 있습니다.

## 값 보존과 경고

첫 정렬된 NUL에서 해석 경로를 끝냅니다. 버전 1은 고정 필드 내 종료 문자 이후의 0이 아닌 바이트를 패딩 경고로 남깁니다. 버전 2는 조기 종료를 길이 불일치로 경고하고 이후 필드 바이트가 0이 아니면 패딩도 경고합니다. 종료 문자와 패딩을 포함한 전체 지원 경로 필드는 `path_utf16_hex`로 보존합니다. 지원 레이아웃 이후의 바이트는 `trailing_data_hex`에 남기고 0으로 된 후미 바이트도 경고합니다. 추가/상태 변형을 복원/제거 플래그로 해석하지 않습니다.

정상 UTF-16LE는 `original_path`가 됩니다. 해독할 수 없는 바이트는 경고와 함께 이스케이프하고 정확한 바이트를 hex 필드/출처 해시에 남깁니다. 빈 경로도 경고와 함께 보존합니다. 저장된 드라이브, UNC, 확장, 상대, 환경 변수와 혼합 구분자 텍스트는 그대로 유지하며 경로를 정규화, 해결, 확장하거나 열지 않습니다. 원래 파일을 실행하거나 복구하지 않습니다.

삭제 `deletion_filetime_raw`는 1601-01-01 UTC 이후의 부호 없는 100 ns 틱을 십진 텍스트로 보존합니다. `deleted_at`은 정수 계산으로 마이크로초까지 절삭한 UTC ISO 텍스트입니다. 원시 필드에는 100 ns 나머지가 남습니다. 0은 미지정/null로 경고하며 범위 초과도 원시 틱을 유지하고 null과 경고를 남깁니다. 고정 지역 시간대 보정이나 획득 파일시스템 시각으로 대체하지 않습니다. `original_size`는 JSON과 SQLite 모두 부호 없는 십진 텍스트이며 SQLite 부호 있는 정수 초과나 JavaScript 정수 반올림 없이 18446744073709551615까지 보존합니다.

## 범위와 원본 EnScript 차이

입력마다 메타데이터 레코드 하나를 만들며 `record_id`는 `source_id` 범위의 헤더 오프셋인 문자열 0입니다. 파일명/내용이 같아도 반복 입력은 별도 출처로 유지합니다. 출처 `sha256`은 획득한 메타데이터 바이트의 해시이며 원래 삭제 파일이나 동반 내용의 해시가 아닙니다. 획득 경로와 해시는 sources에 남습니다. 복사 안정성이 원자적 획득, 증거 완전성이나 증거 인계를 인증하지 않습니다. 보고서는 메모리에 유지하며 입력별 제한은 전체 보고서 메모리 합계 제한이 아닙니다.

`$R` 동반 파일을 읽거나 찾아 해시 계산, 추출, 복원하지 않습니다. 내용 존재, 복원 또는 영구 삭제 여부를 추론하지 않습니다. 지원 `$I` 헤더에는 SID/소유자/계정 정보가 없으며 획득 디렉터리 이름으로 추정하지 않습니다. 원본 EnScript는 사건 파일 메타데이터/MD5와 SID 경로 맥락을 수집했지만 이식판은 `$I` 메타데이터만 다룹니다. 오프셋 24 직후를 항상 경로로 가정하지 않고 버전을 명시적으로 구분하며 고정 시간대 표시를 UTC/원시 틱으로 바꿉니다. EnCase 출력 동등성을 주장하지 않습니다. 메타데이터만으로 사용자 의도, 내용 식별이나 완전한 삭제 이력을 입증하지 않습니다.

## 현재 스키마와 구조

휴지통 입력이 없는 경우도 모든 JSON `format_version`과 SQLite `user_version`은 10입니다. 버전 4는 `recycle_bin`과 개수를 추가하고 기존 브라우저, LNK, Prefetch와 EVTX 필드 의미를 유지합니다. 기존 버전 1/2/3 보고서는 재작성/마이그레이션하지 않으며 소비자는 버전 10을 명시적으로 인식해야 합니다. SQLite 삽입은 값을 바인딩하고 출처 외래 키를 적용합니다. sources의 `source_kind`와 `schema_family`는 recycle_bin, `sha256`은 전체 입력 해시이며 browser/database/WAL 필드는 null입니다.

| 컬렉션/테이블 recycle_bin 필드 | 의미 |
| --- | --- |
| source_id, record_id | 출처 ID와 출처 내 헤더 오프셋 0 |
| version | 저장 형식 버전 1 또는 2; OS 버전 주장 아님 |
| original_size | 바이트 단위 원래 크기의 부호 없는 64비트 십진 텍스트 |
| deleted_at, deletion_filetime_raw | UTC 마이크로초 표시와 정확한 원시 FILETIME 텍스트 |
| original_path | 그대로의 해독 경로 또는 잘못된 텍스트의 이스케이프; 빈 값은 유지 |
| path_length_units | 버전 2의 선언 UTF-16 단위 개수; 버전 1은 null |
| path_utf16_hex | 종료 문자/패딩을 포함한 전체 고정/길이 지정 경로 필드 바이트 |
| trailing_data_hex | 지원 레이아웃 이후의 미해석 바이트; 없으면 빈 문자열 |

[recycle_bin.py](../plaintrace/recycle_bin.py)는 레이아웃 검증과 메타데이터 해석을 담당합니다. [execution.py](../plaintrace/execution.py)는 입력 출처를 결합하고 [model.py](../plaintrace/model.py)는 버전 10/개수를 정의하며 [exports.py](../plaintrace/exports.py)는 테이블을 추가하고 [cli.py](../plaintrace/cli.py)는 반복 플래그를 추가합니다. 기존 LNK/Prefetch 8 MiB와 EVTX 64 MiB 제한은 유지합니다.

## 테스트, 리뷰와 남은 검증

[테스트와 수동 리뷰](RECYCLE_BIN_TESTS.ko.md)는 두 레이아웃, 보조 평면 Unicode, 리터럴 경로, 부호 없는 크기, 정확한 틱, 모든 절단 접두부, 제한, 경고, 출처 보존, JSON/SQLite와 실제 CLI 프로세스를 포함한 신규 검사 28개를 대응합니다. 선택 EVTX extra가 있으면 브라우저 33개, 실행 30개, EVTX 32개, 휴지통 28개로 총 123개가 건너뛰기 없이 통과합니다. 없으면 115개를 실행하고 신규 EVTX 다섯 출처 통합 검사 하나를 포함한 통합 검사 8개를 명시적으로 건너뜁니다. 휴지통 전용 검사는 모두 실행합니다. 합성 파일은 임시 생성하며 획득 증거를 커밋하지 않습니다.

여러 Windows 릴리스의 실제 획득 `$I`, Windows/Linux와 Python 3.10 실행, 독립 포렌식 도구 대조, 대형 컬렉션, 획득 경합과 EnCase 컴파일/실행은 미검증입니다. 기존 브라우저/LNK/Prefetch/EVTX 한계와 미해석 구조도 문서에 유지합니다. 실제 파일 인증, 손상 복구, 동반 내용 분석, 사용자 식별이나 포렌식 완전성을 주장하지 않습니다.

## 형식 참고 자료

[libyal Recycle.Bin 작업 명세](https://github.com/libyal/dtformats/blob/main/documentation/Windows%20Recycle.Bin%20file%20formats.asciidoc)와 [rifiuti2 참조 구현](https://github.com/abelcheung/rifiuti2/blob/master/src/rifiuti-vista.c)을 참고했습니다. 레이아웃/변형 처리를 위한 자료이며 의존성 소스를 포함하지 않고 독립 실행 동등성을 확인하지 않았습니다. 보존된 [EnScript 분석](ANALYSIS.ko.md)을 확인하세요.

## USB 레지스트리 확장

0.5.0에서 스키마 5와 usb_registry 관찰을 도입했습니다. 위의 이전 스키마 도입은 과거 맥락이며 기존 아티팩트 필드 의미는 유지합니다. [USB 레지스트리 계약](USB_REGISTRY_CLI.ko.md)과 [테스트/리뷰](USB_REGISTRY_TESTS.ko.md)를 확인하세요.

## RecentDocs 확장

패키지 0.6.0은 도입 당시 스키마 6과 recent_doc_keys/recent_docs를 추가했습니다. 위의 이전 확장 도입은 과거 맥락이며 현재 소비자는 스키마 10을 지원해야 합니다. [RecentDocs 계약](RECENT_DOCS_CLI.ko.md)과 [테스트/리뷰](RECENT_DOCS_TESTS.ko.md)를 확인하세요. 기존 필드 의미는 유지합니다.
