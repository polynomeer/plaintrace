# 프로젝트 정적 분석

[English](ANALYSIS.md) | **한국어**

분석일: 2026-10-13. 사용자 설명에 따르면 원래 이름은 **Plain View of Multi Artifacts**이며, 학부 재학 중 차세대보안리더양성프로그램(BoB) 디지털포렌식 트랙에서 2017년 7–11월 개발했다. 현재 저장된 최종 소스를 기준으로 분석했고, 실제 당시 일정이나 개인별 기여는 추정하지 않았다.

## 구조와 실행 환경

13개 EnScript 파일이 있다. 진입점은 `Plain View of Multi Artifacts.EnScript`의 `MainClass.Main`이다. 12개 Windows 모듈을 include하고, 케이스의 Windows 볼륨을 찾은 뒤 북마크 폴더와 탭형 `MainDialogClass`를 구성한다. 데이터 행은 대체로 `NameListClass` 파생 클래스, 표는 `HandlerClass`와 `TreeTableEditClass`, 수집은 `ThreadClass`, 검색·진행 표시·종료 처리는 `DialogClass`가 담당한다. 공통 내보내기 경로 선택창은 진입 파일의 `ExportDialogClass`에 정의되어 있다.

EnCase의 `CaseClass`, `EntryClass`, `RegistryClass`, `EventLogParserClass`, `SQLiteClass` 등 호스트 API에 의존한다. EnCase 버전, SDK, 테스트 케이스, 빌드 설정은 저장소에 없다. 독립적인 C++/Java 프로그램이 아니므로 일반 컴파일러로 검증할 수 없다. README의 JavaScript 기술 언급과 HTML 실행 코드가 있지만 실제 웹 타임라인 HTML/JS 자산은 포함되어 있지 않다.

## 전체 모듈 분석

| 파일 | 입력과 핵심 처리 | 출력 및 인터페이스 |
|---|---|---|
| Plain View of Multi Artifacts | Windows 볼륨 검사, include 12개, 북마크 생성, 모듈 조립 | 내보내기 경로 창, 시스템·파일·계정·실행·웹·타임라인 탭 |
| Win_SystemInfo | 선택 항목의 파일/볼륨 정보, SOFTWARE의 OS 정보와 제품 키, SYSTEM 컴퓨터명 조회·미완성 종료 시각 함수, SAM 사용자 순회 | FileReportClass, VolumeReportClass, OSReportClass 문서와 파일 분포 차트 |
| Win_FileMetaData | 선택 항목의 확장자·카테고리·크기·경로·MAC 시각, 삭제/숨김 속성으로 목록 분리 | 일반/숨김/삭제 표, CSV, File_Common/File_Hidden/File_Deleted SQLite, 타임라인용 삭제 목록 |
| Win_UserAccount | SAM Users/Names와 RID 키의 F/V 바이너리 레코드, 로그인/비밀번호 변경 시각, 횟수, 계정 상태, 문자열 정보 | AccountListClass, 검색/진행 표시, CSV 및 PC_UserAccount SQLite |
| Win_RecycleBin | $Recycle 경로와 SID, $I 파일의 헤더·8바이트 크기·삭제 FILETIME·유니코드 원래 경로 | 원본 메타데이터/MD5와 삭제 정보 표, 파일 추출, CSV 및 File_RecycleBin SQLite |
| Win_PowerLogOnOff | Security 이벤트 4624/4634/4647 및 전원 이벤트 12/13, XML 데이터에서 사용자·로그온 ID·주소 등 추출 | 로그인/전원 목록, 로그인 유형 설명 문서, CSV 및 PC_LogOnOff/PC_PowerOnOff SQLite |
| Win_USBInfo | SYSTEM USBSTOR/USB/DeviceClasses/MountedDevices, SOFTWARE 장치·프로필 정보와 DriverFrameworks Operational.evtx | USB 레지스트리 결과 표·CSV 내보내기, 연결 상태·시각·식별자 이벤트 표, CSV 및 USB_EventLog SQLite |
| Win_PrefetchFile | Prefetch 경로의 .pf, 고정 오프셋에서 실행 파일명·시각·횟수·참조 목록 추출, 장치 경로 매핑 | 실행/참조 목록, 파일 추출, CSV, App_PrefetchFile/App_EXEFile SQLite와 실행 빈도 차트 |
| Win_LinkFile | LNK 헤더·경로 블록·추가 데이터, 원본 파일 시각/크기, 드라이브·머신·MAC 등 추적 정보; Recent 경로 별도 수집 | Link/Recent 두 목록·추출 메뉴·CSV, Link 쪽 App_LinkFile/App_EXEFile SQLite; Recent SQLite 분기 미구현 |
| Win_RecentDocuments | 사용자 레지스트리의 최근 문서 목록과 추출한 LNK를 대조; PowerPoint/Word/Excel/HWP/Adobe 별 처리 | RecentDoc 목록, LNK·뷰어별 CSV 및 App_Documents SQLite; 뷰어별 테이블 정의는 주석 처리 |
| Win_WebDownloads | Chrome/Opera History의 downloads, Firefox places.sqlite의 moz_annos, IE WebCache 바이너리 검색; 브라우저별 시간 변환 | 추출 DB/CSV 및 Web_Download SQLite, 다운로드 경로·시각·크기·URL 표 |
| Win_WebVisitKeyword | Chrome/Opera urls, Firefox moz_places, IE index.dat/WebCache; URL 디코딩·검색어·호스트 빈도 추출 | 방문/검색어 두 표, CSV 및 Web_Visit/Web_Keyword/Web_Host SQLite, 호스트 상위 빈도 차트 |
| Win_TimeLine | 독립 모듈의 여러 파서를 다시 구현; 1차 순회에서 삭제·USB·로그온·전원·계정·Prefetch·LNK, 2차 순회에서 최근 문서·웹 수집 | C:\TimeLineArtifacts_Total.sqlite, LNK CSV, 읽어보기 문서, 외부 HTML을 Chrome/IE/Firefox로 실행하는 버튼 |

