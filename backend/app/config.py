# =============================================================
# File   : config.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""환경변수 로딩 단일 진입점.

기존에는 main.py 의 _get_env 가 실행 디렉터리 기준 상대경로로 ".env" 를 열었고,
auth.py 는 os.getenv 만 써서 .env 폴백이 아예 없었다. 그래서 백엔드를 어디서
띄우느냐에 따라 동작이 달라졌고, auth.py 의 SUPABASE_URL 은 항상 비어 있었다.

여기서는 __file__ 기준으로 저장소 루트를 찾아 한 번만 로드한다. CWD 와 무관하다.
python-dotenv 는 이미 backend/requirements.txt 에 있으므로 신규 의존성이 아니다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> backend/app -> backend -> 저장소 루트
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 이미 프로세스 환경에 있는 값이 우선한다(override=False). 배포 환경에서
# 실제 환경변수로 주입한 값을 .env 파일이 덮어쓰지 않도록 하기 위함이다.
load_dotenv(REPO_ROOT / ".env", override=False)


def get_env(key: str, default: str = "") -> str:
    """환경변수를 읽는다. load_dotenv 가 이미 .env 를 os.environ 에 채웠다."""
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    """필수 환경변수를 읽는다. 비어 있으면 빈 문자열을 돌려주고 호출자가 판단한다."""
    return get_env(key).strip()
