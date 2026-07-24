# WEEK_04 — 4주차 작업 계획

**날짜:** 2025-07-27 | **발표자:** 김비오 | **챕터:** Ch.04 (2/2) | **난이도:** 고급

## 이번 주 목표
1. 커스텀 서브에이전트·에이전트 팀·CLI 동적 에이전트 개념 정리
2. 3주차 '뉴스+재무 병렬화'를 확장 → **포트폴리오 분석 에이전트 팀** 구축
3. YAML 정의파일 + 오케스트레이션 스크립트로 실제 시연

## 챕터 핵심 개념 (발표: 자신의 말로)
- **커스텀 서브에이전트(4-3)**: `.claude/agents/*.md`로 정의하는 전용 일꾼. 정의파일은 영구, 실행 인스턴스는 작업 후 소멸.
- **에이전트 팀(4-4)**: 리더+팀원이 태스크 목록·메일박스로 협업. **파일 소유권**으로 충돌 방지.
- **CLI 동적(4-5)**: `--agent`(등록 호출) vs `--agents`(즉석 JSON). 헤드리스 `claude -p`로 자동화.

## 주식 웹 적용 — 포트폴리오 분석 에이전트 팀
**한 줄:** 여러 보유 종목을 3명의 전문가 에이전트가 **병렬 분석**해 포트폴리오 리포트를 생성.
기존 `data/*.json`을 재사용 → Pro 요금제 사용량 절약 + 시연 안정성.

### 팀 구성 (파일 소유권 분리)
| 에이전트 | 역할 | 읽는 것 | 출력 |
|---|---|---|---|
| `portfolio-valuation` | 종목별 고·저평가 판정 | `data/{code}_fundamentals.json` | 종목별 밸류 점수 |
| `portfolio-risk` | 집중도·변동성 리스크 | `data/{code}_market.json` + 비중 | 리스크 지표 |
| `portfolio-allocation` | 목표비중 대비 리밸런싱 | `data/portfolio.json` | 매수/매도/유지 |
| (리더) | 3개 결과 병합·리포트 | 위 3개 출력 | `outputs/portfolio_report_*.html` |

### 산출물 (파일)
- [x] `.claude/agents/portfolio-valuation.md` — 밸류에이션 전문가 정의
- [x] `.claude/agents/portfolio-risk.md` — 리스크 전문가 정의
- [x] `.claude/agents/portfolio-allocation.md` — 배분 전문가 정의
- [x] `portfolio-team.yaml` — 팀 구성·파일 소유권·출력 스키마 (YAML 정의파일)
- [x] `scripts/orchestrate_portfolio.py` — CLI 진입점 (orchestrate_stock_agents.py 확장)
- [x] `data/portfolio.example.json` — 샘플 보유종목(005930·000660·009150·008490 + 비중)
- [x] `outputs/portfolio_report_YYYY-MM-DD.html` — 시연 산출 리포트

### 시연 시나리오
python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json --save
→ valuation·risk·allocation 3개 병렬 실행 → 종합 리포트 생성

## 발표자 작업 목록
- [x] Ch.04 정독 + 핵심 개념 3가지 정리 (슬라이드 완료)
- [ ] 위 산출물 개발 (Claude Code로 생성·검증)
- [ ] 기존 종목 데이터로 테스트 (정상·경계·실패 3케이스)
- [ ] feature/04-Bio-PortfolioAgentTeam 브랜치 PR 오픈
- [ ] Notion 발표 페이지 초안 작성 (D-1까지)

## 발표 구성 (70분)
| 시간 | 내용 |
|------|------|
| 0~5분 | 지난 주 이어서 + 이번 챕터 위치 |
| 5~25분 | 커스텀 서브에이전트·팀·CLI 핵심 개념 |
| 25~55분 | 포트폴리오 분석 팀 실시연 |
| 55~70분 | Q&A + 막힌 점 + 다음 주 예고 |

## 팀원 사전 준비
열정으로 무장

## 다음 주 예고
발표자: **서동필** | 챕터: Ch.05~06