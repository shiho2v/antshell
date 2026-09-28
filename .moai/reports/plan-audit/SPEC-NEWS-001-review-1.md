# SPEC Review Report: SPEC-NEWS-001

Iteration: 1/3
Verdict: **FAIL**
Overall Score: **0.8625** (Tier M PASS 기준 0.80 충족 — 그러나 미해소 MAJOR 1건으로 게이트 불통과)

> Reasoning context ignored per M1 Context Isolation. 호출자가 전달한 작성자 측 설명·의도·이전 초안은 사용하지 않았다. 입력은 `.moai/specs/SPEC-NEWS-001/`의 4개 산출물(`spec.md` 244행 / `plan.md` 214행 / `acceptance.md` 162행 / `progress.md` 52행, 전문 읽음), 형제 SPEC의 1·2차 감사 보고서(**무엇을 점검할지의 목록으로만** 사용), 그리고 저장소 실물뿐이다.
> 저장소 접근은 전부 읽기 전용이었다. SPEC 파일·코드·git 상태를 변경하지 않았고, git 명령은 `git check-ignore`·`git status --porcelain` 두 건(읽기 전용 질의)만 사용했다.
> 형제 SPEC(`SPEC-PORTFOLIO-001`)의 1차 FAIL(0.69) → 2차 PASS(0.875) 기준선을 그대로 적용했다. 같은 결함 계열을 하나씩 대조한 결과는 「형제 결함 계열 대조표」에 있다.

---

## Must-Pass Results

- **[PASS] MP-1 REQ number consistency**
  ```
  $ grep -c '^\*\*REQ-[0-9]*\*\*' spec.md            → 15
  $ grep -o '^\*\*REQ-[0-9]*\*\*' spec.md | sort | uniq -c
        1 **REQ-001**  …  1 **REQ-015**   (각 정확히 1회, 15종)
  ```
  REQ-001~REQ-015 결번 0, 중복 0, 3자리 제로패딩 일관. 작성자 주장(15개)과 독립 재계수 결과가 일치한다. Tier M 상한 16 이하.

- **[PASS] MP-2 EARS/GEARS format compliance** — *요구사항 계층(`spec.md`의 `REQ-XXX`)에 대해 판정함. 검증 계층(`acceptance.md`의 `AC-XXX`)은 Given-When-Then이 정규 형식이며 Group 4에서 따로 채점했다 — 이 기준으로 감점하지 않았다.*
  15개 전부를 태그 대 문장 구조로 대조했다. 태그 분포: Ubiquitous 3(001·012·015), Event-driven 7(002·004·005·006·008·011 + 002 계열), Unwanted 3(003·007·013), State-driven 1(010), Where 2(009·014). 각 항목이 다섯 패턴 중 하나에 대응한다.
  판정을 투명하게 기록한다 — 한 항목은 엄격히 읽으면 논쟁 여지가 있으나 blocking으로 보지 않았다.
  - `spec.md:85` REQ-001 `[Ubiquitous]`는 (ㄱ) 운영자의 수동 생성·확인·커밋과 (ㄴ) "`scripts/` 아래 코드는 본 SPEC에서 수정하지 않는다"를 한 항목에 담는다. 형제 SPEC 1차의 MP-2 FAIL 근거(구 REQ-012 = 무관한 두 요구사항의 결합)와 형태가 유사하다. 다만 (ㄴ)를 "그 수동 단계를 **스크립트를 고치지 않은 채** 수행한다"는 같은 동작의 제약으로 읽는 해석이 자연스럽고, `AC-001`이 두 절을 한 판정 안에서 함께 행사한다(`git diff --stat scripts/` 공백). 형제 SPEC 2차가 REQ-001의 후행절을 "같은 동작의 관측 가능한 성질"로 통과시킨 잣대와 동일하게 적용해 PASS로 둔다. 별도 MINOR(D6)로 기록한다.
  - `spec.md:115` REQ-014 `[Where]`는 형제 SPEC 1차 D14가 권고한 (b) 재작성 형태("Where 환경 변수가 설정되어 있으면 … 그렇지 않으면 …")를 그대로 따른다 — 태그 오기 없음.

- **[PASS] MP-3 YAML frontmatter validity**
  `spec.md:2-14` — `id`(SPEC-NEWS-001, 정규식 적합) / `title`(인용) / `version`("0.1.0" 인용 semver) / `status`(draft, 8값 enum) / `created`(2026-09-20 ISO) / `updated`(2026-09-20 ISO) / `author`(정우준) / `priority`(P1) / `phase`("v1.0.0" — 금지된 라이프사이클 토큰 `plan`/`run`/`sync`/`mx` 아님) / `module`(경로형) / `lifecycle`(spec-anchored) / `tags`(인용 CSV) 12개 전부 존재, 타입 적합.
  거부 별칭(`created_at`·`updated_at`·`labels`·`spec_id`) 0건. 선택 필드 `tier: M` 존재, `depends_on` 필드 없음(`spec.md:31`은 "`depends_on`을 선언하지 않는다"는 본문 서술일 뿐 frontmatter 키가 아님 — 확인함).

- **[N/A] MP-4 Section 22 language neutrality**
  단일 프로젝트 범위(python 백엔드 + typescript 프론트엔드). 16개 언어 공통 툴링을 다루는 템플릿 바인딩 콘텐츠가 아니므로 해당 없음 → 자동 통과.

- **[PASS] MP-5 D7 cross-SPEC reconciliation**
  ```
  $ grep -Eoh 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/specs/SPEC-NEWS-001/*.md | sort -u
  SPEC-API-001  SPEC-CHART-001  SPEC-NEWS-001  SPEC-PORTFOLIO-001  SPEC-WATCHLIST-001
  $ grep '^status:' .moai/specs/SPEC-API-001/spec.md        → status: draft
  $ grep '^status:' .moai/specs/SPEC-CHART-001/spec.md      → status: in-progress
  $ grep '^status:' .moai/specs/SPEC-PORTFOLIO-001/spec.md  → status: draft
  $ ls -d .moai/specs/*/  → API-001, CHART-001, NEWS-001, PORTFOLIO-001  (WATCHLIST-001 부재)
  ```
  retired / superseded / archived 상태인 참조 SPEC 0건 → BLOCKING 0건. `SPEC-WATCHLIST-001` 미존재는 D7-5 SHOULD 등급이나, `spec.md:216`이 "후속 `SPEC-WATCHLIST-001`(**미작성**)의 범위로 남겨 둔다"로 부재를 명시했다 — 형제 SPEC 1차 D18이 권고한 처리를 선반영했으므로 신규 finding으로 올리지 않는다.

- **[PASS] MP-6 D8 cross-platform discipline**
  `grep -c 'syscall' spec.md` → `0`. D8-4 자동 PASS.

- **[PASS] MP-7 clarification gate**
  `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-NEWS-001/` → 출력 없음. `plan.md` 존재, `research.md`는 Tier M이라 부재. 미해결 마커 0건.

