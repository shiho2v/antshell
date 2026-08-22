#!/usr/bin/env python3
# =============================================================
# File   : render_charts.py
# Author : @suhdongphill
# Week   : 01 | Ch.01~02
# Created: 2026-07-25
# =============================================================
"""블로그용 차트 렌더러 — 이미 수집·계산된 데이터를 그림으로만 옮긴다.

이 스크립트는 normalized·module-results·manifest 를 읽는다.
Claude 의 읽기 화이트리스트(manifest·claims·module-results·evidence)보다 넓은데,
그 화이트리스트의 취지는 **Claude 가 원본을 다시 읽고 숫자를 새로 만드는 것**을
막는 데 있다. 기계적 렌더링은 그 위험이 없고, 오히려 "계산은 Python 이" 라는
원 스킬의 절대 규칙에 부합한다.

새 지표를 계산하지 않는다. 단위 변환(원→억원)과 기준 100 정규화만 한다.

출력
  docs/blog/assets/{ticker}/*.png
  docs/blog/assets/{ticker}/charts.json   ← 차트 원장. validate_blog_post.py 의 FIG 검증 대상

사용법
  python render_charts.py 009240
  python render_charts.py 009240 --base-url https://raw.githubusercontent.com/OWNER/REPO/main/docs/blog/assets
종료코드: 0 성공 / 2 실행 오류
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

# Windows 기본 폰트로는 한글이 전부 □ 로 깨진다.
KOREAN_FONTS = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]


def pick_korean_font() -> str | None:
    """설치된 한글 폰트 하나만 고른다. 없는 폰트를 리스트로 남기면 경고가 도배된다."""
    from matplotlib import font_manager
    installed = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in KOREAN_FONTS:
        if candidate in installed:
            return candidate
    return None


SELECTED_FONT = pick_korean_font()
if SELECTED_FONT:
    plt.rcParams["font.family"] = SELECTED_FONT
plt.rcParams["axes.unicode_minus"] = False

COLOR_BAR = "#4E79A7"
COLOR_LINE = "#F28E2B"
COLOR_INDEX = "#9C9C9C"
COLOR_NA = "#C9C9C9"
COLOR_GOOD = "#59A14F"
COLOR_BAD = "#E15759"

MODULE_LABELS = {
    "business": "사업구조", "quality": "품질", "growth": "성장성", "moat": "경쟁우위",
    "valuation": "밸류에이션", "trend": "추세", "risk": "위험", "catalyst": "촉매",
}
CANSLIM_LABELS = {
    "TRD-C": "C 최근 분기 실적", "TRD-A": "A 연간 이익 성장", "TRD-N": "N 신고가 근접도",
    "TRD-S": "S 수급(거래량)", "TRD-L": "L 주도주 여부", "TRD-I": "I 기관·외국인",
    "TRD-M": "M 시장 방향",
}
RELATIVE_WINDOW_DAYS = 120


class RenderError(Exception):
    """실행 자체가 불가능한 상황."""


def read_json(path: Path) -> dict:
    if not path.exists():
        raise RenderError(f"파일을 찾지 못했다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def account_value(quarter: dict, name: str) -> float | None:
    entry = (quarter.get("accounts") or {}).get(name) or {}
    value = entry.get("value")
    return float(value) if isinstance(value, (int, float)) else None


def save_figure(figure, out_dir: Path, name: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{name}.png"
    figure.savefig(out_dir / file_name, dpi=140, bbox_inches="tight",
                   facecolor="white")
    plt.close(figure)
    return file_name


def chart_annual_performance(normalized: dict, out_dir: Path) -> dict | None:
    """연간 매출(막대)과 영업이익(선). 사업보고서 연간값이라 차분 오류의 영향이 없다."""
    years = sorted(normalized.get("annual") or [], key=lambda row: row["bsns_year"])
    rows = []
    for year in years:
        revenue = account_value(year, "revenue")
        operating_income = account_value(year, "operating_income")
        if revenue is None:
            continue
        rows.append({
            "label": str(year["bsns_year"]),
            "revenue_billion": round(revenue / 1e8, 1),
            "operating_income_billion": (
                round(operating_income / 1e8, 1) if operating_income is not None else None
            ),
        })
    if len(rows) < 2:
        return None
    return _render_revenue_profit(rows, out_dir, "annual_performance",
                                  "연간 매출과 영업이익",
                                  "DART 연결(CFS) 사업보고서 연간값",
                                  "연간값이다. 분기 추이가 아니다.")


def chart_quarterly_performance(normalized: dict, out_dir: Path) -> dict | None:
    """분기 단독 매출(막대)과 영업이익(선).

    분기 단독값은 누적 보고서 차분으로 파생되므로 상류 파이프라인이 '3개월값'과
    '누적값'을 혼동하면 조용히 망가진다. 매출이 음수로 나오는 분기가 있으면
    **차트를 그리지 않는다** — 그럴듯한데 틀린 그림은 틀린 문장보다 위험하다.
    """
    quarters = normalized.get("quarterly_standalone") or []
    rows = []
    for quarter in quarters:
        revenue = account_value(quarter, "revenue")
        operating_income = account_value(quarter, "operating_income")
        if revenue is None:
            continue
        rows.append({
            "label": quarter["period_label"],
            "revenue_billion": round(revenue / 1e8, 1),
            "operating_income_billion": (
                round(operating_income / 1e8, 1) if operating_income is not None else None
            ),
        })
    if len(rows) < 2:
        return None
    negative = [row["label"] for row in rows if row["revenue_billion"] < 0]
    if negative:
        print(f"[WARN] 분기 단독 매출이 음수인 분기가 있어 분기 추이 차트를 건너뛴다: "
              f"{', '.join(negative)}")
        print("       상류 normalize_data.py 의 누적 차분이 3개월값을 누적으로 "
              "간주했을 때 나타나는 증상이다.")
        return None
    return _render_revenue_profit(rows, out_dir, "quarterly_performance",
                                  "분기 단독 매출과 영업이익",
                                  "DART 연결(CFS) 분기 단독값 — 누적 보고서 차분",
                                  "분기 단독값이다. 누적값이 아니다.")


def _render_revenue_profit(rows: list[dict], out_dir: Path, name: str,
                           title: str, source: str, note: str) -> dict:
    """매출 막대 + 영업이익 선. 연간·분기 차트가 같은 형식을 쓴다."""

    labels = [row["label"] for row in rows]
    revenues = [row["revenue_billion"] for row in rows]
    operating = [row["operating_income_billion"] for row in rows]

    figure, axis_revenue = plt.subplots(figsize=(8, 4.2))
    axis_revenue.bar(labels, revenues, color=COLOR_BAR, width=0.6, label="매출 (억원)")
    axis_revenue.set_ylabel("매출 (억원)", color=COLOR_BAR)
    axis_revenue.tick_params(axis="y", labelcolor=COLOR_BAR)
    axis_revenue.set_ylim(0, max(revenues) * 1.15)
    axis_revenue.grid(axis="y", alpha=0.25)

    axis_profit = axis_revenue.twinx()
    plotted = [(index, value) for index, value in enumerate(operating) if value is not None]
    if plotted:
        axis_profit.plot([labels[index] for index, _ in plotted],
                         [value for _, value in plotted],
                         color=COLOR_LINE, marker="o", linewidth=2,
                         label="영업이익 (억원)")
        profit_values = [value for _, value in plotted]
        margin = max(abs(min(profit_values)), abs(max(profit_values))) * 0.35 or 1
        axis_profit.set_ylim(min(0, min(profit_values)) - margin,
                             max(profit_values) + margin)
        # 0 선을 그냥 그으면 매출축의 중간값과 겹쳐 오독된다. 어느 축의 0 인지 밝힌다.
        axis_profit.axhline(0, color="#666666", linewidth=0.8, linestyle="--")
        axis_profit.annotate("영업이익 0", xy=(1.0, 0), xycoords=("axes fraction", "data"),
                             xytext=(-4, 4), textcoords="offset points",
                             ha="right", fontsize=8, color="#666666")
    axis_profit.set_ylabel("영업이익 (억원)", color=COLOR_LINE)
    axis_profit.tick_params(axis="y", labelcolor=COLOR_LINE)

    axis_revenue.set_title(title, fontsize=13, pad=12)
    figure.autofmt_xdate(rotation=45)
    file_name = save_figure(figure, out_dir, name)
    return {
        "name": name,
        "file": file_name,
        "title": title,
        "source": source,
        "note": note,
        "data": rows,
    }


def chart_relative_performance(normalized: dict, out_dir: Path) -> dict | None:
    """주가와 지수를 창 시작일 100 으로 맞춰 비교한다. 새 지표를 만들지 않는다."""
    market = normalized.get("market") or {}
    price_series = market.get("series") or []
    index_block = market.get("index") or {}
    index_series = index_block.get("series") or []
    if len(price_series) < 2 or len(index_series) < 2:
        return None

    index_by_date = {row["date"]: row["close"] for row in index_series}
    paired = [(row["date"], row["close"], index_by_date[row["date"]])
              for row in price_series if row["date"] in index_by_date]
    paired = paired[-RELATIVE_WINDOW_DAYS:]
    if len(paired) < 2:
        return None

    base_price = paired[0][1]
    base_index = paired[0][2]
    dates = [item[0] for item in paired]
    price_rebased = [round(item[1] / base_price * 100, 2) for item in paired]
    index_rebased = [round(item[2] / base_index * 100, 2) for item in paired]

    figure, axis = plt.subplots(figsize=(8, 4.2))
    axis.plot(dates, price_rebased, color=COLOR_BAR, linewidth=2, label="한샘 주가")
    axis.plot(dates, index_rebased, color=COLOR_INDEX, linewidth=2,
              linestyle="--", label=index_block.get("index_name", "지수"))
    axis.axhline(100, color="#666666", linewidth=0.8)
    axis.set_ylabel(f"{dates[0]} = 100")
    axis.set_title(f"주가와 {index_block.get('index_name', '지수')} 비교 "
                   f"({len(paired)}거래일, 시작일 100 기준)", fontsize=13, pad=12)
    axis.grid(alpha=0.25)
    axis.legend(loc="best", frameon=False)
    step = max(len(dates) // 6, 1)
    axis.set_xticks(dates[::step])
    figure.autofmt_xdate(rotation=45)

    file_name = save_figure(figure, out_dir, "relative_performance")
    return {
        "name": "relative_performance",
        "file": file_name,
        "title": f"주가와 {index_block.get('index_name', '지수')} 비교",
        "source": "pykrx(비공식 래퍼) 일별 종가 — 시작일을 100 으로 재기준화",
        "note": "가격 수준이 아니라 시작일 대비 변화율 비교다.",
        "data": {
            "window_start": dates[0],
            "window_end": dates[-1],
            "price_end_rebased": price_rebased[-1],
            "index_end_rebased": index_rebased[-1],
        },
    }


def chart_canslim(trend_module: dict, out_dir: Path) -> dict | None:
    """CANSLIM 7항목 등급. N/A 는 0 이 아니라 회색 '미채점' 으로 그린다."""
    rows = trend_module.get("criteria_scores") or []
    ordered = [row for key in CANSLIM_LABELS
               for row in rows if row["criterion_id"] == key]
    if not ordered:
        return None

    labels = [CANSLIM_LABELS[row["criterion_id"]] for row in ordered]
    levels = [row.get("level") for row in ordered]
    positions = list(range(len(ordered)))[::-1]

    figure, axis = plt.subplots(figsize=(8, 4.0))
    for position, level in zip(positions, levels):
        if level is None:
            axis.barh(position, 3, color=COLOR_NA, alpha=0.45, height=0.6)
            axis.text(1.5, position, "미채점 (데이터 부재)", va="center", ha="center",
                      fontsize=9, color="#4A4A4A")
        else:
            color = COLOR_GOOD if level >= 2 else COLOR_BAD
            axis.barh(position, max(level, 0.06), color=color, height=0.6)
            axis.text(max(level, 0.06) + 0.08, position, f"{level}등급",
                      va="center", fontsize=9, color="#333333")
    axis.set_yticks(positions)
    axis.set_yticklabels(labels, fontsize=10)
    axis.set_xlim(0, 3.6)
    axis.set_xticks([0, 1, 2, 3])
    axis.set_xlabel("등급 (0 최하 ~ 3 최상)")
    axis.set_title("CANSLIM 7항목 채점", fontsize=13, pad=12)
    axis.grid(axis="x", alpha=0.25)

    file_name = save_figure(figure, out_dir, "canslim_grades")
    return {
        "name": "canslim_grades",
        "file": file_name,
        "title": "CANSLIM 7항목 채점",
        "source": "module-results trend 모듈 criteria_scores",
        "note": "N/A 는 0 점이 아니라 미채점이다.",
        "data": [
            {"criterion_id": row["criterion_id"], "level": row.get("level"),
             "metric": row.get("metric"), "metric_value": row.get("metric_value"),
             "na_reason": row.get("na_reason")}
            for row in ordered
        ],
    }


def chart_module_scores(manifest: dict, out_dir: Path) -> dict | None:
    """모듈 8축 점수와 적용 가중치."""
    modules = manifest.get("modules") or []
    if not modules:
        return None
    scored = [row for row in modules if isinstance(row.get("score"), (int, float))]
    if not scored:
        return None
    scored.sort(key=lambda row: row["score"])

    labels = [MODULE_LABELS.get(row["module"], row["module"]) for row in scored]
    scores = [row["score"] for row in scored]
    positions = list(range(len(scored)))

    figure, axis = plt.subplots(figsize=(8, 4.2))
    for position, row, score in zip(positions, scored, scores):
        counted = row.get("counted_in_composite", True)
        color = COLOR_NA if not counted else (COLOR_GOOD if score >= 60 else COLOR_BAD)
        axis.barh(position, score, color=color, height=0.6)
        weight = row.get("weight")
        suffix = f"  (가중치 {weight:g}%)" if counted and weight else "  (종합점수 미반영)"
        axis.text(score + 1.2, position, f"{score:g}점{suffix}",
                  va="center", fontsize=9, color="#333333")
    composite_score = (manifest.get("composite") or {}).get("score")
    if isinstance(composite_score, (int, float)):
        axis.axvline(composite_score, color="#444444", linestyle="--", linewidth=1)
        axis.text(composite_score + 0.6, len(scored) - 0.35,
                  f"종합 {composite_score:g}점", fontsize=9, color="#444444")
    axis.set_yticks(positions)
    axis.set_yticklabels(labels, fontsize=10)
    axis.set_xlim(0, 118)
    axis.set_xticks([0, 20, 40, 60, 80, 100])
    axis.set_xlabel("모듈 점수 (0~100)")
    axis.set_title("모듈별 점수와 가중치", fontsize=13, pad=12)
    axis.grid(axis="x", alpha=0.25)

    file_name = save_figure(figure, out_dir, "module_scores")
    return {
        "name": "module_scores",
        "file": file_name,
        "title": "모듈별 점수와 가중치",
        "source": "manifest.modules (score_modules.py 산출)",
        "note": "점수는 Python 이 계산한 값이다.",
        "data": [
            {"module": row["module"], "score": row["score"],
             "weight": row.get("weight"),
             "counted_in_composite": row.get("counted_in_composite", True)}
            for row in scored
        ],
    }


def resolve_base_url(explicit: str | None) -> str | None:
    """--base-url 이 없으면 origin 원격에서 GitHub raw URL 을 유추한다."""
    if explicit:
        return explicit.rstrip("/")
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?$", remote)
    if not match:
        return None
    owner, repository = match.group(1), match.group(2)
    return (f"https://raw.githubusercontent.com/{owner}/{repository}"
            f"/main/docs/blog/assets")


def main() -> int:
    parser = argparse.ArgumentParser(description="블로그용 차트 렌더러")
    parser.add_argument("ticker")
    parser.add_argument("--data-dir", help="generating-krx-report/data 경로")
    parser.add_argument("--out", default="docs/blog/assets", help="이미지 출력 루트")
    parser.add_argument("--base-url", help="이미지 절대 URL 접두어 (미지정 시 origin 에서 유추)")
    args = parser.parse_args()

    try:
        if not re.fullmatch(r"\d{6}", args.ticker):
            raise RenderError(f"티커는 6자리 숫자여야 한다: {args.ticker}")
        data_dir = (Path(args.data_dir).resolve() if args.data_dir else
                    (Path(__file__).resolve().parents[2]
                     / "generating-krx-report" / "data").resolve())
        normalized = read_json(data_dir / "normalized" / f"{args.ticker}_normalized.json")
        manifest = read_json(data_dir / f"{args.ticker}_manifest.json")
        trend_path = data_dir / "module-results" / f"{args.ticker}_trend.json"
        trend_module = read_json(trend_path) if trend_path.exists() else {}

        out_dir = Path(args.out).resolve() / args.ticker
        charts = [
            chart_annual_performance(normalized, out_dir),
            chart_quarterly_performance(normalized, out_dir),
            chart_relative_performance(normalized, out_dir),
            chart_canslim(trend_module, out_dir),
            chart_module_scores(manifest, out_dir),
        ]
        rendered = [chart for chart in charts if chart]
        if not rendered:
            raise RenderError("렌더링할 데이터가 없다.")

        base_url = resolve_base_url(args.base_url)
        as_of = manifest.get("data_cutoff")
        for chart in rendered:
            chart["as_of"] = as_of
            chart["relative_path"] = f"assets/{args.ticker}/{chart['file']}"
            chart["url"] = (f"{base_url}/{args.ticker}/{chart['file']}"
                            if base_url else None)

        ledger = {
            "ticker": args.ticker,
            "as_of": as_of,
            "base_url": base_url,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "charts": rendered,
        }
        ledger_path = out_dir / "charts.json"
        ledger_path.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except RenderError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2

    print(f"차트 {len(rendered)}개 생성 → {out_dir}")
    for chart in rendered:
        print(f"  FIG:{chart['name']:<24} {chart['file']}")
    print(f"원장: {ledger_path}")
    if not base_url:
        print("[WARN] base-url 을 정하지 못했다. 상대 경로만 기록했다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
