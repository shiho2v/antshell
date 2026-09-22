# SPEC Review Report: SPEC-PORTFOLIO-001

Iteration: 2/3
Verdict: **PASS**
Overall Score: **0.875** (Tier M PASS 기준 0.80 충족)

> Reasoning context ignored per M1 Context Isolation. 호출자가 전달한 작성자 측 설명·의도는 사용하지 않았다. 입력은 `.moai/specs/SPEC-PORTFOLIO-001/`의 4개 산출물, 1차 감사 보고서(`-review-1.md`), 그리고 저장소 실물뿐이다.
> 감사 범위: **Retry Loop Contract에 따른 delta 한정 재감사**. 1차 blocking 6건(D1~D6)의 해소 여부 + 편집이 새로 만들 수 있는 회귀 항목만 본다. 전면 재감사가 아니다.
> 1차 optional 17건(D7~D23)은 재제기하지 않는다. 다만 편집이 건드린 지점에서 관련될 때만 상태를 한 줄로 기록했다.
> 저장소 접근은 전부 읽기 전용이었고 SPEC 파일·코드·git 상태를 변경하지 않았다. git 명령은 `git check-ignore` 한 건(읽기 전용 질의)만 사용했다.

---

## Must-Pass Results

- **[PASS] MP-1 REQ number consistency**
  `grep -o '^\*\*REQ-[0-9]*\*\*' spec.md | sort | uniq -c` → REQ-001 … REQ-016 각 정확히 1회, 총 16개. 결번 0, 중복 0, 3자리 제로패딩 일관.

- **[PASS] MP-2 EARS/GEARS format compliance** — *요구사항 계층(`REQ-XXX` in `spec.md`)에 대해 판정함. 검증 계층(`acceptance.md`의 `AC-XXX`)은 Given-When-Then이 정규 형식이며 Group 4에서 따로 채점했다 — 이 기준으로는 감점하지 않았다.*
  1차 FAIL 근거였던 구 REQ-012의 이중 요구사항이 해소되었다. spec.md:104 `**REQ-012** [Event-driven] **When** 인증되지 않은 사용자가 /portfolio에 접근하면, 프론트엔드는 대시보드와 동일하게 /login으로 이동시킨다.` — 리다이렉트 단일 절. 대시보드 링크는 spec.md:106 `**REQ-013** [Ubiquitous] 대시보드는 /portfolio로 이동하는 링크를 제공한다.`로 분리되었고, AC도 AC-012 / AC-013으로 분리되어 매핑표(acceptance.md:128-129, 147-148)가 함께 갱신되었다.
  16개 전부를 태그 대 문장 구조로 대조했다 — `grep -n '^\*\*REQ-[0-9]*\*\* \[' spec.md` 출력 16행 전문 검토. 태그 분포: Ubiquitous 3(001·013·016), Event-driven 9(002·003·004·005·006·007·009·011·012), State-driven 1(010), Where 1(014), Unwanted 2(008·015). 각 항목이 하나의 동작을 기술하며 단일 테스트 가능 진술로 읽힌다.
  판정을 투명하게 기록한다 — 두 항목은 엄격히 읽으면 논쟁 여지가 있으나 blocking으로 보지 않았다.
  1. spec.md:78 REQ-001 `[Ubiquitous]`의 마지막 절("교체 이전 단계에서 중단되면 … 보존되고 임시 파일도 남지 않는다")은 조건절을 품고 있다. 그러나 두 절은 **서로 독립된 요구사항이 아니라** 같은 저장 동작의 정상 경로와 그 관측 가능한 성질이다. 1차 FAIL의 형태(무관한 두 요구사항의 결합)와 다르다.
  2. spec.md:110 REQ-015 `[Unwanted]`도 부정절 + 긍정 렌더링절 구조인데, 이는 1차 감사가 통과시킨 구 REQ-014와 동일한 구조다. 같은 잣대를 유지했다.
  3. spec.md:108 REQ-014 `[Where]` 태그 오기는 1차 D14(MINOR·optional)로 이미 기록된 항목이며 편집으로 악화되지 않았다 — 재제기하지 않는다.

- **[PASS] MP-3 YAML frontmatter validity**
  spec.md:2-14 — `id`(SPEC-PORTFOLIO-001) / `title`(인용) / `version`("0.1.1" 인용 semver) / `status`(draft) / `created`(2026-09-20) / `updated`(2026-09-20) / `author`(정우준) / `priority`(P1) / `phase`("v1.0.0" — 금지된 라이프사이클 토큰 아님) / `module` / `lifecycle`(spec-anchored) / `tags`(인용 CSV) 12개 전부 존재, 타입 적합. snake_case 별칭(`created_at`·`updated_at`·`labels`·`spec_id`) 0건. 선택 필드 `tier: M` 유지. `version`이 0.1.0 → 0.1.1로 갱신되었고 HISTORY에 대응 행이 있다(spec.md:22).

- **[N/A] MP-4 Section 22 language neutrality**
  단일 프로젝트 범위(python 백엔드·스크립트 + typescript 프론트엔드). 16개 언어 공통 툴링을 다루는 템플릿 바인딩 콘텐츠가 아니므로 해당 없음 → 자동 통과. 1차와 동일.

- **[PASS] MP-5 D7 cross-SPEC reconciliation**
  `grep -Eoh 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/specs/SPEC-PORTFOLIO-001/*.md | sort -u` → SPEC-API-001, SPEC-CHART-001, SPEC-NEWS-001, SPEC-PORTFOLIO-001.
  `grep '^status:' .moai/specs/SPEC-API-001/spec.md` → `status: draft`
  `grep '^status:' .moai/specs/SPEC-CHART-001/spec.md` → `status: in-progress`
  `.moai/specs/SPEC-NEWS-001/spec.md` → MISSING
  retired / superseded / archived 상태인 참조 SPEC 0건 → BLOCKING 0건. SPEC-NEWS-001 미존재는 D7-5 SHOULD 등급(1차 NIT D18, 변동 없음).

- **[PASS] MP-6 D8 cross-platform discipline**
  `grep -c 'syscall' spec.md` → `0`. D8-4 자동 PASS.

