---
name: saving-tistory-draft
description: 완성된 투자 블로그 초안을 docs/blog/ 아래 로컬 Markdown 파일로 저장하고, 티스토리에 붙여넣는 방법을 안내한다. "초안 저장해줘", "블로그 파일로 만들어줘", "티스토리에 올릴 초안 저장" 같은 요청에 발동한다. 티스토리에 자동 로그인·업로드·발행하지 않으며, 외부로 어떤 데이터도 전송하지 않는다. 다음은 발동하지 않는다: 초안 작성 자체(converting-investment-blog 담당), 실제 발행 자동화 요청.
allowed-tools: Read, Write, Bash
---

# 블로그 초안 로컬 저장

**이 스킬은 로컬 파일 저장까지만 한다.** 티스토리 로그인·업로드·발행은 하지 않는다.
발행은 사용자가 직접 붙여넣어 수행한다 — 발행은 되돌리기 어렵고 캐시·색인이 남기 때문이다.

## 절대 규칙

1. **검증을 통과한 초안만 저장한다.** `validate_blog_post.py` 종료코드가 `0` 이 아니면 저장하지 않는다.
2. **기존 파일을 말없이 덮어쓰지 않는다.** 같은 경로에 파일이 있으면 사용자에게 확인받는다.
3. **`generating-krx-report/` 아래에 쓰지 않는다.** 그 디렉터리는 읽기 전용이다.
4. **외부 전송 없음.** 네트워크 호출을 하지 않는다.
5. `status` 는 `draft` 로 저장한다. 발행 상태를 이 스킬이 바꾸지 않는다.

## 1. 저장 경로

```
docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md
예: docs/blog/2026-07-25_009240_한샘.md
```

- `{YYYY-MM-DD}` = `manifest.data_cutoff` (저장 시각이 아니라 **데이터 기준일**).
- 회사명에서 `\ / : * ? " < > |` 와 앞뒤 공백을 제거한다. `(주)` 같은 접두어는 지운다.
- `docs/` 는 루트 `.gitignore` 에 걸리지 않으므로 커밋·공유가 가능하다.
  (스킬 내부 `outputs/` 는 `.gitignore` 로 제외되므로 쓰지 않는다.)

디렉터리가 없으면 만든다.

```bash
mkdir -p docs/blog
```

## 2. 저장 전 검증 (필수)

```bash
python ".claude/skills/converting-investment-blog/scripts/validate_blog_post.py" \
    "docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md" --ticker {TICKER}
echo "exit=$?"
```

| 종료코드 | 처리 |
|---|---|
| `0` | 저장 진행 |
| `1` | **저장 중단.** `[FAIL]` 항목을 그대로 사용자에게 전달하고 수정 요청 |
| `2` | 실행 오류(파일·PyYAML·티커 불일치). 원인을 그대로 전달 |

`[WARN]` 만 있으면 저장하되, 경고 내용을 사용자에게 함께 보고한다.

## 3. frontmatter 최종 확인

저장 직전 아래 필드가 채워져 있는지 본다. 비어 있으면 manifest 에서 채운다.

| 필드 | 출처 |
|---|---|
| `ticker` · `company` · `market` | `manifest.ticker` · `company_name` · `market` |
| `as_of` | `manifest.data_cutoff` |
| `composite_score` · `verdict` · `confidence` · `data_completeness` | `manifest.composite` |
| `source_manifest` | manifest 파일 경로 |
| `claim_count` | `len(manifest.claims)` |
| `status` | `"draft"` 고정 |
| `tags` | 3~6개. `기업분석` + 시장(`KOSPI`/`KOSDAQ`) + 업종 |

`verdict` 는 `manifest.composite.verdict` 와 **정확히 같아야 한다** (검증기가 대조한다).

## 4. 덮어쓰기 확인

```bash
ls -l "docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md" 2>/dev/null || echo "새 파일"
```

이미 있으면 사용자에게 묻는다 — 덮어쓸지, 파일명 뒤에 `_v2` 를 붙일지.

## 5. 저장 후 안내

저장이 끝나면 아래를 사용자에게 알린다.

1. 저장 경로와 글자 수
2. 검증 결과 요약 (인용한 claim 수 / WARN 건수)
3. 티스토리 붙여넣기 방법
   - 티스토리 글쓰기 → 우측 상단 **기본모드 → 마크다운** 으로 전환한 뒤 파일 내용을 붙여넣는다.
   - **frontmatter(`---` 사이 블록)는 붙여넣지 않는다.** 메타데이터일 뿐 본문이 아니다.
   - `<!-- CLM-xxxx -->` 주석은 화면에 보이지 않으므로 지우지 않아도 된다. 근거 추적용이다.
   - 저장은 **비공개**로 먼저 하고, 미리보기로 표·링크가 깨지지 않는지 확인한 뒤 공개한다.
4. 발행 여부는 사용자가 결정한다. 이 스킬은 발행하지 않는다.

## 6. 커밋 (선택)

사용자가 요청할 때만 한다. 프로젝트 규칙(`_claude_core/GIT_RULES.md`)에 따라
`main` 에 직접 커밋하지 않고 현재 기능 브랜치에 올린다.

```bash
git add "docs/blog/{YYYY-MM-DD}_{TICKER}_{회사명}.md"
git commit -m "docs(blog): {회사명}({TICKER}) 기업분석 블로그 초안 추가"
```
