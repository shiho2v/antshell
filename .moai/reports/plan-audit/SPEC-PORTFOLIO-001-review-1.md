# SPEC Review Report: SPEC-PORTFOLIO-001

Iteration: 1/3
Verdict: **FAIL**
Overall Score: **0.69** (Tier M PASS 기준 0.80 미달)

> Reasoning context ignored per M1 Context Isolation. 본 감사는 `.moai/specs/SPEC-PORTFOLIO-001/`의 4개 산출물과 저장소 실물만을 입력으로 삼았다. 작성자의 사고 과정·이전 초안·대화 기록은 사용하지 않았다.
> 감사 범위: Tier M 입력 계약(spec.md + plan.md + acceptance.md) + progress.md. 저장소 접근은 전부 읽기 전용이었고 SPEC 파일·코드·git 상태를 변경하지 않았다.

---

## Must-Pass Results

- **[PASS] MP-1 REQ number consistency**
  `grep -o '^\*\*REQ-[0-9]*\*\*' spec.md | sort | uniq -c` → REQ-001 … REQ-015 각 1회, 총 15개. 결번·중복 없음, 3자리 제로패딩 일관.

- **[FAIL] MP-2 EARS/GEARS format compliance** — *요구사항 계층(`REQ-XXX` in spec.md)에 대해 판정함. 검증 계층(acceptance.md의 `AC-XXX`)은 Given-When-Then이 정상이며 Group 4에서 별도 채점함.*
  spec.md:103 `**REQ-012** [Event-driven] **When** 인증되지 않은 사용자가 `/portfolio`에 접근하면, 프론트엔드는 대시보드와 동일하게 `/login`으로 이동시킨다. **대시보드에는 `/portfolio`로 이동하는 링크가 존재한다.**`
  한 REQ 항목 안에 서로 독립적인 두 요구사항(Event-driven 리다이렉트 / Ubiquitous 대시보드 링크)이 묶여 있어, 항목 전체가 5개 GEARS 패턴 중 **정확히 하나**에 대응하지 않는다. 나머지 14개 항목은 패턴에 부합한다(REQ-013의 `[Where]` 태그 오기는 MINOR로 별도 기록). 단일 항목·한 줄 수정으로 해소 가능한 실패이며 구조적 형식 붕괴는 아니다.

- **[PASS] MP-3 YAML frontmatter validity**
  spec.md:2-14 — `id`/`title`/`version`("0.1.0" 인용)/`status`(draft)/`created`/`updated`(2026-09-20 ISO)/`author`/`priority`(P1)/`phase`("v1.0.0" — 라이프사이클 토큰 아님)/`module`/`lifecycle`(spec-anchored)/`tags`(인용 CSV) 12개 전부 존재. snake_case 별칭(`created_at`/`updated_at`/`labels`/`spec_id`) 0건. 선택 필드 `tier: M` 추가.

- **[N/A] MP-4 Section 22 language neutrality**
  단일 프로젝트 범위(python 백엔드/스크립트 + typescript 프론트엔드). 16개 언어 공통 툴링을 다루는 템플릿 바인딩 콘텐츠가 아니므로 해당 없음 → 자동 통과.

- **[PASS] MP-5 D7 cross-SPEC reconciliation**
  `grep -Eo 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' spec.md | sort -u` → SPEC-API-001, SPEC-CHART-001, SPEC-NEWS-001, SPEC-PORTFOLIO-001.
  `grep '^status:' .moai/specs/SPEC-API-001/spec.md` → `status: draft`
  `grep '^status:' .moai/specs/SPEC-CHART-001/spec.md` → `status: in-progress`
  `ls -d .moai/specs/SPEC-NEWS-001` → `No such file or directory`
  retired/superseded/archived 상태인 참조 SPEC 없음 → BLOCKING 0건. SPEC-NEWS-001 미존재는 D7-5 SHOULD 등급(NIT n2).

- **[PASS] MP-6 D8 cross-platform discipline**
  `grep -c 'syscall' spec.md` → `0`. SPEC 본문에 `syscall` 언급 없음 → D8-4 자동 PASS.

- **[PASS] MP-7 clarification gate**
  `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-PORTFOLIO-001/` → `none`. plan.md 존재, research.md는 Tier M이라 부재. 미해결 마커 0건.

---

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.50 | 0.50 — 다수 요구사항이 해석을 요구, 합리적 엔지니어가 서로 다르게 구현할 수 있음 | spec.md:89 REQ-006 "§4의 필수 키" 집합 미정의(M1 스크립트·M2 백엔드 두 계층에서 독립 구현됨); `--sample` 옵션 동작 전면 미정의(spec.md에 `--sample` 문자열 0회); spec.md:126 `portfolio_file` 상대/절대 경로 형식 미지정; §4 응답 스키마가 `agent` 키를 조용히 탈락시키나 어떤 REQ/AC도 이를 명시하지 않음 |
| Completeness | 0.75 | 0.75 — 섹션·frontmatter 완비, 요구사항 목록에 결손 1건 | HISTORY(17)/개요(25)/요구사항(73)/인수기준 포인터(113)/데이터 계약(117)/제외 범위(194) 전부 존재. `### Out of Scope — <topic>` H3 8개, 각 `-` 불릿 보유(spec.md:196-219) → SC-6 충족. 결손: acceptance.md:75 DoD가 요구하는 `--sample` 산출물에 대응하는 REQ가 §2에 없음 |
| Testability | 0.75 | 0.75 — 대부분 이진 판정 가능, 소수가 최소한의 해석을 요구 | AC-001~AC-008·AC-016(9건)은 자동화 가능한 이진 조건. acceptance.md:44 AC-014 "시각적으로 구분된다"는 판단 개입; acceptance.md:28 AC-006 "`/`·`\`를 포함한 절대 경로 조각"은 이진 술어 아님; acceptance.md:46 AC-015 "응답이 변경 전과 동일"은 기준선 캡처 없음 |
| Traceability | 0.75 | 0.75 — REQ 1건의 매핑이 간접적 | acceptance.md:87-103 매핑표 — 15개 REQ 전부 ≥1 AC 보유, 16개 AC 전부 실재 REQ 참조, 고아 AC 0건·미커버 REQ 0건(작성자 주장 검증됨). 감점: AC-016(acceptance.md:48)이 REQ-001을 인용하지만 REQ-001의 저장 의무가 아닌 서빙 동등성을 검증 → 간접 매핑. REQ-001의 원자적 저장 절(spec.md:77)은 어떤 AC도 실행하지 않음 |

