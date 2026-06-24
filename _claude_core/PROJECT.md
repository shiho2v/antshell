# PROJECT.md — 기술 스택 요약

> 읽는 조건: 기술스택 확인 또는 새 기능 개발 시작 시

## 스택 한눈에 보기

| 레이어 | 기술 | 비고 |
|--------|------|------|
| Frontend | Next.js 14 (App Router) + TypeScript | |
| 스타일 | TailwindCSS | |
| 차트 | TradingView Lightweight Charts | 무료 오픈소스 |
| 상태관리 | Zustand | |
| Backend | FastAPI (Python 3.11) | |
| 비동기 작업 | Celery + Redis | 시세·뉴스 수집 |
| DB | Supabase (PostgreSQL) | 무료 티어 |
| 캐시 | Redis | |
| AI 요약 | Claude API (claude-haiku-4-5) | 비용 절약 |
| 자동화 | Claude Code + MoAI-ADK | |
| CI | GitHub Actions | |
| 문서 | Notion (MCP 자동 연동) | |

## API 출처

| 데이터 | API | 비고 |
|--------|-----|------|
| 재무공시 | DART Open API | 무료 |
| 실시간 시세 | KIS Developers | 무료, 모의투자 가능 |
| 역사적 OHLCV | FinanceDataReader (Python) | 무료 |
| KRX 종목정보 | KRX 정보데이터시스템 | 무료 |
| 뉴스 | BigKinds API | 비상업 무료 쿼터 |

## 모노레포 규칙

- `frontend/` — Next.js. `npm run dev` (port 3000)
- `backend/` — FastAPI. `uvicorn app.main:app --reload` (port 8000)
- 환경변수 → 루트 `.env` 파일 (`.env.example` 참고)

## Claude API 사용 절약 지침

- 요약 모델: `claude-haiku-4-5` (가장 저렴)
- 배치 요약: 개별 호출 X → 뉴스 5건 묶어서 1회 호출
- 캐시: Redis에 요약 결과 24시간 저장 (재호출 방지)
