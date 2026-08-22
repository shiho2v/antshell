# =============================================================
# File   : auth.py
# Author : @JaeHoYang
# Week   : 06 | Ch.07 (1/2)
# Created: 2026-08-22
# =============================================================
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os

bearer = HTTPBearer()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Supabase JWT를 검증해 현재 사용자 정보를 반환한다."""
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}"},
        )
    if res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )
    return res.json()
