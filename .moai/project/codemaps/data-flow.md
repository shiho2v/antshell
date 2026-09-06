# data-flow.md — 데이터 흐름 (세 파이프라인 각각의 종단 추적)

수집일: 2026-09-06 | 근거: `generating-krx-report/SKILL.md`, `scripts/orchestrate_*.py`, `backend/app/main.py`, `frontend/src/app/**`, `frontend/src/lib/supabase.ts` 직접 확인

> `overview.md` §1과 `structure.md` §1이 세 파이프라인이 분리되어 있다고 선언한다. 이 문서는 그 선언을 각 파이프라인의 **실제 함수 호출 순서**로 증명한다.

## 흐름 [A] — KRX 리포트 생성 플로우

`generating-krx-report/SKILL.md`의 7단계 워크플로를 함수/스크립트 호출 순서로 나열한다.

```
1. 종목 식별 (Gate 1)
   resolve_security.py {TICKER}
       ↓ 실패 시 여기서 중단(보고서 생성 안 함)

2. 분석 계약 생성
   build_analysis_contract.py {TICKER} --mode balanced --request-type comprehensive
       ↓ required_modules / optional_modules 결정, unresolved_items 기록

3. 모듈 선택
   (계약이 8개 모듈 중 실행 대상을 정함 — 종합분석은 8개 전부)

4. 데이터 수집 → 정규화 → 계산
   fetch_dart_profile.py {TICKER}      ─┐
   fetch_dart_financials.py {TICKER}    │  DART Open API
   fetch_dart_events.py {TICKER}       ─┘
   fetch_krx_market.py {TICKER}            ← pykrx/Naver 경유 KRX 시세
       ↓
   normalize_data.py {TICKER}    (누적 → 분기단독 차분)
       ↓
   calculate_metrics.py {TICKER}  (모든 산술의 단일 지점 — Claude 미개입)
       ↓ data/*.json 에 축적

5. Evidence Pack 생성 및 검증 (Gate 2)
   build_evidence_packs.py {TICKER}
   validate_evidence.py {TICKER}
       ↓ 실패 시 보고서 생성 안 함

6. 모듈 분석 (Claude, evidence pack + metrics만 읽음 — 원시 API JSON 미열람)
   각 모듈: instructions.md/rubric.md 읽기 → judgment.json 작성
       정성 모듈(business/moat/risk/catalyst): 서수 등급(0~3)만 제출
       정량 모듈(quality/growth/valuation/trend): criteria: [] , 해석 서술만 제출
       ↓
   score_modules.py {TICKER}   (모듈 점수 + 종합점수, Python 전담)

7. 합성 → 검증 (Gate 3·4) → 저장
   claims 구조화 → data/{TICKER}_claims.json
       ↓
   템플릿 채움: full-report.html | compact-report.html | update-report.html
       ↓
   validate_report.py {TICKER} --claims ... --html ...
       ↓ 실패 시 검증 실패 보고서로 대체
   저장: outputs/{TICKER}_report_{as_of}.html
```

**이 흐름의 종착점**은 `outputs/{TICKER}_report_{as_of}.html` 파일이다. 이 HTML은 [C] 웹앱의 어떤 라우트에서도 읽히지 않는다(§3 참고). 대신 `company-blog-pipeline`이 이 리포트의 manifest/claims/module-results를 읽어 블로그 초안으로 변환하는 별도 후속 흐름으로 이어질 수 있다(`modules.md` §8 참고) — 이 후속 흐름도 [A] 파이프라인 내부에 머물며 [B]/[C]와는 무관하다.

## 흐름 [B] — 포트폴리오 에이전트 팀 플로우

`scripts/orchestrate_portfolio.py`의 실제 함수 호출 순서(`main()` 기준).

