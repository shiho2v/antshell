# WEEK_01 — 1주차 작업 계획

**날짜:** 2025-07-05 | **발표자:** 스터디장 | **챕터:** Ch.01~02 | **난이도:** 입문

## 이번 주 목표
1. 팀 전체가 사용할 프로젝트 뼈대 구축
2. Git·Notion 자동화 연결 (발표자 담당)
3. 팀원 온보딩 완료

## 챕터 핵심 개념

### 개념 1: 에이전틱 루프
Claude Code가 도구를 호출하고 결과를 받아 다음 행동을 결정하는 
반복 실행 구조. 사람이 개입 없이 목표까지 스스로 진행한다.

### 개념 2: 컨텍스트 윈도우
...

### 개념 3: settings.json
...

## 이번 주 실습 포인트
- 어떤 기능을 직접 써볼 것인지
- 막힐 것 같은 부분 예상

## 참고 페이지
- p.XX ~ p.XX

## 발표자 작업 목록
- [ ] GitHub 저장소 생성 + 이 PRD 전체 push
- [ ] Notion 워크스페이스 구조 생성 + 팀원 편집 권한 부여
- [ ] `.claude/settings.json` 훅·MCP 설정 완료
- [ ] `.claude/hooks/notion_sync.py` 동작 확인
- [ ] `.github/workflows/ci.yml` + `notion_weekly.yml` push
- [ ] GitHub Secrets 5개 등록 (ENV_GUIDE.md 참고)
- [ ] 팀원 저장소 초대 + ONBOARDING.md 공유

## 팀원 공통 작업
- [ ] 저장소 클론 + 로컬 환경 세팅 (ONBOARDING.md)
- [ ] Claude Code 설치 확인
- [ ] 첫 브랜치 push + PR 생성

## 발표 구성 (70분)
| 시간 | 내용 |
|------|------|
| 0~5분 | 스터디 방향, 12주 일정 공유 |
| 5~25분 | Ch.01~02 핵심: 에이전틱 루프·settings.json·컨텍스트 윈도우 |
| 25~55분 | 실시연: Claude Code → Git 자동화 → Notion 연동 확인 |
| 55~70분 | 팀원 온보딩 Q&A + Ch.03 예고 |

## 주식 웹 적용
- `frontend/` + `backend/` 모노레포 구조 생성
- 백엔드 헬스체크 엔드포인트 `GET /health` 구현

## 다음 주 예고
발표자: **B** | 챕터: Ch.03 (에이전트 스킬)
준비: DART API 키 발급 (opendart.fss.or.kr)