---

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.80 | 0.75 밴드 + 단일 정의 술어에 대한 명시 가산 | 가산 근거: 세 술어(「유효한 뉴스 문서」 `spec.md:148-164`, 「뉴스 정렬 규칙」 `:166-176`, 「안전한 링크」 `:178-188`)가 **각각 한 곳에서만** 정의되고 소비자 REQ를 제목에 명시하며, **위반이 아닌 경계까지** 열거한다(`:159-164`) — 형제 SPEC 1차 D2(술어 미정의)가 구조적으로 재발하지 않았다. 잔여 감점: 뉴스 항목의 **열거되지 않은 키**를 응답에 실을지 미정(D3, `spec.md:161` "위반이 아니다" 대 `:196` 응답 계약의 5키 열거); `AC-011`·`AC-010`(b)의 지연 상태 실현 수단 미정(D1); REQ-001의 이중 절(D6); `AC-015` ④의 `git status` 기대 출력이 커밋 시점에 따라 달라짐(D8) |
| Completeness | 1.00 | 1.00 — 필수 섹션·frontmatter 전부 존재 | HISTORY(17-21) / 개요·선행 SPEC 관계·현재 상태·설계 결정·종목 범위(25-79) / 요구사항(81-119) / 인수기준 포인터(121-123) / 데이터 계약(125-211) / 제외 범위(213-243) 전부 존재. `### Out of Scope — <topic>` H3 **10개**(`grep -c '^### Out of Scope'` → 10), 각 항목이 구체적 `-` 불릿 보유 → SC-6 충족. frontmatter 12/12. Tier M 3산출물 + progress.md. REQ 15 / AC 15 모두 Tier M 상한(16) 이하 |
| Testability | 0.70 | 0.75 밴드 − `AC-011` 실행 불가 감점 | 강점: 완전 자동 6건(AC-002~AC-007)이 전부 이진. 특히 `acceptance.md:29` AC-006이 「유효한 뉴스 문서」 **네 조건을 (a)~(f) 여섯 케이스로 각각 행사**한다(조건1=a, 조건2=b·c, 조건3=d, 조건4=e·f) — 형제 SPEC 2차의 잔여 결함 n4(조건 3·5 미행사)를 선제적으로 막았다. `acceptance.md:31` AC-007의 감시 대상이 `subprocess.run`·`shutil.which`·`httpx`·`urllib.request.urlopen`으로, 이 저장소에 실재하는 라이브러리만 지목한다(형제 1차 D11의 죽은 의존성 `requests` 오류 회피 — `backend/app/main.py:11,15` 실물 대조). 감점: `AC-011`·`AC-010`(b)의 Given(응답 지연)을 만들 수단이 절차 요건(`acceptance.md:79`)에 없다(D1, MAJOR); `AC-012`의 "구체적인 값으로 제시하는 표기" 판정에 재량 개입(D10); `AC-005`의 "mock으로 검증**할 수 있다**"는 단언이 아닌 가능성 서술(D9); `AC-015` ④(D8) |
| Traceability | 0.95 | 1.00 기준 전부 충족, 미행사 분기 2건에 대한 소폭 감점 | 독립 재계수: REQ 15 / AC 15, `acceptance.md:127-143`(REQ→AC)와 `:145-161`(AC→REQ) 양방향 표가 서로 모순 없음. 미커버 REQ 0, 고아 AC 0, 모든 AC가 실재 REQ를 정확히 하나 참조. 본문 인용 REQ 번호와 매핑표가 15행 전부 일치. 감점 근거 2건: (a) REQ-002가 포함하는 「유효한 뉴스 문서」의 **빈 배열** 정상 경로(`spec.md:162`)를 행사하는 자동 AC가 없다(D4); (b) 정렬 규칙 4(파싱 불가 항목끼리 파일 순서 유지)는 `AC-002` 픽스처에 파싱 불가 항목이 **D 한 건뿐**이라 실제로 행사되지 않는다(D5) |

**Aggregate = (0.80 + 1.00 + 0.70 + 0.95) / 4 = 3.45 / 4 = 0.8625** — Tier M PASS 임계 0.80 **충족**.

점수는 임계를 넘지만 게이트 조건(BLOCKER 0 · 미해소 MAJOR 0 · aggregate ≥ 0.80 · must-pass 전부 충족) 중 **미해소 MAJOR 0** 조건이 D1로 깨진다. 따라서 판정은 FAIL이며, 2차는 **전면 재감사가 아니라 D1·D2 델타 한정 재감사**가 되어야 한다.

---

## 5-Section Evidence Report

### 1. Claim (주장)

본 감사가 주장하는 바는 다섯 가지다.

1. **트레이서빌리티는 구조적으로 건전하다.** REQ 15 / AC 15, 결번·중복·고아·미커버 0건이며 작성자의 "1:1 커버" 주장은 독립 재계수로 성립한다. 다만 두 개의 정상 경로 분기(빈 배열, 정렬 규칙 4)가 어떤 AC로도 행사되지 않는다.
2. **`spec.md` §1.1과 `plan.md` §A.1의 저장소 사실 주장은 전수 대조 결과 거짓이 0건이다.** 데이터 파일 형태(4종), `008490_agents.json` 부재, 수집 스크립트 동작, 에이전트 선언 스키마, 백엔드 라우트·상수·헬퍼, 프론트엔드 행 번호 6개, `package.json` devDependencies, CI 11단계/기능 8단계, `ruff.toml`의 E501 비활성 — 전부 실물과 일치한다.
3. **형제 SPEC 1차가 지적한 결함 계열 8개 가운데 7개가 재발하지 않았다.** 특히 D2(술어 미정의)·D5(화면 AC 검증 수단 부재)·D7(ruff 줄 길이 오주장)·D8(경로 바인딩과 monkeypatch 충돌)·D11(죽은 의존성)·D12(무인증 근거 오류)는 선제적으로 처리되어 있다.
4. **두 SPEC의 편집은 줄 단위로 실제 분리된다.** `plan.md` §A.4 겹침표 4행을 형제 SPEC의 `plan.md`와 대조한 결과 네 행 모두 참이며, 어느 쪽 DoD도 상대의 변경으로 무효화되지 않는다.
5. **신규 결함은 MAJOR 1건 · MINOR 7건 · NIT 9건이며 BLOCKER는 없다.** MAJOR 1건은 한 절의 추가로 해소되는 실행 가능성 결함이다.

### 2. Evidence (증거 — 실행한 명령과 그 출력)

**(E-1) REQ/AC 독립 재계수 — 작성자 주장 불신뢰**

```
$ grep -c '^\*\*REQ-[0-9]*\*\*' .moai/specs/SPEC-NEWS-001/spec.md        → 15
$ grep -o '^\*\*REQ-[0-9]*\*\*' spec.md | sort | uniq -c   → REQ-001…REQ-015 각 1회
$ grep -c '^\*\*AC-[0-9]*\*\*' .moai/specs/SPEC-NEWS-001/acceptance.md   → 15
$ grep -o '^\*\*AC-[0-9]*\*\*' acceptance.md | sort | uniq -c → AC-001…AC-015 각 1회
```
Tier M 상한은 REQ 16 / AC 16이며 두 축에 독립 적용된다. 15/15는 상한 이하이고 한 자리의 여유가 있다(형제 SPEC은 16/16 한계선이었다 — 그쪽 잔여 위험 1번이 여기서는 발생하지 않는다).

**(E-2) 데이터 파일 실측 — `spec.md` §1.1 / `plan.md` §A.1 전수 대조**

```
$ ls data/
000660_agents.json  000660_fundamentals.json  000660_market.json  000660_ohlcv.json
005380_agents.json  005930_agents.json  005930_fundamentals.json  005930_market.json
005930_ohlcv.json   008490_fundamentals.json  008490_market.json  008490_ohlcv.json
009150_agents.json  009150_fundamentals.json  009150_market.json  009150_ohlcv.json
portfolio.edge.json portfolio.example.json
```
`008490_agents.json` **부재**, `_market`/`_fundamentals`/`_ohlcv`만 존재 → `plan.md:22`의 주장 참.

python 파싱으로 네 파일의 최상위 키·항목 키·`date` 값을 전수 출력:

| 파일 | 최상위 키 | 뉴스 건수 | 항목 키 | `date` 값 | SPEC 주장 |
|---|---|---|---|---|---|
| `005930_agents.json` | `ticker`·`news`·`financials` (**`name` 없음**) | 6 | 전부 4키, `url` 없음 | 07-06, 07-07, 07-07, 07-06, 07-10, 07-13 (**07-06·07-07 각 2건**) | ✓ 일치 (`spec.md:42`, `plan.md:19`) |
| `000660_agents.json` | `ticker`·`name`·`news`·`financials` | 5 | 전부 4키 + **`url`** | 전부 ISO | ✓ 일치 (`spec.md:43`, `plan.md:20`) |
| `009150_agents.json` | 4개 | 4 | 전부 4키, `url` 없음 | 전부 ISO | ✓ 일치 (`spec.md:44`) |
| `005380_agents.json` | 4개 | 4 | 전부 4키, `url` 없음 | `2026-07-06`, **`"2026-07 (중순)"`**, **`"2026-07 (중순)"`**, **`"2026-07 (초중순)"`** (4건 중 3건 파싱 불가) | ✓ 일치 (`spec.md:46-47`, `plan.md:23`의 "3건" 포함) |

허용 목록 4종목의 커밋된 파일에 파싱 불가 날짜가 **없고**, 허용 목록 밖 `005380`에만 있다는 주장도 참이다. 「뉴스 정렬 규칙」의 파싱 불가 갈래가 현재 데이터로 화면 실증 불가라는 `plan.md:212`의 자기 신고도 사실에 부합한다.

```
$ git check-ignore -v data/008490_agents.json  → NOT ignored
$ git status --porcelain data/                 → (출력 없음, clean)
```
M1의 "생성 후 커밋" 경로가 `.gitignore`에 막히지 않음을 확인했다.