**Aggregate = (0.50 + 0.75 + 0.75 + 0.75) / 4 = 0.6875 ≈ 0.69** — Tier M PASS 임계 0.80 미달.

---

## 5-Section Evidence Report

### 1. Claim (주장)

본 감사가 주장하는 바는 다음 4가지다.

1. **트레이서빌리티는 구조적으로 건전하다.** REQ 15개 / AC 16개, 결번·중복·고아 0건이며 작성자의 "전체 커버" 주장은 성립한다. 단, 일부 AC가 인용한 REQ의 핵심 의무를 실제로는 행사하지 않는다.
2. **plan.md §A.1 / spec.md §1의 저장소 사실 주장은 1건의 중대한 누락을 제외하면 정확하다.** 스크립트 동작·백엔드 라우트·프론트엔드 구조·데이터 파일 형태는 실물과 일치한다. CI 기술은 불완전하다.
3. **데이터 계약에 구현 분기를 유발하는 미정의 지점이 2개 있다** — REQ-006의 "필수 키" 집합, 그리고 `--sample` 모드 전체.
4. **독립성 주장은 성립한다.** SPEC-API-001(draft, 미구현) / SPEC-CHART-001 내부에 대한 숨은 의존은 없고, `GET /api/portfolio`는 기존 라우트와 충돌하지 않는다.

### 2. Evidence (증거 — 실행한 명령과 그 출력)

**(E-1) 스크립트 현재 상태 — spec.md §1.1 / plan.md §A.1 검증**

`Read scripts/orchestrate_portfolio.py` (241행 전체):
- L229 `print(json.dumps(merged, ensure_ascii=False, indent=2))` — 병합 결과는 **표준 출력에만** 나간다. ✓ 주장 일치
- L231-236 `if args.save:` → `out_path = OUTPUTS_DIR / f"portfolio_report_{today}.html"` / `out_path.write_text(render_html(merged), ...)` — `--save`는 **HTML 1개만** 기록, JSON 저장 없음. ✓ 주장 일치
- L92-100 `subprocess.run([claude_bin, "-p", "--output-format", "json", "--allowedTools", "Read,Bash"], ..., timeout=240)` — `claude -p` 호출, 타임아웃 **240초**. ✓ 주장 일치
- 허용 목록 검사: 파일 전체에 존재하지 않음. `load_portfolio`(L62)는 JSON 로드만, `build_prompt`(L68)는 `holdings` 공백 검사(`ValueError`, L71)만 수행. ✓ REQ-003이 신규 요구임이 확인됨
- L71 `raise ValueError("portfolio.holdings가 비어 있습니다.")` — acceptance.md:58의 "빈 배열" 엣지 케이스 서술과 문자열까지 일치. ✓

**(E-2) 서브에이전트 출력 스키마 — REQ-008 "risk 비중 제거"의 실체 검증**

`Read .claude/agents/portfolio-risk.md` L33-51 출력 스키마: `results[]`에 `actual_weight_pct` **존재**(L42), `total_market_value`(L36), `volume_state`(L46), `overall`(L48).
`Read .claude/agents/portfolio-allocation.md` L33-51: `results[]`에 `actual_weight_pct` **존재**(L45), `total_asset`(L36), `cash`(L37), `target_weight_pct`·`drift_pct`·`rebalance_amount`.
`portfolio-risk.md` L19 "총 평가금액으로 실제 비중(actual_weight_pct) 계산" vs `portfolio-allocation.md` L19 "cash 포함 총자산으로 각 종목의 **actual_weight_pct** 계산" — **분모가 다르다는 §1.4의 진단이 에이전트 정의 수준에서 재확인된다.**
→ REQ-008은 실제 데이터 형태에 대해 성립한다. `risk.results[].actual_weight_pct`는 실재하는 필드이며 제거 대상으로 지목한 것이 정확하다.
`Read .claude/agents/portfolio-valuation.md` L34-48: `verdict` 5값 enum, `score`, `basis`, `op_income_growth_pct`는 `number | "turnaround" | null` — spec.md:133의 `number | null`은 **`"turnaround"` 문자열 케이스를 누락**했다(MINOR 계열, 아래 표 m11).

**(E-3) 백엔드 라우트 목록 — REQ-015 / 경로 충돌 검증**

