# ONBOARDING.md — 신규 팀원 세팅 가이드

> 처음 참여하는 팀원은 이 파일만 읽고 따라하면 됩니다.

---

## 0단계: OS별 사전 설치

### Windows
- **Git**: git-scm.com → 설치 시 "Add Git to PATH" 체크
- **Python 3.11+**: python.org → 설치 시 **"Add Python to PATH" 반드시 체크**
- **Node.js 20+**: nodejs.org
- **Redis**: github.com/tporadowski/redis/releases → 최신 `.msi` 설치
- **Claude Code**: 설치 후 아래 확인
  ```cmd
  python --version   # 3.11 이상인지 확인
  node --version
  npm install -g @anthropic-ai/claude-code
  ```
- **줄바꿈 문자 설정** (필수):
  ```cmd
  git config --global core.autocrlf true
  ```

### Mac
- **Homebrew** (없으면 먼저 설치): brew.sh
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
- **Git·Python·Node·Redis**:
  ```bash
  brew install git python@3.11 node redis
  brew services start redis
  ```
- **Claude Code**:
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install git python3.11 python3-pip nodejs npm redis-server
sudo systemctl start redis
npm install -g @anthropic-ai/claude-code
```

---

## 1단계: 저장소 클론

```bash
git clone https://github.com/스터디장계정/P01.git
cd P01
```

---

## 2단계: 환경변수 설정

**Windows:**
```cmd
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

`.env` 파일 열어서 본인 API 키 입력.  
모르는 항목은 `_claude_core/ENV_GUIDE.md` 참고.  
**스터디장에게 Supabase URL/KEY, Notion KEY 받기.**

---

## 3단계: 의존성 설치

```bash
# 프론트엔드
cd frontend && npm install && cd ..

# 백엔드 (Windows는 python, Mac/Linux는 python3)
cd backend

# Windows:
pip install -r requirements.txt

# Mac/Linux:
pip3 install -r requirements.txt

cd ..
```

---

## 4단계: python3 명령어 확인 (Windows 전용)

훅 스크립트가 `python3`를 호출합니다. Windows에서 `python3`가 안 되면:

```cmd
# 방법 1: 별칭 등록 (PowerShell 관리자 권한)
Set-Alias python3 python

# 방법 2: python.org에서 재설치 시 "Add to PATH" 체크 후
#         C:\Users\이름\AppData\Local\Programs\Python\Python311\ 에
#         python3.exe 복사본 만들기
```

---

## 5단계: Claude Code 실행 확인

```bash
claude --version
claude "CLAUDE.md 읽고 이번 주 작업 내용 알려줘"
```

---

## 6단계: 첫 브랜치 만들기

```bash
git checkout -b feature/01-내이름-onboarding
git add .
git commit -m "chore(onboarding): 내이름 온보딩 완료"
git push origin feature/01-내이름-onboarding
```

GitHub에서 PR 생성 → 스터디장이 merge.

---

## Git을 처음 써본다면

**자주 쓰는 명령어:**
```bash
git pull origin main                    # 최신 코드 받기 (작업 시작 전 항상!)
git status                              # 변경된 파일 확인
git add 파일명                          # 특정 파일 스테이징
git add .                               # 전체 스테이징
git commit -m "feat(기능): 설명"        # 저장
git push origin feature/01-이름-기능명  # 업로드
```

**GUI 도구 (명령어 어려우면):**
- GitHub Desktop: desktop.github.com (Windows/Mac 모두 지원)
- VS Code 왼쪽 Source Control 패널

---

## 로컬 개발 서버 실행

```bash
# 터미널 1 — 백엔드
cd backend
uvicorn app.main:app --reload

# 터미널 2 — 프론트엔드
cd frontend
npm run dev

# 브라우저: http://localhost:3000
```

---

## OS별 자주 겪는 문제

| 증상 | OS | 해결 |
|------|----|------|
| `python3: command not found` | Windows | `python` 으로 실행 또는 4단계 참고 |
| `redis: command not found` | Windows | Redis 설치 후 서비스 시작 확인 |
| `permission denied` (npm) | Mac | `sudo npm install -g` 또는 nvm 사용 |
| 줄바꿈 관련 git diff 이상 | Windows | `git config --global core.autocrlf true` |
| `brew: command not found` | Mac | 0단계 Homebrew 설치 먼저 |

---

## 막히면

1. `_claude_core/` 폴더 해당 파일 읽기
2. Claude Code에게 질문: `claude "git push 오류 해결해줘"`
3. 스터디 단톡방에 질문