**(E-3) 수집 스크립트 — `plan.md:25` 대조**

`Read scripts/orchestrate_stock_agents.py` (85행 전체):
- L69-70: 인자 `ticker`(코드 또는 종목명) + `--save` ✓
- L41 `shutil.which("claude")`, L50-58 `subprocess.run([claude_bin, "-p", "--output-format", "json", "--allowedTools", "WebSearch,WebFetch"], …, timeout=180)` ✓ 타임아웃 180초·허용 도구 2종 일치
- L78-79 `DATA_DIR / f"{args.ticker}_agents.json"` → `write_text(...)` ✓ 임시 파일 교체 없음
- 허용 목록 검사: 파일 전체에 없음 ✓ `plan.md:25`·`spec.md:50`의 주장 참

**(E-4) 에이전트 선언 스키마 — 선언·실물 불일치 주장 검증**

`Read .claude/agents/news-collector.md` L14-19:
```
{ "ticker": string, "news": [ { "title": string, "date": string, "source": string, "summary": string } ] }
```
`url` **없음** ✓. L4 `tools: WebSearch, WebFetch` ✓, L21 "검색은 최대 3회로 제한" ✓. `000660_agents.json`이 실제로 `url`을 가지는 것(E-2)과 대조하면 "선언과 실물이 어긋난다"는 `spec.md:49`·`plan.md:24`의 주장이 성립한다. 따라서 `url`을 선택 필드로 두고 화면이 판정한다는 설계 결정의 전제가 사실에 근거한다.

**(E-5) 백엔드 — 라우트·상수·헬퍼·선검사 순서**

```
$ grep -n '@app\.\(get\|put\|post\|delete\)' backend/app/main.py
47:/health  123·132·165:/api/settings/notion  183:/api/report/notion
236:/api/github/issues  311:/api/stocks/{code}/ohlcv  327:/api/stocks/{code}/indicators
```
REQ-015(`spec.md:119`)가 열거한 7개 라우트와 **정확히 일치**, 누락 0. `/api/stocks/{code}/news`는 아직 없고 기존 두 `/api/stocks/{code}/…` 라우트와 충돌하지 않는다 — 독립성 주장 성립.

`Read backend/app/main.py:270-354`:
- L277 `DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"` ✓
- L280 `CHART_STOCK_CODES = frozenset({"005930","000660","009150","008490"})` ✓
- L290-301 `_read_ohlcv_document` — 파일 접근 단일 지점, L300 `target.open(encoding="utf-8")` ✓ (`plan.md:163`의 완화책 전제와 일치)
- L304-308 `_load_ohlcv_or_404` — **L306의 허용 목록 검사가 L308의 파일 접근보다 먼저** ✓ REQ-005가 계승한다고 주장한 패턴이 실재한다
- L19 `from app import auth, config, indicators` ✓ `plan.md:26`의 import 블록 기술 일치

**(E-6) 테스트 전략 호환성 — 형제 1차 D8 계열 선제 회피 확인**

```
$ ls backend/tests/
__init__.py  conftest.py  test_chart.py  test_indicators.py  test_notion_settings.py   (뉴스 테스트 없음 ✓)
$ grep -n 'monkeypatch\|DATA_DIR' backend/tests/test_chart.py
54: def data_dir(tmp_path, monkeypatch):
56:     monkeypatch.setattr(main, "DATA_DIR", tmp_path)
111:    monkeypatch.setattr(main, "_read_ohlcv_document", fail_if_called)
148:    monkeypatch.setattr(main.urllib.request, "urlopen", fail_if_called)
```
`plan.md:31`·`plan.md:76-78`(§A.2 결정 3)이 "신규 코드가 import 시점에 경로를 확정하면 이 교체가 무력화된다 … `news.py`가 **디렉터리를 인자로 받는 함수**를 노출하고 `main.py`가 호출 시점에 `DATA_DIR`를 넘긴다"로 착수 전에 못 박았다. 형제 SPEC 1차 D8(`PORTFOLIO_ANALYSIS_FILE` 모듈 전역 바인딩과 `monkeypatch` 전략 충돌, 2차에서도 미해소 optional로 남은 항목)이 여기서는 계획 단계에서 차단되어 있다. L111·L148의 감시 패턴도 `AC-005`·`AC-007`이 그대로 따를 수 있는 선례로 실재한다.

**(E-7) CI 실물 — `plan.md:32` 전수 대조**

`Read .github/workflows/ci.yml` (71행 전체). 단일 job `lint-and-test`, `steps:` 배열 **11개**(`actions/checkout@v4` L13, `setup-python@v5` L16, `setup-node@v4` L21 포함), 그중 기능 단계 **8개**:

| # | ci.yml 실물 | `plan.md:32` 기술 | 일치 |
|---|---|---|---|
| ① | `pip install -r backend/requirements.txt ruff pytest` (L28) | 동일 | ✓ |
| ② | `npm ci` (frontend, L32) | 동일 | ✓ |
| ③ | `ruff check backend/` (L35) | 동일 | ✓ |
| ④ | `npm run lint` (frontend, L39) | 동일 | ✓ |
| ⑤ | `pytest backend/tests/ -v` + `env: DATABASE_URL: ${{ secrets.DATABASE_URL }}` (L42-44) | **env 주입까지 기술함** | ✓ |
| ⑥ | `npm run build` (frontend, L48) | 동일 | ✓ |
| ⑦ | `pip-audit`, `continue-on-error: true` (L64-66) | 동일 | ✓ |
| ⑧ | `npm audit --audit-level=high`, `continue-on-error: true` (L68-70) | 동일 | ✓ |

"차단 게이트는 ③~⑥ 네 개이고 ⑦·⑧은 경고다"도 `continue-on-error` 실물과 일치. **"`steps:` 배열은 11개이고 그중 기능 단계는 8개다"라는 표기와 `env: DATABASE_URL` 기술은 형제 SPEC 2차의 잔여 NIT n5가 지적한 두 부정확성을 모두 선제 교정한 형태다.**

```
$ cat ruff.toml
# select 를 지정하지 않아 ruff 기본 규칙을 그대로 쓴다. 아래 항목만 예외로 둔다.
[lint.flake8-bugbear] extend-immutable-calls = [ "fastapi.Depends", … ]
```
`select` 미지정 → 기본 규칙(E4·E7·E9·F), **E501 비활성** ✓. `plan.md:33`·`plan.md:161`이 "줄 길이(E501)는 루트 `ruff.toml`에서 비활성이다"로 정정해 적었다 — 형제 SPEC 1차 D7(거짓 리스크 주장)이 재발하지 않았고, 그쪽은 2차에서도 미수정으로 남은 항목이다.

**(E-8) 프론트엔드 — 인용된 행 번호 6개 전수 검증**

`awk`로 실제 행 번호를 찍어 대조:

| SPEC/plan 인용 | 실물 | 일치 |
|---|---|---|
| `:16` `const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'` | L16 동일 | ✓ |
| `:18-23` `MOCK_STOCKS` | L18 `const MOCK_STOCKS = [` … L23 `]` | ✓ |
| `:25-29` `MOCK_NEWS`(`{title, time}` 3건) | L25 `const MOCK_NEWS = [` … L29 `]`, 3항목 전부 `{title, time}` | ✓ |
| `:48` `selectedStock` 상태 | L48 `const [selectedStock, setSelectedStock] = useState<…>(null)` | ✓ |
| `:50-56` Supabase 미인증 시 `/login` 리다이렉트 | L50-56 `useEffect` + L53 `router.replace('/login')` | ✓ |
| `:117-122` `<Link href="/settings">` | L117 `<Link` … L122 `</Link>` | ✓ |
| `:205-217` 차트 구간 | L205 `{/* 주가 차트 · 기술지표 (SPEC-CHART-001) */}` … L217 `</div>` | ✓ |
| `:220-230` 뉴스 렌더 구간 | L219 `{/* 최신 뉴스 */}`, L220 `<div …>` … L230 `</div>` (`MOCK_NEWS.map`은 L223) | ✓ (주석 L219는 구간 밖 표기, 실질 영향 없음) |

