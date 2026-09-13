# =============================================================
# File   : auth.py
# Author : @JaeHoYang
# Week   : 06 | Ch.07 (1/2)
# Created: 2026-08-22
# =============================================================
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from app import config

bearer = HTTPBearer()


def supabase_url() -> str:
    """Supabase 프로젝트 URL.

    모듈 상수가 아니라 함수로 둔다. import 시점에 한 번만 읽으면 환경변수가
    나중에 채워지는 경우(테스트, 지연 로딩)를 잡지 못한다.
    """
    return config.require_env("NEXT_PUBLIC_SUPABASE_URL")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Supabase JWT를 검증해 현재 사용자 정보를 반환한다."""
    return (await get_auth_context(credentials))["user"]


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """검증된 사용자 정보와 원본 토큰을 함께 반환한다.

    토큰이 필요한 이유: 사용자 설정을 Supabase PostgREST 로 조회할 때 그 사용자의
    JWT 로 호출해야 RLS 가 본인 행만 보이도록 걸러준다. service_role 키를 쓰면
    RLS 를 우회하게 되므로 사용하지 않는다.
    """
    base_url = supabase_url()
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase 환경변수 미설정",
        )

    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/auth/v1/user",
            headers={
                # apikey 는 선택이 아니다. 없으면 Supabase 가 토큰을 보기도 전에
                # 401 "No apikey request header was found" 로 거절한다.
                "apikey": config.require_env("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )
    return {"user": response.json(), "token": token}
