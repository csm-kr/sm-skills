#!/usr/bin/env python3
"""Validate an evidence-sized, non-repeating Coupang detail-page plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MIN_PAGES = 3
MAX_PAGES = 10

# A plan may freely select from these roles. A role may repeat when each page owns
# a different INFO_ID, Fact set, proof, shot, scene, and layout; PRODUCT_INTRO is
# still unique. CTA variants combine new information with the closing action so a
# repetitive summary-only page is not required.
ALLOWED_ROLES = {
    "PROBLEM_HOOK": ("문제 후킹", "H1+BODY+PROBLEM_SCENE"),
    "NEED_REASON": ("상품이 필요한 이유", "H1+BODY+SELECTION_CRITERIA"),
    "PRODUCT_INTRO": ("상품 메인 소개", "PRODUCT_NAME+HERO+CORE_ADVANTAGES"),
    "FEATURE_EVIDENCE": ("핵심 기능과 근거", "FEATURE+EVIDENCE+BOUNDARY"),
    "FIT_STRUCTURE": ("착용 구조", "FIT+STRUCTURE+DETAIL"),
    "MEASURED_SIZE": ("실측 사이즈", "SIZE_DIAGRAM+MEASUREMENTS"),
    "FIT_SIZE": ("착용감·실측 사이즈", "FIT+SIZE_DIAGRAM+MEASUREMENTS"),
    "MATERIAL_SPEC": ("소재·제품 사양", "MATERIAL+SPEC+DETAIL"),
    "COMPONENTS": ("구성품 안내", "COMPONENT_LIST+PACKAGE_IMAGE"),
    "OPTIONS": ("옵션 안내", "OPTIONS+CURRENT_VARIANTS"),
    "HOW_TO_USE": ("사용 방법", "STEP_BY_STEP+USE_SCENE"),
    "SITUATION_COMPARE": (
        "사용 상황 비교",
        "SITUATION_BEFORE+SITUATION_AFTER",
    ),
    "NEUTRAL_COMPARE": ("중립 선택 비교", "NEUTRAL_COMPARE+CRITERIA"),
    "RECOMMENDATION": ("추천 대상", "RECOMMENDATION+CHECKLIST"),
    "USE_CASES": ("다양한 사용 장면", "USE_CASES+CAPTIONS"),
    "SITUATION_USE": ("사용 상황·구매 안내", "USE_SCENE+USAGE_INFO+CTA"),
    "CARE_GUIDE": ("관리·보관 안내", "CARE+STORAGE+CAUTION"),
    "SAFETY_GUIDE": ("주의사항 안내", "CAUTION+SAFE_USE"),
    "EVIDENCE": ("객관 근거 안내", "SOURCE+VERIFIED_FACT+BOUNDARY"),
    "SPEC_CTA": ("실측 정보·구매 안내", "SIZE_DIAGRAM+MEASUREMENTS+CTA"),
    "GUIDE_CTA": ("사용 방법·구매 안내", "STEP_BY_STEP+USE_SCENE+CTA"),
    "USE_CASE_CTA": ("사용 장면·구매 안내", "USE_CASES+CAPTIONS+CTA"),
    "CARE_CTA": ("관리 정보·구매 안내", "CARE+STORAGE+CTA"),
    "EVIDENCE_CTA": ("객관 근거·구매 안내", "SOURCE+VERIFIED_FACT+CTA"),
    "COMPONENTS_CTA": ("구성품·구매 안내", "COMPONENT_LIST+PACKAGE_IMAGE+CTA"),
    "OPTIONS_CTA": ("옵션·구매 안내", "OPTIONS+CURRENT_VARIANTS+CTA"),
    "SAFETY_CTA": ("주의사항·구매 안내", "CAUTION+SAFE_USE+CTA"),
}

CTA_ROLE_IDS = {
    role_id for role_id, (_, modules) in ALLOWED_ROLES.items() if "CTA" in modules.split("+")
}

# Backward-compatible import used by validate_generation_gate.py.  The full
# selected-role contract is enforced here; the approval gate only needs to check
# that these two universal roles reached the rendered review board.
EXPECTED_ROLES = {
    "FIRST": ("PROBLEM_HOOK",) + ALLOWED_ROLES["PROBLEM_HOOK"],
    "INTRO": ("PRODUCT_INTRO",) + ALLOWED_ROLES["PRODUCT_INTRO"],
}

UNIQUE_COLUMNS = {
    4: "고유 구매 질문",
    6: "INFO_ID",
    10: "SHOT_ID",
    11: "SCENE_ID",
    12: "LAYOUT_ID",
}

PAGE_COUNT_FIELD_LABELS = (
    "목표 장수",
    "정보 단위 수",
    "선정 장수",
    "장수 결정 근거",
    "삭제·병합 역할",
    "장수 결정 상태",
)

FUNCTIONAL_FIELD_LABELS = (
    "핵심 기능 소구",
    "기능 근거 Fact ID",
    "기능이 답하는 구매 불편",
    "디자인 보조 소구",
    "기능 우선 적용 장",
    "기능 없음 사유",
    "기능 우선 상태",
)

EMPTY_VALUES = {"", "미기록", "미정", "미확인", "작성 필요", "-"}


def normalize_project_number(value: str) -> str:
    if not value.isdigit() or not 1 <= int(value) <= 999:
        raise ValueError("project number must be between 001 and 999")
    return f"{int(value):03d}"


def normalize_cell(value: str) -> str:
    return re.sub(r"[\s`*_]+", "", value).casefold()


def table_page_entries(text: str) -> list[tuple[str, list[str]]]:
    entries: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and re.fullmatch(r"\d{1,2}", cells[0]):
            page = f"{int(cells[0]):02d}"
            entries.append((page, cells))
    return entries


def table_rows(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for page, cells in table_page_entries(text):
        rows.setdefault(page, cells)
    return rows


def labeled_field(text: str, label: str) -> str:
    match = re.search(
        rf"^{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)$", text, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def positive_integer(value: str, label: str, errors: list[str]) -> int | None:
    if not re.fullmatch(r"\d+", value.strip()):
        errors.append(f"{label} must be a positive integer")
        return None
    parsed = int(value)
    if parsed < 1:
        errors.append(f"{label} must be a positive integer")
        return None
    return parsed


def fact_ids(value: str) -> set[str]:
    return {item.upper() for item in re.findall(r"\bF\d{2,}\b", value, re.IGNORECASE)}


def ledger_fact_ids(skill_root: Path, project_no: str) -> set[str]:
    path = skill_root / "outputs" / project_no / "fact-ledger.md"
    if not path.is_file():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and re.fullmatch(r"F\d{2,}", cells[0], re.IGNORECASE):
            ids.add(cells[0].upper())
    return ids


def parse_priority_pages(value: str) -> set[str]:
    return {
        f"{int(item):02d}"
        for item in re.findall(r"(?<!\d)\d{1,2}(?!\d)", value)
    }


def validate_page_count_decision(
    text: str, rows: dict[str, list[str]]
) -> tuple[dict[str, str], list[str]]:
    fields = {label: labeled_field(text, label) for label in PAGE_COUNT_FIELD_LABELS}
    errors: list[str] = []

    for label, value in fields.items():
        if value.casefold() in EMPTY_VALUES:
            errors.append(f"page-count decision field is empty: {label}")

    target = positive_integer(fields["목표 장수"], "목표 장수", errors)
    information_units = positive_integer(
        fields["정보 단위 수"], "정보 단위 수", errors
    )
    selected = positive_integer(fields["선정 장수"], "선정 장수", errors)
    actual = len(rows)

    for label, value in (("목표 장수", target), ("선정 장수", selected)):
        if value is not None and not MIN_PAGES <= value <= MAX_PAGES:
            errors.append(f"{label} must be between {MIN_PAGES} and {MAX_PAGES}")
    if target is not None and selected is not None and target != selected:
        errors.append("목표 장수 must match 선정 장수 after the evidence-based decision")
    if selected is not None and selected != actual:
        errors.append(
            f"선정 장수 {selected} does not match the {actual} selected page rows"
        )
    if information_units is not None and selected is not None and information_units != selected:
        errors.append(
            "정보 단위 수 must equal 선정 장수; select one distinct information unit per page"
        )
    if fields["장수 결정 상태"] != "완료":
        errors.append("set '장수 결정 상태: 완료' only after page selection is final")

    return fields, errors


def validate_function_priority(
    skill_root: Path,
    project_no: str,
    text: str,
    rows: dict[str, list[str]],
) -> tuple[dict[str, str], list[str]]:
    fields = {label: labeled_field(text, label) for label in FUNCTIONAL_FIELD_LABELS}
    errors: list[str] = []

    for label, value in fields.items():
        if label == "기능 없음 사유":
            continue
        if value.casefold() in EMPTY_VALUES:
            errors.append(f"functional priority field is empty: {label}")

    if fields["기능 우선 상태"] != "완료":
        errors.append("set '기능 우선 상태: 완료' only after the functional priority gate is filled")

    function_value = fields["핵심 기능 소구"].strip()
    no_function = function_value == "없음"
    evidence_value = fields["기능 근거 Fact ID"].strip()
    pages_value = fields["기능 우선 적용 장"].strip()
    reason_value = fields["기능 없음 사유"].strip()

    if no_function:
        if evidence_value != "없음":
            errors.append("when 핵심 기능 소구 is '없음', 기능 근거 Fact ID must be '없음'")
        if pages_value != "없음":
            errors.append("when 핵심 기능 소구 is '없음', 기능 우선 적용 장 must be '없음'")
        if reason_value.casefold() in EMPTY_VALUES or reason_value == "없음":
            errors.append("record a concrete 기능 없음 사유 instead of inventing a feature")
        return fields, errors

    if reason_value not in EMPTY_VALUES and reason_value != "없음":
        errors.append("기능 없음 사유 must be '없음' when a 핵심 기능 소구 is present")

    source_ids = fact_ids(evidence_value)
    if not source_ids:
        errors.append("기능 근거 Fact ID must contain at least one Fact ID such as F01")
    else:
        known_ids = ledger_fact_ids(skill_root, project_no)
        missing_ids = sorted(source_ids - known_ids)
        if missing_ids:
            errors.append(
                "기능 근거 Fact ID is not present in fact-ledger.md: "
                + ", ".join(missing_ids)
            )

    priority_pages = parse_priority_pages(pages_value)
    if "01" not in priority_pages:
        errors.append("기능 우선 적용 장 must include page 01 so the problem hook starts with function")
    if not ({"02", "03"} & priority_pages):
        errors.append("기능 우선 적용 장 must include page 02 or 03 so the early explanation stays function-first")
    unknown_pages = sorted(priority_pages - set(rows))
    if unknown_pages:
        errors.append(
            "기능 우선 적용 장 contains pages outside the selected plan: "
            + ", ".join(unknown_pages)
        )

    owned_ids: set[str] = set()
    for page in priority_pages:
        cells = rows.get(page)
        if cells is not None and len(cells) > 5:
            owned_ids.update(fact_ids(cells[5]))
    if source_ids and not (source_ids & owned_ids):
        errors.append(
            "at least one 기능 우선 적용 장 must use a 기능 근거 Fact ID as PRIMARY_FACT"
        )

    if (
        fields["디자인 보조 소구"] != "없음"
        and normalize_cell(fields["디자인 보조 소구"]) == normalize_cell(function_value)
    ):
        errors.append("디자인 보조 소구 must be distinct from the 핵심 기능 소구")

    return fields, errors


def validate(skill_root: Path, project_no: str) -> dict[str, object]:
    path = skill_root / "outputs" / project_no / "plan-gate.md"
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "ok": False,
            "project": project_no,
            "path": str(path),
            "errors": [f"missing plan gate file: {path}"],
            "warnings": warnings,
        }

    text = path.read_text(encoding="utf-8")
    status = re.search(r"^검증 상태\s*:\s*(.+)$", text, re.MULTILINE)
    if not status or status.group(1).strip() != "완료":
        errors.append("set '검증 상태: 완료' only after the variable-page plan is filled")

    entries = table_page_entries(text)
    rows = table_rows(text)
    duplicate_pages = sorted(
        page for page in rows if sum(entry_page == page for entry_page, _ in entries) > 1
    )
    if duplicate_pages:
        errors.append("duplicate page rows: " + ", ".join(duplicate_pages))

    if not MIN_PAGES <= len(rows) <= MAX_PAGES:
        errors.append(f"selected page rows must be between {MIN_PAGES} and {MAX_PAGES}")
    expected_sequence = [f"{number:02d}" for number in range(1, len(rows) + 1)]
    if sorted(rows, key=lambda item: int(item)) != expected_sequence:
        errors.append(
            "page rows must be continuous from 01: expected "
            + ", ".join(expected_sequence)
            + "; found "
            + ", ".join(sorted(rows, key=lambda item: int(item)))
        )

    page_count_decision, page_count_errors = validate_page_count_decision(text, rows)
    errors.extend(page_count_errors)
    function_priority, function_errors = validate_function_priority(
        skill_root, project_no, text, rows
    )
    errors.extend(function_errors)

    ordered_pages = sorted(rows, key=lambda item: int(item))
    known_fact_ids = ledger_fact_ids(skill_root, project_no)
    product_intro_pages: list[str] = []
    for page in ordered_pages:
        cells = rows[page]
        if len(cells) < 15:
            errors.append(f"page {page} needs all 15 columns including INFO_ID")
            continue
        role_id = cells[1].strip()
        role_contract = ALLOWED_ROLES.get(role_id)
        if role_contract is None:
            errors.append(f"page {page} uses unsupported ROLE_ID '{role_id}'")
        else:
            expected_role, expected_modules = role_contract
            if normalize_cell(cells[2]) != normalize_cell(expected_role):
                errors.append(
                    f"page {page} role must be '{expected_role}', found '{cells[2]}'"
                )
            if cells[3].replace(" ", "") != expected_modules:
                errors.append(
                    f"page {page} required modules must be '{expected_modules}', found '{cells[3]}'"
                )
        if role_id == "PRODUCT_INTRO":
            product_intro_pages.append(page)

        for index, label in (
            (4, "고유 구매 질문"),
            (5, "PRIMARY_FACT"),
            (6, "INFO_ID"),
            (7, "ADVANTAGE_ID"),
            (8, "필수 시각 증거"),
            (9, "H1 핵심어"),
            (10, "SHOT_ID"),
            (11, "SCENE_ID"),
            (12, "LAYOUT_ID"),
            (13, "다음 장과 연결"),
            (14, "모션 역할"),
        ):
            if not cells[index].strip():
                errors.append(f"page {page} has empty {label}")
        if cells[6].strip() and not re.fullmatch(r"I\d{2,}", cells[6].strip(), re.IGNORECASE):
            errors.append(f"page {page} INFO_ID must use a value such as I01")
        primary_fact_ids = fact_ids(cells[5])
        if not primary_fact_ids:
            errors.append(f"page {page} PRIMARY_FACT must cite at least one allowed Fact ID")
        else:
            missing_primary_facts = sorted(primary_fact_ids - known_fact_ids)
            if missing_primary_facts:
                errors.append(
                    f"page {page} PRIMARY_FACT uses Fact IDs absent from the allowed-facts table: "
                    + ", ".join(missing_primary_facts)
                )

    if ordered_pages:
        first_page = ordered_pages[0]
        last_page = ordered_pages[-1]
        first_cells = rows[first_page]
        last_cells = rows[last_page]
        if len(first_cells) > 1 and first_cells[1].strip() != "PROBLEM_HOOK":
            errors.append("page 01 ROLE_ID must be PROBLEM_HOOK")
        if len(last_cells) > 3:
            final_role_id = last_cells[1].strip()
            final_modules = last_cells[3].replace(" ", "").split("+")
            if final_role_id not in CTA_ROLE_IDS or "CTA" not in final_modules:
                errors.append(
                    "the last page must own new information through a supported *_CTA role and include a CTA module"
                )
    if len(product_intro_pages) != 1:
        errors.append(
            "the selected plan must contain exactly one PRODUCT_INTRO page; found "
            + str(len(product_intro_pages))
        )

    for index, label in UNIQUE_COLUMNS.items():
        seen: dict[str, str] = {}
        for page in ordered_pages:
            cells = rows[page]
            if len(cells) <= index or not cells[index].strip():
                continue
            value = normalize_cell(cells[index])
            if value in seen:
                errors.append(
                    f"duplicate {label}: pages {seen[value]} and {page} use '{cells[index]}'"
                )
            else:
                seen[value] = page

    # The final information page may summarize its own fact in the CTA.  Every
    # earlier page, however, must own a distinct primary fact.
    seen_primary: dict[str, str] = {}
    for page in ordered_pages[:-1]:
        cells = rows[page]
        if len(cells) <= 5 or not cells[5].strip():
            continue
        value = normalize_cell(cells[5])
        if value in seen_primary:
            errors.append(
                f"duplicate PRIMARY_FACT on non-final pages: pages {seen_primary[value]} and {page} use '{cells[5]}'"
            )
        else:
            seen_primary[value] = page

    return {
        "ok": not errors,
        "project": project_no,
        "path": str(path),
        "rows": ordered_pages,
        "page_count_decision": page_count_decision,
        "function_priority": function_priority,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate evidence-sized page selection, allowed roles, and uniqueness."
    )
    parser.add_argument("project", help="Project number, for example 003 or 3")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()
    try:
        project_no = normalize_project_number(args.project)
    except ValueError as exc:
        parser.error(str(exc))

    skill_root = Path(__file__).resolve().parents[1]
    report = validate(skill_root, project_no)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"PLAN READY: project {project_no} ({len(report['rows'])} pages)")
    else:
        print(f"PLAN NOT READY: project {project_no}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