`REQ-015`/`AC-015`가 열거한 대시보드 6개 구간(포트폴리오 요약·보유 종목 테이블·주가 차트·GitHub 이슈·Notion 저장 버튼·헤더)도 실물과 대조했다: 헤더 L112, Notion 토스트 L132, **포트폴리오 요약 L140**, 보유 종목 L157, 주가 차트 L205, 최신 뉴스 L219, GitHub 이슈 L232 — 열거가 정확하며 형제 SPEC의 AC-016(5개 구간, 「포트폴리오 요약」 누락)보다 완전하다.

```
$ cat frontend/package.json
scripts: dev, build, start, lint          (test 없음 ✓)
devDependencies: @types/node, @types/react, @types/react-dom, autoprefixer,
                 eslint, eslint-config-next, postcss, tailwindcss, typescript
```
jest / vitest / `@testing-library` 전부 부재 ✓ `spec.md:53`·`plan.md:37`·`acceptance.md:51`의 주장 참. `frontend/src/components/` → `StockChart.tsx` 하나 ✓.

**(E-9) 의존성·설정 — `plan.md:28-30, 39` 대조**

```
$ cat backend/requirements.txt
# NOTE: ASCII only. pip reads this file with the system locale encoding,
# so non-ASCII comments break `pip install -r` on Korean Windows (cp949).
fastapi==0.141.1 / uvicorn[standard]==0.52.4 / httpx==0.27.0 / python-dotenv==1.2.2   (pytest 없음 ✓)
$ cat backend/requirements-dev.txt   → pytest==8.3.4, pytest-cov==6.0.0, httpx==0.27.0   (존재 ✓)
$ cat .moai/config/sections/language.yaml | grep code_comments   → code_comments: "ko"  ✓
```
네 패키지 버전·ASCII 주의 문구·`pytest` 부재·`requirements-dev.txt` 존재가 전부 일치한다. `plan.md:213`(§A.9)이 "`requirements-dev.txt`의 내용은 이번 조사에서 읽지 않았다"고 **미검증 사실을 정직하게 남긴** 점도 확인했다 — 실제 내용은 `pytest`/`pytest-cov`/`httpx`이며, 읽지 않았다는 신고는 참이다(확인하지 않은 것을 확인한 것처럼 적지 않았다).

**(E-10) 형제 SPEC과의 겹침 — `plan.md` §A.4 4행 실물 대조**

`SPEC-PORTFOLIO-001/plan.md`를 읽어 네 행을 각각 검증했다:

| 파일 | NEWS의 주장 | PORTFOLIO 실물 | 판정 |
|---|---|---|---|
| `backend/app/main.py` | "M2가 파일 **끝에** 구획 주석 + `PORTFOLIO_ANALYSIS_FILE` + `_read_portfolio_document()` + `GET /api/portfolio` 추가" | `plan.md:100` 동일 문구, `plan.md:81` "신규 라우트는 `main.py` **끝에** 구획 주석과 함께 추가" | ✓ 참. 양쪽 모두 추가만 하고 기존 함수 본문을 고치지 않는다(`plan.md:160` PRESERVE) |
| `frontend/src/app/dashboard/page.tsx` | "M3가 **헤더 구간**에 `/portfolio` 링크 1개 추가. import는 추가하지 않는다(`Link`는 `:11`에 이미 있다)" | `plan.md:111` "헤더에 `/portfolio` 링크 1개 추가", `plan.md:34` "`Link` from `next/link` 이미 import". 실물 L11 `import Link from 'next/link'` | ✓ 참. 헤더(L113-130)와 뉴스(L219-230)는 완전 분리 |
| `docs/weekly/WEEK_10.md` | "M3가 「`/portfolio` 화면 수동 검증 절차」, M4가 모듈 요약" | `plan.md:112`(M3 절 신설), `plan.md:118`(M4 모듈 요약) | ✓ 참 |
| `.github/workflows/ci.yml` | "M4가 '`Backend 테스트`' 단계 한 줄 수정 / 본 SPEC은 건드리지 않는다" | `plan.md:120` "`pytest backend/tests/ scripts/tests/ -v`로 확장 … 이 단계 외의 CI 단계는 건드리지 않는다" | ✓ 참, 겹치지 않음 |

**DoD 상호 무효화 여부**: PORTFOLIO의 DoD(`acceptance.md:99-111`)와 AC-016(`:49`)을 읽었다. AC-016은 "대시보드의 보유 종목 테이블·주가 차트·**최신 뉴스**·GitHub 이슈·Notion 저장 버튼이 정상 동작한다"를 요구하고, PRESERVE(`plan.md:162`)는 `MOCK_NEWS`를 수정 금지 목록에 올린다. NEWS가 먼저 착지하면 `MOCK_NEWS`는 사라지지만 「최신 뉴스」 영역 자체는 남아 동작하므로 AC-016은 여전히 판정 가능하고, PRESERVE 행은 PORTFOLIO **자신의** 수정을 금지하는 조항이므로 NEWS의 삭제를 막지 않는다. → **어느 쪽 DoD도 무효화되지 않는다.** 다만 나중에 착지하는 쪽이 상대의 PRESERVE/AC 문구를 다시 읽어야 한다는 점이 NEWS의 겹침표에 없다(D13, NIT). NEWS의 DoD가 요구하는 "`.github/workflows/ci.yml` 변경 없음"도 자기 diff에 대한 조항이므로 PORTFOLIO M4의 수정과 충돌하지 않는다.

**(E-11) 계약 건전성 — 술어별 엣지 케이스 손검사**

| 검사 항목 | SPEC의 규정 | 판정 |
|---|---|---|
| `2026-02-30` | `spec.md:168` "형식은 맞지만 존재하지 않는 날짜(`2026-02-30`)는 파싱 불가" — 명시 | ✓ 규정됨 |
| 시각/타임존 접미사(`2026-07-10T09:00Z`) | 정규식 `^\d{4}-\d{2}-\d{2}$` **전체 일치** 요구 → 불일치 → 파싱 불가 | ✓ 닫힘 |
| 빈 문자열 `""` | 전체 일치 실패 → 파싱 불가. 또한 `spec.md:163` "문자열이 비어 있어도 위반이 아니다" | ✓ 일관 |
| 문자열이 아닌 `date` | 「유효한 뉴스 문서」 조건 4가 네 값의 문자열성을 요구 → 문서 자체가 무효 → 500 | ✓ 상위 술어가 선제 처리 |
| 파싱 불가 항목 간 순서 | 정렬 규칙 4가 "파일에 저장된 상대 순서를 그대로 유지" | ✓ 규정됨 (다만 AC 미행사 — D5) |
| `news`가 빈 배열 | `spec.md:162` "위반이 아니다", `acceptance.md:89` "API는 `200`에 빈 배열" | ✓ 규정됨 (자동 AC 미행사 — D4) |
| 열거되지 않은 **항목** 키 | `spec.md:161` "위반이 아니다"(유효성) / `:196` 응답 계약은 5키만 열거 / `:188` "저장된 `news` 배열을 그대로 내보내는 것으로 정의" | ✗ **응답에 실을지 미규정** — D3 |
| `url` 스킴 화이트리스트 | `spec.md:180-186`: 키 존재 + 문자열 + **대소문자 무시** `http://`/`https://` 로 시작. 키 부재·비문자열·빈 문자열·기타 스킴(`javascript:`·`data:`·`file:`)·상대 경로 전부 불안전 | ✓ 화이트리스트 = **fail-closed**. 앞쪽 공백(`" https://…"`)·프로토콜 상대(`//example.com`)·`https:/\…` 모두 "로 시작"에 실패해 링크 미생성 — 미열거 케이스도 안전 쪽으로 떨어진다 |
| `rel`/`target` | REQ-009가 `target="_blank"`·`rel="noopener noreferrer"`를 명문화, AC-009가 대문자 스킴 포함 4경우 검사 | ✓ |
| 원시 HTML 렌더링 금지 | 명시 없음 | ✗ D7 (React 기본 이스케이프로 실질 위험은 낮음) |
| `008490` 미생성 상태의 런타임 동작 | REQ-004 → `404`(AC-004), 화면은 오류 상태(`plan.md:66-70` 결정 2, AC-010 (c)). 실패 시 사유와 AC-001 FAIL을 `progress.md`에 기록(`plan.md:110`, "허위 PASS를 적지 않는다") | ✓ 규정됨 — 다만 DoD가 자기모순(D2) |
| 무인증 `GET /api/stocks/{code}/news` | `spec.md:242-243`이 근거("커밋된 공개 기사 메타데이터, 개인정보 없음")와 **전이 조건**("사용자별로 달라지는 순간 인증 적용이 선행 조건")을 함께 명시 | ✓ 형제 1차 D12가 권고한 형태 그대로 |
| 오류 메시지 누출 | REQ-006 + AC-006이 절대 경로·파일명·`Traceback`·예외 클래스명 4종을 이진 술어로 금지 | ✓ 형제 1차 D10이 권고한 구체 술어 형태 |
| 경로 조작 | AC-005가 `../005380`·`..%2F..%2Fetc%2Fpasswd`를 추가 단언, 허용 목록이 리터럴 집합이라 선검사에서 거부 | ✓ |