`Read backend/app/main.py`:
`/health`(L47), `/api/settings/notion` GET(L123)·PUT(L132)·DELETE(L165), `/api/report/notion`(L183), `/api/github/issues`(L236), `/api/stocks/{code}/ohlcv`(L311), `/api/stocks/{code}/indicators`(L327).
→ REQ-015(spec.md:111)가 열거한 7개 라우트와 **정확히 일치**, 누락 0건.
→ `/api/portfolio` 경로는 존재하지 않으며 `/api/stocks/{code}/...`와 접두 충돌하지 않는다. ✓ 독립성 주장 성립.
`DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"`(L277), `CHART_STOCK_CODES = frozenset({"005930","000660","009150","008490"})`(L280), `_read_ohlcv_document`(L290), 허용목록-선-검사 `_load_ohlcv_or_404`(L304-308). → plan.md §A.1 / §A.2 "구현 패턴 계승" 주장 전부 일치.

**(E-4) 데이터 파일 형태**

`cat data/portfolio.example.json` — `as_of: "2026-07-25"`, `cash: 5000000`, holdings 4종목(005930/000660/009150/008490) = §1.3 허용목록과 일치. ✓ spec.md:128의 "실행일과 다를 수 있음" + plan.md:21 "`as_of` 실측값 `2026-07-25`" 일치.
`cat data/portfolio.edge.json` — holdings 3종목: `005930`(허용), **`005380`**, **`999999`**(둘 다 목록 밖), `cash: 1000000`. ✓ AC-003의 고정 입력 주장 성립.
`ls data/` — 4종목 각각 `_market.json`·`_fundamentals.json`·`_ohlcv.json` 전부 존재, `portfolio_analysis.json` 부재. `005380_market.json`·`005380_fundamentals.json` 부재(= acceptance.md:55의 근거 성립), `005380_agents.json`은 존재.
`git check-ignore -v data/portfolio_analysis.json` → `NOT ignored` — M1의 "생성 후 커밋" 경로가 .gitignore에 막히지 않음을 확인.

**(E-5) 프론트엔드**

`sed -n '1,60p' frontend/src/app/dashboard/page.tsx`:
- L16 `const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'` — **AC-013이 인용한 `dashboard/page.tsx:16`이 정확히 일치.**
- L11 `import Link from 'next/link'` ✓, L53 `if (!data.user) router.replace('/login')` ✓, L117-122 `<Link href="/settings">` ✓, L18 `MOCK_STOCKS` / L25 `MOCK_NEWS` ✓
`ls frontend/src/app/` → dashboard, login, signup, settings, + layout.tsx/page.tsx/globals.css. **`portfolio` 없음** ✓
`ls -a frontend/` → `.eslintrc.json` 존재, `tsconfig.json` 존재 → `npm run lint` / `npx tsc --noEmit` 실행 가능.
`sed -n '1,40p' frontend/package.json` — devDependencies: `@types/*`, `autoprefixer`, `eslint`, `eslint-config-next`, `postcss`, `tailwindcss`, `typescript`. **jest / vitest / @testing-library 없음 → 프론트엔드 컴포넌트 테스트 인프라 부재.**

**(E-6) CI 게이트 — plan.md §A.1 CI 행 검증**

`cat .github/workflows/ci.yml` 단계 순서:
1. `pip install -r backend/requirements.txt ruff pytest`
2. `npm ci` (frontend)
3. `ruff check backend/`
4. `npm run lint` (frontend)
5. **`pytest backend/tests/ -v`**
6. **`npm run build` (frontend)**
7. `pip-audit` (continue-on-error: true)
8. `npm audit` (continue-on-error: true)

plan.md:30 CI 행은 "`pip install …` → `ruff check backend/` → `npm run lint`"에서 **끝난다** — 단계 5·6(둘 다 차단 게이트)을 누락했다.
결과적 사실: 테스트 게이트 경로가 `backend/tests/`로 한정되므로 **`scripts/tests/`는 CI에서 실행되지 않는다**(기존 `scripts/tests/test_fetch_ohlcv.py`도 동일 상태). AC-001~AC-003의 검증 파일이 CI 밖에 놓인다.

**(E-7) ruff 실제 동작 — plan.md §A.5 "줄 길이" 리스크 검증**

`cat ruff.toml` — `select` 미지정, `[lint.flake8-bugbear] extend-immutable-calls`만 설정. → ruff 기본 규칙(E4, E7, E9, F) 적용, **E501(line-too-long)은 미포함**.
실측: 200자 라인 파일 생성 후
`ruff check --config ruff.toml /tmp/.../longline.py` → `All checks passed!` / `exit=0` (ruff 0.16.8)
→ plan.md:134 "신규 코드의 **줄 길이**·미사용 import로 파이프라인이 멈춘다"의 앞 절은 **거짓**이다. 미사용 import(F401)만 실제 게이트다.

**(E-8) 의존성 / 테스트 픽스처 패턴**

`cat backend/requirements.txt` — fastapi/uvicorn/httpx/python-dotenv (pytest 없음 ✓ plan 주장 일치).
`cat backend/requirements-dev.txt` — `pytest==8.3.4`, `pytest-cov==6.0.0`, `httpx`. **plan.md §A.1은 이 파일의 존재를 언급하지 않는다.** CI는 `requirements-dev.txt`를 설치하지 않으므로 `pytest-cov`가 없고, acceptance.md:69 "신규 백엔드 코드는 커버리지 측정 대상에 포함되어야 한다"는 CI에서 강제 불가하다.
`grep -n "monkeypatch\|DATA_DIR" backend/tests/test_chart.py` → L56 `monkeypatch.setattr(main, "DATA_DIR", tmp_path)` — 기존 테스트는 **모듈 전역 `DATA_DIR`를 교체**한다. plan.md:92의 신규 `PORTFOLIO_ANALYSIS_FILE` 상수가 import 시점에 `DATA_DIR / "…"`로 확정되면 이 교체가 무력화된다.