- **[PASS] MP-7 clarification gate**
  `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-PORTFOLIO-001/` → 출력 없음. plan.md 존재, research.md는 Tier M이라 부재. 미해결 마커 0건.

---

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 — 소수 요구사항에 해석 여지가 남으나 합리적 엔지니어가 일관되게 해소할 수준 | 1차 0.50의 핵심 근거 두 개가 모두 제거됨: (a) spec.md:172-186에 「필수 키 집합」 다섯 조건이 한 곳에 정의되고 REQ-002·REQ-004·REQ-007이 모두 이를 인용, (b) spec.md:84 REQ-004가 `--sample` 전체 동작을 명문화. 잔여: spec.md:129 `portfolio_file` 상대/절대 경로 형식 미지정(1차 D15), 응답 스키마의 `agent` 키 탈락 미명시(1차 D9), 신규 n2(`--sample` 단독 실행 시 저장 여부) |
| Completeness | 1.00 | 1.00 — 필수 섹션·frontmatter 전부 존재, 1차의 결손 1건 해소 | HISTORY(17-22) / 개요·설계 결정(26-72) / 요구사항(74-114) / 인수기준 포인터(116-118) / 데이터 계약(120-211) / 제외 범위(213-241) 전부 존재. `### Out of Scope — <topic>` H3 **9개**, 각 `-` 불릿 보유 → SC-6 충족. frontmatter 12/12. 1차 결손(DoD가 요구하는 `--sample` 산출물에 REQ 없음)은 REQ-004·AC-004 신설로 해소. 신규 보강: 수동 검증 절차 문서의 요건이 acceptance.md:64-73에 4항목(준비/실행/관찰/PASS 조건)으로 규정됨 |
| Testability | 0.80 | 0.75 밴드 + 신규 이진 AC에 대한 명시 가산 | 신규·보강 AC가 전부 이진 판정 가능: acceptance.md:21 AC-002(b) `os.replace` 직전 예외 주입 → 종료 코드 ≠0 + 바이트 동일 + 잔여 임시 파일 0; acceptance.md:25 AC-004 바이트 동일 + `subprocess`·`shutil.which` 호출 0 + 5조건 충족 + 판정 값 분포; acceptance.md:29 AC-006 (a)~(e) 5케이스 각각 상태 코드 고정. 잔여 감점(전부 1차 optional·변동 없음): AC-006의 "`/`·`\` 포함 절대 경로 조각" 술어(1차 D10), AC-015 "시각적으로 구분된다"(1차 D14 계열), AC-016 "응답이 변경 전과 동일"의 기준선 부재(1차 D16). 다만 AC-015·AC-016의 화면분은 acceptance.md:71이 "PASS 조건은 이진 판정이 되도록 쓴다"를 절차 문서 요건으로 고정해 완화됨 |
| Traceability | 0.95 | 1.00 기준 전부 충족, 간접 매핑 1건에 대한 소폭 감점 | acceptance.md:115-151 양방향 매핑표를 독립 검증: 16개 REQ 전부 ≥1 AC 보유(미커버 0), 16개 AC 전부 실재 REQ 참조(고아 0), 두 표가 서로 모순 없음. 1차 지적(AC-016이 REQ-001의 저장 의무를 행사하지 않음)은 AC-002(b) 신설로 해소 — REQ-001의 원자적 저장 절을 실제로 행사하는 AC가 생겼다. 감점 근거: AC-005가 REQ-004를 부차 참조하나 실제로 검증하는 것은 서빙 측 등가성이며, REQ-004의 직접 커버는 AC-004가 전담한다(간접 매핑 1건) |

**Aggregate = (0.75 + 1.00 + 0.80 + 0.95) / 4 = 3.50 / 4 = 0.875** — Tier M PASS 임계 0.80 충족.

**점수 추이**: iter1 0.69 → iter2 0.875. 상승이므로 LEAN 워크플로의 STOP 에스컬레이션(점수 회귀 시 발동) 조건에 해당하지 않는다.

---

## 5-Section Evidence Report

### 1. Claim (주장)

본 재감사가 주장하는 바는 다섯 가지다.

1. **1차 blocking 6건(D1~D6)이 전부 해소되었다.** 각 항목마다 요구된 산출물이 실제 파일에 존재하며, 그 내용이 요구된 술어를 만족한다.
2. **Tier M 예산(REQ 16 / AC 16)을 정확히 지켰고, 예산을 맞추기 위한 병합으로 테스트 가능성을 잃지 않았다.** 병합된 3건 각각에 대해 병합 후에도 이진 판정 AC가 대응함을 확인했다.
3. **편집이 새로 만든 저장소 사실 주장은 전부 참이다.** `ci.yml` 8단계, `frontend/package.json` devDependencies, 스크립트 import 목록, `SPEC-CHART-001`의 `--sample` 선례 — 실물과 대조해 일치한다.
4. **승인된 설계 결정 7개가 모두 그대로다.** 편집이 범위·구조를 바꾸지 않았다.
5. **신규 결함은 MINOR 2건·NIT 3건이며 BLOCKER·MAJOR는 없다.** 그중 하나(M1·M2 병렬성 서술 충돌)는 D2 수정 텍스트가 직접 만들어 낸 것이다.

### 2. Evidence (증거 — 실행한 명령과 그 출력)

**(E-1) REQ/AC 독립 재계수 — 작성자 주장 불신뢰**

```
$ grep -o '^\*\*REQ-[0-9]*\*\*' spec.md | sort | uniq -c
      1 **REQ-001**  …  1 **REQ-016**      (각 1회, 16종)
$ grep -c '^\*\*REQ-[0-9]*\*\*' spec.md        → 16
$ grep -o '^\*\*AC-[0-9]*\*\*' acceptance.md | sort | uniq -c
      1 **AC-001**   …  1 **AC-016**       (각 1회, 16종)
$ grep -c '^\*\*AC-[0-9]*\*\*' acceptance.md   → 16
```
Tier M 상한은 REQ 16 / AC 16이며 두 축에 **독립적으로** 적용된다. 16/16은 상한 초과가 아니라 정확히 한계선이다.

**(E-2) D4 검증 — `plan.md` CI 기술 대 `.github/workflows/ci.yml` 실물**