### 3. Baseline-attribution (baseline 귀속)

- 저장소: `/home/woojun/playground/antshell`, 브랜치 `main`, 대화 시작 스냅샷 HEAD `29395f5`.
- 모든 사실 확인은 **이 실행, 이 트리**에서 수행했다. 형제 SPEC의 1·2차 감사 보고서는 *무엇을 점검할지*의 목록으로만 사용했고, 그 보고서가 기록한 측정값(ci.yml 8단계, devDependencies 목록, `dashboard/page.tsx:16`, 라우트 목록, `ruff.toml` 동작)을 그대로 옮겨 적지 않았다 — 전부 이번에 다시 읽었다.
- SPEC 산출물 4개(`spec.md` 244행 / `plan.md` 214행 / `acceptance.md` 162행 / `progress.md` 52행)를 **전문** 읽었다. 표본 추출이 아니다.
- REQ/AC 계수는 작성자 주장과 무관하게 `grep -o … | sort | uniq -c`로 독립 재계수했다(결과 15/15, 작성자 주장과 일치).
- 데이터 파일 형태는 `python3 -c "json.load(...)"`로 파싱해 최상위 키·항목 키·`date` 값을 전수 출력해 대조했다(육안 `cat` 판독 아님).
- git 명령은 `git check-ignore -v data/008490_agents.json`(→ NOT ignored)과 `git status --porcelain data/`(→ 출력 없음) 두 건뿐이다. 상태를 바꾸는 명령은 실행하지 않았다.

### 4. Gaps (미검증 — 본 감사가 관찰하지 못한 것)

- **어떤 테스트·린트·빌드도 실행하지 않았다.** `pytest backend/tests/ -v`, `ruff check backend/`, `npm run lint`, `npm run build` 전부 미실행. `AC-015`가 전제하는 "기존 테스트 통과"의 현재 상태는 관찰 범위 밖이다. 확인한 것은 도구 설정 파일(`ruff.toml`)과 테스트 파일의 실재뿐이다. `plan.md:211`(§A.9)이 같은 사실을 스스로 미해결로 신고해 두었다.
- **`scripts/orchestrate_stock_agents.py`를 실행하지 않았다.** `claude -p`가 이 환경에서 성공하는지, `008490` 수집 결과가 「유효한 뉴스 문서」를 만족하는지, 그 `date` 형태가 ISO인지는 전부 미확인이다. 이것이 이 SPEC의 유일한 외부 의존 단계이며 M1에서 처음 드러난다.
- **화면 렌더링을 관찰하지 않았다.** `AC-008`~`AC-014`의 실현 가능성은 코드·패키지 구성으로부터의 추론이다. 수동 검증 절차 문서(`docs/weekly/WEEK_10.md`의 해당 절)는 M2 산출물이라 아직 존재하지 않으므로, 본 감사가 판정한 것은 *요건의 구체성*이며 *절차 자체의 품질*이 아니다.
- **`data/008490_agents.json`이 부재하므로** §4 파일 스키마를 실제 수집 결과와 대조하지 못했다. 「유효한 뉴스 문서」 네 조건이 실제 에이전트 출력으로 충족 가능한지는 M1에서 처음 확인된다.
- **`backend/tests/test_news.py`·`frontend/src/components/StockNews.tsx`가 아직 없으므로** 구현 가능성은 기존 선례(`test_chart.py`, `StockChart.tsx`) 구조로부터의 추론이다.
- **형제 SPEC `SPEC-PORTFOLIO-001`의 2차 잔여 항목(n1~n5 및 1차 optional 17건)이 이후 수정되었는지 전수 재확인하지 않았다.** 이번 겹침 검증에 필요한 범위(§A.3 M1~M4, §A.4, §A.6, AC-016, DoD)만 읽었다.
- **`.moai/specs/SPEC-API-001/`·`SPEC-CHART-001/`의 본문을 읽지 않았다.** 확인한 것은 `status:` 한 줄뿐이며, `spec.md` §1.0이 주장하는 두 SPEC의 범위 서술(예: "`MOCK_STOCKS` 제거는 `SPEC-API-001`의 몫")은 그 SPEC 본문과 대조하지 않았다.

### 5. Residual-risk (잔여 위험 — 관찰했음에도 남는 위험)

- **완전 수동 AC가 6건(AC-001, AC-008~AC-012), 혼합이 3건이다.** 자동 게이트를 PASS 근거로 쓰지 못하게 `acceptance.md:62`가 차단했고 `:101`이 "절차 문서 인용 없이 '확인함'"을 PASS 불인정으로 못 박았지만, 최종 판정 품질은 아직 쓰이지 않은 절차 문서의 품질에 전적으로 의존한다.
- **`008490` 수집이 실패하면 REQ-001이 미충족 상태로 SPEC이 닫힌다.** `plan.md:110`이 이 결말을 정직하게 허용하지만, 그 경우 "허용 목록 4종목 중 1종목은 항상 오류 상태"가 잔존 부채로 남고 DoD의 자기모순(D2)이 판정 시점에 표면화된다.
- **`news-collector` 선언 스키마와 실물의 불일치가 이미 관측된 상태(`url`)이므로**, 새 수집 결과가 다른 축에서도 어긋날 수 있다(예: `date`가 `"2026-07 (중순)"` 형태로 나옴). 정렬 규칙은 이를 정상 경로로 흡수하지만, 필수 4키 중 하나가 빠지면 그 종목 전체가 `500`이 된다. REQ-006이 명시적 실패를 선택했으므로 조용한 손실은 없으나, 발표 시연 중 발생하면 복구 수단이 재수집뿐이다.
- **「유효한 뉴스 문서」가 단일 이진 술어라 한 항목의 결함이 문서 전체를 `500`으로 만든다.** `acceptance.md:87`이 이 선택의 근거를 적고 있고 타당하지만, 6건 중 1건만 깨져도 그 종목 뉴스가 전부 사라진다는 뜻이다.
- **응답의 항목 단위 키 통과 여부가 미정이므로(D3)**, 수집 결과에 새 키가 붙는 날 응답 형태가 구현자의 해석에 따라 갈린다. 어느 해석이든 현재 AC를 전부 통과한다.
- **PORTFOLIO와의 병합은 줄 단위로 분리되지만 순서 의존이 남는다.** `main.py` 끝에 두 구간이 나란히 붙고, `dashboard/page.tsx`의 import 블록은 NEWS만 건드린다 — 자동 병합이 실패하지는 않겠으나, 나중에 착지하는 쪽이 상대의 PRESERVE 문구(`MOCK_NEWS`)와 CI 명령 문자열을 다시 읽어야 한다(D12·D13).
- **`tags`에 `agent-team`이 들어 있다(D16).** MoAI 오케스트레이션 모드 토큰과 같은 문자열이라 검색·분류에서 오해를 부를 수 있다.

---

## 형제 결함 계열 대조표 (`SPEC-PORTFOLIO-001` 1차 지적의 재발 여부)