**(E-9) `--sample` 산출물 추적**

```
spec.md   | '--sample' 문자열 0회 | '--save-json' 3회
plan.md   | '--sample' 5회        | '--save-json' 2회
acceptance.md | '--sample' 1회 (L75 DoD) | '--save-json' 4회
```
`grep -n 'sample' spec.md` → L99(REQ-010, `source`가 `"sample"`일 때의 표기), L124(§4 `source` enum 값). **CLI 옵션 `--sample`을 정의하는 요구사항은 §2에 존재하지 않는다.**
`grep -n 'sample' acceptance.md` → L36(AC-010), L48(AC-016), **L75 DoD "`--save-json`·`--sample` 추가"**.
→ DoD가 산출물로 요구하지만 REQ도 AC도 없다.

### 3. Baseline-attribution (baseline 귀속)

- 저장소: `/home/woojun/playground/antshell`, 브랜치 `main`, 대화 시작 시점 스냅샷 기준 HEAD `29395f5`.
- 모든 사실 확인은 **이 실행, 이 트리**에서 수행했다. 외부 기억·이전 감사 결과·다른 SPEC의 측정값을 재사용하지 않았다.
- 도구 버전: `ruff 0.16.8` (`/home/woojun/.local/bin/ruff`, `ruff --version`로 실측).
- SPEC 산출물 크기: spec.md 218행 / plan.md 177행 / acceptance.md 103행 / progress.md 37행 (`wc -l` 실측). **4개 파일 전체를 읽었다** — 표본 추출 아님.
- REQ/AC 계수는 작성자 주장을 신뢰하지 않고 `grep -o … | sort | uniq -c`로 독립 재계수했다(결과: REQ 15 / AC 16, 작성자 주장과 일치).

### 4. Gaps (미검증 — 본 감사가 관찰하지 못한 것)

- **`scripts/orchestrate_portfolio.py`를 실행하지 않았다.** spec.md §1.1 / plan.md §A.1이 "2026-09-20 스크립트 1회 실행"으로 얻었다고 주장하는 실측값 — `risk` 47.8 vs `allocation` 44.54(spec.md:67), 서흥 `volume_state: "stale"`(spec.md:167), `as_of: "2026-07-25"`(plan.md:21) — 중 **`as_of`만 `data/portfolio.example.json`에서 독립 확인**했다. 비중 두 값과 `stale` 값은 원본 실행 로그가 저장소에 남아 있지 않아 재현하지 못했다. 두 주장은 에이전트 정의(E-2)와 **정합적이지만 실측 재확인된 것은 아니다.**
- **`data/portfolio_analysis.json`이 존재하지 않으므로** 실제 병합 결과의 전체 키 구조를 §4 스키마와 대조하지 못했다. §4의 검증은 서브에이전트 정의 파일의 선언 스키마(E-2)를 통한 간접 검증이다.
- **백엔드·프론트엔드 테스트를 실행하지 않았다.** `pytest backend/tests/`, `npm run lint`, `npm run build`는 모두 미실행 — AC-015가 전제하는 "기존 테스트 통과" 현 상태는 본 감사의 관찰 범위 밖이다.
- **`claude -p` 호출 가능 여부를 확인하지 않았다.** plan.md §A.9가 스스로 미해결로 둔 항목이며 본 감사도 해소하지 못했다.
- **프론트엔드 화면 렌더링을 관찰하지 않았다.** AC-009~AC-014의 실현 가능성은 코드·패키지 구성으로부터의 추론이다.
- **acceptance.md:57의 "현금이 0" / L58의 "빈 배열" 엣지 케이스**는 대응 픽스처가 저장소에 없어(`data/`에 cash=0 포트폴리오 파일 부재) 실행 검증 경로를 확인하지 못했다.

### 5. Residual-risk (잔여 위험 — 관찰했음에도 남는 위험)

- **`--sample` 결정론 규칙이 구현자 재량으로 남는다.** plan.md:65의 "고정 규칙으로 분석 결과 형태를 만들어"만으로는, 모든 종목을 `verdict: "unknown"`으로 채운 샘플도 적법하다. 그 경우 커밋되는 데이터 파일로는 AC-009(판정·점수 표시)와 AC-014(정상 판정과 `unknown`의 시각적 구분)를 **동시에 실증할 수 없다**. `claude -p`가 실패해 `--sample`이 주 경로가 되면(plan.md §A.9) 이 위험이 현실화된다.
- **REQ-006의 "필수 키" 집합이 M1(스크립트 측 REQ-002)과 M2(백엔드 측)에서 서로 다르게 구현될 수 있다.** 두 마일스톤은 plan.md §A.4상 병렬 진행 가능이므로 상호 조정 기회가 없다. 저장은 통과하는데 서빙이 500을 내는(또는 그 반대) 비대칭이 남는다.
- **CI가 `scripts/tests/`를 실행하지 않으므로**, AC-001~AC-003의 검증은 SPEC 종료 후 조용히 회귀 감시 대상에서 벗어난다. M4에서 1회 수동 실행하고 끝난다.
- **`npx tsc --noEmit`(DoD)와 `npm run build`(실제 CI 게이트)가 어긋난다.** `next build`가 타입 검사를 포함하므로 실무상 겹치지만, DoD가 실제 차단 게이트를 이름으로 호명하지 않아 로컬 통과 후 CI 실패 여지가 남는다.
- **미인증 `GET /api/portfolio` + 인증 리다이렉트(REQ-012)의 비대칭.** 현재 데이터는 저장소에 커밋된 샘플이므로 실질 위험은 낮으나, §5가 범위 밖으로 둔 "사용자별 보유 종목"이 후속 SPEC에서 들어오는 순간 이 엔드포인트는 무인증으로 개인 보유·현금 잔고를 노출한다. SPEC은 그 전이 조건을 명시하지 않는다.
- **Windows/cp949 위험은 완화되어 있으나 신규 경로에 대해 미검증.** plan.md:133의 완화책(전부 `__file__` 기준, `encoding="utf-8"` 명시, `sys.stdout.reconfigure` 유지)은 기존 코드(L216-217, L235)와 정합적이지만, 신규 `--save-json` 저장 함수가 이를 따르는지는 구현 시점에만 확인 가능하다.

