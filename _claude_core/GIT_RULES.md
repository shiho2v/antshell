# GIT_RULES.md — 브랜치·커밋 규칙

> 읽는 조건: 브랜치 생성 또는 커밋 작업 시

## 브랜치 전략 (GitHub Flow)

```
main                                  ← 항상 배포 가능. 직접 push 금지.
  └── feature/<주차>-<이름>-<기능명>   ← 기능 개발
  └── fix/<주차>-<이름>-<버그내용>     ← 버그 수정
  └── hotfix/<이름>-<내용>             ← 긴급 수정
```

예시:
- `feature/01-alice-project-init`
- `feature/03-bob-dart-api`
- `fix/05-carol-chart-null`
- `hotfix/dave-env-missing`

## 커밋 메시지 형식

지침서 §11.2 Conventional Commits 준수: `<type>(<scope>): <subject>`

```
feat(dart): DART API 재무데이터 파싱 추가
fix(chart): 캔들차트 null 데이터 오류 수정
docs(readme): 온보딩 가이드 업데이트
refactor(auth): JWT 검증 미들웨어 분리
test(portfolio): 포트폴리오 계산 단위 테스트 추가
chore(ci): pip-audit 취약점 스캔 단계 추가
```

타입 목록:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `refactor`: 리팩토링 (동작 변경 없음)
- `test`: 테스트 추가·수정
- `chore`: 빌드·설정 변경

## 작업 흐름

```bash
git pull origin main                            # 1. 최신화
git checkout -b feature/01-이름-기능명           # 2. 브랜치 생성
# ... 작업 ...
git add .                                       # 3. 스테이징
git commit -m "feat(dart): DART API 재무데이터 연동"  # 4. 커밋
git push origin feature/01-이름-기능명           # 5. 푸시
# GitHub에서 PR 생성 → 리뷰 → main merge
```

## 보안 주의

절대 커밋하면 안 되는 파일:
- `.env` (환경변수)
- `*.pem`, `*.key` (인증서)
- `secrets.yaml`

→ `.gitignore`에 이미 등록되어 있음. 추가 실수 방지를 위해
  `git status` 확인 후 커밋할 것.

## PR 규칙

- PR 제목: `[N주차] 기능명 — 이름`
- PR 본문: 변경 내용 요약 + 테스트 방법
- 최소 1명 리뷰 후 merge
