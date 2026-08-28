# =============================================================
# File   : main.py
# Author : @JaeHoYang
# Week   : 07 | Ch.07 (2/2)
# Created: 2026-08-22
# =============================================================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import urllib.request
import urllib.error
from datetime import datetime

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
    val = os.environ.get(key, "")
    if not val:
        try:
            with open(".env", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "=") and not line.startswith("#"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    return val


@app.get("/health")
def health():
    return {"status": "ok"}


class StockReportRequest(BaseModel):
    code: str
    name: str
    price: str
    change: str


@app.post("/api/report/notion")
def save_report_to_notion(req: StockReportRequest):
    api_key = _get_env("NOTION_API_KEY")
    page_id = _get_env("NOTION_CHANGELOG_PAGE_ID")
    if not api_key or not page_id:
        raise HTTPException(status_code=503, detail="Notion 환경변수 미설정")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
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
    payload = json.dumps({"children": blocks}).encode()
    req_obj = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        method="PATCH",
    )
    try:
        urllib.request.urlopen(req_obj, timeout=5)
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Notion API 오류: {e.code}")

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