`Read .github/workflows/ci.yml` (72행 전체). 단일 job `lint-and-test`. 기능 단계 순서:

| # | ci.yml 실물 | plan.md:30 기술 | 일치 |
|---|---|---|---|
| ① | `pip install -r backend/requirements.txt ruff pytest` (L28) | 동일 | ✓ |
| ② | `npm ci` (frontend, L32) | 동일 | ✓ |
| ③ | `ruff check backend/` (L35) | 동일 | ✓ |
| ④ | `npm run lint` (frontend, L39) | 동일 | ✓ |
| ⑤ | `pytest backend/tests/ -v` (L42) | 동일 | ✓ |
| ⑥ | `npm run build` (frontend, L48) | 동일 | ✓ |
| ⑦ | `pip-audit`, `continue-on-error: true` (L64-66) | 동일 | ✓ |
| ⑧ | `npm audit --audit-level=high`, `continue-on-error: true` (L68-71) | 동일 | ✓ |

1차 D4의 누락 2건(⑤ `pytest`, ⑥ `npm run build`)이 복원되었고, "차단 게이트는 ③~⑥ 네 개이고 ⑦·⑧은 경고다"도 `continue-on-error` 실물과 일치한다. `ruff.toml`이 저장소 루트에 존재함을 확인했다(`ls -la ruff.toml` → 893바이트) — "루트 `ruff.toml`" 표기도 참이다.

**(E-3) `scripts/tests/`의 CI 밖 처리 — 정합성·정직성**

```
$ ls scripts/tests/
test_fetch_ohlcv.py
```
`ci.yml` L42가 `backend/tests/`만 지정하므로 이 디렉터리는 실제로 CI에서 실행되지 않는다 — plan.md:31의 주장은 참이다. 이 사실이 다섯 곳에 일관되게 반영되어 있다: plan.md:31(현재 상태), plan.md:146(A.5 리스크 행 — 1차에 없던 신규 행), plan.md:120(M4 작업 + 실패 시 보류 조건), acceptance.md:57·95(검증 수단 표 + 품질 게이트), progress.md:29. DoD:105도 대응 항목을 갖는다.
정직성 점검: plan.md:197(A.9)이 "`scripts/tests/test_fetch_ohlcv.py`가 지금 초록인지는 실행으로 확인하지 못했다(이 환경에 `pytest` 미설치)"로 미검증 사실을 그대로 남겼다. 확인되지 않은 것을 확인된 것처럼 적지 않았다.
plan.md:31의 부수 주장("대상 스크립트와 테스트의 import는 표준 라이브러리 + `pytest`뿐")도 실측으로 참이다:
```
$ grep -n '^import\|^from' scripts/orchestrate_portfolio.py
argparse, datetime, html, json, shutil, subprocess, sys, pathlib   (전부 표준 라이브러리)
$ grep -n '^import\|^from' scripts/fetch_ohlcv.py
argparse, json, random, sys, datetime, pathlib                      (전부 표준 라이브러리)
$ grep -n '^import\|^from' scripts/tests/test_fetch_ohlcv.py
json, sys, pathlib, pytest, fetch_ohlcv
```

**(E-4) D5 검증 — 수동 검증 절차의 구체성과 의존성 무증가**

```
$ cat frontend/package.json
devDependencies: @types/node, @types/react, @types/react-dom, autoprefixer,
                 eslint, eslint-config-next, postcss, tailwindcss, typescript
```
jest / vitest / `@testing-library` 전부 부재 → 신규 프론트엔드 의존성이 도입되지 않았음을 확인. plan.md:33과 acceptance.md:53의 기술이 실물과 정확히 일치한다. `spec.md:236-237`이 프레임워크 도입을 §5 제외 범위로 명시했고, plan.md:164(A.6 PRESERVE)가 `frontend/package.json` 수정 금지를 못 박았으며, DoD:109가 "신규 의존성 추가 없음"을 체크 항목으로 둔다 — 세 층이 서로를 강화한다.
절차의 구체성: acceptance.md:64-73이 위치(`docs/weekly/WEEK_10.md`의 「`/portfolio` 화면 수동 검증 절차」), 대상(AC-009~AC-015 + AC-016의 대시보드 항목), 항목당 4줄(준비 / 실행 / 관찰 대상 / PASS 조건), PASS 조건의 이진성까지 규정한다. 실행 예시도 명령 수준으로 적혀 있다(`uvicorn app.main:app --reload` → `npm run dev` → `http://localhost:3000/portfolio`). 증거 경로는 progress.md 매트릭스이며, acceptance.md:91이 "절차 문서 인용 없이 '확인함'이라고만 적은 항목은 PASS로 보지 않는다"로 회피 경로를 닫았다.
정직성: acceptance.md:62가 "자동 게이트 통과를 해당 AC의 PASS 근거로 삼지 않는다"고 명시해, 린트·빌드 통과를 화면 AC의 증거로 위장하는 경로를 차단했다. `docs/weekly/WEEK_10.md`는 실재하며(`ls docs/weekly/`) 현재 portfolio 언급 1회 — M3가 절을 신설할 여지가 있다.

**(E-5) D6 검증 — 비원자적 쓰기를 실제로 떨어뜨리는 AC**

acceptance.md:21 AC-002 (b): "저장 함수가 임시 파일을 만든 **뒤** 교체(`os.replace`) 직전에 예외를 던지도록 패치한 경우 … 종료 코드가 0이 아니고, 대상 파일의 내용(바이트)이 실행 전과 동일하며, 대상 파일이 있는 디렉터리에 잔여 임시 파일이 남지 않는다."
세 조건 전부 1차 D6이 요구한 그대로다. `write_text` 직접 호출 구현은 임시 파일 단계가 없어 이 주입 지점 자체를 만들 수 없으므로 AC-002(b)를 통과할 수 없다 — 1차가 지적한 "비원자적 구현도 통과" 구멍이 막혔다. 요구사항 측도 보강되었다(spec.md:78 REQ-001 말미에 "임시 파일도 남지 않는다" 추가). plan.md:92(M1 산출물)와 plan.md:188(A.8 MX 태그)이 같은 주입 경로를 명시해 3개 문서가 정합한다.

**(E-6) D1 검증 — `--sample`의 4개 요건**

