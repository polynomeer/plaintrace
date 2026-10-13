# 사후 재구성한 개발 기록

작성일: **2026-10-13**. 이 저장소의 **2017-07-01–2017-11-30 (+09:00)** 커밋은 실제 당시 Git 기록을 복구한 것이 아니라, 현재 남아 있는 최종 소스에서 만든 **기록용 사후 재구성**이다. 날짜, 개발 순서 및 작업 간격은 임의로 배치했다. 실제 당시 활동이나 기여를 입증하는 자료로 사용하지 않는다.

## 재구성 방법

- 기존 `master`의 5개 커밋은 새 체인의 부모로 사용하지 않았다.
- 원래 README와 13개 EnScript 파일을 그대로 보존했다. 최초 README에도 나중에 작성된 내용이 있을 수 있으므로 원래의 2017년 문서라고 주장하지 않는다.
- README → 시스템 정보 → 파일 메타데이터 → 계정 → 휴지통 → 로그인/전원 → USB → Prefetch → LNK → 최근 문서 → 다운로드 → 웹 방문/검색어 → 타임라인 → 메인 조립 순서로 배치했다. 이는 설명을 위한 순서이고 실제 작업 순서는 아니다.
- 클래스의 필드/생성자, 메서드 단위로 263개 커밋을 만들었다. 작은 데이터 클래스는 클래스 단위로 묶었고 메서드 내부를 임의의 줄 수로 더 잘게 자르지 않았다.
- 날짜는 2017-07-01 10:00:00부터 2017-11-30 18:00:00까지 균등 배치했다. author date와 committer date를 동일하게 설정했으며 기존 로컬 Git 작성자 설정을 사용했다. 당시 작성자별 기여는 추정하지 않았다.
- 모든 제목은 `archive:`로 시작하며 본문에 retrospective reconstruction 및 synthetic date/order를 명시했다.
- 단계별 클래스 닫는 중괄호를 임시로 추가하여 소스를 점진적으로 보존했다. 나중에 추가되는 메서드/다른 모듈/공통 클래스에 의존하는 중간 단계는 완성된 빌드가 아니다. 매 커밋의 컴파일 가능성을 보장하지 않는다.
- 마지막 2017년 커밋의 Git tree는 기존 최종 커밋과 완전히 동일하다. 인코딩, BOM, CRLF, 주석 및 기존 구현상 문제까지 보존했다.
- Codex 환경, 분석 문서, 검증 도구는 현재 날짜의 후속 커밋으로 분리했다. 원격 저장소에는 push하지 않았다.

## 확인하기

```sh
python3 tools/inspect_sources.py
python3 tools/inspect_sources.py Win_TimeLine.EnScript --start 2006 --end 2120
python3 tools/verify_archive.py
git log --reverse --format='%h %aI %s' master
```

`docs/history-map.json`에는 전체 순번·날짜·파일·제목·커밋 ID가 있고 `docs/source-manifest.json`에는 원본 14개 파일의 SHA-256과 크기가 있다.

UTF-16 소스의 diff 표시에는 로컬 설정 `diff.enscript.textconv = python3 tools/enscript_textconv.py`를 사용한다. 새 clone에서는 다음 명령을 한 번 실행할 수 있다. 원본 blob은 바뀌지 않는다.

```sh
git config --local diff.enscript.textconv 'python3 tools/enscript_textconv.py'
```

## 백업 및 복구

기존 최종 커밋: `6814d18c75aa` (전체 ID는 archive ref에서 조회 가능).

- Git ref: `refs/archive/pre-reconstruction`
- 원래 모든 refs의 Git bundle: `.history-backup/original-6814d18c75aa.bundle` (로컬 백업, ignore됨)
- 원격 추적 refs도 유지된다. 따라서 `git log --all`에는 원래 기록이 함께 보일 수 있다. 새 개발 기록은 `git log master`로 확인한다.

원본을 별도 디렉터리에 복구하려면 다음 명령을 사용한다. 현재 재구성 기록을 덮어쓰지 않는다.

```sh
git bundle verify .history-backup/original-6814d18c75aa.bundle
git clone .history-backup/original-6814d18c75aa.bundle /tmp/plaintrace-original
```

로컬 백업을 잃지 않으려면 bundle 파일을 별도 보관한다. 히스토리 교체 때문에 원격과의 일반 push는 fast-forward가 아닐 수 있다. 원격 반영은 이번 작업에 포함하지 않았다.