| 결함 계열 (형제 1차) | NEWS에서의 재발 | 근거 |
|---|---|---|
| plan·acceptance에는 있으나 spec REQ에 없는 옵션·모드 (D1) | **없음** | `--save`는 REQ-001이 명령 전문을 적시. `grep`으로 plan/acceptance의 모든 CLI 옵션이 REQ-001에 포함됨을 확인 |
| 여러 곳이 검사하는 스키마·술어의 단일 정의 부재 (D2) | **없음** | 「유효한 뉴스 문서」가 `spec.md:148`에 제목으로 소비자 3개(REQ-001·002·006)를 명시하고 한 곳에서만 정의. 비위반 경계까지 열거(`:159-164`). `plan.md:49`가 구현 지침으로, `:107`이 테스트 구성 지침으로 강화 |
| 한 REQ에 두 요구사항·두 GEARS 패턴 (D3) | **경미 1건** | REQ-001(D6, MINOR/optional). 나머지 14개는 단일 패턴 |
| CI 기술이 실물과 다름 (D4) | **없음** | E-7 8단계 전수 일치. 11 vs 8 구분과 `env: DATABASE_URL`까지 기술해 형제 2차 n5도 선제 교정 |
| 자동 경로도 구체적 수동 절차도 없는 화면 AC (D5) | **부분 재발** | 절차 요건 4항목은 `acceptance.md:70-79`에 규정됨. 그러나 `AC-011`·`AC-010`(b)의 준비 상태(응답 지연)를 만들 수단이 열거에 없음 → **D1 (MAJOR)** |
| `monkeypatch.setattr(main, "DATA_DIR", tmp_path)`와 충돌하는 테스트 전략 (D8) | **없음** | `plan.md:72-78` 결정 3이 요청 시점 해석 + 디렉터리 인자 함수를 착수 전에 지정 |
| 마일스톤 병렬/선행 서술 모순 (2차 n1) | **없음** | `plan.md:99` "세 마일스톤은 **순차 진행한다**. 병렬 진행을 주장하지 않는다", A.4 선행 조건 열(M1 완료 → M2 완료), `progress.md:21`이 전부 일치 |
| AC가 인용 REQ의 핵심 의무를 실제로 행사하지 않음 (1차 Traceability 감점) | **경미 2건** | 정상 경로 분기 2개가 미행사(D4·D5). 인용-불일치는 0건 |
| 검증되지 않은 저장소 주장 | **없음** | E-2~E-9 전수 대조, 거짓 0건. 미검증 사실은 `plan.md` §A.9에 정직하게 신고됨 |
| 죽은 의존성 단언 (D11) | **없음** | `AC-007`이 `httpx`·`urllib.request.urlopen`·`subprocess.run`·`shutil.which`만 지목, 전부 실재 |
| ruff 줄 길이 오주장 (D7) | **없음** | `plan.md:33,161`이 E501 비활성을 정확히 기술 |
| 무인증 근거 오류 (D12) | **없음** | `spec.md:242-243`이 근거 + 전이 조건 명시 |
| 미존재 SPEC 전방 참조 (D18) | **없음** | `spec.md:216` "`SPEC-WATCHLIST-001`(미작성)" |

---

## Defects Found (structured defect-list)

