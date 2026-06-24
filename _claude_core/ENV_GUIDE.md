# ENV_GUIDE.md — 환경변수 설정 가이드

> 읽는 조건: 환경변수 오류 또는 새 API 연동 시

## 설정 순서

```bash
cp .env.example .env
# .env 파일 열어서 아래 항목 채우기
```

## 항목별 발급 위치

| 변수명 | 발급 위치 | 비고 |
|--------|-----------|------|
| `DART_API_KEY` | opendart.fss.or.kr → 인증키 신청 | 무료, 즉시 발급 |
| `KIS_APP_KEY` | apiportal.koreainvestment.com | 계좌 필요, 모의투자 가능 |
| `KIS_APP_SECRET` | 위 동일 | |
| `KIS_IS_MOCK` | `true` (모의투자) / `false` (실계좌) | 개발 중엔 true |
| `NOTION_API_KEY` | notion.so/my-integrations | NOTION_SETUP.md 참고 |
| `NOTION_CHANGELOG_PAGE_ID` | Notion 페이지 URL | 32자리 |
| `NOTION_WEEKLY_PAGE_ID` | Notion 페이지 URL | 32자리 |
| `ANTHROPIC_API_KEY` | console.anthropic.com | Pro 계정 공용 or 개인 |
| `NEXT_PUBLIC_SUPABASE_URL` | supabase.com → 프로젝트 Settings | |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 위 동일 | |
| `SUPABASE_SERVICE_ROLE_KEY` | 위 동일 (비공개 유지) | |
| `DATABASE_URL` | Supabase → Database → Connection | |
| `REDIS_URL` | 로컬: `redis://localhost:6379/0` | |
| `BIGKINDS_API_KEY` | bigkinds.or.kr | 비상업 무료 신청 |

## Claude API 절약 팁

- `ANTHROPIC_API_KEY`는 haiku 모델 전용으로 사용
- 스터디 중 코드 생성은 각자 Pro 계정의 Claude Code 사용
- 웹 서비스의 요약 기능만 API 키 사용 (배치 처리로 최소화)

## GitHub Secrets 등록 (Actions용)

Settings → Secrets and variables → Actions → New repository secret:
- `NOTION_API_KEY`
- `NOTION_CHANGELOG_PAGE_ID`  
- `NOTION_WEEKLY_PAGE_ID`
- `DATABASE_URL`
- `ANTHROPIC_API_KEY`
