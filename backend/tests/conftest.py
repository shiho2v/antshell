# =============================================================
# File   : conftest.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""pytest 공통 설정.

백엔드는 `uvicorn app.main:app` 으로 backend/ 안에서 실행되므로(ONBOARDING.md:157),
테스트도 동일하게 backend/ 를 루트로 보고 `from app.xxx import ...` 형태로 import 한다.
저장소 루트에서 pytest 를 돌려도 같은 import 가 동작하도록 sys.path 를 맞춘다.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
