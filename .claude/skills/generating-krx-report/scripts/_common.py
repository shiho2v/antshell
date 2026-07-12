#!/usr/bin/env python3
"""공용 유틸리티 — 경로 해석, JSON I/O, DART HTTP 클라이언트, 자격증명 탐지, 안전 산술.

이 모듈은 다른 스크립트가 import 한다. 단독 실행 대상이 아니다.
Phase 12(토큰 효율) 규칙 "동일 계산을 여러 스크립트에서 반복하지 않음"을 지키기 위한 단일 지점이다.

핵심 설계:
  - 스킬 루트는 __file__ 기준으로 계산한다. **CWD 와 무관**하게 항상 스킬 디렉터리에 쓴다.
  - DART 는 오류도 HTTP 200 으로 준다. 반드시 본문 status 로 판정한다.
  - status 013/014(데이터 없음)는 **오류가 아니며 0 으로 변환하지 않는다** → None 을 반환한다.
  - NaN/Infinity 는 JSON 직렬화 전에 차단한다.

Python 3.10+ (이 환경은 3.10.5 — design-review.md C1 참조).
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

# ── 경로 ────────────────────────────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
NORM_DIR = DATA_DIR / "normalized"
EVID_DIR = DATA_DIR / "evidence"
MODRES_DIR = DATA_DIR / "module-results"
OUTPUT_DIR = SKILL_ROOT / "outputs"
CONFIG_DIR = SKILL_ROOT / "config"
SCHEMA_DIR = SKILL_ROOT / "schemas"
TEMPLATE_DIR = SKILL_ROOT / "templates"

DART_BASE = "https://opendart.fss.or.kr/api"
DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"

# reprt_code — 11012 는 2분기가 아니라 **반기**다 (design-review.md 2.2)
REPRT_Q1 = "11013"
REPRT_HALF = "11012"
REPRT_Q3 = "11014"
REPRT_ANNUAL = "11011"
REPRT_LABELS = {
    REPRT_Q1: "1분기보고서",
    REPRT_HALF: "반기보고서",
    REPRT_Q3: "3분기보고서",
    REPRT_ANNUAL: "사업보고서",
}

# DART status 분류 (design-review.md 2.6)
DART_OK = "000"
DART_NO_DATA = {"013", "014"}          # 오류 아님 — 빈 결과
DART_RATE_LIMIT = "020"
DART_TRANSIENT = {"800", "900"}
DART_HARD = {"010", "011", "012", "021", "100", "101", "901"}
DART_STATUS_MSG = {
    "010": "등록되지 않은 인증키",
    "011": "사용할 수 없는 인증키",
    "012": "접근할 수 없는 IP",
    "013": "조회된 데이터 없음",
    "014": "파일이 존재하지 않음",
    "020": "요청 제한 초과",
    "021": "조회 가능한 회사 개수 초과",
    "100": "부적절한 필드 값",
    "101": "부적절한 접근",
    "800": "시스템 점검 중",
    "900": "정의되지 않은 오류",
    "901": "개인정보 보유기간 만료",
}


class SkillError(Exception):
    """조용한 실패를 막기 위한 명시적 예외. 메시지는 사용자에게 그대로 노출된다."""


class DartNoData(Exception):
    """status 013/014 — 정상적인 '데이터 없음'. 호출자가 N/A 로 처리해야 하며 0 이 아니다."""


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# ── 티커 ────────────────────────────────────────────────────────────────────
def validate_ticker(ticker: str) -> str:
    """6자리 숫자 종목코드만 허용한다. 우선주/스팩 등도 6자리이므로 형식만 검사한다."""
    t = (ticker or "").strip()
    if not (len(t) == 6 and t.isdigit()):
        raise SkillError(f"종목코드는 6자리 숫자여야 합니다: '{ticker}'")
    return t


# ── 자격증명 ────────────────────────────────────────────────────────────────
def credentials() -> dict[str, bool]:
    """자격증명의 **존재 여부만** 반환한다. 값은 절대 저장/출력하지 않는다."""
    return {
        "DART_API_KEY": bool(os.environ.get("DART_API_KEY", "").strip()),
        "KRX_ID": bool(os.environ.get("KRX_ID", "").strip()),
        "KRX_PW": bool(os.environ.get("KRX_PW", "").strip()),
        "KRX_OPEN_API_KEY": bool(os.environ.get("KRX_OPEN_API_KEY", "").strip()),
    }


def has_krx_login() -> bool:
    c = credentials()
    return c["KRX_ID"] and c["KRX_PW"]


def require_dart_key() -> str:
    key = os.environ.get("DART_API_KEY", "").strip()
    if not key:
        raise SkillError(
            "환경변수 DART_API_KEY 가 없습니다. https://opendart.fss.or.kr 에서 발급 후 설정하세요.\n"
            "  PowerShell:  $env:DART_API_KEY = '...'\n"
            "  bash:        export DART_API_KEY=..."
        )
    return key


# ── HTTP ────────────────────────────────────────────────────────────────────
def _http_get(url: str, timeout: int = 30, retries: int = 3) -> bytes:
    """timeout + 제한된 retry. 재시도는 일시적 오류에만 적용한다."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except HTTPError as e:
            # 4xx 는 재시도 무의미
            if 400 <= e.code < 500:
                raise SkillError(f"HTTP {e.code} — 요청이 거부되었습니다: {_redact(url)}") from e
            last = e
        except URLError as e:
            last = e
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    raise SkillError(f"네트워크 실패({last}): {_redact(url)}")


