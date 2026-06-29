# WEEK_01 실시연 데모 스크립트
> 25~55분 구간 (30분) 사용. 각 단계 앞에서 화면 공유 시작.

---

## 데모 전 체크리스트

- [ ] Claude Code 터미널 열기
- [ ] 프로젝트 디렉토리: `cd C:\Users\eunjungson\Desktop\antshell\P01`
- [ ] `.env` 파일에 실제 NOTION_API_KEY 있는지 확인
- [ ] Notion 변경 로그 페이지 브라우저에 미리 열어두기
- [ ] GitHub Actions 페이지 미리 열어두기

---

## STEP 1 — `claude` vs `claude -p` 차이 (5분)

**발표 멘트**
> "Claude Code는 두 가지 모드가 있습니다. 대화형과 비대화형인데, 실제로 어떻게 다른지 보여드릴게요."

```bash
# 대화형 모드 — 터미널에서 직접 채팅
claude
# → "안녕, 이 프로젝트 구조 간단히 설명해줘" 입력
# → 응답 확인 후 /exit
```

```bash
# 비대화형 모드 — 결과만 출력하고 바로 종료
claude -p "이 프로젝트의 디렉토리 구조를 한 줄로 요약해줘"
```

**포인트**: 비대화형은 `npm run lint:claude` 같은 자동화에 쓰임

---

## STEP 2 — 체크포인트 되감기 체험 (5분)

**발표 멘트**
> "Claude가 파일을 수정하면 자동으로 체크포인트가 생깁니다. 실수했을 때 되돌리는 걸 직접 해볼게요."

```bash
claude
# → "README.md 파일 맨 아래에 '테스트 줄입니다' 한 줄 추가해줘" 입력
# → 파일 변경 확인
# → ESC 두 번 또는 /rewind 입력
# → "코드만 복구" 선택
# → README.md 원래대로 됐는지 확인
```

**포인트**: Bash 직접 변경(`echo`, `cp`)은 추적 안 됨 — Git이 진짜 안전망

---

## STEP 3 — 파일 저장 시 헤더 주석 자동 삽입 (7분)

**발표 멘트**
> "이번 주에 만든 첫 번째 훅입니다. 새 파이썬 파일을 저장하면 자동으로 헤더가 달립니다."

```bash
claude
# → "test_demo.py 파일을 만들고 hello world를 출력하는 함수를 넣어줘" 입력
```

파일이 생성되면 즉시 확인:
```bash
# 에디터나 cat으로 test_demo.py 열어서 상단 확인
# =============================================================
# File   : test_demo.py
# Author : @shiho2v
# Week   : 01 | Ch.01~02
# Created: 2025-07-05
# =============================================================
```

```bash
# 확인 후 파일 삭제
# claude 에서 → "test_demo.py 삭제해줘"
```

**포인트**: `.claude/hooks/auto_header.py` + `settings.json`의 `PostToolUse Write` 훅 덕분

---

## STEP 4 — git commit → Notion 자동 기록 (8분)

**발표 멘트**
> "두 번째 훅입니다. Claude가 git commit을 실행하면 Notion 변경 로그에 자동으로 기록됩니다."

```bash
claude
# → "README.md 아래에 '데모 확인용 줄'을 추가하고 커밋해줘" 입력
```

Claude가 커밋하는 순간:
- 터미널에 `[notion_sync] ✓ Notion 기록 완료` 출력되는지 확인
- 브라우저에서 Notion 변경 로그 페이지 새로고침

**포인트**: `PostToolUse Bash` 훅이 `git commit` 키워드를 감지해 실행

```bash
# 데모용 커밋 되돌리기 (발표 끝나고)
git revert HEAD --no-edit
```

---

## STEP 5 — GitHub Actions 주간 리포트 확인 (5분)

**발표 멘트**
> "매주 토요일 오전에 자동으로 Notion에 주간 리포트가 올라갑니다. 방금 수동으로도 실행해봤는데 결과를 같이 보겠습니다."

브라우저에서 확인:
1. `https://github.com/shiho2v/antshell/actions` → `Weekly Notion Report` 클릭
2. 가장 최근 실행 → `success` 상태 보여주기
3. Notion 주간 리포트 페이지로 전환해서 결과 확인

**포인트**: `.github/workflows/notion_weekly.yml` + GitHub Secrets가 없으면 실행 안 됨

---

## STEP 6 — settings.json deny 규칙 실습 (5분, 여유 있을 때)

**발표 멘트**
> "settings.json에 deny 규칙을 추가하면 Claude가 특정 파일에 절대 손대지 못합니다."

```bash
claude
# → ".env 파일을 읽어줘" 입력
# → 현재는 읽을 수 있음을 보여주기
```

`settings.json`에 추가:
```json
"permissions": {
  "deny": ["Read(.env)", "Write(.env)"]
}
```

```bash
# Claude Code 재시작 후
claude
# → ".env 파일을 읽어줘" 입력
# → deny 규칙으로 거부됨 확인
```

**포인트**: deny는 allow보다 항상 먼저 적용됨 (평가 순서: deny → ask → allow)

```bash
# 실습 후 deny 규칙 다시 제거
```

---

## 데모 마무리 멘트

> "정리하면 이번 주에 만든 자동화는 세 가지입니다.
> 1. 파일 저장 → 헤더 주석 자동 삽입
> 2. git commit → Notion 변경 로그 자동 기록
> 3. 매주 토요일 → Notion 주간 리포트 자동 발행
>
> 이게 다 Claude Code의 훅과 GitHub Actions 덕분에 가능합니다."
