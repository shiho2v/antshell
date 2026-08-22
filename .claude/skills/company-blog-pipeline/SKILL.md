---
name: company-blog-pipeline
description: 이미 생성된 KRX 기업 종합평가 보고서를 개인 투자 블로그용 한국어 Markdown 초안으로 바꾸는 전 과정을 조율한다. 종목명 또는 6자리 티커와 함께 "블로그 글 써줘", "블로그 초안 만들어줘", "티스토리에 올릴 글", "포스팅으로 정리해줘", "블로그로 바꿔줘" 같은 게시용 글쓰기 의도가 있을 때 발동한다. manifest 의 4개 검증 게이트가 모두 통과한 보고서만 변환하며, 사실 검증(financial-fact-checker)과 반론(investment-devils-advocate) 에이전트를 병렬로 돌린 뒤 로컬 Markdown 초안까지만 만든다(외부 발행 없음). 다음은 발동하지 않는다: 종목 분석·보고서 생성 요청(generating-krx-report 담당), 종목과 무관한 글쓰기, 티스토리 자동 발행·업로드 요청.
allowed-tools: Read, Write, Bash, Agent
---

# 기업분석 → 블로그 초안 파이프라인

**교육·연구용.** 산출물은 투자 자문이 아니다. 매수·매도 의견을 내지 않는다.

이 스킬은 조율만 한다. 실제 작업은 아래에 위임한다.

| 단계 | 담당 |
|---|---|
| 변환 | `converting-investment-blog` 스킬 |
| 사실 검증 | `financial-fact-checker` 에이전트 |
| 반론 | `investment-devils-advocate` 에이전트 |
| 저장 | `saving-tistory-draft` 스킬 |

`generating-krx-report` 는 **읽기 전용 상류**다. 그 디렉터리의 파일을 수정하지 않는다.
특히 `validate_report.py` 를 호출하지 않는다 — 이 스크립트는 `manifest.json` 을 다시 써서 원장을 오염시킨다.

## 절대 규칙 (위반 시 중단)

1. **게이트 미통과 보고서는 블로그로 만들지 않는다.** `manifest.gates` 4개(identity·data·analysis·report)가
   전부 `passed` 여야 한다. 하나라도 아니면 즉시 중단하고 실패 사유를 그대로 전달한다.
2. **보고서를 자동 생성하지 않는다.** manifest 가 없으면 사용자에게 물어본다.
   (`generating-krx-report` 실행은 DART API 호출·토큰 비용이 크다.)
3. **산술하지 않는다.** 모든 수치는 manifest·claims·evidence 에서 그대로 인용한다.
4. **claim 없는 주장을 쓰지 않는다.** 수치·판단 문장은 `<!-- CLM-xxxx -->` 또는 `<!-- MANIFEST -->` 주석 필수.
5. **발행하지 않는다.** 이 파이프라인의 종착점은 `docs/blog/` 의 로컬 Markdown 파일이다.
6. **반론을 삭제하지 않는다.** 결론에 불리해도 6절에 남긴다.

## 워크플로 (8단계)

### 1. 입력 확인

- 6자리 티커를 받으면 그대로 쓴다. 종목명만 받으면 **추측하지 말고** 아래 목록에서 후보를 제시한다.

```bash
ls .claude/skills/generating-krx-report/data/*_manifest.json
```

- manifest 가 없으면 **중단**하고 묻는다: "보고서가 아직 없다. `generating-krx-report` 로 먼저 분석할까?"

### 2. 게이트 확인 (중단 조건)

```bash
python - <<'PY'
import json
TICKER = "{TICKER}"
path = f".claude/skills/generating-krx-report/data/{TICKER}_manifest.json"
manifest = json.load(open(path, encoding="utf-8"))
for name, gate in manifest["gates"].items():
    print(name, gate["status"])
composite = manifest["composite"]
print("verdict:", composite["verdict"], "/ score:", composite["score"])
print("completeness:", composite["data_completeness"], "/ confidence:", composite["confidence"])
PY
```