def _redact(url: str) -> str:
    """URL 에서 API 키를 가린다. 로그·예외 메시지에 키가 새지 않게 한다."""
    import re
    return re.sub(r"(crtfc_key=)[^&]+", r"\1***", url)


def dart_get_json(endpoint: str, params: dict[str, str], timeout: int = 30) -> dict[str, Any]:
    """DART JSON 엔드포인트 호출.

    DART 는 **오류도 HTTP 200** 으로 반환하므로 본문 status 로 판정한다.
    - status 000  → 그대로 반환
    - status 013/014 → DartNoData 예외 (호출자가 N/A 로 처리. **0 아님**)
    - status 020  → 백오프 후 재시도, 계속되면 SkillError
    - 그 외       → SkillError (조용한 실패 금지)
    """
    key = require_dart_key()
    q = {"crtfc_key": key, **params}
    url = f"{DART_BASE}/{endpoint}?{urlencode(q)}"

    for attempt in range(3):
        raw = _http_get(url, timeout=timeout)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise SkillError(f"DART 응답 JSON 파싱 실패 ({endpoint}): {e}") from e

        status = str(data.get("status", ""))
        if status == DART_OK:
            return data
        if status in DART_NO_DATA:
            raise DartNoData(f"{endpoint}: {DART_STATUS_MSG.get(status)} (params={params})")
        if status == DART_RATE_LIMIT:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise SkillError(
                f"DART 요청 제한 초과(status=020). 잠시 후 다시 실행하세요. ({endpoint})"
            )
        if status in DART_TRANSIENT and attempt < 2:
            time.sleep(3 * (attempt + 1))
            continue
        msg = DART_STATUS_MSG.get(status, data.get("message", "알 수 없는 오류"))
        raise SkillError(f"DART 오류 (status={status}, {msg}) — endpoint={endpoint}, params={params}")

    raise SkillError(f"DART 호출 실패 ({endpoint})")