정확한 파일별 인코딩·라인 수·클래스 목록은 `python3 tools/inspect_sources.py`, 바이트/해시 기준은 `docs/source-manifest.json`을 참조한다. 클래스와 메서드별 보존 단계 전체는 `docs/history-map.json`에 기록했다.

## 보존한 제약과 후속 검토 사항

이번 작업은 기록 복원으로 한정하므로 아래 구현을 수정하지 않았다. 다음은 소스에서 확인한 사실 또는 그에 따른 검토 필요 사항이며, 런타임 재현 결과가 아니다.

- SQL은 대부분 문자열 연결로 만든다. 파일명/URL에 작은따옴표가 들어갈 때 문법이나 데이터 보존 문제가 생길 가능성이 있다. CSV 역시 단순 쉼표 연결이 많아 쉼표·줄바꿈·따옴표가 포함된 데이터의 검증이 필요하다.
- `Win_LinkFile`과 `Win_PrefetchFile`의 일부 `SELECT COUNT(*) FROM sqlite_master WHERE name 'App_EXEFile'` 문자열에는 비교 연산자가 없다. 내보내기 오류 처리와 함께 검토할 필요가 있다.
- `Win_PowerLogOnOff`의 로그인 목록 복사(425행)와 필터 재구성(761/767행)은 생성자 선언과 인자 순서가 다르다. 전원 목록 복사(567행)는 이벤트 시각 자리에 `n.event`를 전달한다.
- Prefetch는 0x80/0x98 등 고정 오프셋을 사용하고 포맷 버전 분기나 압축 해제는 확인되지 않는다. 휴지통은 $I의 고정 헤더 뒤 문자열을 읽는다. 다양한 Windows 버전 지원을 보장할 근거는 없다.
- 날짜 표시는 여러 곳에서 고정 `-9*3600` 값을 사용한다. EnCase 시간 API의 의미 및 브라우저별 epoch 변환을 실제 케이스로 검증해야 한다.
- C 드라이브의 고정 경로가 많고 실제 출력에는 `WindowsArtifacts.sqlite`, `TimeLineArtifacts.sqlite`, `TimeLineArtifacts_Total.sqlite`가 사용된다. `WindowsArtifact.sqlite`는 오래된 주석에만 남아 있고 실행 경로 할당에는 없다. 테이블 생성/재실행과 파일 잠금 처리를 확인해야 한다.
- `Win_TimeLine.Run`은 1차 순회의 WebArtifact 호출이 주석 처리되어 있으나, 2차 순회에서는 비볼륨 항목에 호출한다. 웹 수집 자체가 전부 비활성인 것은 아니다.
- 타임라인 실행 버튼의 `C:\PlainView.html` 변수와 브라우저 명령의 `C:\PlainView\PlainView.html` 경로가 다르며, 해당 자산은 저장소에 없다. 현 스냅샷만으로 웹 시각화의 완전한 실행은 검증할 수 없다.
- 각 모듈과 타임라인 파서에 중복 구현이 있다. 독립 실행 경로의 수정이 자동으로 타임라인에 반영되지 않는 구조다.
- 상태 표시 및 세마포어 해제는 주로 정상 흐름에 있다. 조기 종료, 빈 선택, 여러 디바이스 및 잘못된 바이너리 입력에 대한 동작은 별도 검증이 필요하다.

- `Win_SystemInfo.GetShutdownTime`(346–361행)은 레지스트리 값을 디코딩하지 않는다. sumTime에 상수를 넣고 시각 변환은 주석 처리되어 있어 결과 문자열에 시각을 할당하는 실행 코드 없이 반환한다. 컴퓨터명 조회도 두 값 모두 ComputerName 명령 결과를 사용한다(319–320행).
- `Win_TimeLine`은 Web_Visit·Web_Host에 INSERT를 시도하지만 두 테이블의 CREATE TABLE 실행 코드는 없다. IE WebCache 방문 SQL(1861행)에는 VALUES도 없다. 런타임 검증 없이 웹 기록이 정상 통합된다고 설명할 수 없다.
- `Win_WebVisitKeyword.visit_csv`(723–726행)와 `Win_TimeLine.visit_csv`(1563–1565행)는 sql2csv가 읽은 DataReader를 재조회·재설정 없이 keyword_extract에 전달한다. 검색어 수집 범위를 호스트에서 검증해야 한다.
- `Win_USBInfo` 이벤트 CSV(207–211행)는 실제 이벤트 필드와 다른 레지스트리 헤더와 일관되지 않은 따옴표를 사용한다. `Win_LinkFile.RecentHandlerClass`는 BuildMenu(322행)에 SQLite를 표시하지만 MenuEvent(326–350행)는 CSV만 처리한다. 메뉴 표시는 내보내기 구현의 근거가 아니다.

## 검증 범위

전체 13개 파일을 BOM에 맞춰 디코딩하고 클래스·메서드 경계를 정적 추출했다. 주석과 문자열을 제외한 중괄호 균형, 재구성 마지막 단계의 원본 바이트 일치, 전체 최종 Git tree 일치, 해시 매니페스트, 커밋 부모/작성·커밋 날짜/대상 파일을 검증한다. 이는 프로그램 컴파일, 아티팩트 정확도, 보안성 또는 모든 중간 커밋의 실행 가능성을 입증하지 않는다.