- `passed` 가 아닌 게이트가 하나라도 있으면 **여기서 끝낸다.**
- `verdict` 가 `판단 유보` 면 변환은 하되, 1절 첫 문장에 판단 유보 사유를 반드시 넣도록 지시한다.

### 3. 변환

`converting-investment-blog` 스킬을 따라 8절 초안을 만들고 `docs/blog/` 에 임시 저장한다.
그 스킬의 읽기 화이트리스트(manifest·claims·module-results·evidence)를 벗어나지 않는다.

### 4. 병렬 검증 — 에이전트 2개를 한 번에 띄운다

두 에이전트는 서로 의존하지 않으므로 **한 메시지에서 동시에** 호출한다.

| 에이전트 | 역할 | 입력 |
|---|---|---|
| `financial-fact-checker` | 수치·기간·단위·연결구분 대조 | 초안 경로 + 티커 |
| `investment-devils-advocate` | 근거 초과·숨은 반론 적발 | 초안 경로 + 티커 |

두 에이전트 모두 `tools: Read` 다 — 웹을 검색하지 않는다.
외부 지식으로 공시 데이터를 보완하는 것은 원 스킬의 절대 규칙 위반이기 때문이다.

### 5. 반영 (필수 조치 규칙)

| 입력 | 조치 |
|---|---|
| fact-checker `severity: block` | 해당 문장의 수치를 근거대로 고치거나 **문장을 삭제**한다 |
| fact-checker `severity: warn` | 표현 강도를 낮춘다 ("…다" → "…로 보인다") |
| devils-advocate `overreach` | **문장 수정 또는 삭제** (필수) |
| devils-advocate `counterpoint` | **6절 「이 분석에 대한 반론」에 병기** (필수, 생략 금지) |
| devils-advocate `missing_context` | 해당 문단에 한계·미확인 사실을 덧붙인다 |

> 고칠 방법이 없으면 **문장을 지운다.** 근거를 늘려서 맞추지 않는다.
> 원 스킬의 원칙과 같다 — "보고서를 고치는 게 아니라 주장을 삭제하거나 N/A 로 되돌린다."

### 6. 기계 검증

```bash
python ".claude/skills/converting-investment-blog/scripts/validate_blog_post.py" \
    "docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md" --ticker {TICKER}
```

- `[FAIL]` 이 있으면 5단계로 돌아간다. **최대 2회 회귀**, 그래도 남으면 사용자에게 보고하고 멈춘다.
- `[WARN]` 은 확인 후 근거가 없으면 삭제, 오탐이면 그대로 둔다.

### 7. 저장

`saving-tistory-draft` 스킬로 넘긴다. 덮어쓰기 확인·frontmatter 점검·붙여넣기 안내를 그 스킬이 한다.

### 8. 보고

사용자에게 아래를 요약한다.

1. 저장 경로
2. 인용한 claim 수 / 전체 claim 수
3. fact-checker 결과 (block·warn 건수와 처리 내역)
4. devils-advocate 반론 건수와 6절 반영 여부
5. 남은 `[WARN]` 목록
6. 발행은 사용자가 직접 한다는 안내

## 에러 케이스

| 케이스 | 처리 |
|---|---|
| manifest 없음 | 중단. 보고서 생성 여부를 **질문** (자동 실행 금지) |
| 게이트 실패 1건 이상 | 중단. 실패한 게이트·체크 항목 그대로 전달 |
| evidence 파일 없음 | 경고. 수치 대조가 약해지므로 사용자에게 알리고 진행 여부 확인 |
| 검증기 종료코드 2 | 실행 오류(PyYAML 부재·티커 불일치 등). 원인 그대로 전달 |
| 회귀 2회 후에도 FAIL | 중단. 남은 FAIL 목록과 함께 사용자 판단 요청 |
| 같은 경로에 파일 존재 | 덮어쓸지 사용자에게 확인 |

## 하지 않는 일

- 티스토리 로그인·업로드·발행, 외부 네트워크 전송
- 새 종목 분석, DART·KRX 데이터 수집
- 재무 계산, 목표주가·컨센서스 생성
- `generating-krx-report/` 아래 파일 쓰기