---

## Defects Found (structured defect-list)

| # | ID | 위치 | 설명 | Severity | Class | Required fix |
|---|---|---|---|---|---|---|
| D1 | SAMPLE-UNSPEC | spec.md §2 (`--sample` 0회) / plan.md:63-67, 81 / acceptance.md:75 | `--sample` CLI 모드가 **요구사항도 인수기준도 없이** M1 산출물과 DoD 체크리스트에 등장한다. 허용목록 검사 적용 여부, REQ-002의 비덮어쓰기 준수 여부, 생성되는 `verdict`/`overall`/`action` 값 분포가 전부 미정의다. plan.md §A.9에 따르면 `claude -p` 실패 시 **이것이 유일한 데이터 생성 경로**가 된다. | **BLOCKER** | blocking | 택1: (a) `REQ-016 [Event-driven] When --sample 옵션으로 실행하면, 스크립트는 에이전트를 호출하지 않고 data/portfolio.example.json으로부터 결정론적 규칙으로 §4 스키마를 만족하는 결과를 생성해 source:"sample"로 저장하며, REQ-003의 허용목록 검사와 REQ-001의 원자적 저장을 동일하게 적용한다`를 추가하고 대응 AC-017(동일 입력 2회 실행 시 바이트 동일 + 9개 최상위 키 + 최소 1종목은 `unknown`이 아닌 판정)을 신설한다. (b) `--sample`을 §5 제외 범위로 옮기고 acceptance.md:75 DoD에서 제거한다. |
| D2 | SCHEMA-PREDICATE | spec.md:89 (REQ-006), spec.md:79 (REQ-002), acceptance.md:28 (AC-006) | "§4의 필수 키"가 어디에도 열거되지 않는다. 최상위 키만인지, `allocation.results` 같은 중첩 키까지인지, `meta` 구성 5개 필드의 부재를 스키마 위반으로 볼지 불명. AC-006은 `allocation` 누락 1케이스만 고정한다. M1(저장 전 검사)과 M2(읽기 시 검사)가 **병렬 구현되므로** 불일치가 조정되지 않는다. | MAJOR | blocking | spec.md §4에 `필수 키(REQ-002·REQ-006 공통 술어)` 소절을 추가해 정확한 집합을 열거한다 — 예: 최상위 9키 + `valuation.results`·`risk.results`·`allocation.results`가 list일 것 + `allocation.total_asset`·`allocation.cash`가 number일 것. AC-006을 이 집합의 대표 3케이스(최상위 키 누락 / results 비-list / 파싱 불가)로 확장한다. |
| D3 | GEARS-REQ012 | spec.md:103 | REQ-012가 Event-driven 리다이렉트와 Ubiquitous 대시보드 링크 **두 요구사항**을 한 번호에 담아 GEARS 패턴 1:1 대응이 깨진다(MP-2 FAIL 근거). AC-012도 두 절을 한 AC에 묶어 부분 실패 시 귀속이 모호해진다. | MAJOR | blocking | REQ-012를 리다이렉트만 남기고, 대시보드 링크를 `REQ-016 [Ubiquitous] 대시보드는 /portfolio로 이동하는 링크를 제공한다`로 분리한다. AC-012도 AC-012(리다이렉트) / AC-017(링크 존재·이동)로 분리하고 매핑표를 갱신한다. |
| D4 | CI-INCOMPLETE | plan.md:30 (A.1 CI 행) | CI 기술이 `npm run lint`에서 끊겨 실제 차단 게이트 2개(`pytest backend/tests/ -v`, `npm run build`)를 누락한다. 귀결: `scripts/tests/test_orchestrate_portfolio.py`(AC-001~AC-003)는 CI에서 **한 번도 실행되지 않는다**. §A.5 리스크 표에도 이 사실이 없다. | MAJOR | blocking | plan.md:30을 실제 8단계로 정정한다. 그 위에서 택1: (a) `.github/workflows/ci.yml`의 테스트 단계를 `pytest backend/tests/ scripts/tests/ -v`로 확장하는 작업을 M4 산출물에 추가, 또는 (b) "스크립트 테스트는 CI 밖 수동 게이트"임을 §A.5 리스크 행으로 명시하고 acceptance.md 품질 게이트에 그 한계를 기록한다. |
| D5 | FE-AC-UNVERIFIABLE | acceptance.md:66, 34-44 (AC-009~AC-014) / frontend/package.json devDependencies | 16개 AC 중 6개의 검증 수단이 "컴포넌트 테스트 또는 브라우저 실측 + 기록"인데, 저장소에 프론트엔드 테스트 프레임워크가 없다(jest/vitest/@testing-library 부재 — E-5). 실제 경로는 수동 검증뿐이나, acceptance.md:63이 요구하는 "**문서화된** 수동 검증 절차"를 어느 마일스톤도 산출물로 만들지 않는다. | MAJOR | blocking | M3(또는 M4) 산출물에 "AC-009~AC-014 수동 검증 절차"를 추가한다 — 각 AC별로 (실행 명령 → 진입 경로 → 관찰 대상 → PASS 조건)을 `docs/weekly/WEEK_10.md` 또는 SPEC 디렉터리에 기록하고, progress.md의 PASS/FAIL 매트릭스가 그 문서를 인용하도록 한다. 테스트 프레임워크 도입은 범위 밖임을 §5에 명시한다. |
| D6 | ATOMIC-UNTESTED | spec.md:77 (REQ-001 마지막 문장) / acceptance.md:18(AC-001), 20(AC-002) | REQ-001의 "임시 파일 기록 후 교체" 절을 실제로 행사하는 AC가 없다. AC-001은 성공 후 내용만 확인하고, AC-002가 강제하는 실패는 **저장 이전**에 발생하므로 원자적 교체 경로를 지나지 않는다. 비원자적 `write_text` 구현도 두 AC를 모두 통과한다. | MAJOR | blocking | AC-002에 절을 추가하거나 AC-017을 신설한다 — 예: "저장 함수를 `os.replace` 직전에 예외를 던지도록 패치했을 때, 대상 파일의 바이트가 실행 전과 동일하고 같은 디렉터리에 잔여 임시 파일이 남지 않는다." |
| D7 | RUFF-CLAIM-FALSE | plan.md:134 | "신규 코드의 **줄 길이**·미사용 import로 파이프라인이 멈춘다" — 저장소 `ruff.toml`은 `select` 미지정이라 ruff 기본값(E4/E7/E9/F)만 적용되며 E501은 비활성이다. 200자 라인 실측 결과 `All checks passed! / exit=0`(E-7). 잘못된 리스크는 잘못된 완화책을 낳는다. | MINOR | optional | 해당 행을 "미사용 import(F401)·미정의 이름(F821) 등 ruff 기본 규칙 위반으로 멈춘다. 줄 길이(E501)는 현재 `ruff.toml`에서 비활성"으로 정정한다. |
| D8 | PATH-BINDING | plan.md:92 (`PORTFOLIO_ANALYSIS_FILE` 상수) vs plan.md:69 / backend/tests/test_chart.py:56 | 기존 테스트 전략은 `monkeypatch.setattr(main, "DATA_DIR", tmp_path)`로 전역을 교체한다. 신규 `PORTFOLIO_ANALYSIS_FILE`이 import 시점에 `DATA_DIR / "portfolio_analysis.json"`로 확정되면 `DATA_DIR` 교체가 무효가 되어 "임시 디렉터리 픽스처" 전략이 깨진다. | MINOR | optional | plan.md §A.2 구현 패턴에 한 줄 추가: 경로는 `_read_portfolio_document()` **내부에서** `DATA_DIR / PORTFOLIO_ANALYSIS_FILENAME`으로 해석한다(파일명 상수만 모듈 전역). 또는 테스트가 `PORTFOLIO_ANALYSIS_FILE`을 직접 교체하도록 plan에 명시한다. |
| D9 | AGENT-KEY-DROP | spec.md:130·139·152 (파일 스키마 `"agent": str`) vs spec.md:177-181 (응답 스키마) | 응답 스키마가 세 블록 모두에서 `agent` 키를 탈락시키지만, 이를 지시하는 REQ가 없고 검증하는 AC도 없다. `agent`를 그대로 통과시키는 구현도 AC-004·AC-008·AC-016을 전부 통과한다. REQ-008이 `risk.actual_weight_pct` 제거만 명시하므로 "명시된 것만 제거"로 읽는 구현자와 "스키마에 없으면 제거"로 읽는 구현자가 갈린다. | MINOR | optional | §4 응답 스키마 아래에 한 줄 추가: "`agent` 필드는 응답에 포함하지 않는다(진단용 메타이며 화면이 쓰지 않음)" 또는 반대로 "파일의 `agent`를 그대로 보존한다". AC-004에 해당 키 유무 단언을 추가한다. |
| D10 | AC006-VAGUE | acceptance.md:28 | "파일 시스템 경로(`/`·`\`를 포함한 절대 경로 조각)"는 이진 술어가 아니다. 본문에 `/`가 하나라도 있으면 실패로 볼지, 특정 접두사만 볼지 판정 규칙이 없다. | MINOR | optional | 구체 술어로 교체한다 — 예: "응답 본문에 `DATA_DIR`의 절대 경로 문자열, `portfolio_analysis.json` 파일명, `Traceback`, 예외 클래스명(`JSONDecodeError`·`KeyError` 등)이 포함되지 않는다." |
| D11 | AC007-DEADDEP | acceptance.md:30 | `requests` 호출 부재를 단언하지만 `requests`는 이 프로젝트의 의존성이 아니다(`backend/requirements.txt` 미포함). 검증 불가능하거나 무의미한 단언이다. | MINOR | optional | `requests`를 제거하고 실제 사용 라이브러리로 한정한다: `httpx`, `urllib.request.urlopen`, `subprocess.run`, `shutil.which`. 기존 `test_chart.py:148`의 `monkeypatch.setattr(main.urllib.request, "urlopen", fail_if_called)` 패턴을 인용한다. |
| D12 | AUTH-RATIONALE | spec.md:217-218 (§5 마지막 제외 항목) | 무인증 유지 근거를 "기존 무인증 라우트(`/api/github/issues`, `/api/stocks/...`)와 동일"로 든다. 그 두 라우트는 **공개 시장 데이터**를 서빙하고 신규 라우트는 **보유 수량·평가금액·현금 잔고**를 서빙한다 — 유비가 성립하지 않는다. 실질 위험은 낮으나(데이터가 이미 저장소에 커밋된 샘플) 근거가 틀려 있고, REQ-012의 로그인 리다이렉트가 반대 신호를 준다. | MINOR | optional | 근거를 사실에 맞게 교체한다: "서빙 대상이 저장소에 커밋된 고정 샘플이라 개인정보가 아니므로 무인증을 유지한다. §5의 '사용자별 보유 종목 입력'이 후속 SPEC에서 구현되는 시점에 본 엔드포인트의 인증 적용이 **선행 조건**이 된다." |
| D13 | COVERAGE-UNENFORCEABLE | acceptance.md:69 / .github/workflows/ci.yml:29 / backend/requirements-dev.txt | "신규 백엔드 코드는 커버리지 측정 대상에 포함되어야 한다"가 CI에서 강제 불가하다 — CI는 `pytest`만 설치하고 `pytest-cov`가 있는 `requirements-dev.txt`를 설치하지 않는다. plan.md §A.1도 `requirements-dev.txt`의 존재 자체를 기술하지 않는다. | MINOR | optional | plan.md §A.1에 `backend/requirements-dev.txt`(pytest 8.3.4 / pytest-cov 6.0.0) 행을 추가하고, acceptance.md:69를 "M4에서 `pip install -r backend/requirements-dev.txt && pytest --cov=app backend/tests/`를 로컬 1회 실행해 신규 코드 커버리지를 progress.md에 기록한다"로 실행 가능하게 바꾼다. |
| D14 | WHERE-MISLABEL | spec.md:105 (REQ-013) | `[Where]` 태그가 붙었으나 문장은 Where 절 구조가 없는 Ubiquitous 형태다(설정 분기를 괄호로 인라인). GEARS Where는 capability gate / static config를 **선행 절**로 세우는 패턴이다. | MINOR | optional | 택1: (a) 태그를 `[Ubiquitous]`로 정정, (b) 문장을 `Where NEXT_PUBLIC_API_URL이 설정되어 있으면 프론트엔드는 그 값을 사용하고, 그렇지 않으면 http://localhost:8000을 사용한다`로 재작성. |
| D15 | PORTFOLIO-FILE-FORM | spec.md:77 (REQ-001), spec.md:126 (§4 예시) / acceptance.md:18 (AC-001) | `portfolio_file` 값의 형식(저장소 루트 기준 상대 경로 vs 절대 경로)이 규정되지 않는다. §4 예시는 상대 경로지만 예시는 계약이 아니며, AC-001은 키 존재만 확인한다. 절대 경로가 들어가면 커밋되는 파일에 개발자 홈 경로가 남는다. | MINOR | optional | REQ-001에 "`portfolio_file`은 저장소 루트 기준 상대 경로(POSIX 구분자)로 기록한다"를 추가하고, AC-001에 `portfolio_file == "data/portfolio.example.json"` 단언을 넣는다. |
| D16 | AC015-NOBASELINE | acceptance.md:46 | "모든 라우트의 응답이 변경 전과 동일하다"는 기준선 캡처 절차가 없어 기계적으로 판정 불가하다. 실제 검증 가능한 절반은 "기존 테스트 3종 통과"뿐이다. | MINOR | optional | AC-015를 검증 가능한 형태로 좁힌다: "기존 백엔드 테스트(`test_chart.py`·`test_indicators.py`·`test_notion_settings.py`)가 전부 통과하고, `backend/app/main.py`의 기존 라우트 함수 본문 diff가 0줄이며(`git diff` 확인), 대시보드의 기존 5개 영역이 수동 확인 절차에서 정상 동작한다." |
| D17 | CALQUE-세축 | spec.md:27 | "밸류에이션·리스크·리밸런싱 **세 축**의 분석 결과" — `.claude/rules/moai/core/native-idiom-and-register.md`의 번역투 목록에 명시된 표현("3축 / 세 축" → "세 가지 핵심"). | NIT | optional | "세 갈래" 또는 "세 가지"로 교체. |
| D18 | SPEC-NEWS-MISSING | spec.md:200 | `SPEC-NEWS-001`을 참조하지만 `.moai/specs/SPEC-NEWS-001`이 존재하지 않는다(D7-5 SHOULD 등급 — 오타가 아니라 미래 SPEC에 대한 전방 참조로 보임). | NIT | optional | "별도 SPEC(가칭 `SPEC-NEWS-001`, 미작성)의 범위다"처럼 미존재를 명시한다. |
| D19 | A1-OMISSIONS | plan.md:28, 33 | `backend/tests/` 행이 `__init__.py`를 누락하고, `data/` 행이 4개 `*_agents.json`(`000660`/`005380`/`005930`/`009150`)을 누락한다. 핵심 주장("포트폴리오 테스트 없음", "`portfolio_analysis.json` 없음")은 모두 참이므로 결론에는 영향 없다. | NIT | optional | 두 행에 누락 파일을 보강하거나, "관련 파일만 발췌"임을 행 머리에 명시한다. |
| D20 | A4-WORDING | plan.md:122 vs plan.md:125 | 표의 M3 선행 조건이 "M2의 응답 계약 확정"인데, 표 아래 문단은 "M3는 `spec.md` §4의 응답 스키마를 계약으로 삼고 목 응답으로 작업한다"로 사실상 M2 비의존을 선언한다. 표만 읽으면 병렬 불가로 읽힌다. | NIT | optional | 표의 M3 선행 조건을 "`spec.md` §4 응답 스키마 확정(plan 시점에 완료)"으로 바꾸고, M2 완료 후 1회 대조를 별도 행/각주로 뺀다. |
| D21 | EDGE-NOFIXTURE | acceptance.md:57-58 | "현금이 0인 포트폴리오"와 "보유 종목이 빈 배열" 엣지 케이스에 대응 픽스처가 `data/`에 없고 대응 AC도 없다. 서술로만 존재해 run 단계에서 검증 여부가 임의가 된다. | NIT | optional | 엣지 케이스 절 머리에 "아래 항목 중 AC로 승격되지 않은 것은 구현 시 참고 사항이며 게이트가 아니다"를 명시하거나, `scripts/tests/`의 인라인 픽스처로 커버함을 기록한다. |
| D22 | SOURCE-ENUM-LOOSE | spec.md:174 (§4 응답 `"source": str`) vs spec.md:124 (파일 `"agent-team" \| "sample"`) | 응답 스키마가 `source`를 자유 문자열로 완화한다. REQ-010이 `"sample"` 분기 표기를 요구하므로 프론트엔드는 enum을 전제하는데 계약은 이를 보장하지 않는다. | NIT | optional | 응답 스키마도 `"source": "agent-team" \| "sample"`로 맞춘다. |
| D23 | VALUATION-TYPE | spec.md:133 vs `.claude/agents/portfolio-valuation.md`:42 | §4가 `op_income_growth_pct`를 `number \| null`로 선언하나, 에이전트 정의는 `number \| "turnaround" \| null`이다(직전 영업이익이 음수/0일 때 문자열 `"turnaround"`). 화면이 숫자 포맷팅을 가정하면 런타임에 깨진다. | MINOR | optional | §4의 타입을 `number \| "turnaround" \| null`로 정정하고, REQ-014의 "판정 불가" 처리 대상에 이 값이 포함되는지(또는 그대로 표기하는지)를 한 줄로 규정한다. |

