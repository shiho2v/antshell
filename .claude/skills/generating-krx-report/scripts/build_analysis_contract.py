#!/usr/bin/env python3
"""분석 계약(Analysis Contract) 생성 — 모든 분석의 전제조건.

'무엇을 분석하고 무엇을 하지 않을지'를 먼저 고정한다.
**사용자가 명시하지 않은 것은 임의로 채우지 않는다.**
  - 기본값이 있으면 → 적용하고 assumptions 에 기록
  - 결과에 중대한 영향을 주는데 기본값이 없으면 → unresolved_items 에 기록
  - 투자기간 미지정 → 장기/단기로 임의 해석하지 않고 unspecified 유지

사용법:
    python build_analysis_contract.py 009150 --mode balanced
    python build_analysis_contract.py 009150 --request-type canslim
    python build_analysis_contract.py 009150 --horizon long --peers 000660,005930

출력:
    data/{ticker}_analysis_contract.json
    data/analysis_contract.json          (최신 계약의 별칭 — 프롬프트 호환)
"""
from __future__ import annotations

import argparse

from _common import (
    DATA_DIR,
    SkillError,
    contract_path,
    credentials,
    die,
    load_modes,
    load_registry,
    load_source_priority,
    now_iso,
    raw_path,
    read_json,
    today_str,
    validate_schema,
    validate_ticker,
    write_json,
)


def collect_unsupported() -> list[str]:
    """source-priority.yaml 에서 unsupported 로 확인된 항목을 계약에 그대로 새긴다."""
    sp = load_source_priority()
    return [
        f"{k}: {v.get('reason', '공식 경로 없음')}"
        for k, v in sp.get("items", {}).items()
        if v.get("status") == "unsupported"
    ]


def build(
    ticker: str,
    mode: str,
    request_type: str,
    horizon: str,
    peers: list[str],
    peer_rule: str | None,
    target_price: bool,
    consensus: bool,
    news: bool,
    forecast: bool,
) -> dict:
    modes = load_modes()
    registry = load_registry()

    if mode not in modes["modes"]:
        raise SkillError(
            f"알 수 없는 분석 모드: {mode}. 가능한 값: {', '.join(modes['modes'])}"
        )
    profiles = registry["request_profiles"]
    if request_type not in profiles:
        raise SkillError(
            f"알 수 없는 요청 유형: {request_type}. 가능한 값: {', '.join(profiles)}"
        )

    profile = profiles[request_type]
    required = list(profile.get("full") or [])
    optional = list(profile.get("summary") or [])

    # CANSLIM 의 C·A 는 growth 지표를 재사용하므로 growth 가 없으면 성립하지 않는다.
    if "trend" in required and "growth" not in required:
        required.append("growth")

    assumptions: list[dict] = []
    unresolved: list[dict] = []

    # ── 기본값 적용 사실을 반드시 기록한다 ──────────────────────────────────
    if mode == modes["default"]:
        assumptions.append({
            "field": "analysis_mode",
            "applied_value": mode,
            "reason": "사용자가 분석 관점을 지정하지 않아 기본값(balanced)을 적용했다. "
                      "보고서 Executive Summary 에 표시한다.",
        })

    # ── 기본값이 없는 항목은 임의 해석하지 않는다 ──────────────────────────
    if horizon == "unspecified":
        unresolved.append({
            "field": "investment_horizon",
            "impact": "투자기간에 따라 밸류에이션·추세·촉매의 상대적 중요도가 달라진다. "
                      "장기/단기로 임의 해석하지 않고 미지정 상태로 분석한다.",
            "question_for_user": "투자기간을 알려주시면 모드를 조정할 수 있습니다 (단기/중기/장기).",
        })

    creds = credentials()
    if not creds["DART_API_KEY"]:
        unresolved.append({
            "field": "DART_API_KEY",
            "impact": "재무 데이터 일체를 조회할 수 없다. quality/growth/valuation 모듈 실행 불가.",
            "question_for_user": "DART_API_KEY 환경변수를 설정해 주세요 (https://opendart.fss.or.kr).",
        })
    if not (creds["KRX_ID"] and creds["KRX_PW"]):
        assumptions.append({
            "field": "krx_credentials",
            "applied_value": False,
            "reason": "KRX_ID/KRX_PW 가 없어 수급(CANSLIM I), 지수(M), 업종 상대강도(L), "
                      "역사적 PER 밴드가 N/A 로 처리된다. **0점으로 채점하지 않는다.** "
                      "시세는 pykrx→Naver 경유(비공식)로만 수집된다.",
        })

    # ── 금지 추론 ───────────────────────────────────────────────────────────
    prohibited = [
        "목표주가 산출 — 컨센서스/Forward EPS 의 공식 데이터 출처가 존재하지 않는다.",
        "Forward PER 계산 — 검증된 Forward EPS 가 없다.",
        "컨센서스·전망치 생성 — 무료 공식 API 가 없다.",
        "시장점유율 추정 — 공시에 존재하지 않는다.",
        "경쟁사 임의 선정 — 선정 규칙 없이 비교기업을 고르지 않는다.",
        "적자기업 PER 적용 금지.",
        "데이터 조회 실패를 0 으로 해석 금지.",
        "외부 지식으로 누락 수치 보완 금지.",
        "누적·분기단독, 연결·별도 수치 혼용 금지.",
    ]
    if not news:
        prohibited.append("뉴스로 공시 데이터를 보완하지 않는다.")

    # 목표주가를 요청했더라도 데이터 출처가 없으므로 생성하지 않는다.
    if target_price:
        unresolved.append({
            "field": "target_price",
            "impact": "목표주가를 요청했으나 컨센서스·Forward EPS 의 공식 데이터 출처가 존재하지 않는다. "
                      "근거 없이 생성하지 않으며, 밸류에이션 모듈은 현재 멀티플과 "
                      "'현재 가격에 내재된 기대'로만 서술한다.",
        })

    # ── 비교기업 ────────────────────────────────────────────────────────────
    peer_requested = bool(peers) or bool(peer_rule)
    if peer_requested and not peers and not peer_rule:
        unresolved.append({
            "field": "peer_comparison.selection_rule",
            "impact": "비교기업 선정 규칙이 없으면 경쟁사를 임의 선택하지 않는다. 동종비교를 생략한다.",
            "question_for_user": "비교기업 티커를 직접 지정하거나 선정 규칙을 알려주세요.",
        })

    contract = {
        "company_name": None,
        "ticker": ticker,
        "market": None,
        "corp_code": None,
        "request_type": request_type,
        "analysis_mode": mode,
        "investment_horizon": horizon,
        "valuation_requested": "valuation" in required or "valuation" in optional,
        "target_price_requested": target_price,
        "forecast_allowed": forecast,
        "consensus_allowed": consensus,
        "news_allowed": news,
        "peer_comparison": {
            "requested": peer_requested,
            "selection_rule": peer_rule,
            "explicit_peers": peers,
        },
        "required_modules": required,
        "optional_modules": optional,
        "assumptions": assumptions,
        "unresolved_items": unresolved,
        "prohibited_inferences": prohibited,
        "unsupported_data": collect_unsupported(),
        "credentials_available": creds,
        "data_cutoff": today_str(),
        "created_at": now_iso(),
    }

    # Gate 1 결과가 있으면 식별 정보를 채운다 (없으면 null 유지 — 임의로 채우지 않는다)
    idp = raw_path(ticker, "identity")
    if idp.exists():
        ident = read_json(idp)
        contract["company_name"] = ident.get("company_name")
        contract["market"] = ident.get("market")
        contract["corp_code"] = ident.get("corp_code")

    return contract


