# =============================================================
# File   : test_notion_settings.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""사용자별 Notion 설정 엔드포인트 검증.

실제 Supabase / Notion 을 호출하지 않는다. 인증 의존성과 외부 호출을 교체해
라우팅·검증·권한 경계만 확인한다.
"""

import pytest
from app import auth, main
from fastapi.testclient import TestClient

FAKE_USER_ID = "11111111-2222-3333-4444-555555555555"
FAKE_TOKEN = "fake-jwt-token"
PAGE_ID = "abcdef0123456789abcdef0123456789"


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def authed_client():
    """인증을 통과한 상태의 클라이언트."""
    main.app.dependency_overrides[auth.get_auth_context] = lambda: {
        "user": {"id": FAKE_USER_ID},
        "token": FAKE_TOKEN,
    }
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


# --- 인증 경계 ---------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/settings/notion"),
        ("put", "/api/settings/notion"),
        ("delete", "/api/settings/notion"),
        ("post", "/api/report/notion"),
    ],
)
def test_endpoints_require_authentication(client, method, path):
    """토큰 없이 호출하면 통과하면 안 된다.

    변경 전 /api/report/notion 은 무인증이어서 누구나 저장할 수 있었다.
    """
    # GET/DELETE 에는 본문을 싣지 않는다 (httpx 가 거부한다).
    if method in ("get", "delete"):
        response = getattr(client, method)(path)
    else:
        response = getattr(client, method)(path, json={})

    assert response.status_code in (401, 403), f"{method.upper()} {path} 가 무인증 통과"


# --- 페이지 ID 정규화 --------------------------------------------------------


@pytest.mark.parametrize(
    "raw_value",
    [
        PAGE_ID,
        f"https://www.notion.so/{PAGE_ID}",
        f"https://www.notion.so/My-Page-{PAGE_ID}",
        f"https://www.notion.so/workspace/My-Page-{PAGE_ID}?pvs=4",
        f"  https://www.notion.so/{PAGE_ID}/  ",
        "abcdef01-2345-6789-abcd-ef0123456789",
    ],
)
def test_page_id_is_normalized_from_various_inputs(raw_value):
    assert main._normalize_notion_page_id(raw_value) == PAGE_ID


@pytest.mark.parametrize("raw_value", ["", "   ", "not-a-page", "1234"])
def test_invalid_page_id_is_rejected(raw_value):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        main._normalize_notion_page_id(raw_value)
    assert error.value.status_code == 400


# --- 설정 조회 / 저장 --------------------------------------------------------


def test_get_settings_reports_not_connected_when_absent(authed_client, monkeypatch):
    async def no_settings(user_id, user_token):
        return None

    monkeypatch.setattr(main, "_load_notion_settings", no_settings)

    response = authed_client.get("/api/settings/notion")

    assert response.status_code == 200
    assert response.json() == {"connected": False, "page_id": None}


def test_get_settings_never_returns_the_token(authed_client, monkeypatch):
    """토큰은 사용자 본인 것이라도 응답에 실어 보내지 않는다."""

    async def with_settings(user_id, user_token):
        return {"page_id": PAGE_ID, "access_token": "secret-token-value"}

    monkeypatch.setattr(main, "_load_notion_settings", with_settings)

    response = authed_client.get("/api/settings/notion")

    assert response.status_code == 200
    assert response.json() == {"connected": True, "page_id": PAGE_ID}
    assert "secret-token-value" not in response.text
    assert "access_token" not in response.text


def test_save_settings_rejects_empty_token(authed_client):
    response = authed_client.put(
        "/api/settings/notion",
        json={"access_token": "   ", "page_id": PAGE_ID},
    )

    assert response.status_code == 400


# --- 미연동 상태에서의 저장 시도 ---------------------------------------------


def test_report_requires_connected_settings(authed_client, monkeypatch):
    async def no_settings(user_id, user_token):
        return None

    monkeypatch.setattr(main, "_load_notion_settings", no_settings)

    response = authed_client.post(
        "/api/report/notion",
        json={"code": "005930", "name": "삼성전자", "price": "74,500", "change": "+1.2%"},
    )

    assert response.status_code == 409
    assert "설정" in response.json()["detail"]


def test_report_posts_to_the_user_configured_page(authed_client, monkeypatch):
    """서버 고정 페이지가 아니라 사용자가 저장한 page_id 로 보내야 한다."""
    captured = {}

    async def with_settings(user_id, user_token):
        return {"page_id": PAGE_ID, "access_token": "user-token"}

    class FakeResponse:
        status_code = 200

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def patch(self, url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["auth"] = headers["Authorization"]
            return FakeResponse()

    monkeypatch.setattr(main, "_load_notion_settings", with_settings)
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda *a, **kw: FakeClient())

    response = authed_client.post(
        "/api/report/notion",
        json={"code": "005930", "name": "삼성전자", "price": "74,500", "change": "+1.2%"},
    )

    assert response.status_code == 200
    assert captured["url"] == f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    assert captured["auth"] == "Bearer user-token"


# --- Supabase 토큰 검증 호출 형태 --------------------------------------------


def test_auth_sends_apikey_header_to_supabase(monkeypatch):
    """apikey 가 빠지면 Supabase 가 토큰을 보기도 전에 401 로 거절한다.

    기존 auth.py 는 Authorization 만 보냈고, 어떤 라우트에도 연결돼 있지 않아
    드러나지 않았다. 인증을 라우트에 붙이면서 표면화된 결함이라 회귀를 막는다.
    """
    import asyncio

    from fastapi.security import HTTPAuthorizationCredentials

    captured = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"id": FAKE_USER_ID}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def get(self, url, headers=None, timeout=None):
            captured.update(headers or {})
            return FakeResponse()

    monkeypatch.setattr(auth, "supabase_url", lambda: "https://example.supabase.co")
    monkeypatch.setattr(auth.config, "require_env", lambda key: "anon-key-value")
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda *a, **kw: FakeClient())

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=FAKE_TOKEN)
    result = asyncio.run(auth.get_auth_context(credentials))

    assert captured.get("apikey") == "anon-key-value"
    assert captured.get("Authorization") == f"Bearer {FAKE_TOKEN}"
    assert result["token"] == FAKE_TOKEN
    assert result["user"]["id"] == FAKE_USER_ID


# --- 환경변수 경로 회귀 방지 -------------------------------------------------


def test_env_is_loaded_independently_of_working_directory(monkeypatch, tmp_path):
    """_get_env 가 실행 디렉터리에 의존하지 않아야 한다 (기존 결함 회귀 방지)."""
    import os

    from app import config

    monkeypatch.setitem(os.environ, "MOAI_TEST_SENTINEL", "sentinel-value")
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert main._get_env("MOAI_TEST_SENTINEL") == "sentinel-value"
        assert config.get_env("MOAI_TEST_SENTINEL") == "sentinel-value"
    finally:
        os.chdir(original_cwd)
