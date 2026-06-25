# 🔥 돌아온 불타는 개미지옥

> "클로드 코드로 시작하는 실전 에이전틱 코딩" 12주 스터디  
> 매주 일요일 | 2025.07.05 ~ 09.21 | 9명

---

## 📌 프로젝트 소개

Claude Code를 활용해 국내 주식 분석 웹을 공동 개발하는 스터디 프로젝트입니다.  
매주 담당자가 책의 챕터 내용을 발표하고, 해당 내용을 실제 웹에 반영합니다.

---

## 🛠 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | FastAPI (Python 3.11) |
| Database | Supabase (PostgreSQL) |
| 차트 | TradingView Lightweight Charts |
| 자동화 | Claude Code, MoAI-ADK |
| CI/CD | GitHub Actions |
| 문서 | Notion |

---

## 📅 스터디 일정

| 주차 | 날짜 | 챕터 |
|------|------|------|
| 1주 | 07/05 | Ch.01~02 Claude Code 시작·워크플로 |
| 2주 | 07/13 | Ch.03 에이전트 스킬 |
| 3주 | 07/20 | Ch.04 (1/2) 서브에이전트 |
| 4주 | 07/27 | Ch.04 (2/2) 에이전트 팀 |
| 5주 | 08/03 | Ch.05~06 출력·메모리·세션 |
| 6주 | 08/10 | Ch.07 (1/2) 자동화·훅 |
| 7주 | 08/17 | Ch.07 (2/2) MCP·플러그인 |
| 8주 | 08/24 | Ch.08 MoAI-ADK |
| 9주 | 08/31 | Ch.09 (1/2) plan-run-sync |
| 10주 | 09/07 | Ch.09 (2/2) 에이전트 팀 병렬 |
| 11주 | 09/14 | Ch.10 실전 실습 |
| 12주 | 09/21 | APPENDIX + 최종 통합 |

---

## 🚀 온보딩 (처음 시작하는 팀원)

### 1. 필수 설치

**Windows**
```cmd
# Git: https://git-scm.com
# Node.js 20+: https://nodejs.org
# Python 3.11+: https://python.org  ← 설치 시 "Add Python to PATH" 체크 필수
# Claude Code
npm install -g @anthropic-ai/claude-code

# 줄바꿈 설정 (필수)
git config --global core.autocrlf true
```

**Mac**
```bash
brew install git python@3.11 node redis
brew services start redis
npm install -g @anthropic-ai/claude-code
```

### 2. 저장소 클론

```bash
git clone https://github.com/shiho2v/antshell.git
cd antshell
```

### 3. 환경변수 설정

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

`.env` 파일 열어서 스터디장에게 받은 값 입력  
(Supabase URL/KEY, Notion KEY)

### 4. 의존성 설치

```bash
# 프론트엔드
cd frontend && npm install && cd ..

# 백엔드
cd backend && pip install -r requirements.txt && cd ..
```

### 5. Claude Code 실행

```bash
claude "CLAUDE.md 읽고 이번 주 작업 내용 알려줘"
```

### 6. 첫 브랜치 생성 후 PR

```bash
git checkout -b feature/01-내이름-onboarding
git add .
git commit -m "chore(onboarding): 내이름 온보딩 완료"
git push origin feature/01-내이름-onboarding
```

GitHub에서 PR 생성 → 스터디장 merge

---

## 📁 프로젝트 구조

```
antshell/
├── CLAUDE.md              ← Claude Code 가이드 (항상 읽힘)
├── DEV_PRINCIPLES.md      ← 개발 원칙
├── .env.example           ← 환경변수 템플릿
├── _claude_core/          ← Claude 참조 문서
├── docs/
│   ├── weekly/            ← 주차별 작업 계획
│   └── setup/             ← 온보딩 상세 가이드
├── .claude/hooks/         ← Notion 자동화 훅
├── .github/workflows/     ← CI/CD
├── frontend/              ← Next.js
└── backend/               ← FastAPI
```

> 상세 온보딩 가이드: [`docs/setup/ONBOARDING.md`](docs/setup/ONBOARDING.md)

---

## 🌿 Git 규칙

- 브랜치: `feature/<주차>-<이름>-<기능명>`
- 커밋: `feat(scope): 설명` (Conventional Commits)
- `main` 직접 push 금지 → PR 필수

---

## 🔗 링크

- [Notion 스터디 페이지](https://www.notion.so/38ab326d0fb280ddb02bd6b7009e4c2c)
- [개발 원칙](DEV_PRINCIPLES.md)
- [온보딩 상세 가이드](docs/setup/ONBOARDING.md)
