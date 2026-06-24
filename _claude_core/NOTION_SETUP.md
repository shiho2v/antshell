# NOTION_SETUP.md — Notion 연동 설정

> 읽는 조건: Notion 관련 작업 또는 훅 디버깅 시

## 구조

Notion 워크스페이스 구조 (스터디장이 생성, 팀원 편집 권한 부여):

```
📁 주식 스터디 2025
  ├── 📄 변경 로그          ← 커밋마다 자동 append (NOTION_CHANGELOG_PAGE_ID)
  ├── 📄 주간 리포트         ← 매주 토요일 자동 생성 (NOTION_WEEKLY_PAGE_ID)
  └── 📁 주차별 발표 자료
      ├── 📄 1주차 | Ch.01~02 | 스터디장
      └── ...
```

## 설정 방법 (최초 1회)

1. notion.so/my-integrations → "새 통합" 생성
2. API 키 복사 → `.env`의 `NOTION_API_KEY`에 저장
3. "변경 로그" 페이지 열기 → Share → 생성한 통합 연결
4. 페이지 URL에서 ID 추출 (32자리) → `NOTION_CHANGELOG_PAGE_ID`
5. "주간 리포트" 페이지도 동일하게 → `NOTION_WEEKLY_PAGE_ID`
6. GitHub Secrets에도 동일 값 등록 (Actions용)

## 자동화 동작 방식

| 트리거 | 동작 | 파일 |
|--------|------|------|
| `git commit` (Claude Code에서) | 변경 로그 페이지에 append | `.claude/hooks/notion_sync.py` |
| 매주 토요일 18:00 UTC | 주간 리포트 자동 생성 | `.github/workflows/notion_weekly.yml` |

## 수동 동작 확인

```bash
# 훅 직접 테스트
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' \
  | python3 .claude/hooks/notion_sync.py
```

## 페이지 ID 추출 방법

```
URL: https://notion.so/워크스페이스/페이지제목-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                              ↑ 이 32자리가 PAGE_ID
```
