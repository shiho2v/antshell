# 돌아온 불타는 개미지옥 — Claude Code 가이드

## 프로젝트 한 줄 요약
9명 스터디팀이 "클로드 코드로 시작하는 실전 에이전틱 코딩" 책을 매주 학습하며
국내 주식 분석 웹을 공동 개발하는 12주 프로젝트 (2025.07.05 ~ 10.18)

## ⚠️ 토큰 절약 규칙 (반드시 준수)
- 이 파일 외 다른 파일은 **작업에 필요한 것만** 읽을 것
- 주차별 작업이면 → `docs/weekly/WEEK_04.md` 만 읽을 것
- 전체 파일을 한 번에 읽지 말 것

## 필수 파일 위치 (필요할 때만 읽기)

| 목적 | 파일 |
|------|------|
| 프로젝트 전체 구조·기술스택 | `_claude_core/PROJECT.md` |
| 환경변수·API 키 설정 | `_claude_core/ENV_GUIDE.md` |
| Git 브랜치·커밋 규칙 | `_claude_core/GIT_RULES.md` |
| Notion 연동 설정 | `_claude_core/NOTION_SETUP.md` |
| 현재 주차 작업 계획 | `docs/weekly/WEEK_04.md` ← XX를 현재 주차로 교체 |
| 아키텍처 다이어그램 | `docs/architecture/ARCH.md` |
| 초기 환경 세팅 (신규 팀원) | `docs/setup/ONBOARDING.md` |
| 코드 작성·리뷰 시 준수 기준 | `DEV_PRINCIPLES.md` ← **코드 작업 시에만** 읽기 |

## 현재 진행 주차
<!-- 매주 발표자가 업데이트 -->
CURRENT_WEEK=07
CURRENT_PRESENTER=양재호
CURRENT_CHAPTER=Ch.07 (2/2)

## 새로운 팀원이라면
`docs/setup/ONBOARDING.md` 를 먼저 읽으세요.

## 작업 시작 전 체크
1. `git pull origin main` 으로 최신화
2. `CURRENT_WEEK` 확인 후 해당 WEEK_XX.md 읽기
3. 본인 브랜치 생성: `feature/<주차>-<이름>-<기능명>` (예: `feature/01-alice-init`)
