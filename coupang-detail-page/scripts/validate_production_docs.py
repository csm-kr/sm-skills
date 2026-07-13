#!/usr/bin/env python3
"""Validate prompt, typography, and visible-copy production contracts."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import re
import sys
from pathlib import Path

from validate_plan import normalize_project_number, table_rows


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def table_dict_rows(text: str, required: set[str]) -> list[dict[str, str]]:
    lines = text.splitlines()
    for index in range(len(lines) - 1):
        if not lines[index].strip().startswith("|"):
            continue
        header = table_cells(lines[index])
        divider = table_cells(lines[index + 1])
        if len(header) != len(divider) or not required.issubset(set(header)):
            continue
        if not all(
            re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in divider
        ):
            continue
        rows: list[dict[str, str]] = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].strip().startswith("|"):
            cells = table_cells(lines[cursor])
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
            cursor += 1
        return rows
    return []


def forbidden_phrases(text: str) -> list[str]:
    match = re.search(
        r"^##\s+forbidden claims\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return []
    phrases: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip().startswith("- "):
            continue
        statement = line.strip()[2:]
        statement = re.split(r"(?:^|[.;])\s*(?:단|다만)[, ]", statement, maxsplit=1)[0]
        for part in re.split(r"[,·]", statement):
            phrase = part.strip().strip("`* .;:")
            if len(phrase) >= 3 and phrase not in phrases:
                phrases.append(phrase)
    return phrases


def numeric_claim_tokens(value: str) -> set[str]:
    """Extract canonical numeric claims so Korean/unit aliases compare equally."""

    def canonical_number(raw: str) -> str:
        try:
            normalized = format(Decimal(raw), "f")
        except InvalidOperation:
            return raw
        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")
        return normalized or "0"

    tokens: set[str] = set()
    for match in re.finditer(
        r"(?<![A-Za-z0-9])UPF\s*(?P<number>\d+(?:\.\d+)?)\s*(?P<plus>\+?)",
        value,
        re.IGNORECASE,
    ):
        tokens.add(
            "upf" + canonical_number(match.group("number")) + match.group("plus")
        )

    unit_aliases = {
        "센티미터": "cm",
        "센치": "cm",
        "㎝": "cm",
        "cm": "cm",
        "°c": "℃",
        "℃": "℃",
        "set": "set",
    }
    unit_pattern = (
        r"센티미터|센치|㎝|mm|cm|kg|ml|set|m|g|l|w|v|a|%|℃|°\s*c|"
        r"도|시간|분|초|회|개|장|세트"
    )
    for match in re.finditer(
        rf"(?<![A-Za-z0-9])(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>{unit_pattern})(?![A-Za-z0-9])",
        value,
        re.IGNORECASE,
    ):
        raw_unit = re.sub(r"\s+", "", match.group("unit")).casefold()
        unit = unit_aliases.get(raw_unit, raw_unit)
        tokens.add(canonical_number(match.group("number")) + unit)
    return tokens


def validate(skill_root: Path, project_no: str) -> dict[str, object]:
    project_no = normalize_project_number(project_no)
    output_root = skill_root / "outputs" / project_no
    prompt_path = output_root / "prompt-set.md"
    font_path = output_root / "font-plan.md"
    ledger_path = output_root / "fact-ledger.md"
    plan_path = output_root / "plan-gate.md"
    errors: list[str] = []
    warnings: list[str] = []

    required_paths = (prompt_path, font_path, ledger_path, plan_path)
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        return {
            "ok": False,
            "project": project_no,
            "errors": ["missing production contract files: " + ", ".join(missing)],
            "warnings": warnings,
        }

    prompt_text = prompt_path.read_text(encoding="utf-8")
    font_text = font_path.read_text(encoding="utf-8")
    ledger_text = ledger_path.read_text(encoding="utf-8")
    plan_text = plan_path.read_text(encoding="utf-8")

    required_prompt_headings = (
        "## SOURCE_ROLES",
        "## R2P_LINEAGE",
        "## COPY_SYSTEM",
        "## TYPOGRAPHY_SYSTEM",
        "## FUNCTION_PRIORITY",
        "## DESIGN_SYSTEM",
    )
    for heading in required_prompt_headings:
        if heading not in prompt_text:
            errors.append(f"prompt-set.md is missing required section: {heading}")
    if len(prompt_text.strip()) < 800:
        errors.append("prompt-set.md is too short to contain a usable generation contract")
    if not re.search(r"800\s*[x×]\s*2400", prompt_text, re.IGNORECASE):
        errors.append("prompt-set.md must lock the 800x2400 canvas")
    for term in ("RAW_ASSET_IDS", "정확한 카피", "최소 32px"):
        if term not in prompt_text:
            errors.append(f"prompt-set.md is missing required production rule: {term}")

    plan = table_rows(plan_text)
    prompt_rows = table_dict_rows(prompt_text, {"장", "ROLE_ID", "INFO_ID"})
    actual_prompt_pages: dict[str, tuple[str, str]] = {}
    for row in prompt_rows:
        raw_page = row.get("장", "")
        if not raw_page.isdigit():
            continue
        page = f"{int(raw_page):02d}"
        actual_prompt_pages[page] = (
            row.get("ROLE_ID", "").strip(),
            row.get("INFO_ID", "").strip(),
        )
    expected_prompt_pages = {
        page: (cells[1].strip(), cells[6].strip())
        for page, cells in plan.items()
        if len(cells) >= 7
    }
    if actual_prompt_pages != expected_prompt_pages:
        errors.append(
            "prompt-set.md page ROLE_ID/INFO_ID rows must exactly match plan-gate.md"
        )
    for page in expected_prompt_pages:
        expected_output = f"outputs/{project_no}/raw/page-{page}.png"
        if expected_output not in prompt_text:
            errors.append(
                f"prompt-set.md is missing the raw output contract for page {page}: {expected_output}"
            )

    if len(font_text.strip()) < 500:
        errors.append("font-plan.md is too short to contain a usable typography contract")
    for term in ("폰트 잠금", "H1", "BODY", "LABEL", "32px", "한글 QA"):
        if term not in font_text:
            errors.append(f"font-plan.md is missing required typography rule: {term}")
    if not re.search(r"800\s*[x×]\s*2400", font_text, re.IGNORECASE):
        errors.append("font-plan.md must define tokens for the 800x2400 canvas")
    if re.search(r"(?:주 한글 서체|폰트 경로 또는 조판 환경):\s*$", font_text, re.MULTILINE):
        errors.append("font-plan.md still contains an empty required font field")

    copy_rows = table_dict_rows(ledger_text, {"장", "H1", "BODY", "근거 Fact ID"})
    copy_pages = {
        f"{int(row['장']):02d}"
        for row in copy_rows
        if row.get("장", "").isdigit()
    }
    if copy_pages != set(plan):
        errors.append("fact-ledger.md copy manifest pages must exactly match the selected plan")
    visible_fields = (
        "EYEBROW",
        "H1",
        "BODY",
        "CARD·CHIP·CAPTION",
        "CTA",
    )
    visible_copy = "\n".join(
        row.get(field, "").replace("`", "")
        for row in copy_rows
        for field in visible_fields
    )
    for phrase in forbidden_phrases(ledger_text):
        if phrase and phrase in visible_copy:
            errors.append(f"visible copy contains forbidden phrase: {phrase}")

    allowed_fact_rows = table_dict_rows(
        ledger_text, {"Fact ID", "허용 사실", "사용 범위"}
    )
    allowed_fact_text = {
        row.get("Fact ID", "").strip().upper(): " ".join(
            (row.get("허용 사실", ""), row.get("사용 범위", ""))
        )
        for row in allowed_fact_rows
    }
    for row in copy_rows:
        page = f"{int(row['장']):02d}" if row.get("장", "").isdigit() else "?"
        row_visible_copy = " ".join(
            row.get(field, "").replace("`", "") for field in visible_fields
        )
        fact_ids = {
            fact_id.upper()
            for fact_id in re.findall(
                r"\bF\d{2,}\b", row.get("근거 Fact ID", ""), re.IGNORECASE
            )
        }
        allowed_text = " ".join(allowed_fact_text.get(fact_id, "") for fact_id in fact_ids)
        unsupported_numeric = sorted(
            numeric_claim_tokens(row_visible_copy) - numeric_claim_tokens(allowed_text)
        )
        if unsupported_numeric:
            errors.append(
                f"copy manifest page {page} contains numeric/unit claims absent from its allowed facts: "
                + ", ".join(unsupported_numeric)
            )

    return {
        "ok": not errors,
        "project": project_no,
        "prompt": str(prompt_path),
        "font": str(font_path),
        "pages": sorted(expected_prompt_pages),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate prompt, typography, and visible-copy production contracts."
    )
    parser.add_argument("project", help="Project number, for example 003 or 3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    report = validate(skill_root, args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"PRODUCTION DOCS READY: project {report['project']}")
    else:
        print(f"PRODUCTION DOCS NOT READY: project {report['project']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