**Severity 집계**: BLOCKER 1 · MAJOR 5 · MINOR 11 · NIT 6 (총 23)
**Class 집계**: blocking 6 · optional 17

---

## Regression Check (Iteration 2+ only)

해당 없음 — iteration 1.

---

## Recommendation

**Verdict FAIL의 직접 근거**: (1) MP-2 GEARS 형식 불합치 1건(D3), (2) BLOCKER 1건(D1), (3) aggregate 0.69 < Tier M 임계 0.80. M5 Must-Pass Firewall에 따라 다른 차원의 점수가 이를 상쇄하지 않는다.

**공정을 위해 함께 기록한다.** 이 SPEC은 평균 이상이다. 스크립트가 JSON을 저장하지 않는다는 사실을 실행으로 확인한 점, 비중 분모 불일치를 발견하고 표시 기준을 단일화한 점(§1.4 → REQ-008 → AC-008), SPEC-API-001 미구현 상태를 확인하고 `depends_on`을 선언하지 않기로 한 판단, 제외 범위 8개 항목의 구체성, `dashboard/page.tsx:16` 같은 행 단위 인용 — 모두 실물과 대조해 정확했다. 아래 수정은 재설계가 아니라 국소 보강이다.

**manager-spec 재위임 시 우선순위 (blocking 6건만 처리하면 재감사 통과 가능)**