def main() -> None:
    ap = argparse.ArgumentParser(description="분석 계약 생성")
    ap.add_argument("ticker")
    ap.add_argument("--mode", default="balanced",
                    choices=["balanced", "growth", "value", "long-term", "momentum"])
    ap.add_argument("--request-type", default="comprehensive",
                    choices=["comprehensive", "canslim", "valuation", "update"])
    ap.add_argument("--horizon", default="unspecified",
                    choices=["unspecified", "short", "mid", "long"])
    ap.add_argument("--peers", default="", help="쉼표구분 6자리 티커. 사용자가 명시한 경우만.")
    ap.add_argument("--peer-rule", default=None, help="비교기업 선정 규칙 (없으면 비교 생략)")
    ap.add_argument("--target-price", action="store_true")
    ap.add_argument("--consensus", action="store_true")
    ap.add_argument("--news", action="store_true")
    ap.add_argument("--forecast", action="store_true")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        peers = [validate_ticker(p) for p in args.peers.split(",") if p.strip()]

        contract = build(
            ticker, args.mode, args.request_type, args.horizon,
            peers, args.peer_rule, args.target_price,
            args.consensus, args.news, args.forecast,
        )

        errs = validate_schema(contract, "analysis-contract.schema.json")
        if errs:
            die("분석 계약이 스키마를 위반했습니다:\n  - " + "\n  - ".join(errs))

        out = write_json(contract_path(ticker), contract)
        write_json(DATA_DIR / "analysis_contract.json", contract)  # 프롬프트 호환 별칭

        print(f"분석 계약 생성: {out}")
        print(f"  요청유형: {contract['request_type']} / 모드: {contract['analysis_mode']}")
        print(f"  정식 채점 모듈: {', '.join(contract['required_modules']) or '(없음)'}")
        print(f"  요약 인용 모듈: {', '.join(contract['optional_modules']) or '(없음)'}")
        if contract["assumptions"]:
            print(f"  적용된 기본값 {len(contract['assumptions'])}건 (assumptions 참조)")
        if contract["unresolved_items"]:
            print(f"  미해결 항목 {len(contract['unresolved_items'])}건:")
            for u in contract["unresolved_items"]:
                print(f"    - {u['field']}: {u['impact'][:70]}...")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