spec.md:84 REQ-004와 acceptance.md:25 AC-004를 요건별로 대조:

| D1 요건 | REQ-004 | AC-004 |
|---|---|---|
| 결정론 | "같은 입력 파일과 같은 실행일로 두 번 실행하면 저장된 바이트가 동일하다" | "같은 날 두 번 실행 … 두 번의 저장 결과가 바이트 단위로 동일" |
| 허용 목록 준수 | "REQ-003의 허용 목록 검사 … 그대로 적용된다" | 후반절: 입력을 `portfolio.edge.json`으로 바꾸면 종료 코드 ≠0, 파일 미생성 |
| 실패 시 비덮어쓰기 | "REQ-001의 임시 파일 교체 저장, REQ-002의 비덮어쓰기 규칙이 그대로 적용된다" | 후반절(간접) + AC-002가 저장 경로 전반을 담당 |
| `claude` 미호출 | "`claude` 실행과 서브에이전트 호출을 한 번도 하지 않고" | "`subprocess`·`shutil.which` 호출이 한 번도 발생하지 않으며" |

`shutil.which`까지 감시 대상에 넣은 점은 실물과 맞다 — `scripts/orchestrate_portfolio.py` L84가 `shutil.which("claude")`, L92가 `subprocess.run(...)`이다. plan.md:66-73(A.2 결정 3)과 plan.md:91(M1), plan.md:148(A.5 리스크 행)이 같은 규칙을 반복하며 어긋나지 않는다.
plan.md:65의 신규 주장 "`SPEC-CHART-001`의 `--sample` 선례를 따라"도 실물로 확인했다:
```
$ grep -n 'sample' scripts/fetch_ohlcv.py
6:  python scripts/fetch_ohlcv.py --sample   # 결정론적 샘플 데이터 생성
68: generator = random.Random(SAMPLE_SEED + int(stock_code))   ← 시드 고정 = 결정론
197: source = "sample" if arguments.sample else "pykrx"
```
선례가 실재하고, 그 선례 자체도 시드 고정으로 결정론을 달성한다.

**(E-7) D2 검증 — 술어의 단일 정의와 양측 참조**

spec.md:172 「필수 키 집합 (REQ-002 · REQ-004 · REQ-007 공통 술어)」 — 제목에 소비자 3개를 명시. 본문 spec.md:176-184에 다섯 조건 열거(최상위 9키 / 세 블록의 `results`가 리스트 / 숫자 3필드 / 세 `results` 길이 동일 / 원소별 최소 키). spec.md:184가 경계도 규정한다 — "열거되지 않은 키가 더 있거나 없는 것은 위반이 아니며, 값의 범위나 enum 적합성도 이 술어의 판정 대상이 아니다". spec.md:186이 `meta` 키 부재가 위반이 아님을 따로 처리한다.
참조 측 확인: 스크립트 측 REQ-002(spec.md:80) "§4 「필수 키 집합」을 만족하지 못함", REQ-004(spec.md:84) "§4 「필수 키 집합」을 만족하는 분석 결과", 백엔드 측 REQ-005(spec.md:88) "§4 「필수 키 집합」을 만족하면", REQ-007(spec.md:92) "§4 「필수 키 집합」을 만족하지 못하면". **네 곳 전부 같은 §4 정의를 인용하며 자체 정의를 만들지 않는다.** plan.md:49(A.2 결정 1)가 "「필수 키 집합」은 한 곳에만 정의"를 구현 지침으로 못 박고, plan.md:103(M2)이 테스트 케이스를 같은 다섯 조건에서 뽑도록 지시한다.
AC 확장 확인: acceptance.md:29 AC-006은 (a) 부재 → 404, (b) 파싱 불가 → 500, (c) 최상위 키 `allocation` 누락 → 500, (d) `risk.results`가 비-리스트 → 500, (e) `valuation.results` 길이 불일치 → 500. **`allocation` 단일 케이스를 넘어 다섯 조건 중 1·2·4를 각각 행사한다** — 1차 D2가 요구한 확장을 충족한다.

**(E-8) 승인 결정 7개 불변 확인**

| 결정 | 근거 | 상태 |
|---|---|---|
| 오프라인 생성 → 파일 서빙 | spec.md:48-52(§1.2 표), plan.md:56-60(결정 2, 후보 4개 비교) | 불변 |
| 고정 샘플 보유 종목 파일 | spec.md:60 "저장소에 고정된 `data/portfolio.example.json` 한 개", spec.md:216(§5) | 불변 |
| `SPEC-API-001`에 `depends_on` 없음 | frontmatter에 `depends_on` 필드 자체가 없음, spec.md:32-34(§1.0) | 불변 |
| 백엔드 API + `/portfolio` 화면 | REQ-005~REQ-008(백엔드), REQ-009~REQ-015(화면) | 불변 |
| 허용 4종목 | spec.md:58 `005930`·`000660`·`009150`·`008490` | 불변. 실물 대조: `ls data/`에서 이 4종목만 `_market.json`+`_fundamentals.json` 동시 보유, `005380`은 `_agents.json`만 존재 |
| allocation의 현금 포함 비중만, risk 비중은 응답에서 제거 | REQ-005(spec.md:88), §4 비중 정의(spec.md:204), AC-008(acceptance.md:33) | 불변 |
| `GET /api/portfolio` 무인증 | spec.md:239-240(§5 마지막 항목) | 불변 |

**(E-9) 신규 라우트 충돌 재확인**
```
$ grep -n '@app\.\(get\|put\|post\|delete\)' backend/app/main.py
47:/health  123·132·165:/api/settings/notion  183:/api/report/notion
236:/api/github/issues  311:/api/stocks/{code}/ohlcv  327:/api/stocks/{code}/indicators
```
REQ-016(spec.md:114)이 열거한 7개 항목과 정확히 일치, 누락 0. `/api/portfolio`는 아직 없고 `/api/stocks/{code}/...`와 접두 충돌하지 않는다.

**(E-10) 마일스톤 커버리지 열 대 실제 REQ/AC 범위**

