#!/usr/bin/env python3
# =============================================================
# File   : fetch_dart.py
# Role   : DART OpenAPI로 종목의 최근 3개년 사업보고서 + 최근 4개 분기보고서
#          영업이익/매출/EPS를 조회해 data/{code}_fundamentals.json 생성
# Note   : 스터디 예제. 조용한 실패 금지 — 실패 시 명확한 에러로 종료.
# =============================================================
"""사용법:
    python fetch_dart.py 009150

환경변수:
    DART_API_KEY  (필수) — https://opendart.fss.or.kr 에서 발급

출력:
    data/{code}_fundamentals.json
    각 수치에 rcept_no(접수번호)와 보고서 기준일(bsns_year/reprt)을 포함한다.
"""
import argparse
import io
import json
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, date
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

DART_BASE = "https://opendart.fss.or.kr/api"

# 분기보고서 코드 (reprt_code): 1분기 11013, 반기 11012, 3분기 11014, 사업보고서 11011
REPRT_CODES = {
    "11013": "1Q",
    "11012": "HY",
    "11014": "3Q",
    "11011": "FY",
}

# 재무제표에서 뽑을 계정 (account_nm 부분일치용 키워드)
ACCOUNT_KEYS = {
    "revenue": ["매출액", "수익(매출액)", "영업수익"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "eps": ["주당순이익", "기본주당이익", "기본주당순이익"],
}


def die(msg: str, code: int = 1):
    """에러 메시지를 stderr로 내보내고 즉시 종료 (조용한 실패 금지)."""
    print(f"[fetch_dart] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def get_api_key() -> str:
    key = os.environ.get("DART_API_KEY", "").strip()
    if not key:
        die("환경변수 DART_API_KEY가 설정되지 않았습니다. "
            "https://opendart.fss.or.kr 에서 키를 발급받아 설정하세요.")
    return key


def http_get(url: str) -> bytes:
    try:
        with urlopen(url, timeout=30) as resp:
            return resp.read()
    except HTTPError as e:
        die(f"HTTP {e.code} 오류: {url}")
    except URLError as e:
        die(f"네트워크 오류({e.reason}): {url}")


def resolve_corp_code(api_key: str, stock_code: str) -> str:
    """corpCode.xml(zip)을 내려받아 stock_code → corp_code 매핑."""
    url = f"{DART_BASE}/corpCode.xml?" + urlencode({"crtfc_key": api_key})
    raw = http_get(url)
    # DART가 zip 대신 JSON 에러를 주는 경우(키 오류 등) 감지
    if raw[:2] != b"PK":
        try:
            err = json.loads(raw.decode("utf-8"))
            die(f"corpCode 조회 실패 (status={err.get('status')}): "
                f"{err.get('message')}")
        except json.JSONDecodeError:
            die("corpCode.xml 응답이 zip 형식이 아닙니다. 키를 확인하세요.")
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        xml_bytes = zf.read(zf.namelist()[0])
    except (zipfile.BadZipFile, IndexError) as e:
        die(f"corpCode zip 파싱 실패: {e}")

    root = ET.fromstring(xml_bytes)
    for item in root.iter("list"):
        sc = (item.findtext("stock_code") or "").strip()
        if sc == stock_code:
            corp = (item.findtext("corp_code") or "").strip()
            name = (item.findtext("corp_name") or "").strip()
            if corp:
                print(f"[fetch_dart] 매핑: {stock_code} → corp_code={corp} "
                      f"({name})", file=sys.stderr)
                return corp
    die(f"종목코드 {stock_code}에 해당하는 corp_code를 찾지 못했습니다. "
        "상장 6자리 코드가 맞는지 확인하세요.")


def fetch_statement(api_key: str, corp_code: str, year: int, reprt_code: str):
    """단일회사 주요재무제표(fnlttSinglAcnt) 조회. 리스트[dict] 반환 (없으면 [])."""
    url = f"{DART_BASE}/fnlttSinglAcnt.json?" + urlencode({
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": reprt_code,
    })
    raw = http_get(url)
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        die(f"재무제표 응답 JSON 파싱 실패 (year={year}, reprt={reprt_code})")
    status = data.get("status")
    if status == "013":  # 데이터 없음
        return []
    if status != "000":
        # 조회 자체 오류(키·요청 문제)는 종료, 013(무데이터)만 허용
        die(f"재무제표 조회 실패 (status={status}): {data.get('message')} "
            f"(year={year}, reprt={reprt_code})")
    return data.get("list", [])


def pick_account(rows, keys):
    """account_nm 부분일치로 계정 값 추출. (value:int|None, rcept_no, account_nm)."""
    for row in rows:
        name = (row.get("account_nm") or "").strip()
        if any(k in name for k in keys):
            amount = (row.get("thstrm_amount") or "").replace(",", "").strip()
            rcept = row.get("rcept_no", "")
            if amount in ("", "-"):
                return None, rcept, name
            try:
                return int(float(amount)), rcept, name
            except ValueError:
                return None, rcept, name
    return None, "", ""


def build_record(rows, bsns_year, reprt_code, reprt_label):
    """한 보고서에서 revenue/operating_income/eps를 (출처, 기준일) 태그와 함께 구성."""
    rec = {
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "reprt_label": reprt_label,
    }
    for field, keys in ACCOUNT_KEYS.items():
        value, rcept, acc_nm = pick_account(rows, keys)
        rec[field] = {
            "value": value,
            "account_nm": acc_nm or None,
            "rcept_no": rcept or None,
            "basis": f"{bsns_year} {reprt_label}",  # 보고서 기준
        }
    return rec


def main():
    parser = argparse.ArgumentParser(
        description="DART 재무 데이터 수집 → data/{code}_fundamentals.json")
    parser.add_argument("code", help="6자리 종목코드 (예: 009150)")
    args = parser.parse_args()

    code = args.code.strip()
    if not (code.isdigit() and len(code) == 6):
        die(f"종목코드는 6자리 숫자여야 합니다: '{code}'")

    api_key = get_api_key()
    corp_code = resolve_corp_code(api_key, code)

    this_year = date.today().year
    # 최근 3개년 사업보고서(FY): 전전년 ~ 3년 전 (당해 사업보고서는 미공시일 수 있음)
    annual = []
    for year in range(this_year - 1, this_year - 5, -1):
        rows = fetch_statement(api_key, corp_code, year, "11011")
        if rows:
            annual.append(build_record(rows, year, "11011", "사업보고서"))
        if len(annual) >= 3:
            break

    # 최근 4개 분기보고서: 최근 2년 범위에서 분기/반기 보고서를 최신순으로 수집
    quarterly = []
    q_order = ["11014", "11012", "11013", "11011"]  # 3Q, HY, 1Q, FY(연간=4Q 누적)
    for year in range(this_year, this_year - 3, -1):
        for rc in q_order:
            rows = fetch_statement(api_key, corp_code, year, rc)
            if rows:
                quarterly.append(
                    build_record(rows, year, rc, REPRT_CODES.get(rc, rc)))
            if len(quarterly) >= 4:
                break
        if len(quarterly) >= 4:
            break

    if not annual and not quarterly:
        die("사업보고서·분기보고서 데이터를 하나도 조회하지 못했습니다. "
            "종목코드/키/공시 여부를 확인하세요.")

    result = {
        "stock_code": code,
        "corp_code": corp_code,
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "DART OpenAPI (fnlttSinglAcnt)",
        "unit": "KRW (원). EPS는 원/주.",
        "annual": annual,        # 최근 3개년 사업보고서
        "quarterly": quarterly,  # 최근 4개 분기(누적) 보고서
    }

    out_dir = os.path.join("data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{code}_fundamentals.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[fetch_dart] 저장 완료: {out_path} "
          f"(annual={len(annual)}, quarterly={len(quarterly)})")


if __name__ == "__main__":
    main()