| # | ID | 위치 (file:line) | 설명 | Severity | Class | Required fix |
|---|---|---|---|---|---|---|
| D1 | AC011-SETUP-UNSPEC | `acceptance.md:39` (AC-011) · `acceptance.md:37` (AC-010 (b)) · `acceptance.md:79` (절차 요건) | `AC-011`의 Given은 "백엔드가 `005930` 요청에는 **3초 지연** 후 응답하고 `000660` 요청에는 즉시 응답하도록 만든 상태"이고, `AC-010`(b)의 Given은 "백엔드 응답을 **지연**시켜 요청이 진행 중"이다. 그런데 이 두 상태를 만들 수단을 규정하는 곳이 없다 — `acceptance.md:79`는 AC-009·AC-010·AC-011을 **이름으로 지목하면서** 준비 수단으로 "임시 픽스처 파일을 `data/`에 잠시 놓거나 **백엔드를 멈추는** 방법"만 열거하는데, 둘 중 어느 것도 지연을 만들지 못한다(파일은 즉시 읽히고, 멈춘 백엔드는 지연이 아니라 오류다). 백엔드는 로컬 파일을 읽으므로 응답이 사실상 즉시이고, 비대칭 지연을 만들려면 라우트에 `sleep`을 넣는 코드 수정(§A.6 PRESERVE·PORTFOLIO 겹침과 충돌)이나 SPEC이 이름 대지 않은 도구가 필요하다. 결과적으로 **REQ-011의 유일한 AC가 기재된 대로 실행될 수 없고**, M2가 acceptance 산출물에 없는 수단을 즉석에서 고안해야 한다. 완전 수동 AC에서 이는 "확인함"으로 흘러가는 경로이며, `acceptance.md:101`의 품질 게이트가 막으려던 바로 그 상태다 | **MAJOR** | **blocking** | 택1: **(a)** `acceptance.md:79`의 준비 수단 열거에 지연 주입 수단을 한 항목 추가하고(예: 브라우저 개발자도구의 네트워크 스로틀링, 또는 검증 종료 후 되돌리는 일회성 로컬 지연) AC-011·AC-010(b)의 준비 줄에서 그 수단을 지목하도록 M2 요건에 명시한다. **(b)** `AC-011`의 Given을 실현 가능한 등가 형태로 좁힌다 — 비대칭 지연 대신 "두 요청 모두 지연된 상태에서 A 선택 직후 B를 선택"으로 바꾸면 균일 스로틀링만으로 경쟁 상태가 재현되고 동일한 Then("SK하이닉스의 뉴스만 표시")을 판정할 수 있다. (b)가 더 적은 변경으로 끝난다 |
| D2 | DOD-SELF-CONTRADICTION | `acceptance.md:110` 대 `acceptance.md:111` | DoD 첫 항목은 "REQ-001~REQ-015가 모두 구현되고 각 REQ에 매핑된 AC가 **PASS**"를 요구하는데, 둘째 항목은 "`data/008490_agents.json` 생성·검증·커밋 (**실패 시** 사유와 **AC-001 FAIL**을 `progress.md`에 기록)"으로 AC-001의 FAIL을 명시적으로 허용한다. `008490` 수집이 실패하는 시나리오(`plan.md:110`·`:154`가 정상 경로로 다루는 상태)에서 두 체크박스가 서로를 부정하며, 어느 쪽이 완료 판정을 지배하는지 규정되지 않는다 | MINOR | **blocking** | `acceptance.md:110`을 "REQ-001~REQ-015가 모두 구현되고, **AC-001을 제외한** 각 REQ의 매핑 AC가 PASS (AC-001은 둘째 항목의 규칙을 따른다)"로 한정하거나, 둘째 항목 말미에 "이 경우 첫 항목의 예외로 기록하고 잔존 부채로 명시한다"를 덧붙인다 |
| D3 | ITEM-KEY-PASSTHROUGH | `spec.md:161` 대 `spec.md:196` · `spec.md:188` | 「유효한 뉴스 문서」는 "열거되지 않은 키의 존재나 부재는 위반이 아니다"라고 하지만, 응답 계약의 항목 스키마(`:196`)는 `title`·`date`·`source`·`summary`·`url?` 다섯 키만 적는다. 한편 `:188`은 "응답은 저장된 `news` 배열을 **그대로** 내보내는 것으로 정의했고"라고 쓴다. 파일의 항목에 `sentiment` 같은 미열거 키가 있을 때 응답에 실리는지 떨어지는지 어떤 REQ/AC도 정하지 않는다. 두 해석(통과 / 5키 추출) 모두 AC-002~AC-007을 전부 통과한다. 최상위 키는 `:201`이 "정확히 이 두 개"로 못 박았으나 항목 키에는 대응 조항이 없다 | MINOR | optional | `spec.md:196` 아래에 한 줄 추가: "파일 항목의 열거되지 않은 키는 응답에 **그대로 싣는다**"(또는 "응답에 싣지 않는다"). 어느 쪽이든 `AC-002`에 대응 단언 한 절을 붙인다(예: 픽스처의 한 항목에 `"extra": "x"`를 넣고 응답에서의 유무를 고정) |
| D4 | EMPTY-NEWS-UNEXERCISED | `spec.md:162` · `acceptance.md:89` 대 `acceptance.md:21` (AC-002) | "`news`가 빈 리스트인 것은 위반이 아니다 … API는 `200`에 빈 배열"이 두 곳에 규정되지만, 이 분기를 행사하는 **자동** AC가 없다. AC-002는 4건 픽스처만 쓰고, 빈 배열은 `AC-010`(d)의 화면 측 수동 판정에서만 등장한다. 빈 배열에서 `500`이나 `404`를 내는 구현도 현재 자동 테스트를 전부 통과한다 | MINOR | optional | `AC-002`에 절을 하나 붙이거나 `AC-006`의 여섯 케이스와 나란히 "`news: []` 픽스처에서 `200` + `news` 길이 0 + 최상위 키 2개"를 자동 단언으로 추가한다. AC 예산에 한 자리 여유가 있으므로(15/16) 신설도 가능하다 |
| D5 | SORT-RULE4-UNEXERCISED | `spec.md:175` (정렬 규칙 4) 대 `acceptance.md:21` (AC-002) | 규칙 4("파싱 불가한 항목끼리는 파일에 저장된 상대 순서를 그대로 유지")를 행사하려면 파싱 불가 항목이 **둘 이상** 필요한데, AC-002 픽스처의 파싱 불가 항목은 `D` 한 건뿐이다. 파싱 불가 항목들을 임의 순서로 뒤섞는 구현도 AC-002를 통과한다. `acceptance.md:88`의 "모든 날짜가 파싱 불가" 엣지 케이스도 AC로 승격되지 않았다 | MINOR | optional | AC-002 픽스처에 파싱 불가 항목을 하나 더 넣고(예: `E = "2026-08 (하순)"`) 기대 순서를 `[B, A, C, D, E]`로 고정한다 — 픽스처 한 줄 추가로 규칙 4가 행사된다 |
| D6 | REQ001-DUAL-CLAUSE | `spec.md:85` (REQ-001) | 한 REQ 항목이 (ㄱ) 운영자의 수동 생성·확인·커밋 `[Ubiquitous]`와 (ㄴ) "`scripts/` 아래 코드는 본 SPEC에서 수정하지 않는다"(부정형 = Unwanted 계열)를 함께 담는다. (ㄴ)는 §5 「Out of Scope — 수집 스크립트 변경」(`:236-237`)과 `plan.md:178` PRESERVE에서 이미 규정되므로 중복이기도 하다. MP-2는 "같은 수동 단계의 제약"이라는 해석으로 PASS 처리했으나, 부분 실패 시 귀속이 한 단계 흐려진다. 또한 주어가 시스템·컴포넌트가 아닌 **사람(운영자)**이라 GEARS 주어 일반화의 경계에 있다 | MINOR | optional | (ㄴ)를 삭제하고 §5·PRESERVE에 맡기거나, "(이 단계는 스크립트를 수정하지 않은 상태로 수행한다)"처럼 (ㄱ)의 수행 조건으로 종속시킨다. `AC-001`의 `git diff --stat scripts/` 단언은 그대로 두어도 무방하다 |
| D7 | XSS-RAWHTML-UNSTATED | `spec.md:178-188` (「안전한 링크」) · REQ-008/REQ-009 | SPEC은 `url` 스킴이라는 XSS 경로 하나는 화이트리스트로 촘촘히 막지만, 형제 경로인 **원시 HTML 렌더링 금지**는 어디에도 적지 않는다. `title`·`summary`는 제3자(수집 에이전트)가 만든 문자열이며 `spec.md:228`이 "`summary`는 … 그대로 표시할 뿐"이라고 한다. React의 기본 이스케이프로 실질 위험은 낮으나, 한쪽 벡터만 명문화한 비대칭이 남고 `dangerouslySetInnerHTML`을 쓰는 구현도 어떤 AC에도 걸리지 않는다 | MINOR | optional | 「안전한 링크」 아래 또는 REQ-009 말미에 한 줄: "`title`·`summary`·`source`는 텍스트로만 렌더링하며 원시 HTML로 해석하지 않는다." `AC-009`에 "HTML 태그가 포함된 `title` 픽스처가 태그 그대로 표시된다" 단언을 덧붙이면 이진 판정이 된다 |
| D8 | AC015-GITSTATUS-VACUOUS | `acceptance.md:47` AC-015 ④ | "`git status --porcelain data/`가 `data/008490_agents.json` 한 줄 외에 아무 줄도 내지 않는다"는 단언이 커밋 시점에 따라 의미가 달라진다. REQ-001은 그 파일을 **커밋**하라고 요구하므로 판정 시점에는 커밋 완료 상태이고, 그때 이 명령의 출력은 **아무 줄도 없다**(실측: 현재 `git status --porcelain data/` → 출력 없음). 즉 기대 출력이 "한 줄"인지 "0줄"인지 SPEC이 정하지 않았고, 어느 쪽이든 단언이 참이 되어 "기존 파일 미변경"이라는 본래 목적은 우연히 달성된다 | MINOR | optional | "커밋 완료 후 `git status --porcelain data/`의 출력이 **비어 있다**(즉 `data/` 아래 미커밋 변경이 없다). 추가로 `git diff --stat HEAD~1 -- data/`가 `data/008490_agents.json` 한 파일만 보고한다"처럼 시점과 기대 출력을 함께 고정한다 |
| D9 | AC005-CAPABILITY-PHRASING | `acceptance.md:27` AC-005 | Then 절이 "파일 열기가 한 번도 호출되지 않았음을 mock으로 **검증할 수 있다**"로 끝난다. 나머지 절(상태 코드 `404`, 본문에 뉴스 내용 없음)은 단언인데 이 절만 *가능성* 서술이라, 테스트가 실제로 그 단언을 포함하지 않아도 문면상 통과한다 | NIT | optional | "파일 열기가 한 번도 호출되지 **않는다**(`_read_ohlcv_document` 대체 패턴과 동일하게 mock으로 검증한다)"로 단언화한다. 실물 선례는 `backend/tests/test_chart.py:111` |
| D10 | AC012-JUDGMENT | `acceptance.md:41` AC-012 | "수집 시각·수집 주기·수집 방법을 **구체적인 값으로 제시하는 표기**는 존재하지 않는다"는 부정 단언이 "구체적인 값"의 경계를 정하지 않는다. 예를 들어 "매주 수집"은 주기 표기인가 일반 안내인가 — 판정에 재량이 개입한다 | NIT | optional | 금지 대상을 열거형으로 좁힌다: "화면에 날짜·시각 형식의 문자열, 또는 `n일 전`·`n시간 전` 형태의 상대 시각이 뉴스 영역 안에 나타나지 않는다"(기존 `MOCK_NEWS`의 `time` 필드가 정확히 이 형태였다) |
| D11 | REQ013-IMPL-IDENTIFIERS | `spec.md:113` (REQ-013) | 요구사항 본문이 구현 식별자(`MOCK_NEWS` 상수명, `frontend/src/app/dashboard/page.tsx` 경로)를 직접 지목한다 — 요구사항 계층의 WHAT/WHY 원칙(HOW 배제)에서 벗어난다. 다만 "특정 하드코딩 데이터의 제거"라는 요구의 성격상 대상 지목이 불가피한 면이 있다 | NIT | optional | 앞절("하드코딩된 뉴스 목록을 표시하지 않는다")만 REQ로 두고, 뒷절(상수·파일 지목)은 `AC-013`에만 남긴다 — AC-013은 이미 `grep` 명령으로 같은 내용을 검증한다 |
| D12 | CI-CMD-QUOTE-STALE | `acceptance.md:56` · `acceptance.md:104` · `plan.md:82` | 세 곳이 CI 테스트 단계를 `pytest backend/tests/ -v`로 **문자열째** 인용하는데, `SPEC-PORTFOLIO-001` M4(`plan.md:120`)가 같은 줄을 `pytest backend/tests/ scripts/tests/ -v`로 바꾼다. `backend/tests/`는 여전히 포함되므로 `test_news.py`는 계속 실행되어 **기능상 영향은 없으나**, PORTFOLIO가 먼저 착지하면 세 인용이 실물과 어긋난다 | NIT | optional | 인용을 "CI 기능 단계 ⑤(`backend/tests/`를 포함하는 pytest 단계)"처럼 경로 기준으로 완화하거나, §A.4 겹침표의 `ci.yml` 행에 "PORTFOLIO가 이 명령 문자열을 바꾸지만 `backend/tests/` 포함은 유지된다"는 한 줄을 덧붙인다 |
| D13 | OVERLAP-SEMANTIC-OMISSION | `plan.md:140` ("아래가 겹침의 전부이며") · `plan.md:145` 대 `SPEC-PORTFOLIO-001/plan.md:162` · `acceptance.md:49` | 겹침표는 **파일·줄 단위**로는 정확하다(E-10 전수 검증). 그러나 PORTFOLIO의 PRESERVE 목록이 `MOCK_NEWS`를 수정 금지 대상으로 **이름을 지목**하고 그 AC-016이 「최신 뉴스」를 회귀 검사 대상으로 열거한다는 사실이 표에 없다. NEWS가 먼저 착지하면 PORTFOLIO의 그 두 문구는 사라진 심볼을 가리키게 된다(무효화는 아니며, 나중 착지 측이 다시 읽어야 할 뿐) | NIT | optional | `dashboard/page.tsx` 행의 「겹침 판정」 칸에 한 줄 추가: "PORTFOLIO의 PRESERVE가 `MOCK_NEWS`를, AC-016이 「최신 뉴스」를 이름으로 지목하므로, 본 SPEC이 먼저 착지하면 그쪽 두 문구는 갱신 대상이 된다(요구 충돌은 아니다)" |
| D14 | AC013-GREP-EXIT | `acceptance.md:43` AC-013 · `acceptance.md:120` DoD | `grep -c 'MOCK_NEWS' …` 결과가 `0`일 때 grep의 **종료 코드는 1**이다. 이 명령을 품질 게이트 스크립트에 그대로 넣고 `set -e`를 쓰면 성공 상태가 실패로 뒤집힌다 | NIT | optional | `grep -c … \|\| true`를 덧붙이거나 `! grep -q 'MOCK_NEWS' …` 형태로 바꾼다 |
| D15 | M2-COVERAGE-COLUMN | `plan.md:117` 대 `plan.md:119` · `progress.md:18` | M2 본문은 수동 검증 절차를 "AC-008~AC-014**와 AC-015의 대시보드 항목**"에 대해 쓰라고 하는데, 같은 마일스톤의 「커버」 줄과 `progress.md`의 커버 열은 `AC-008~AC-014`만 적는다. AC-015의 절차 작성 주체가 M2인지 M3인지 표만 읽으면 흐려진다 | NIT | optional | 커버 열을 "AC-008~AC-014 (+ AC-015 대시보드 항목의 절차 작성)"으로 보정하거나, A.4 소유권 표의 M2 행에 같은 단서를 넣는다 |
| D16 | TAGS-AGENT-TEAM | `spec.md:13` | `tags: "backend, frontend, news, fastapi, nextjs, **agent-team**"` — `agent-team`은 MoAI 오케스트레이션 모드 토큰과 같은 문자열이다. 이 SPEC은 수집 서브에이전트(`news-collector`)를 가리키려는 것으로 보이나, 태그 검색·분류에서 오해를 부른다 | NIT | optional | `agent-team` → `subagent` 또는 `news-collector`로 교체 |
| D17 | REQ006-IO-ERROR-UNSPEC | `spec.md:97` (REQ-006) | REQ-006의 트리거는 "JSON으로 파싱되지 않거나 「유효한 뉴스 문서」를 만족하지 못하면"이다. 파일이 존재하되 **읽을 수 없는** 경우(권한 오류·I/O 오류)는 REQ-002(200)·REQ-004(404)·REQ-006(500) 어디에도 명시적으로 걸리지 않는다. 실무상 500으로 떨어지겠으나 규정은 없다 | NIT | optional | REQ-006의 트리거에 "읽을 수 없거나"를 한 단어 추가한다 |

