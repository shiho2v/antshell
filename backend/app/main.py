# =============================================================
# File   : main.py
# Author : @JaeHoYang
# Week   : 07 | Ch.07 (2/2)
# Created: 2026-08-22
# =============================================================
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import httpx

# config 를 가장 먼저 import 해야 한다. 모듈 본문에서 루트 .env 를 os.environ 에
# 채우므로, 아래 os.getenv 호출과 auth 모듈이 그 값을 볼 수 있다.
from app import auth, config, indicators, news
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Antshell API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_REPO = "shiho2v/antshell"


def _get_env(key: str) -> str:
    """환경변수 조회. config 가 이미 루트 .env 를 os.environ 에 채워 두었다.

    이전 구현은 실행 디렉터리 기준 상대경로로 ".env" 를 열었기 때문에, 백엔드를
    backend/ 가 아닌 곳에서 띄우면 값을 찾지 못했다(빈 문자열 -> 503). 호출부는
    그대로 두고 조회 경로만 config 로 일원화한다.
    """
    return config.get_env(key)


@app.get("/health")
def health():
    return {"status": "ok"}


class StockReportRequest(BaseModel):
    code: str
    name: str
    price: str
    change: str


class NotionSettingsRequest(BaseModel):
    access_token: str
    page_id: str


NOTION_VERSION = "2022-06-28"
# 끝에 고정한다. 페이지 제목이 URL 에 섞여 들어오면(예: /My-Page-<id>) 하이픈 제거
# 후 제목의 hex 문자(a~f)가 앞에서 먼저 잡혀 ID 가 밀리기 때문이다.
NOTION_PAGE_ID_PATTERN = re.compile(r"[0-9a-fA-F]{32}$")
SETTINGS_TABLE = "user_notion_settings"


def _normalize_notion_page_id(raw_value: str) -> str:
    """페이지 URL 이든 하이픈이 섞인 ID 든 32자 hex 로 정규화한다.

    사용자는 보통 주소창의 URL 을 통째로 붙여넣으므로, ID 만 요구하면 실패율이 높다.
    """
    cleaned = raw_value.strip()
    cleaned = cleaned.split("?")[0].split("#")[0]      # 쿼리·프래그먼트 제거
    cleaned = cleaned.rstrip("/").rsplit("/", 1)[-1]   # URL 이면 마지막 경로 조각만
    cleaned = cleaned.replace("-", "")
    match = NOTION_PAGE_ID_PATTERN.search(cleaned)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Notion 페이지 ID를 찾을 수 없습니다. 페이지 URL 또는 32자리 ID를 입력하세요.",
        )
    return match.group(0)