1. **D1 (BLOCKER)** — `--sample`의 처분을 결정한다. 권장: REQ-016 + AC-017 신설(결정론성 + 9키 + 최소 1종목 비-`unknown` 판정). 이 결정이 D5·잔여 위험 1번과 연동되므로 먼저 처리한다.
2. **D3 (MP-2)** — spec.md:103의 REQ-012를 두 REQ로 분리하고 acceptance.md의 AC-012와 매핑표를 갱신한다. 한 줄 작업이며 MP-2 FAIL이 즉시 해소된다.
3. **D2** — spec.md §4에 "필수 키" 술어를 명시적으로 열거한다. M1/M2 병렬 진행의 유일한 계약 접점이므로 구현 착수 전에 확정되어야 한다.
4. **D6** — REQ-001 원자적 저장을 실제로 행사하는 AC를 추가한다(AC-002 확장 또는 AC 신설).
5. **D4** — plan.md:30 CI 행을 실제 8단계로 정정하고, `scripts/tests/`가 CI 밖이라는 사실을 §A.5 리스크 또는 M4 산출물로 반영한다.
6. **D5** — AC-009~AC-014 수동 검증 절차를 M3 또는 M4의 산출물로 승격한다.

**optional 17건은 오케스트레이터 재량이다.** 다만 D7(ruff 줄 길이 주장 오류)·D23(`"turnaround"` 타입 누락)·D8(`PORTFOLIO_ANALYSIS_FILE` 바인딩)은 run 단계에서 실제 시간을 잃게 할 항목이라 함께 반영할 것을 권한다. D17~D22는 문구 수준이며 수정하지 않아도 구현에 영향이 없다 — 일괄 반영을 강요하지 말 것.

**재감사 범위**: iteration 2는 위 blocking 6건의 delta에 한정한다(Retry Loop Contract). 전면 재감사는 필요하지 않다.

---

VERDICT: FAIL