| 마일스톤 | plan.md A.3 커버 | progress.md 커버 | spec.md §2 블록 | acceptance.md 검증 수단 표 | 일치 |
|---|---|---|---|---|---|
| M1 | REQ-001~004 / AC-001~004 | 동일 | 오프라인 생성 = REQ-001~004 | AC-001~004 = `scripts/tests/` | ✓ |
| M2 | REQ-005~008 / AC-005~008 | 동일 | 백엔드 = REQ-005~008 | AC-005~008 = `backend/tests/test_portfolio.py` | ✓ |
| M3 | REQ-009~015 / AC-009~015 | 동일 | 프론트엔드 = REQ-009~015 | AC-009~015 = 수동 | ✓ |
| M4 | REQ-016 / AC-016 | 동일 | 기존 기능 호환성 = REQ-016 | AC-016 = 자동+수동 | ✓ |

네 문서의 번호 범위가 전부 맞물린다. **구 번호(REQ-015 이하 체계, 구 AC-016)가 남은 곳은 없다.**

### 3. Baseline-attribution (baseline 귀속)

- 저장소: `/home/woojun/playground/antshell`, 브랜치 `main`, 대화 시작 스냅샷 HEAD `29395f5`.
- 모든 사실 확인은 **이 실행, 이 트리**에서 수행했다. 1차 감사 보고서는 *무엇을 확인할지*의 목록으로만 사용했고, 1차가 보고한 측정값을 그대로 옮겨 적지 않았다 — `ci.yml` 8단계, `package.json` devDependencies, 스크립트 import, `dashboard/page.tsx:16`, 백엔드 라우트 목록, `portfolio.edge.json`·`portfolio.example.json` 내용은 전부 이번에 다시 읽었다.
- SPEC 산출물 4개(`spec.md` 241행 / `plan.md` 199행 / `acceptance.md` 152행 / `progress.md` 51행)를 **전문** 읽었다. 표본 추출이 아니다.
- REQ/AC 계수는 작성자 주장과 무관하게 `grep | sort | uniq -c`로 독립 재계수했다(결과 16/16, 작성자 주장과 일치).
- git 명령은 `git check-ignore -v data/portfolio_analysis.json`(→ NOT ignored) 한 건만 사용했다. 상태를 바꾸는 명령은 실행하지 않았다.

### 4. Gaps (미검증 — 본 감사가 관찰하지 못한 것)

- **어떤 테스트·빌드도 실행하지 않았다.** `pytest backend/tests/`, `pytest scripts/tests/`, `npm run lint`, `npm run build`, `npx tsc --noEmit` 전부 미실행. AC-016이 전제하는 "기존 테스트 통과" 현 상태는 관찰 범위 밖이다. 확인한 것은 도구 설정 파일의 실재뿐이다(`ruff.toml`, `frontend/tsconfig.json`, `frontend/.eslintrc.json`).
- **`scripts/orchestrate_portfolio.py`를 실행하지 않았다.** spec.md §1.4의 실측값(`risk` 47.8 대 `allocation` 44.54)과 서흥 `volume_state: "stale"`은 1차와 마찬가지로 재현하지 못했다. 에이전트 정의와 정합적이라는 1차 판단을 이번에 다시 검증하지도 않았다 — delta 범위 밖이기 때문이다.
- **`data/portfolio_analysis.json`이 여전히 부재**하므로 §4 파일 스키마를 실제 병합 결과와 대조하지 못했다. 「필수 키 집합」 다섯 조건이 실제 에이전트 출력으로 충족 가능한지는 M1에서 처음 확인된다.
- **수동 검증 절차 문서가 아직 존재하지 않는다.** `docs/weekly/WEEK_10.md`에 해당 절이 없음을 확인했다(M3 산출물이므로 정상). 따라서 판정한 것은 *요건의 구체성*이며 *절차 자체의 품질*이 아니다.
- **「필수 키 집합」 조건 3(숫자 필드)과 조건 5(원소별 최소 키)를 행사하는 AC가 없다.** AC-006은 조건 1·2·4만 다룬다. 이 두 조건의 구현 여부는 run 단계에서만 드러난다.
- **1차 optional 17건 중 D7~D23의 현재 상태를 전수 재확인하지 않았다.** 편집이 건드린 지점(D9·D10·D14·D15·D16·D18·D19)만 변동 여부를 확인했고, 나머지는 delta 범위 밖으로 두었다.

### 5. Residual-risk (잔여 위험 — 관찰했음에도 남는 위험)

- **Tier M 예산이 정확히 한계선(16/16)이다.** run 단계에서 요구사항이 하나라도 추가로 필요해지면 다시 병합해야 하고, 그때는 이번처럼 테스트 가능성을 지키며 병합할 여유가 없다. 1차 → 2차 사이에 이미 3건의 병합이 있었다(구 REQ-004+008 → REQ-005, 구 AC-004+016 → AC-005, 구 AC-005+006 → AC-006). 추가 요구가 생기면 SPEC 분할이 정공법이다.
- **REQ-004·REQ-005가 조밀하다.** REQ-004는 네 문장에 결정론·판정 값 분포·세 규칙 승계를 담고, REQ-005는 성공 응답 구조와 비중 필드 제외를 함께 담는다. 각각 AC-004, AC-005+AC-008이 대응하므로 판정 가능성은 유지되지만, 부분 실패 시 어느 절이 깨졌는지 귀속이 한 단계 흐려진다.
- **「필수 키 집합」 조건 3·5가 AC로 행사되지 않으므로**, M1의 저장 전 검사와 M2의 읽기 시 검사가 이 두 조건을 서로 다르게(혹은 한쪽만) 구현해도 어떤 테스트도 이를 잡지 못한다. D2가 막으려던 비대칭이 다섯 조건 중 두 개에 대해서는 여전히 열려 있다.
- **`--sample`이 주 데이터 경로가 될 위험은 남아 있으나 관리되고 있다.** plan.md:196(A.9)이 `claude -p` 실행 가능 여부를 미해결로 두지만, REQ-004가 판정 값 분포를 요구사항으로 고정했으므로 이 경로로 빠져도 화면 검증 가능성은 보장된다. 1차의 잔여 위험 1번이 실질적으로 축소되었다.
- **CI 확장이 조건부다.** plan.md:120은 `test_fetch_ohlcv.py`가 현재 실패 상태면 확장을 보류하도록 한다. 보류되면 AC-001~AC-004는 M4의 수동 1회 실행으로 끝나고 이후 회귀 감시가 없다. 문서는 이 결말을 정직하게 허용하지만, 그 경우 최종 상태는 1차 D4 지적 당시와 실질적으로 같아진다.
- **무인증 `GET /api/portfolio`의 전이 조건이 여전히 미명시다.** 현재 서빙 대상이 커밋된 고정 샘플이라 위험은 낮으나, §5가 범위 밖으로 둔 "사용자별 보유 종목"이 후속 SPEC에서 들어오는 순간 이 엔드포인트는 무인증으로 개인 보유·현금 잔고를 노출한다(1차 D12, optional, 변동 없음).

