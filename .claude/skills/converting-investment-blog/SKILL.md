---
name: converting-investment-blog
description: 이미 생성된 KRX 기업 종합평가 보고서(manifest·claims·module-results)를 읽어 개인 투자 블로그용 한국어 Markdown 초안 8절 구조로 변환한다. company-blog-pipeline 이 위임하거나, 사용자가 "보고서를 블로그 문체로 바꿔줘", "블로그 글로 다시 써줘"라고 명시할 때 발동한다. 데이터 수집·재무 계산·보고서 생성·외부 발행은 하지 않는다. 다음은 발동하지 않는다: 새 종목 분석 요청(generating-krx-report 담당), 종목과 무관한 글쓰기.
allowed-tools: Read, Write, Bash
---

# 투자 보고서 → 블로그 초안 변환

**교육·연구용.** 산출물은 투자 자문이 아니다. 매수·매도 의견을 내지 않는다.

이 스킬은 `generating-krx-report` 의 **하류 소비자**다. 원 스킬의 어떤 파일도 수정하지 않는다.

## 절대 규칙 (위반 시 중단)

1. **산술하지 않는다.** 모든 수치는 `manifest.json` / `claims.json` / `module-results` 에서 **그대로 인용**한다.
   보고서에 없는 숫자는 블로그에도 없다.
2. **claim 없는 주장을 쓰지 않는다.** 수치나 판단을 담은 모든 문장은 `<!-- CLM-xxxx -->` 주석을 달아
   출처 claim 을 지목한다. 지목할 claim 이 없으면 **그 문장을 쓰지 않는다.**
3. **원본 데이터를 다시 읽지 않는다.** `data/raw/`, `data/normalized/`, 재무제표 전문, 보고서 HTML 은
   읽기 화이트리스트 밖이다 (아래 2절).
4. **게이트 미통과 보고서는 변환하지 않는다.** `manifest.gates` 4개가 전부 `passed` 여야 한다.
5. **금지 표현**: 매수 · 매도 · 목표주가 · 적정주가 · 컨센서스 · buy · sell.
   결론 등급은 `긍정적 관찰` · `중립적 관찰` · `보수적 관찰` · `판단 유보` 4개뿐이다.
6. **반론을 삭제하지 않는다.** 상충 근거는 6절에 남긴다. 불리해서 빼는 것은 위반이다.

## 실행 전제

```bash
pip install PyYAML          # Python 3.10+ (generating-krx-report 와 공유)
```

아래 `SKILL` 은 이 스킬 디렉터리, `REPORT` 는 `generating-krx-report` 디렉터리다.
Bash 에서는 `${CLAUDE_SKILL_DIR}` 로 이 스킬을 참조한다.

## 1. 입력 확인

- 6자리 티커가 필요하다. 종목명만 받으면 **추측하지 않고** `REPORT/data/*_manifest.json` 목록에서 후보를 제시한다.
- `REPORT/data/{TICKER}_manifest.json` 이 없으면 **중단**하고, 보고서를 먼저 생성할지 사용자에게 묻는다.
  **`generating-krx-report` 를 자동 실행하지 않는다** (DART API 호출·토큰 비용이 크다).

```bash
python - <<'PY'
import json, sys
manifest = json.load(open(r"REPORT/data/{TICKER}_manifest.json", encoding="utf-8"))
gates = {name: gate["status"] for name, gate in manifest["gates"].items()}
print(gates)
PY
```

**4개 게이트 중 하나라도 `passed` 가 아니면 변환하지 않는다.** 실패한 게이트 이름과 사유를 그대로 전달한다.

## 2. 읽기 화이트리스트

| 읽는다 | 경로 |
|---|---|
| 최종 원장 (단일 진입점) | `REPORT/data/{TICKER}_manifest.json` |
| 주장 목록 | `REPORT/data/{TICKER}_claims.json` |
| 모듈 서술·강약점 | `REPORT/data/module-results/{TICKER}_{module}.json` |
| 개별 근거 (**ID 로 지목해서만**) | `REPORT/data/evidence/{TICKER}_evidence.json` |

**읽지 않는다:** `data/raw/*`, `data/normalized/*`, `outputs/*.html`, 재무제표 전문.

> 이유는 원 스킬의 `references/synthesis-policy.md` 와 같다 — 원본을 다시 읽으면
> 없는 숫자가 생기고, 이미 검증된 근거 체인을 벗어난 문장이 섞인다.
> 보고서 HTML 을 파싱하지 않는 이유는 템플릿이 바뀌면 깨지기 때문이다. **JSON 만 읽는다.**

## 3. 소재 선별

| 블로그 재료 | 원천 |
|---|---|
| 결론·점수·신뢰도·완전성 | `manifest.composite` |
| 투자 포인트 3 | 전 모듈 `strengths[]` 중 **가중치 높은 모듈 · evidence 2개 이상** 우선 3개 |
| 리스크 3 | 전 모듈 `weaknesses[]` + `{TICKER}_risk.json` 우선 3개 |
| 반론 재료 | 각 모듈 `counter_evidence[]`, claims 의 `counter_evidence_ids` |
| 확인 못한 것 | `claim_type == "unknown"` claim + `manifest.unsupported_items` + 모듈 `unknowns[]` |
| 출처 표 | `manifest.sources[]` (기계적으로 전량 옮긴다) |

`manifest` 에는 "핵심 투자 포인트 3개" 집계 필드가 **없다.** 위 규칙으로 직접 선별하되,
선별한 항목은 반드시 `strengths[].evidence_ids` 를 가진 것이어야 한다.

## 4. 변환

`references/blog-style.md` 를 읽고 `templates/blog-post.md` 를 채운다.

- 8절 구조를 지킨다. 절을 **생략하지 않는다** — 쓸 내용이 없으면 "해당 없음"과 사유를 적는다.
- 문장마다 출처 claim 을 `<!-- CLM-xxxx -->` 로 지목한다 (HTML 주석이라 티스토리에서 보이지 않는다).
- 저장 경로: `docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md`
  (`{YYYY-MM-DD}` 는 `manifest.data_cutoff`. 회사명의 `\ / : * ? " < > |` 는 제거)

## 5. 검증

```bash
python "${CLAUDE_SKILL_DIR}/scripts/validate_blog_post.py" \
    "docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md" --ticker {TICKER}
```

- 종료코드 `0` 통과 / `1` 실패 / `2` 실행 오류.
- `[FAIL]` 이 하나라도 있으면 **저장·발행하지 않는다.** 문장을 고치는 게 아니라
  **근거 없는 문장을 삭제하거나 `unknown` 으로 되돌린다.**
- `[WARN] manifest 에 없는 숫자` 는 오탐일 수 있다 (연도·개수·서수). 확인 후 근거가 없으면 삭제한다.

검증을 통과시키려고 문구를 우회하지 않는다.

## 참고 문서

| 파일 | 언제 읽나 |
|---|---|
| `references/blog-style.md` | 변환 직전 (문체·출처 표기·claim 매핑 규칙) |
| `templates/blog-post.md` | 초안 작성 시 |
| `../generating-krx-report/references/report-style.md` | 원 보고서의 표기 규칙을 확인할 때만 |
