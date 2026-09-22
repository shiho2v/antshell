# =============================================================
# File   : news.py
# Week   : 10 | Ch.09 (2/2)
# =============================================================
"""종목 뉴스 문서 읽기 + 검증 + 정렬. SPEC-NEWS-001.

data/{code}_agents.json 의 news 배열만 다룬다. 디렉터리를 인자로 받는 이유는
main.py 의 기존 테스트 전략(monkeypatch.setattr(main, "DATA_DIR", tmp_path))과
충돌하지 않기 위해서다 — 이 모듈이 import 시점에 경로를 확정하면 그 교체가
무력화된다 (plan.md §A.2 결정 3).
"""

import json
from datetime import date
from pathlib import Path

from fastapi import HTTPException

# REQ-005: 허용 목록. SPEC-CHART-001 의 CHART_STOCK_CODES 와 값은 같지만
# 별도 상수로 둔다 — 결합하면 차트 종목 범위가 바뀔 때 뉴스 범위가 조용히
# 따라 움직인다 (spec.md §1.2 결정 3).
NEWS_STOCK_CODES = frozenset({"005930", "000660", "009150", "008490"})

_REQUIRED_NEWS_ITEM_KEYS = ("title", "date", "source", "summary")


def _is_valid_news_document(document) -> bool:
    """spec.md §4 「유효한 뉴스 문서」 네 조건을 그대로 검사한다.

    운영자의 생성 후 확인(REQ-001)과 백엔드의 읽기 시 검사(REQ-006)가 같은
    네 조건을 써야 하므로, 두 곳 모두 이 함수 하나를 부른다.
    """
    if not isinstance(document, dict):
        return False
    news_items = document.get("news")
    if not isinstance(news_items, list):
        return False
    for item in news_items:
        if not isinstance(item, dict):
            return False
        for key in _REQUIRED_NEWS_ITEM_KEYS:
            if not isinstance(item.get(key), str):
                return False
    return True


def _is_parseable_date(value: str) -> bool:
    """spec.md §4 「뉴스 정렬 규칙」의 「파싱 가능한 날짜」.

    형식(YYYY-MM-DD)과 일치하고 달력상 실제로 존재하는 날짜일 때만 참이다.
    """
    if not isinstance(value, str) or len(value) != 10:
        return False
    year_part, sep1, rest = value[:4], value[4], value[5:]
    month_part, sep2, day_part = rest[:2], rest[2], rest[3:]
    if sep1 != "-" or sep2 != "-":
        return False
    if not (year_part.isdigit() and month_part.isdigit() and day_part.isdigit()):
        return False
    try:
        date(int(year_part), int(month_part), int(day_part))
    except ValueError:
        return False
    return True


def _sort_news(news_items: list) -> list:
    """뉴스 정렬 규칙 1~5.

    # @MX:NOTE: [AUTO] date 문자열을 정규화하지 않고 파싱 가능/불가 두 갈래로만
    # 나눠 정렬하는 이유 (spec.md §4·§1.2 결정 2). "2026-07 (중순)" 같은 값을
    # 특정 일자로 바꾸면 원본에 없던 정밀도를 만들어 내므로, 값은 그대로 두고
    # 순서만 정한다. sorted(..., reverse=True) 는 안정 정렬이므로 같은 날짜인
    # 항목들의 파일 내 상대 순서가 그대로 유지된다(규칙 3).
    """
    parseable = [item for item in news_items if _is_parseable_date(item["date"])]
    unparseable = [item for item in news_items if not _is_parseable_date(item["date"])]
    parseable.sort(key=lambda item: item["date"], reverse=True)
    return parseable + unparseable


def _read_news_document(data_dir: Path, stock_code: str) -> dict:
    """파일 시스템 접근 단일 지점.

    # @MX:ANCHOR: [AUTO] 요청 경로가 data/ 에 쓰지 않는다(REQ-007)는 사실과
    # 파싱·스키마 실패 시 500 일반화 메시지만 내보낸다(REQ-006)는 사실이 이
    # 함수 하나에 걸려 있다. 우회 접근 경로가 생기면 두 요구사항이 동시에
    # 무너진다.
    # @MX:REASON: 파일 접근 지점이 여러 곳으로 흩어지면 404/500 판정 순서와
    # 예외 상세 은닉을 호출부마다 다르게 구현할 위험이 있다.
    """
    target = data_dir / f"{stock_code}_agents.json"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"{stock_code} 뉴스 데이터가 없습니다")
    try:
        with target.open(encoding="utf-8") as data_file:
            return json.load(data_file)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="뉴스 데이터를 처리할 수 없습니다") from None


def build_news_response(data_dir: Path, stock_code: str) -> dict:
    """GET /api/stocks/{code}/news 응답 본문을 만든다.

    호출부(main.py)가 허용 목록 검사를 이미 마쳤다는 전제로 동작한다
    (REQ-005 — 검사는 파일 접근보다 먼저 와야 하므로 이 함수 바깥에 둔다).
    """
    document = _read_news_document(data_dir, stock_code)
    if not _is_valid_news_document(document):
        raise HTTPException(status_code=500, detail="뉴스 데이터를 처리할 수 없습니다")
    # financials·ticker·name 은 여기서 아예 읽지 않는다(REQ-003) — news 배열만
    # 꺼내 정렬해 싣는다. financial-data 에이전트가 financials 스키마를
    # 독립적으로 바꿀 수 있으므로, 뉴스 계약이 거기 묶이면 함께 깨진다.
    return {
        "stock_code": stock_code,
        "news": _sort_news(document["news"]),
    }