def dart_get_zip(endpoint: str, params: dict[str, str], timeout: int = 60) -> zipfile.ZipFile:
    """corpCode.xml / document.xml 등 ZIP 바이너리 엔드포인트."""
    key = require_dart_key()
    url = f"{DART_BASE}/{endpoint}?{urlencode({'crtfc_key': key, **params})}"
    raw = _http_get(url, timeout=timeout)
    if raw[:2] != b"PK":
        # 키 오류 등은 ZIP 대신 JSON/XML 로 온다
        try:
            data = json.loads(raw.decode("utf-8"))
            status = str(data.get("status", ""))
            if status in DART_NO_DATA:
                raise DartNoData(f"{endpoint}: {DART_STATUS_MSG.get(status)}")
            raise SkillError(
                f"DART 오류 (status={status}, "
                f"{DART_STATUS_MSG.get(status, data.get('message', ''))}) — {endpoint}"
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise SkillError(f"{endpoint} 응답이 ZIP 이 아닙니다. API 키를 확인하세요.")
    try:
        return zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise SkillError(f"{endpoint} ZIP 파싱 실패: {e}") from e


# ── corp_code 매핑 (캐시) ───────────────────────────────────────────────────
CORPCODE_CACHE = RAW_DIR / "_corpcode_map.json"
CORPCODE_TTL_DAYS = 7


def load_corpcode_map(force_refresh: bool = False) -> dict[str, dict[str, str]]:
    """stock_code → {corp_code, corp_name} 매핑. corpCode.xml 은 크므로 7일 캐시한다."""
    if not force_refresh and CORPCODE_CACHE.exists():
        age = (datetime.now() - datetime.fromtimestamp(CORPCODE_CACHE.stat().st_mtime)).days
        if age < CORPCODE_TTL_DAYS:
            return read_json(CORPCODE_CACHE)["map"]

    zf = dart_get_zip("corpCode.xml", {})
    names = zf.namelist()
    if not names:
        raise SkillError("corpCode.xml ZIP 이 비어 있습니다.")
    root = ET.fromstring(zf.read(names[0]))

    mapping: dict[str, dict[str, str]] = {}
    for item in root.iter("list"):
        sc = (item.findtext("stock_code") or "").strip()
        if not sc or sc == " " or len(sc) != 6:
            continue  # 비상장은 stock_code 가 비어 있다
        mapping[sc] = {
            "corp_code": (item.findtext("corp_code") or "").strip(),
            "corp_name": (item.findtext("corp_name") or "").strip(),
            "modify_date": (item.findtext("modify_date") or "").strip(),
        }
    if not mapping:
        raise SkillError("corpCode.xml 에서 상장사 매핑을 하나도 얻지 못했습니다.")

    write_json(CORPCODE_CACHE, {"cached_at": now_iso(), "map": mapping})
    return mapping


# ── 시간 ────────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_str() -> str:
    return date.today().isoformat()


def is_future(d: str | None) -> bool:
    """미래일자 금지 검사 (Gate 2)."""
    if not d:
        return False
    try:
        parsed = datetime.fromisoformat(str(d)[:10]).date()
    except ValueError:
        return False
    return parsed > date.today()


# ── 안전 산술 ───────────────────────────────────────────────────────────────
def safe_div(numer: float | None, denom: float | None) -> float | None:
    """분모 0/None → None. **0 을 반환하지 않는다** (Gate 3: 분모 0 검사)."""
    if numer is None or denom is None:
        return None
    if denom == 0:
        return None
    r = numer / denom
    return None if (math.isnan(r) or math.isinf(r)) else r


def pct_change(cur: float | None, prev: float | None) -> float | None:
    """YoY 증감률(%). 기준값이 0 이거나 **음수면 None**.

    음수 기준 성장률은 의미가 없다(적자→적자 축소를 +로 표기하는 왜곡). Gate 3.
    """
    if cur is None or prev is None:
        return None
    if prev <= 0:
        return None
    return (cur - prev) / prev * 100.0


def cagr(last: float | None, first: float | None, years: float) -> float | None:
    """CAGR(%). **기준연도(first)가 0 이하이면 None** (Gate 3: 음수 기준연도 CAGR 금지)."""
    if last is None or first is None or years <= 0:
        return None
    if first <= 0:
        return None
    if last <= 0:
        return None  # 최종값이 음수면 실수 거듭제곱이 정의되지 않는다
    r = (last / first) ** (1.0 / years) - 1.0
    return None if (math.isnan(r) or math.isinf(r)) else r * 100.0


def clean_number(v: Any) -> float | None:
    """DART 금액 문자열 → float. '-', '', None → None (**0 아님**)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if (math.isnan(v) or math.isinf(v)) else float(v)
    s = str(v).replace(",", "").strip()
    if s in ("", "-", "N/A", "해당사항없음"):
        return None
    neg = s.startswith("(") and s.endswith(")")  # 회계 괄호 음수 표기
    if neg:
        s = s[1:-1]
    try:
        f = float(s)
    except ValueError:
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return -f if neg else f


def assert_finite(obj: Any, path: str = "$") -> None:
    """NaN/Infinity 가 JSON 에 새어 들어가는 것을 차단한다 (Gate 2)."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise SkillError(f"NaN/Infinity 가 감지되었습니다: {path}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            assert_finite(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_finite(v, f"{path}[{i}]")


# ── JSON I/O ────────────────────────────────────────────────────────────────
def read_json(path: Path | str) -> Any:
    p = Path(path)
    if not p.exists():
        raise SkillError(f"필요한 파일이 없습니다: {p}\n  선행 스크립트를 먼저 실행하세요.")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path | str, obj: Any) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    assert_finite(obj)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


def load_yaml(path: Path | str) -> Any:
    try:
        import yaml
    except ImportError as e:
        raise SkillError("PyYAML 이 필요합니다: pip install PyYAML") from e
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_registry() -> dict:
    return load_yaml(CONFIG_DIR / "module-registry.yaml")


def load_modes() -> dict:
    return load_yaml(CONFIG_DIR / "analysis-modes.yaml")


def load_source_priority() -> dict:
    return load_yaml(CONFIG_DIR / "source-priority.yaml")


# ── JSON Schema 검증 ────────────────────────────────────────────────────────
def validate_schema(obj: Any, schema_name: str) -> list[str]:
    """스키마 위반 목록을 반환한다. 빈 리스트면 통과."""
    try:
        import jsonschema
    except ImportError as e:
        raise SkillError("jsonschema 가 필요합니다: pip install jsonschema") from e
    schema = read_json(SCHEMA_DIR / schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in err.path) or '$'}: {err.message}"
        for err in validator.iter_errors(obj)
    ]


# ── 표준 경로 헬퍼 ──────────────────────────────────────────────────────────
def raw_path(ticker: str, name: str) -> Path:
    return RAW_DIR / f"{ticker}_{name}.json"


def contract_path(ticker: str) -> Path:
    return DATA_DIR / f"{ticker}_analysis_contract.json"


def normalized_path(ticker: str) -> Path:
    return NORM_DIR / f"{ticker}_normalized.json"


def metrics_path(ticker: str) -> Path:
    return NORM_DIR / f"{ticker}_metrics.json"


def evidence_path(ticker: str) -> Path:
    return EVID_DIR / f"{ticker}_evidence.json"


def module_result_path(ticker: str, module: str) -> Path:
    return MODRES_DIR / f"{ticker}_{module}.json"


def judgment_path(ticker: str, module: str) -> Path:
    """정성 모듈에서 Claude 가 서수 등급만 기록하는 파일. 산술은 하지 않는다."""
    return MODRES_DIR / f"{ticker}_{module}_judgment.json"


def log(msg: str) -> None:
    """진행 로그는 stderr 로. stdout 은 요약 결과 전용 (원시 API 응답 출력 금지)."""
    print(f"  {msg}", file=sys.stderr)
