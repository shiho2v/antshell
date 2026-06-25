# PRD: 돌아온 불타는 개미지옥 — 주식 스터디 공동 개발 프로젝트

**문서 버전:** 1.0  
**작성일:** 2025-07-05  
**작성자:** 스터디장  
**대상:** Claude Code (에이전틱 코딩 자동화용)

---

## 1. 프로젝트 개요

### 목표
- "클로드 코드로 시작하는 실전 에이전틱 코딩" 12주 스터디 진행
- 매주 담당 챕터 내용을 국내 주식 분석 웹에 실제 반영
- Git·Notion 자동화로 협업 이력 관리

### 팀 구성
- 인원: 9명 (스터디장 포함)
- 일정: 매주 일요일 / 2025.07.05 ~ 10.18
- Claude 요금제: 전원 Pro (사용량 제한 고려 필수)

### 핵심 제약
- 유료 클라우드 서비스 최소화
- Git 초보자 포함 → 자동화로 진입 장벽 낮추기
- Claude Code 토큰 절약 → 파일 분리·선택적 로드 설계

---

## 2. 구현 범위 (12주)

### Phase 1: 기반 구축 (1~2주차)
- [ ] 프로젝트 초기화 (모노레포 구조)
- [ ] Git 브랜치 전략 설정
- [ ] `.gitignore` / `.env.example` 배포
- [ ] Notion MCP 연결 및 훅 설정
- [ ] GitHub Actions CI 설정
- [ ] CLAUDE.md + _claude_core 파일 작성
- [ ] 팀원 온보딩 문서 작성

### Phase 2: 주식 웹 핵심 기능 (3~9주차)
- [ ] DART API 연동 (재무데이터)
- [ ] KIS API 연동 (실시간 시세)
- [ ] TradingView 차트 컴포넌트
- [ ] 뉴스·공시 요약 (Claude API)
- [ ] 포트폴리오 관리 기능
- [ ] 사용자 인증 (Supabase Auth)

### Phase 3: 에이전트 고도화 (10~12주차)
- [ ] MoAI-ADK 도입
- [ ] 멀티 에이전트 병렬 데이터 수집
- [ ] 전체 통합 테스트 및 최종 문서화

---

## 3. 파일 구조 설계

```
P01/
├── CLAUDE.md                    ← 항상 읽힘 (200줄 이내 유지)
├── PRD.md                       ← 이 파일
├── .env.example                 ← 환경변수 템플릿 (git 추적)
├── .gitignore
│
├── _claude_core/                ← Claude가 필요시 읽는 핵심 문서
│   ├── PROJECT.md               ← 기술스택·아키텍처 요약
│   ├── ENV_GUIDE.md             ← 환경변수 상세 가이드
│   ├── GIT_RULES.md             ← Git 규칙
│   └── NOTION_SETUP.md          ← Notion 연동 설정
│
├── docs/
│   ├── weekly/                  ← 주차별 PLAN (필요 주차만 읽기)
│   │   ├── WEEK_01.md
│   │   ├── WEEK_02.md
│   │   └── ...WEEK_12.md
│   ├── setup/
│   │   └── ONBOARDING.md        ← 신규 팀원 세팅 가이드
│   └── architecture/
│       └── ARCH.md
│
├── .claude/
│   ├── settings.json            ← 훅·MCP 설정
│   └── hooks/
│       ├── notion_sync.py       ← 커밋→Notion 자동 기록
│       └── commit_format.py     ← 커밋 메시지 자동 포맷
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── notion_weekly.yml
│
├── frontend/                    ← Next.js 14
│   ├── src/
│   └── package.json
│
└── backend/                     ← FastAPI
    ├── app/
    └── requirements.txt
```

---

## 4. 토큰 절약 설계 원칙

### 계층적 로딩 규칙
```
레벨 1 (항상): CLAUDE.md 만
레벨 2 (작업 시작): _claude_core/PROJECT.md + 현재 WEEK_XX.md
레벨 3 (특정 작업): 해당 기능 파일만
레벨 4 (절대 금지): 전체 docs/ 일괄 읽기
```

### 파일 크기 제한
- CLAUDE.md: 200줄 이내
- 각 WEEK_XX.md: 150줄 이내
- _claude_core 각 파일: 100줄 이내

### 주차 전환 시
- CLAUDE.md의 `CURRENT_WEEK` 숫자만 업데이트
- 이전 주차 WEEK 파일은 건드리지 않음 (아카이브)

---

## 5. 구현 순서 (Claude Code 작업 지시)

아래 순서대로 하나씩 구현할 것. 한 번에 전부 하지 말 것.

```
STEP 01: _claude_core 파일 4개 생성
STEP 02: docs/setup/ONBOARDING.md 생성
STEP 03: docs/weekly/WEEK_01.md ~ WEEK_12.md 생성
STEP 04: .gitignore + .env.example 생성
STEP 05: .claude/settings.json (훅·MCP 설정) 생성
STEP 06: .claude/hooks/notion_sync.py 생성
STEP 07: .claude/hooks/commit_format.py 생성
STEP 08: .github/workflows/ci.yml 생성
STEP 09: .github/workflows/notion_weekly.yml 생성
STEP 10: frontend/ 초기 구조 생성
STEP 11: backend/ 초기 구조 생성
```