def _supabase_headers(user_token: str) -> dict:
    """PostgREST 호출 헤더. 사용자 JWT 로 호출해야 RLS 가 본인 행만 통과시킨다."""
    return {
        "apikey": config.get_env("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


def _supabase_rest_url(table: str) -> str:
    base_url = auth.supabase_url()
    if not base_url:
        raise HTTPException(status_code=503, detail="Supabase 환경변수 미설정")
    return f"{base_url}/rest/v1/{table}"


async def _load_notion_settings(user_id: str, user_token: str) -> dict | None:
    """사용자의 Notion 설정을 조회한다. 없으면 None."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _supabase_rest_url(SETTINGS_TABLE),
            params={"select": "page_id,access_token", "user_id": f"eq.{user_id}"},
            headers=_supabase_headers(user_token),
            timeout=10,
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"설정 조회 실패 ({response.status_code})",
        )
    rows = response.json()
    return rows[0] if rows else None


@app.get("/api/settings/notion")
async def get_notion_settings(context: dict = Depends(auth.get_auth_context)):
    """연동 여부와 대상 페이지만 반환한다. 토큰은 절대 돌려주지 않는다."""
    settings = await _load_notion_settings(context["user"]["id"], context["token"])
    if not settings:
        return {"connected": False, "page_id": None}
    return {"connected": True, "page_id": settings["page_id"]}


@app.put("/api/settings/notion")
async def save_notion_settings(
    req: NotionSettingsRequest,
    context: dict = Depends(auth.get_auth_context),
):
    """사용자별 Notion 토큰과 대상 페이지를 저장한다(upsert)."""
    access_token = req.access_token.strip()
    if not access_token:
        raise HTTPException(status_code=400, detail="Notion 토큰을 입력하세요.")
    page_id = _normalize_notion_page_id(req.page_id)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _supabase_rest_url(SETTINGS_TABLE),
            headers={
                **_supabase_headers(context["token"]),
                "Prefer": "resolution=merge-duplicates",
            },
            json={
                "user_id": context["user"]["id"],
                "access_token": access_token,
                "page_id": page_id,
            },
            timeout=10,
        )
    if response.status_code not in (200, 201, 204):
        raise HTTPException(
            status_code=502,
            detail=f"설정 저장 실패 ({response.status_code})",
        )
    return {"ok": True, "connected": True, "page_id": page_id}


@app.delete("/api/settings/notion")
async def delete_notion_settings(context: dict = Depends(auth.get_auth_context)):
    """연동을 해제한다."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            _supabase_rest_url(SETTINGS_TABLE),
            params={"user_id": f"eq.{context['user']['id']}"},
            headers=_supabase_headers(context["token"]),
            timeout=10,
        )
    if response.status_code not in (200, 204):
        raise HTTPException(
            status_code=502,
            detail=f"연동 해제 실패 ({response.status_code})",
        )
    return {"ok": True, "connected": False}


@app.post("/api/report/notion")
async def save_report_to_notion(
    req: StockReportRequest,
    context: dict = Depends(auth.get_auth_context),
):
    """로그인한 사용자 본인이 지정한 Notion 페이지에 분석 결과를 append 한다.

    이전에는 서버 환경변수의 토큰/페이지 하나로 모든 사용자가 같은 곳에 저장했다.
    이제 각 사용자가 설정 페이지에서 연결한 본인 페이지로 저장된다.
    """
    settings = await _load_notion_settings(context["user"]["id"], context["token"])
    if not settings:
        raise HTTPException(
            status_code=409,
            detail="Notion 연동이 설정되지 않았습니다. 설정 페이지에서 먼저 연결하세요.",
        )

    # astimezone() 으로 실행 환경의 지역 시간을 쓴다. 표기용 문자열이라 UTC 로
    # 바꾸면 한국 사용자에게 9시간 어긋난 시각이 보인다.
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    summary = f"[종목 분석] {req.name} ({req.code}) — {req.price}원 {req.change}  |  {now}"
    blocks = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "📈"},
                "rich_text": [{"type": "text", "text": {"content": summary}}],
            },
        }
    ]

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.notion.com/v1/blocks/{settings['page_id']}/children",
            headers={
                "Authorization": f"Bearer {settings['access_token']}",
                "Content-Type": "application/json",
                "Notion-Version": NOTION_VERSION,
            },
            json={"children": blocks},
            timeout=10,
        )
    if response.status_code != 200:
        # Notion 응답 본문에는 토큰이 포함되지 않지만, 그대로 흘리지 않고 코드만 전달한다.
        raise HTTPException(
            status_code=502,
            detail=f"Notion API 오류: {response.status_code}",
        )

    return {"ok": True, "message": f"{req.name} 분석 결과를 Notion에 저장했습니다."}


@app.get("/api/github/issues")
def get_github_issues():
    token = _get_env("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token and not token.startswith("ghp_xxx"):
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open&per_page=10"
    req_obj = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req_obj, timeout=5) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"GitHub API 오류: {e.code}")

    issues = [
        {
            "number": i["number"],
            "title": i["title"],
            "user": i["user"]["login"],
            "url": i["html_url"],
            "created_at": i["created_at"][:10],
            "labels": [lb["name"] for lb in i.get("labels", [])],
        }
        for i in data
        if "pull_request" not in i
    ]
    return {"issues": issues}


# =============================================================
# SPEC-CHART-001 — 주가 차트와 기술지표 (Week 09 / @injeinnam)
#
# 여기서부터는 사전에 수집해 커밋해 둔 data/{code}_ohlcv.json 만 읽는다.
# 요청 처리 중 pykrx 호출이나 파일 생성은 하지 않는다 (REQ-007).
# 수집은 scripts/fetch_ohlcv.py 가 오프라인에서 담당한다.
# =============================================================

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# REQ-001 / REQ-005: 허용 목록. 값이 리터럴 문자열 집합이므로 경로 조작이 성립하지 않는다.
CHART_STOCK_CODES = frozenset({"005930", "000660", "009150", "008490"})

