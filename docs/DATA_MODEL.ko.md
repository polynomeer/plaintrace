# 데이터 모델과 출력 계약

[English](DATA_MODEL.md) | **한국어**

2026-10-13 보존된 소스를 기준으로 작성한 사후 문서입니다. 2017년 당시의 원본 산출물이 아닙니다.

## 저장 모델

메모리 NameList 행, EnCase 북마크·보고서, 로컬 추출 증거 사본, 구분자 텍스트, 여러 SQLite 파일을 사용합니다. 외래키 관계 그래프나 통일된 이벤트 테이블은 확인되지 않습니다. 아티팩트별 컬럼을 유지하며 정수 기본키는 테이블의 행 식별자이지 아티팩트 간 공통 식별자가 아닙니다.

| 출력 | 목적 | 주의할 동작 |
| --- | --- | --- |
| 사용자가 선택한 CSV/SQLite 경로 | 모듈 메뉴 내보내기 | ExportDialogClass에서 경로 선택 |
| C:\WindowsArtifacts.sqlite | 여러 Handler 기본 내보내기 | WindowsArtifact.sqlite와 철자가 다름 |
| C:\WindowsArtifact.sqlite | 레거시 수집 코드의 다른 경로 | 모듈별 확인 필요; 단일 출력으로 가정하지 않음 |
| C:\TimeLineArtifacts.sqlite | 독립 모듈의 타임라인 보조 출력 | 기존 테이블·반복 기록 검토 필요 |
| C:\TimeLineArtifacts_Total.sqlite | 통합 타임라인 생성 | WRITE로 열기; 재생성 전 이전 결과 보존 |
| 케이스 내보내기 폴더 | 브라우저 사본·중간 파일, link_files, lnk_parse.csv, help.txt | 브라우저별 여러 폴더·파일명 |

소스의 경로 문자열이며 설정 가능한 배포 명세가 아닙니다. 타임라인 `lnk_parse.csv` 등 일부 .csv는 탭 구분이므로 작성 코드별 구분자·헤더를 확인해야 합니다.

## 테이블 계열

| 계열 | 테이블 | 해석 |
| --- | --- | --- |
| 컴퓨터·계정 | PC_UserAccount, PC_LogOnOff, PC_PowerOnOff | 계정 상태·이벤트; SID/RID/LogonID의 의미는 서로 다름 |
| 파일 | File_Common, File_Hidden, File_Deleted, File_RecycleBin | 메타데이터·속성·삭제 정보 |
| 실행 | App_PrefetchFile, App_PrefetchFile_Sorted, App_LinkFile, App_EXEFile | 실행 흔적과 차트 집계; 모든 실행을 입증하지 않음 |
| 문서 | App_Documents | 뷰어·이름·시각·크기·드라이브 종류·경로 |
| USB | USB_EventLog | 장치·연결 이벤트 |
| 웹 | Web_Visit, Web_Keyword, Web_Host, Web_Download | 방문·검색·횟수·다운로드 |
| 중간 | 동적 Web_cr/ff/op 방문·다운로드·검색어 및 뷰어별 테이블 | 브라우저별 중간 데이터; 단일 표준 스키마가 아님 |

SQL 리터럴과 위치는 [스키마 참조](SCHEMA_REFERENCE.ko.md)에 있습니다. 변형 선언을 그대로 제공하며 임의로 정규화하지 않았습니다.

## 시각과 식별자 규칙

파일 메타데이터·여러 바이너리 포맷은 DateClass/FILETIME을 읽습니다. 브라우저별 epoch 변환이 따로 있고 시각을 LONGVARCHAR 형식 문자열로 보관하는 경우가 많습니다. 고정 `-9*3600` 표시가 여러 곳에 있습니다. 비교 시 원본 문자열과 아티팩트 출처를 유지해야 하며 공통 UTC 이벤트 계약은 구현되어 있지 않습니다.

경로, SID, RID, LogonID, 머신 ID, 장치 시리얼, GUID는 서로 다른 필드입니다. 테이블 간 문자열 일치만으로 선언된 관계를 뜻하지 않습니다. 최근 문서와 LNK의 대조는 휴리스틱 코드이며 외래키 제약이 아닙니다.

## 스키마·내보내기 제약

Web_Visit에는 title 포함·미포함 변형이 있습니다. App_EXEFile의 RunCount는 LONGVARCHAR 또는 제약을 가진 INTEGER로 나타납니다. Web_Download의 TotalBytes는 타입 포함·미포함으로 선언됩니다. 계정 선언의 LONGVARHAR 오타도 있습니다. SQL 문자열과 CSV 이스케이프가 일관되지 않습니다. 마이그레이션·버전 레지스트리나 공통 멱등 내보내기 장치는 없습니다. 소비자는 실제 DB 스키마를 확인해야 합니다.

## 조회 예시

증거 입력이 아닌 생성 SQLite 사본에서 실행합니다. 점검 쿼리이며 플러그인 API나 보장된 브라우저 계약이 아닙니다.

```sql
SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name;
PRAGMA table_info('PC_LogOnOff');
SELECT COUNT(*) FROM PC_LogOnOff;
```

마지막 두 쿼리는 테이블이 존재할 때만 실행합니다. DB 해시·컬럼·행 수·출력 경로·선택 증거·호스트 버전·시각 해석을 결과와 함께 기록하세요. 인수 케이스는 [검증 계획](TEST_PLAN.ko.md)에 있습니다.
