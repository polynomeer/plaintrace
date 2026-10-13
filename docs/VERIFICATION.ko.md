# 문서 산출물 검증 보고서

[English](VERIFICATION.md) | **한국어**

2026-10-13 보존된 소스를 기준으로 작성한 사후 문서입니다. 2017년 당시의 원본 산출물이 아닙니다.

## 범위

보고일: 2026-10-13. 보존 구현의 사후 문서 작업을 검증합니다. 변경은 문서와 소스 참조 생성 도구에 한정하며 EnScript는 수정하지 않습니다. 아래 검사는 저장소 일관성이며 런타임 정확성을 입증하지 않습니다.

## 수행한 검사

| 검사 | 방법 | 결과 |
| --- | --- | --- |
| 원본 소스·히스토리 | 원래 작업 공간의 python3 tools/verify_archive.py | 통과: 소스 13개·과거 README·263개 커밋·기준 tree |
| 소스 참조 생성 | python3 tools/generate_source_reference.py --check | 통과: 두 언어 참조가 소스 추출과 일치 |
| 소스 행 인용 | 대상 디코딩·클래스/메서드/SQL 위치 대조 | 명시한 제한 범위에서 통과 |
| 상대 문서 링크 | Markdown별 경로·파일/행 앵커 해석 | 저장소 내부 대상 통과 |
| 언어 쌍 | 영문·국문 존재와 전환 링크 | 모든 문서 주제 통과 |
| 번역 구조 | 절·표 행·코드 블록 수 대조 | 통과; 기술 ID·명령 유지 |
| 도표 구조 | Mermaid 구분자와 선언 점검 | 정적 점검 통과; 렌더링 미실행 |
| 공백 | git diff --check | 통과 |

## 수행하지 않은 검사

EnCase 컴파일·실행, 증거 파싱 정답 대조, GUI 조작, DB 내보내기 왕복, 웹 타임라인 렌더링, 버전별 호환성, 성능 측정은 수행하지 않았습니다. HTML 런타임 항목은 자산 누락으로 blocked입니다. 당시 원본 설계·테스트 기록은 제공되지 않았습니다.

## 재현 명령

```sh
python3 tools/inspect_sources.py
python3 tools/generate_source_reference.py --check
python3 tools/verify_documentation.py
python3 tools/verify_archive.py
git diff --check
```

전체 아카이브 검증에는 원래 로컬 백업 ref가 필요합니다. [설정](USER_GUIDE.ko.md)을 참조하세요. 런타임 인수 항목·결과 양식은 [검증 계획](TEST_PLAN.ko.md)에 있습니다. SQL 부록은 선언 목록이며 실행을 통과한 마이그레이션이 아닙니다.