---

## D1~D6 해소 판정표

| # | ID | 판정 | 근거 (file:line) |
|---|---|---|---|
| D1 | SAMPLE-UNSPEC | **RESOLVED** | `spec.md:84` REQ-004 신설 — 에이전트 미호출·결정론·판정 값 분포·REQ-001/002/003 승계 4요건 전부 명문화. `acceptance.md:25` AC-004 신설 — 바이트 동일 + `subprocess`·`shutil.which` 0회 + 5조건 + `source: "sample"` + 값 분포 + edge 입력 거부. `plan.md:66-73` 결정 3 / `plan.md:91` M1 / `plan.md:148` 리스크 행 / `plan.md:189` MX 태그가 모두 정합. `spec.md:234`가 "실제 판정 품질을 주장하지 않는다"로 범위를 봉합. 1차가 제시한 선택지 (a) 경로를 택했다 |
| D2 | SCHEMA-PREDICATE | **RESOLVED** | `spec.md:172-186` 「필수 키 집합 (REQ-002 · REQ-004 · REQ-007 공통 술어)」 — 다섯 조건 + 비위반 경계 + `meta` 예외까지 **한 곳에서만** 정의. 참조 측 4곳(`spec.md:80`, `:84`, `:88`, `:92`)이 전부 이 정의를 인용. `plan.md:49`가 구현 지침으로, `plan.md:103`이 테스트 구성 지침으로 강화. `acceptance.md:29` AC-006이 `allocation` 단일 케이스에서 5케이스((a)~(e), 조건 1·2·4 행사)로 확장 |
| D3 | GEARS-REQ012 | **RESOLVED** | `spec.md:104` REQ-012가 리다이렉트 단일 절로 축소, `spec.md:106` REQ-013 `[Ubiquitous]` 신설로 대시보드 링크 분리. `acceptance.md:41` AC-012 / `acceptance.md:43` AC-013으로 AC도 분리, 양방향 매핑표(`acceptance.md:128-129`, `:147-148`) 갱신 완료. 16개 REQ 전부를 태그 대 문장 구조로 대조해 1:1 대응 확인 — MP-2 FAIL 해소 |
| D4 | CI-INCOMPLETE | **RESOLVED** | `plan.md:30`이 실제 8단계로 정정되어 `ci.yml` L28~L71과 단계별 일치(E-2 표). 누락됐던 `pytest backend/tests/ -v`·`npm run build` 복원, 차단 게이트 ③~⑥ 구분도 `continue-on-error` 실물과 일치. `scripts/tests/` 처리: `plan.md:31`(사실 명시) + `plan.md:146`(A.5 신규 리스크 행) + `plan.md:120`(M4 확장 작업 + 보류 조건) + `acceptance.md:57·95` + `progress.md:29` + DoD `acceptance.md:105` — 1차가 제시한 (a)+(b) 양쪽을 모두 반영했고 미검증 사실은 `plan.md:197`에 정직하게 남겼다 |
| D5 | FE-AC-UNVERIFIABLE | **RESOLVED** | 위치·단계·증거 3요소 모두 구체화: `acceptance.md:59`(위치 = `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」), `acceptance.md:64-73`(AC별 준비/실행/관찰 대상/PASS 조건 4줄 + PASS 조건 이진성 요구 + 실행 명령 예시), `acceptance.md:91`·`progress.md:27`(증거 = progress.md 매트릭스에 PASS 조건 인용, 인용 없는 "확인함"은 PASS 불인정). M3 산출물로 승격(`plan.md:112`, A.4 소유권 `plan.md:134`, A.7 `plan.md:180`). 신규 의존성 0건 — `frontend/package.json` 실물 대조(E-4) + `spec.md:236-237` §5 명시 + `plan.md:164` PRESERVE + DoD `acceptance.md:109`. 정직성: `acceptance.md:62`가 자동 게이트를 화면 AC의 PASS 근거로 쓰지 못하게 차단 |
| D6 | ATOMIC-UNTESTED | **RESOLVED** | `acceptance.md:21` AC-002 (b) — `os.replace` 직전 예외 주입 시 ① 종료 코드 ≠0 ② 대상 파일 바이트가 실행 전과 동일 ③ 잔여 임시 파일 없음. 1차가 요구한 세 조건 그대로. 요구사항 측도 `spec.md:78` REQ-001 말미에 "임시 파일도 남지 않는다" 추가. `plan.md:92`(M1 테스트 항목)·`plan.md:188`(MX 태그)이 같은 주입 경로를 지시. 비원자적 `write_text` 구현은 주입 지점을 만들 수 없어 AC-002(b)를 통과할 수 없다 |

**해소 집계**: RESOLVED 6 / PARTIAL 0 / UNRESOLVED 0

---

## New Findings (편집이 새로 만든 것만)

| # | ID | 위치 | 설명 | Severity | Class |
|---|---|---|---|---|---|
| n1 | MILESTONE-PARALLEL-CONTRA | `spec.md:174` · `plan.md:49` 대 `plan.md:128` · `plan.md:133` | D2 수정 텍스트가 "**M1과 M2가 병렬로 진행되므로** 구현 중에 그 어긋남을 맞출 기회가 없다"(spec.md:174)와 "두 마일스톤이 병렬로 진행되므로"(plan.md:49)를 근거로 든다. 그러나 `plan.md:128`은 "M2와 M3는 … 병렬로 진행할 수 있다. **M1은 두 마일스톤의 입력(데이터 파일)을 만들므로 선행되어야 한다**"고, A.4 표(plan.md:133)는 M2의 선행 조건을 "M1의 데이터 계약 확정"으로 적는다. M1∥M2와 M1→M2가 같은 SPEC 안에서 동시에 주장된다. 계약(단일 술어 정의) 자체는 어느 쪽이든 성립하므로 구현 결과는 바뀌지 않으나, 근거 문장이 서로를 부정한다 | MINOR | blocking(내부 일관성) — 다만 아래 PASS 게이트 기준(BLOCKER 0 / MAJOR 0)에는 걸리지 않음 |
| n2 | SAMPLE-SAVE-COUPLING | `spec.md:84` REQ-004 대 `acceptance.md:25` AC-004 | REQ-004는 "`--sample` 옵션으로 실행하면 … 저장한다"로 `--sample` 단독 실행이 저장까지 수행하는 것처럼 읽힌다. 반면 AC-004는 항상 `--sample --save-json <대상>` 조합만 검사한다. `--sample` 단독 실행 시 (ㄱ) 기본 경로에 저장하는지 (ㄴ) 표준 출력만 하는지 규정이 없다. REQ-001의 "기본 대상 `data/portfolio_analysis.json`"이 `--save-json`의 기본값인지 스크립트 전체의 기본값인지도 구분되지 않는다. 검사되는 조합은 정의되어 있으므로 구현 위험은 낮다 | MINOR | optional |
| n3 | AC004-WEAKER-CLAUSE | `acceptance.md:25` AC-004 후반절 대 `acceptance.md:23` AC-003 | 같은 허용 목록 거부 시나리오인데 AC-003은 "대상 경로에 파일이 생성되지 않고(**기존 파일이 있었다면 그대로이며**)"로 기존 파일 보존까지 단언하는 반면, AC-004 후반절은 "대상 경로에 파일이 생성되지 않는다"로만 끝난다. `--sample` 경로의 비덮어쓰기는 REQ-004가 요구하지만 AC가 그 절을 행사하지 않는다 | NIT | optional |
| n4 | KEYSET-COND-3-5-UNEXERCISED | `spec.md:180·182` 대 `acceptance.md:29` AC-006 | 「필수 키 집합」 다섯 조건 중 조건 3(`risk.total_market_value`·`allocation.total_asset`·`allocation.cash`가 숫자)과 조건 5(원소별 최소 키)를 행사하는 AC가 없다. AC-006은 조건 1·2·4만 다룬다. D2가 막으려던 M1/M2 술어 비대칭이 두 조건에 대해서는 검증 없이 남는다. AC 예산이 16/16 한계선이라 단순 신설로는 해소할 수 없다 | NIT | optional |
| n5 | CI-STEP-COUNT-PRECISION | `plan.md:30` | "순서대로 8단계"로 적지만 `ci.yml`의 `steps:` 배열은 실제로 11개다(`actions/checkout@v4`, `setup-python@v5`, `setup-node@v4` 3개가 추가). 열거된 8개는 전부 실물과 정확히 일치하므로 판단에 영향을 주지 않으나, "8단계"는 기능 단계 수이지 워크플로 단계 수가 아니다. `pytest` 단계의 `env: DATABASE_URL` 주입도 기술되지 않았다 | NIT | optional |

**Severity 집계**: BLOCKER 0 · MAJOR 0 · MINOR 2 · NIT 3 (총 5)

---

## Regression Check (Iteration 2+)

1차 blocking 6건(D1~D6)의 해소 여부는 위 「D1~D6 해소 판정표」가 담당한다 — 전부 RESOLVED, 미해소 0건이므로 Retry Loop Contract의 자동 FAIL 조건("이전 반복의 미해소 결함")에 해당하지 않는다. 3회 연속 미변경 결함(stagnation)도 없다.

아래는 이번 편집이 새로 만들 수 있었던 회귀만 점검한 결과다.

| 점검 항목 | 방법 | 결과 |
|---|---|---|
| Tier M 예산 (REQ 16 / AC 16) | `grep`으로 독립 재계수 | **PASS** — REQ 16, AC 16. 두 축 각각 상한 이하(정확히 한계선) |
| 병합으로 인한 테스트 가능성 손실 | 병합 3건 각각의 대응 AC 확인 | **PASS** — REQ-005(구 004+008) → AC-005(구조) + AC-008(비중)으로 분담 검증. AC-005(구 004+016) → 성공 구조 + `source` 등가성 둘 다 이진. AC-006(구 005+006) → 5케이스 각각 상태 코드 고정. 어느 병합도 이진 판정을 잃지 않았다 |
| REQ→AC 전수 커버 | `acceptance.md:115-132` 표 대조 | **PASS** — 16개 REQ 전부 ≥1 AC. 미커버 0 |
| AC→REQ 유효 참조 | `acceptance.md:134-151` 표 + 본문 인용 대조 | **PASS** — 16개 AC 전부 실재 REQ 참조. 고아 0. 두 표 상호 모순 0 |
| `plan.md` 커버리지 열의 구 번호 잔존 | A.3 M1~M4 커버 행 대조 | **PASS** — REQ-001~004 / 005~008 / 009~015 / 016, AC 동일. `spec.md` §2 블록 경계와 정확히 일치 |
| `progress.md` 커버리지 열의 구 번호 잔존 | 마일스톤 현황 표 대조 | **PASS** — plan.md A.3과 동일. 구 15-REQ 체계 잔존 0 |
| 상태 코드 정합 (spec ↔ acceptance) | REQ-005/006/007 대 AC-005/AC-006 | **PASS** — 200 / 404 / 500 세 경로가 어긋나지 않음 |
| 필드명 정합 (§4 ↔ AC ↔ plan) | 9개 최상위 키, `meta` 5필드, 비중 필드 | **PASS** — AC-001의 9키, AC-005의 `meta` 5필드, AC-008의 비중 처리가 §4와 일치. REQ-009가 표시를 요구하는 6필드(`verdict`·`score`·`overall`·`action`·`drift_pct`·`rebalance_amount`)가 「필수 키 집합」 조건 5의 최소 키에 전부 포함됨 |
| 파일 경로 정합 | A.4 소유권 / A.7 신규 파일 / DoD / 검증 수단 표 | **PASS** — `scripts/tests/test_orchestrate_portfolio.py`, `backend/tests/test_portfolio.py`, `frontend/src/app/portfolio/page.tsx`, `data/portfolio_analysis.json`, `docs/weekly/WEEK_10.md`, `.github/workflows/ci.yml` 6개 경로가 네 문서에서 동일하게 표기됨 |
| 마일스톤 파일 소유권 충돌 | A.4 표 + plan.md:137 | **PASS** — M3와 M4가 `docs/weekly/WEEK_10.md`를 공유하나 서로 다른 절이고 순서가 분리됨을 명시. `ci.yml`은 M4 단독, PRESERVE(plan.md:163)가 다른 단계 수정을 금지 |
| 병렬성 주장 정합 | M1/M2/M3 선후 관계 서술 대조 | **FAIL(경미)** — n1. M1∥M2(spec.md:174, plan.md:49)와 M1→M2(plan.md:128, :133)가 충돌. M2∥M3 주장 자체는 파일 소유권 표와 정합 |
| 저장소 사실 주장 (신규분) | `ci.yml`·`package.json`·스크립트 import·`fetch_ohlcv --sample`·`dashboard/page.tsx:16`·라우트 목록 실물 대조 | **PASS** — 전부 참(E-2, E-3, E-4, E-6, E-9). 거짓 주장 0건 |
| 승인 결정 7개 불변 | E-8 표 | **PASS** — 7/7 불변 |
| 1차 optional 항목의 악화 | D9·D10·D14·D15·D16·D18·D19 현재 상태 확인 | **악화 0건** — D10(AC-006 경로 술어)은 "예외 클래스명·`Traceback`" 추가로 오히려 개선. 나머지는 변동 없음. 재제기하지 않는다 |

---

## Recommendation

**PASS 판정의 근거** — 게이트 4조건을 모두 만족한다.
1. BLOCKER 0건.
2. 미해소 MAJOR 0건 — 1차 MAJOR 5건(D2~D6)과 BLOCKER 1건(D1)이 전부 RESOLVED이며, 신규 MAJOR는 없다.
3. Aggregate 0.875 ≥ Tier M 임계 0.80.
4. Must-Pass MP-1~MP-7 전부 PASS 또는 N/A — 1차 FAIL이었던 MP-2가 해소되었다.

**공정을 위해 함께 기록한다.** 이번 개정은 1차 지적을 형식적으로 때우지 않았다. 세 가지가 특히 그렇다. 첫째, D2를 "AC 하나 더 추가"가 아니라 **술어의 단일 정의 + 네 곳의 참조 통일**로 풀었고 비위반 경계(열거되지 않은 키, enum 적합성)까지 규정해 두 계층이 다르게 해석할 여지를 좁혔다. 둘째, D4에서 미검증 사실(`test_fetch_ohlcv.py`의 현재 통과 여부)을 확인된 것처럼 적지 않고 A.9에 남긴 뒤 M4에 보류 조건을 달았다 — 검증하지 않은 것을 검증했다고 적는 것이 가장 비싼 결함인데, 그 함정을 피했다. 셋째, D5에서 "테스트 프레임워크를 도입하자"는 손쉬운 길 대신 **수동 절차를 산출물로 고정하고 자동 게이트를 PASS 근거로 쓰지 못하게 차단**했다 — 범위를 지키면서 판정 근거를 만드는 쪽을 택했다.

**run 단계 착수 전 처리를 권하는 항목 (전부 MINOR 이하, 재감사 불필요)**

1. **n1** — 한 줄 수정이면 끝난다. `spec.md:174`와 `plan.md:49`의 "M1과 M2가 병렬로 진행되므로"를 "M2와 M3가 병렬로 진행되고 M1의 검사 코드와 M2의 검사 코드가 서로 다른 파일에 있으므로"처럼 A.4의 선후 관계와 맞추거나, 반대로 `plan.md:128`을 "M1은 데이터 파일을 만들지만 M2는 픽스처로 선행 없이 착수할 수 있다"로 정리한다. 어느 쪽이든 근거 문장이 서로를 부정하지 않게만 하면 된다.
2. **n2** — REQ-004에 "`--save-json`과 함께 지정된 대상에 저장한다" 또는 "`--save-json` 미지정 시 기본 대상 `data/portfolio_analysis.json`에 저장한다" 한 구절을 넣어 CLI 조합을 확정한다.
3. **n4** — AC 예산이 한계선이라 신설이 어렵다. AC-006의 (c)~(e) 케이스 중 하나를 조건 3 또는 5 위반으로 바꾸거나, `plan.md:103`(M2 테스트 구성 지침)에 "다섯 조건 각각에 최소 1케이스"를 명시해 테스트 계층에서 메우는 편이 현실적이다.
4. **n3 · n5** — 문구 수준이다. 반영하지 않아도 구현에 영향이 없다.

**1차 optional 17건(D7~D23)은 이번에도 오케스트레이터 재량이다.** 재감사가 이를 근거로 추가 반복을 만들지 않는다. 다만 D7(ruff 줄 길이 주장 오류, `plan.md:151`에 그대로 남아 있음)·D23(`op_income_growth_pct`의 `"turnaround"` 타입 누락)·D8(`PORTFOLIO_ANALYSIS_FILE` 바인딩과 `monkeypatch` 전략 충돌)은 run 단계에서 실제 시간을 잃게 할 항목이라, 손댈 기회가 있을 때 함께 반영하기를 권한다. 특히 D8은 `plan.md:100`이 여전히 `PORTFOLIO_ANALYSIS_FILE` 상수를 모듈 전역으로 두도록 읽히고 `plan.md:103`은 임시 디렉터리 픽스처를 요구하므로, 두 지시가 M2 구현 시점에 충돌할 수 있다.

**반복 종료 권고**: iteration 2에서 PASS이며 점수도 0.69 → 0.875로 상승했다. iteration 3은 불필요하다. 다음 단계는 Implementation Kickoff Approval 게이트다 — 이 PASS는 plan-audit 검증에 한정되며 plan→run 인간 승인 게이트를 대신하지 않는다.

---

VERDICT: PASS