```
1. load_portfolio(Path(args.portfolio))
       ↓ data/portfolio.example.json 등을 읽어 dict 반환 (holdings, cash, ...)

2. build_prompt(portfolio)
       ↓ holdings에서 tickers_json/holdings_json/portfolio_json 3종을 조립해
         ORCHESTRATOR_PROMPT_TEMPLATE 에 삽입한 단일 프롬프트 문자열 생성
         (3개 서브에이전트를 "하나의 메시지에서 병렬 호출"하도록 명시적으로 지시)

3. run_orchestrator(prompt)
       ↓ subprocess.run([claude_bin, "-p", "--output-format", "json",
                          "--allowedTools", "Read,Bash"], input=prompt, ...)
       ↓ Claude Code 헤드리스 세션 내부에서 3개 서브에이전트가 병렬 실행:
             portfolio-valuation  ← data/{code}_fundamentals.json 만 읽음
             portfolio-risk       ← data/{code}_market.json 만 읽음
             portfolio-allocation ← data/{code}_market.json (시세만) 읽음
         (portfolio-team.yaml 의 ownership_rules.read_only_all 이 이 3-way
          읽기 공유를 "충돌 없음"으로 선언 — 전원 읽기 전용이므로)
       ↓ envelope["result"] 를 JSON.parse → merged: dict
         {portfolio_name, as_of, valuation{...}, risk{...}, allocation{...}}

4. print(json.dumps(merged, ...))     ← stdout 출력 (--save 없어도 항상 수행)

5. (옵션) --save 시:
   render_html(merged)
       ↓ 3개 표(밸류에이션/리스크/리밸런싱)를 가진 정적 HTML 문자열 생성
       ↓ outputs/portfolio_report_{today}.html 로 저장
         (portfolio-team.yaml 의 writable_by_leader_only 가 이 경로를
          "리더(오케스트레이터 스크립트)만 쓸 수 있음"으로 선언)
```

`orchestrate_stock_agents.py`는 동일한 구조를 2개 에이전트(`news-collector`, `financial-data`)로 단순화한 버전이며, `--save` 시 `data/{ticker}_agents.json`으로 저장한다(HTML 렌더링 없음).

**이 흐름의 종착점**은 `outputs/portfolio_report_*.html` 또는 `data/{ticker}_agents.json`이다. `backend/app/main.py`는 이 두 산출물을 참조하지 않는다.

## 흐름 [C] — 웹앱 요청 플로우

```
[브라우저]
    │
    ├─ 페이지 진입: /login, /signup, /dashboard
    │
    ├─(로그인/회원가입 페이지)
    │   supabase.auth.signInWithPassword({email, password})
    │   supabase.auth.signUp({email, password})
    │       ↓
    │   ──────────────→ Supabase Auth  (백엔드 미경유, 브라우저 직접 호출)
    │       ↓ 성공 시 router.push('/dashboard')
    │
    └─(대시보드 페이지, /dashboard)
        │
        ├─ useEffect: supabase.auth.getUser()
        │       ↓ 미인증이면 router.replace('/login')로 리다이렉트 (게이트 역할)
        │       ──────────────→ Supabase Auth
        │
        ├─ 렌더링: MOCK_STOCKS(하드코딩 4종), MOCK_NEWS(하드코딩 3건)
        │       ← 어떤 fetch도 거치지 않음. 소스는 page.tsx 파일 상단 상수뿐.
        │
        ├─ useEffect: fetch(`${API}/api/github/issues`)
        │       ──────────────→ backend/app/main.py  GET /api/github/issues
        │                           ──────────────→ GitHub REST API
        │       ← issues: GithubIssue[] 를 state에 반영, 실패 시 빈 배열
        │
        └─ 버튼 클릭 시: saveToNotion(stock)  (stock ∈ MOCK_STOCKS)
                ──────────────→ backend/app/main.py  POST /api/report/notion
                                    ──────────────→ Notion API (PATCH blocks/children)
                ← {ok, message} 를 토스트로 표시
```

**이 흐름이 [A]/[B]와 연결되지 않는 지점(명시 확인)**:

- `dashboard/page.tsx`는 `data/*.json`, `outputs/*.html`, `docs/blog/*.md` 중 어느 것도 `fetch`하지 않는다 — import도, HTTP 호출도 없다.
- `backend/app/main.py`는 자신의 두 프록시 라우트(`/api/report/notion`, `/api/github/issues`) 외에 `data/` 디렉터리를 여는 코드가 없다(grep 결과 0건, `structure.md` §1에서 이미 확인됨).
- `POST /api/report/notion`이 받는 `StockReportRequest`는 `MOCK_STOCKS`의 한 항목을 그대로 전송한 것이며, [A] 파이프라인이 계산한 실제 지표(성장률, CANSLIM 점수 등)와는 무관한 문자열 가격이다.
- 따라서 사용자가 대시보드에서 보는 "종목 가격·등락률·뉴스"는 [A]/[B] 어느 파이프라인의 산출물과도 대응하지 않는, 페이지 컴포넌트 안에 직접 작성된 상수다.

`product.md` §7 로드맵 1번("백엔드-분석 파이프라인 연결")이 실현되면 이 흐름 [C]의 렌더링 단계가 [A]의 `data/*.json`/`outputs/*.html`을 서빙하는 새 백엔드 엔드포인트로 대체될 예정이나, 현재 코드에는 그 연결이 존재하지 않는다.
