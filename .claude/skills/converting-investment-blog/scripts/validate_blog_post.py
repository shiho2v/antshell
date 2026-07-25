#!/usr/bin/env python3
# =============================================================
# File   : validate_blog_post.py
# Author : @suhdongphill
# Week   : 04 | Ch.04 (2/2)
# Created: 2026-07-25
# =============================================================
"""블로그 초안 기계 검증 — 저장·발행 전 마지막 게이트.

의미 판단(문장이 근거를 왜곡했는가, 인과를 과장했는가)은
financial-fact-checker / investment-devils-advocate 에이전트가 맡는다.
이 스크립트는 **결정적으로 판정 가능한 것만** 본다.

검사 항목
  [FAIL] 매수·매도 표현 (제목 포함)      [FAIL] 목표주가·적정주가·컨센서스
  [FAIL] 면책 문구 부재                  [FAIL] 존재하지 않는 claim_id 참조
  [FAIL] 수치 문장에 근거 주석 없음      [FAIL] MANIFEST 주석 줄의 수치 불일치
  [FAIL] 데이터 완전성과 결론 강도 불일치
  [WARN] manifest 에서 확인되지 않는 숫자

generating-krx-report 의 어떤 파일도 수정하지 않는다. **읽기 전용**이다.
특히 validate_report.py 를 호출하지 않는다 — 그 스크립트는 manifest 를 다시 쓴다.

사용법
  python validate_blog_post.py <draft.md> --ticker 009240
  python validate_blog_post.py <draft.md> --ticker 009240 --data-dir <경로>

종료코드: 0 통과 / 1 검증 실패 / 2 실행 오류
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 기본 콘솔(cp949)에서는 '—' 같은 문자가 UnicodeEncodeError 를 낸다.
# 검증 실패 메시지가 예외로 죽지 않도록 출력 스트림을 UTF-8 로 고정한다.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

# generating-krx-report 의 금지어 규칙을 그대로 이식한다.
# (원본: generating-krx-report/scripts/validate_report.py gate4)
PRICE_TARGET_PHRASES = ("목표주가", "적정주가", "컨센서스", "target price")
BUY_SELL_PHRASES = ("매수", "매도")
NEGATION_PATTERN = r"않|없|금지|아니|권유|제시하지|산출하지|불가"
DISCLAIMER_KEYS = ("투자 자문", "투자자문")

MODULES = (
    "business", "quality", "growth", "moat",
    "valuation", "trend", "risk", "catalyst",
)
ANNOTATION_PATTERN = re.compile(
    r"<!--\s*(CLM-\d{4}|MANIFEST|MOD:[a-z_]+/[A-Z]+-[A-Z0-9]+)\s*-->"
)
CLAIM_ID_PATTERN = re.compile(r"CLM-\d{4}")
# MANIFEST·MOD 는 "원장·채점표를 그대로 옮겼다"는 선언이므로 수치 대조를 엄격히 적용한다.
STRICT_PREFIXES = ("MANIFEST", "MOD:")
NUMBER_PATTERN = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}(?:T[\d:]+)?")
LONG_DIGITS_PATTERN = re.compile(r"\d{11,}")
MARKDOWN_LINK_TARGET = re.compile(r"\]\([^)]*\)")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\|[\s|:-]+\|$")
LIST_ITEM_PATTERN = re.compile(r"^(?:[-*+]\s|\d+[.)]\s)")
HEADING_PATTERN = re.compile(r"^#{1,6}\s")
SOURCES_HEADING_PATTERN = re.compile(r"^#{1,6}\s*8[.)\s]|출처")


class ValidationError(Exception):
    """실행 자체가 불가능한 상황 (파일 부재·파싱 실패)."""


def parse_front_matter(text: str) -> tuple[dict, str, int]:
    """frontmatter 를 파싱하고 (메타, 본문, 본문 시작 줄번호) 를 돌려준다."""
    if not text.startswith("---"):
        raise ValidationError("frontmatter 가 없다. '---' 로 시작해야 한다.")
    closing = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if closing is None:
        raise ValidationError("frontmatter 종료 표시('---')를 찾지 못했다.")
    raw_front = text[3: closing.start() + 3]
    body = text[closing.end() + 3:]
    offset = text[: closing.end() + 3].count("\n") + 1
    try:
        import yaml
    except ImportError as exc:
        raise ValidationError("PyYAML 이 필요하다: pip install PyYAML") from exc
    meta = yaml.safe_load(raw_front) or {}
    if not isinstance(meta, dict):
        raise ValidationError("frontmatter 가 key: value 형식이 아니다.")
    return meta, body, offset


def load_module_criteria(data_dir: Path, ticker: str) -> dict[str, dict]:
    """module-results 의 criteria_scores 를 'module/criterion_id' 키로 펼친다."""
    criteria: dict[str, dict] = {}
    for module_name in MODULES:
        path = data_dir / "module-results" / f"{ticker}_{module_name}.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        for row in result.get("criteria_scores") or []:
            criteria[f"{module_name}/{row['criterion_id']}"] = row
    return criteria


def collect_known_numbers(manifest: dict, evidence: dict | None,
                          criteria: dict[str, dict]) -> set[float]:
    """블로그에 등장해도 되는 숫자 집합 — manifest·evidence·채점표에서만 모은다."""
    known: set[float] = set()

    def remember(value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        numeric = float(value)
        known.add(numeric)
        known.add(abs(numeric))
        if 0.0 <= abs(numeric) <= 1.0:
            known.add(round(numeric * 100, 4))
            known.add(round(abs(numeric) * 100, 4))

    composite = manifest.get("composite", {})
    for key in ("score", "confidence", "data_completeness"):
        remember(composite.get(key))
    for weight in (composite.get("weights_used") or {}).values():
        remember(weight)
    for module_row in manifest.get("modules", []):
        for key in ("score", "confidence", "evidence_coverage", "weight"):
            remember(module_row.get(key))
    remember(len(manifest.get("claims", [])))

    for claim in manifest.get("claims", []):
        for token in NUMBER_PATTERN.findall(claim.get("claim", "")):
            parsed = to_float(token)
            if parsed is not None:
                remember(parsed)

    if evidence:
        for item in evidence.get("evidence", []):
            remember(item.get("value"))
            comparison = item.get("comparison") or {}
            remember(comparison.get("compared_value"))
            calculation = item.get("calculation") or {}
            for input_value in (calculation.get("inputs") or {}).values():
                remember(input_value)

    for row in criteria.values():
        remember(row.get("metric_value"))
        remember(row.get("level"))
        remember(row.get("weight"))
    return known


def to_float(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


def is_whitelisted(token: str, value: float) -> bool:
    """오탐이 잦은 숫자는 근거 대조 대상에서 제외한다 (연도·서수·작은 정수)."""
    if "." not in token and "," not in token:
        integer_value = abs(value)
        if 1900 <= integer_value <= 2100:
            return True
        if integer_value <= 20 and integer_value == int(integer_value):
            return True
    return False


def matches_known(value: float, decimals: int, known: set[float]) -> bool:
    """본문 표기 자릿수까지만 반올림해 비교한다 (1.3 ↔ 1.3125 를 같게 본다)."""
    target = round(value, decimals)
    for candidate in known:
        if round(candidate, decimals) == target:
            return True
    return False


def strip_noise(line: str) -> str:
    """숫자 대조 대상이 아닌 조각을 지운다 — 주석·링크주소·날짜·접수번호."""
    cleaned = HTML_COMMENT_PATTERN.sub(" ", line)
    cleaned = MARKDOWN_LINK_TARGET.sub("] ", cleaned)
    cleaned = ISO_DATE_PATTERN.sub(" ", cleaned)
    cleaned = LONG_DIGITS_PATTERN.sub(" ", cleaned)
    return cleaned


def starts_new_unit(stripped: str) -> bool:
    """표의 한 행과 목록의 한 항목은 각각 독립된 근거 단위다."""
    return bool(stripped.startswith("|") or LIST_ITEM_PATTERN.match(stripped))


def iter_checkable_units(body: str, line_offset: int):
    """근거 주석의 적용 범위 단위로 묶어 흘린다.

    Markdown 은 한 문장이 여러 줄로 접힐 수 있고 주석은 문장 끝에 붙는다.
    따라서 줄 단위가 아니라 **문단·표행·목록항목** 단위로 근거를 찾는다.
    코드블록·표 구분선·제목·출처절은 제외한다.
    """
    in_code_block = False
    in_sources_section = False
    unit: list[tuple[int, str]] = []
    for index, line in enumerate(body.splitlines()):
        line_number = line_offset + index + 1
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if HEADING_PATTERN.match(stripped):
            if unit:
                yield unit
                unit = []
            if SOURCES_HEADING_PATTERN.search(stripped):
                in_sources_section = True
            continue
        if in_sources_section:
            continue
        if not stripped or TABLE_SEPARATOR_PATTERN.match(stripped):
            if unit:
                yield unit
                unit = []
            continue
        if starts_new_unit(stripped) and unit:
            yield unit
            unit = []
        unit.append((line_number, line))
    if unit:
        yield unit


def check_forbidden_phrases(title: str, body: str) -> list[str]:
    """매수·매도·목표주가 표현. 부정문과 수급 용어(순매수)는 허용한다."""
    failures: list[str] = []
    plain = HTML_TAG_PATTERN.sub(" ", HTML_COMMENT_PATTERN.sub(" ", body))
    for scope_name, text in (("제목", title), ("본문", plain)):
        for phrase in PRICE_TARGET_PHRASES:
            for match in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                context = text[max(0, match.start() - 40): match.end() + 40]
                if not re.search(NEGATION_PATTERN, context):
                    failures.append(
                        f"{scope_name}에 '{phrase}' 가 부정문 없이 등장: ...{context.strip()}..."
                    )
        for phrase in BUY_SELL_PHRASES:
            for match in re.finditer(phrase, text):
                if match.start() > 0 and text[match.start() - 1] == "순":
                    continue
                if re.search(NEGATION_PATTERN, text[match.end(): match.end() + 16]):
                    continue
                context = text[max(0, match.start() - 30): match.end() + 30]
                failures.append(f"{scope_name}에 '{phrase}' 표현 사용: ...{context.strip()}...")
    return failures


def check_annotations(body: str, line_offset: int, manifest: dict, known: set[float],
                      criteria: dict[str, dict]) -> tuple[list[str], list[str], set[str], set[str]]:
    """근거 주석·claim 참조·채점항목 참조·수치 대조를 한 번에 훑는다."""
    failures: list[str] = []
    warnings: list[str] = []
    used_claim_ids: set[str] = set()
    used_criteria: set[str] = set()
    valid_claim_ids = {claim["claim_id"] for claim in manifest.get("claims", [])}

    for unit in iter_checkable_units(body, line_offset):
        annotations: list[str] = []
        found: list[tuple[int, str, float]] = []
        for line_number, line in unit:
            annotations.extend(ANNOTATION_PATTERN.findall(line))
            for orphan in CLAIM_ID_PATTERN.findall(HTML_COMMENT_PATTERN.sub(" ", line)):
                failures.append(
                    f"{line_number}행: claim ID {orphan} 가 본문에 노출됐다 — HTML 주석으로 감춘다."
                )
            for token in NUMBER_PATTERN.findall(strip_noise(line)):
                value = to_float(token)
                if value is None or is_whitelisted(token, value):
                    continue
                found.append((line_number, token, value))

        for annotation in annotations:
            if annotation == "MANIFEST":
                continue
            if annotation.startswith("MOD:"):
                reference = annotation[4:]
                used_criteria.add(reference)
                if reference not in criteria:
                    failures.append(
                        f"{unit[0][0]}행: 존재하지 않는 채점 항목 {reference} 를 지목했다."
                    )
                continue
            used_claim_ids.add(annotation)
            if annotation not in valid_claim_ids:
                failures.append(
                    f"{unit[0][0]}행: 존재하지 않는 근거 {annotation} 를 지목했다."
                )
        if not found:
            continue
        if not annotations:
            preview = unit[0][1].strip()[:60]
            failures.append(
                f"{unit[0][0]}행: 수치가 있는데 근거 주석(<!-- CLM-xxxx --> · "
                f"<!-- MANIFEST --> · <!-- MOD:모듈/항목 -->)이 없다 — {preview}"
            )
            continue

        is_manifest_line = any(
            annotation.startswith(STRICT_PREFIXES) for annotation in annotations
        )
        for line_number, token, value in found:
            decimals = len(token.split(".")[1]) if "." in token else 0
            if matches_known(value, decimals, known):
                continue
            message = (
                f"{line_number}행: 숫자 {token} 을 manifest·evidence·채점표에서 확인하지 못했다."
            )
            if is_manifest_line:
                failures.append(
                    message + " (MANIFEST·MOD 주석은 원장·채점표 값만 허용한다)"
                )
            else:
                warnings.append(message)
    return failures, warnings, used_claim_ids, used_criteria


def check_conclusion_strength(manifest: dict, meta: dict) -> list[str]:
    """데이터 완전성이 낮은데 확정적 결론을 내지 않았는지 본다."""
    composite = manifest.get("composite", {})
    completeness = composite.get("data_completeness")
    verdict = meta.get("verdict")
    if completeness is not None and completeness < 0.5 and verdict != "판단 유보":
        return [
            f"데이터 완전성 {completeness:.0%} 인데 결론이 '{verdict}' 다 — '판단 유보' 여야 한다."
        ]
    if verdict and verdict != composite.get("verdict"):
        return [
            f"frontmatter 결론 '{verdict}' 가 manifest 결론 "
            f"'{composite.get('verdict')}' 와 다르다."
        ]
    return []


def resolve_data_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return (Path(__file__).resolve().parents[2] / "generating-krx-report" / "data").resolve()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise ValidationError(f"파일을 찾지 못했다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="블로그 초안 검증 (저장 전 게이트)")
    parser.add_argument("draft", help="블로그 초안 Markdown 경로")
    parser.add_argument("--ticker", required=True, help="6자리 티커")
    parser.add_argument("--data-dir", help="generating-krx-report/data 경로 (기본: 형제 스킬)")
    args = parser.parse_args()

    try:
        if not re.fullmatch(r"\d{6}", args.ticker):
            raise ValidationError(f"티커는 6자리 숫자여야 한다: {args.ticker}")
        draft_path = Path(args.draft).resolve()
        if not draft_path.exists():
            raise ValidationError(f"초안을 찾지 못했다: {draft_path}")

        data_dir = resolve_data_dir(args.data_dir)
        manifest = read_json(data_dir / f"{args.ticker}_manifest.json")
        evidence_path = data_dir / "evidence" / f"{args.ticker}_evidence.json"
        evidence = read_json(evidence_path) if evidence_path.exists() else None

        raw_text = draft_path.read_text(encoding="utf-8")
        meta, body, line_offset = parse_front_matter(raw_text)
        if str(meta.get("ticker", "")) != args.ticker:
            raise ValidationError(
                f"frontmatter 티커 '{meta.get('ticker')}' 가 --ticker {args.ticker} 와 다르다."
            )

        criteria = load_module_criteria(data_dir, args.ticker)
        known = collect_known_numbers(manifest, evidence, criteria)
        failures = check_forbidden_phrases(str(meta.get("title", "")), body)

        annotation_failures, warnings, used_claim_ids, used_criteria = check_annotations(
            body, line_offset, manifest, known, criteria
        )
        failures.extend(annotation_failures)
        failures.extend(check_conclusion_strength(manifest, meta))

        if not any(key in raw_text for key in DISCLAIMER_KEYS):
            failures.append("면책 문구(투자 자문 아님)가 없다.")
        if not used_claim_ids and not used_criteria:
            failures.append(
                "근거를 지목한 문장이 하나도 없다 — claim 또는 채점 항목 주석을 달아야 한다."
            )

    except ValidationError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2

    total_claims = len(manifest.get("claims", []))
    print(f"검증 대상: {draft_path.name}")
    print(f"근거 인용: {len(used_claim_ids)} / {total_claims} claim"
          f" · 채점 항목 {len(used_criteria)} / {len(criteria)}")
    for warning in warnings:
        print(f"  [WARN] {warning}")
    for failure in failures:
        print(f"  [FAIL] {failure}")

    if failures:
        print(f"\n검증 실패 — FAIL {len(failures)}건. 저장·발행하지 않는다.")
        print("문구를 우회하지 말고, 근거 없는 문장을 삭제하거나 '확인하지 못한 것'으로 되돌린다.")
        return 1
    print(f"\n검증 통과 (WARN {len(warnings)}건).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