SMA_PERIODS = (5, 20, 60)
EMA_PERIODS = (12, 26)
RSI_PERIOD = 14
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9


def _read_ohlcv_document(stock_code: str) -> dict:
    """수집해 둔 OHLCV 파일을 읽는다. 파일이 없으면 404.

    허용 목록 검사를 통과한 코드로만 호출되어야 한다. 파일 접근을 이 함수 하나로
    모아 두어야 "허용 목록 밖 코드는 파일시스템을 건드리지 않는다"를 테스트로
    증명할 수 있다 (AC-004).
    """
    target = DATA_DIR / f"{stock_code}_ohlcv.json"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"{stock_code} OHLCV 데이터가 없습니다")
    with target.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def _load_ohlcv_or_404(stock_code: str) -> dict:
    """REQ-005: 허용 목록 검사를 파일 접근보다 먼저 수행한다."""
    if stock_code not in CHART_STOCK_CODES:
        raise HTTPException(status_code=404, detail="지원하지 않는 종목 코드입니다")
    return _read_ohlcv_document(stock_code)


@app.get("/api/stocks/{code}/ohlcv")
def get_stock_ohlcv(code: str):
    """REQ-004: 일별 OHLCV 시계열을 그대로 서빙한다.

    source 를 함께 내려보내 프론트엔드가 실제 시세(pykrx)와 샘플 데이터를
    구분해 표기할 수 있게 한다 (spec.md §4).
    """
    document = _load_ohlcv_or_404(code)
    return {
        "stock_code": code,
        "source": document.get("source", "unknown"),
        "fetched_date": document.get("fetched_date"),
        "records": document["records"],
    }


@app.get("/api/stocks/{code}/indicators")
def get_stock_indicators(code: str):
    """REQ-008: 종가 시계열로부터 SMA / EMA / RSI / MACD 를 계산해 응답한다.

    모든 지표 배열은 records 와 길이가 같고, 최소 관측 기간을 채우지 못한
    앞 구간은 null 이다 (REQ-010).
    """
    document = _load_ohlcv_or_404(code)
    records = document["records"]
    closing_prices = [record["close"] for record in records]
    macd_result = indicators.macd(
        closing_prices, MACD_FAST_PERIOD, MACD_SLOW_PERIOD, MACD_SIGNAL_PERIOD
    )

    response = {
        "stock_code": code,
        "source": document.get("source", "unknown"),
        "dates": [record["date"] for record in records],
        "rsi_14": indicators.relative_strength_index(closing_prices, RSI_PERIOD),
        "macd": macd_result["macd"],
        "macd_signal": macd_result["signal"],
        "macd_histogram": macd_result["histogram"],
    }
    for period in SMA_PERIODS:
        response[f"sma_{period}"] = indicators.simple_moving_average(closing_prices, period)
    for period in EMA_PERIODS:
        response[f"ema_{period}"] = indicators.exponential_moving_average(closing_prices, period)
    return response


# =============================================================
# SPEC-NEWS-001 — 종목 뉴스 모듈 (Week 10 / @정우준)
#
# 뉴스 문서 읽기·검증·정렬은 app/news.py 로 분리했다 — 파일이 늘어날 이
# 구간에 로직을 더 얹지 않기 위함이다 (plan.md §A.2 결정 3).
# =============================================================


@app.get("/api/stocks/{code}/news")
def get_stock_news(code: str):
    """REQ-002~REQ-007: 종목 뉴스 서빙.

    # @MX:ANCHOR: [AUTO] 허용 목록 검사를 파일 접근(news.build_news_response)
    # 보다 먼저 수행한다(REQ-005). data/005380_agents.json 이 허용 목록 밖
    # 코드로 실제 존재하므로, 순서가 뒤집히면 그 파일이 바로 노출된다.
    # @MX:REASON: _load_ohlcv_or_404 와 같은 순서를 지키지 않으면 AC-005의
    # "파일 열기가 한 번도 호출되지 않았음" 단언이 깨진다.
    """
    if code not in news.NEWS_STOCK_CODES:
        raise HTTPException(status_code=404, detail="지원하지 않는 종목 코드입니다")
    return news.build_news_response(DATA_DIR, code)