**Severity 집계**: BLOCKER **0** · MAJOR **1** · MINOR **7** · NIT **9** (총 17)
**Class 집계**: blocking **2** (D1 · D2) · optional **15** (D3~D17)

---

## blocking / optional 분리 (재작업 루프를 구동하는 범위)

**blocking (2건 — 2차 재감사의 델타 범위)**
- **D1 (MAJOR)** — `AC-011`·`AC-010`(b)의 준비 상태를 만들 수단 미규정. REQ-011의 유일한 검증 경로가 기재된 대로 실행 불가.
- **D2 (MINOR)** — DoD 두 항목의 자기모순. `008490` 수집 실패 시 완료 판정이 갈린다.

**optional (15건 — 오케스트레이터 재량, 재감사 불필요)**
- 구현 시간에 실제로 영향을 줄 순서: **D3**(항목 키 통과 여부 — 구현자 해석이 갈림) → **D5**(픽스처 한 줄로 정렬 규칙 4 행사) → **D4**(빈 배열 자동 AC) → **D7**(원시 HTML 금지 한 줄) → **D8**(AC-015 ④ 시점 고정).
- 나머지(D6·D9~D17)는 문구·표기 수준이며 반영하지 않아도 구현 결과가 달라지지 않는다.
- **optional 15건의 수는 그 자체로 FAIL 근거가 아니며 본 판정에 사용하지 않았다.** 판정은 must-pass 방화벽과 게이트 4조건에만 근거한다.

---

## Regression Check

iteration 1이므로 이전 반복의 결함 목록이 없다. stagnation 판정 대상 아님.

---

## Recommendation

**FAIL 판정의 근거** — 게이트 4조건 중 하나가 깨진다.
1. BLOCKER 0건 ✓
2. 미해소 MAJOR **1건(D1)** ✗ ← 이 항목 하나가 판정을 결정한다
3. Aggregate 0.8625 ≥ Tier M 임계 0.80 ✓
4. Must-Pass MP-1~MP-7 전부 PASS 또는 N/A ✓

**판정의 성격을 분명히 기록한다.** 이 SPEC은 형제 SPEC이 1차에서 6건의 blocking을 받았던 자리를 대부분 선제적으로 메운 상태다 — 술어의 단일 정의(D2 계열), 네 조건 전수 행사 AC, 경로 바인딩과 `monkeypatch` 전략의 사전 정렬(D8 계열), CI 8단계 정확 기술(D4 계열), ruff E501 정정(D7 계열), 죽은 의존성 회피(D11 계열), 무인증 근거와 전이 조건(D12 계열), 미존재 SPEC 명시(D18 계열)가 전부 반영되어 있다. 저장소 사실 주장은 전수 대조에서 거짓이 0건이고, 미검증 사실은 §A.9에 정직하게 남아 있다. **따라서 FAIL은 품질 붕괴의 신호가 아니라 단일 실행 가능성 결함에 대한 게이트 작동이며, 2차는 전면 재감사가 아니라 D1·D2 델타 한정 재감사여야 한다.**

**2차 착수 전 처리 항목 (순서대로)**

1. **D1 — `AC-011`을 실행 가능한 형태로 만든다.** 가장 적은 변경은 위 표의 (b)안이다: `AC-011`의 Given을 "두 종목 요청이 모두 지연된 상태(브라우저 개발자도구 네트워크 스로틀링)에서 삼성전자를 선택한 직후 응답 도착 전에 SK하이닉스를 선택하고 충분히 기다리면"으로 바꾸면 비대칭 지연 없이 같은 경쟁 상태가 재현되고 Then은 그대로 둘 수 있다. 동시에 `acceptance.md:79`의 준비 수단 열거에 그 도구를 한 항목으로 추가해 `AC-010`(b)도 함께 덮는다.
2. **D2 — DoD 한 줄 한정.** `acceptance.md:110`을 "AC-001을 제외한" 형태로 좁히거나, `:111`에 "이 경우 첫 항목의 예외로 기록한다"를 덧붙인다.
3. **여유가 있으면 함께** — D3(항목 키 통과 여부 한 줄), D5(AC-002 픽스처에 파싱 불가 항목 한 건 추가), D4(빈 배열 자동 AC 신설 — AC 예산 15/16이라 한 자리 여유 있음), D7(원시 HTML 금지 한 줄). 네 건 모두 run 단계에서 실제 시간을 잃게 할 항목이며, 지금 손대면 한 줄씩이다.
4. **D6·D8~D17은 오케스트레이터 재량이다.** 재감사가 이를 근거로 추가 반복을 만들지 않는다.

**본 PASS/FAIL은 plan-audit 검증에 한정된다.** D1·D2 해소 후 2차에서 PASS가 나오더라도 plan→run 인간 승인 게이트(Implementation Kickoff Approval)를 대신하지 않는다.

---

## 본 감사가 실행하지 않은 것 (명시)

- `pytest backend/tests/ -v` — **미실행** (이 환경에 `pytest` 미설치)
- `ruff check backend/` — **미실행**
- `npm run lint` / `npm run build` — **미실행**
- `python scripts/orchestrate_stock_agents.py 008490 --save` (수집 스크립트) — **미실행** (`claude -p` 호출·Claude 사용량 소모·저장소에 파일 생성)
- 백엔드·프론트엔드 서버 기동 및 화면 렌더링 관찰 — **미실행**
- 상태를 변경하는 어떤 git 명령도 실행하지 않음 (사용한 것은 `git check-ignore -v`, `git status --porcelain` 두 건의 읽기 전용 질의뿐)
- SPEC 파일·코드·설정 파일에 대한 편집 — **없음**

---

VERDICT: FAIL
