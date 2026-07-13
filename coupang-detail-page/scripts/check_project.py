#!/usr/bin/env python3
"""Check whether a numbered project has enough verified input to generate pages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".avif"}
REQUIRED_FIELDS = (
    "상품명",
    "카테고리",
    "가장 중요한 기능적 구매 이유와 근거",
    "타깃 고객",
    "대표 불편",
    "사용 상황",
    "사용 방법",
    "구성품",
    "판매 구성 수량",
    "소재/재질",
    "색상",
    "실측값",
    "실측 사진 상태",
    "주의사항",
    "경쟁 제품 대비 검증된 차별점",
    "강조할 분위기",
    "객관적인 수치/인증/시험 정보",
    "사용하면 안 되는 표현",
)


def normalize_project_number(value: str) -> str:
    if not value.isdigit():
        raise ValueError("project number must contain digits only")
    number = int(value)
    if not 1 <= number <= 999:
        raise ValueError("project number must be between 001 and 999")
    return f"{number:03d}"


def field_value(text: str, label: str) -> str:
    match = re.search(
        rf"^{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)$", text, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def advantage_value(text: str, number: int) -> str:
    match = re.search(rf"^{number}\.[ \t]*([^\r\n]*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def image_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def research_rows(text: str) -> dict[str, list[list[str]]]:
    rows: dict[str, list[list[str]]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0] in {"동일 제품", "유사 제품", "상세 구조"}:
            rows.setdefault(cells[0], []).append(cells)
    return rows


def valid_research_location(value: str, *, allow_none: bool) -> bool:
    if allow_none and value == "검색 결과 없음":
        return True
    return bool(re.fullmatch(r"https?://\S+", value))


def manifest_roles(skill_root: Path, project_no: str) -> dict[str, str]:
    """Return local asset paths and explicit roles from asset-map.md when present."""

    path = skill_root / "outputs" / project_no / "asset-map.md"
    if not path.is_file():
        return {}
    roles: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if (
            len(cells) >= 4
            and re.fullmatch(r"A\d{2,}", cells[0], re.IGNORECASE)
            and cells[3]
            and not re.match(r"https?://", cells[3])
        ):
            roles[cells[3].lstrip("./")] = cells[1]
    return roles


def check(
    skill_root: Path, project_no: str, conversation_original_count: int = 0
) -> dict[str, object]:
    if conversation_original_count < 0:
        raise ValueError("conversation original count cannot be negative")
    if conversation_original_count > 5:
        raise ValueError(
            "conversation-only originals cannot exceed 5; copy extras locally or select at most 5"
        )
    input_root = skill_root / "inputs" / project_no
    info_path = input_root / "product-info.md"
    original_dir = input_root / "original-images"
    web_confirmed_dir = input_root / "web-confirmed"
    reference_dir = input_root / "real-references"
    output_root = skill_root / "outputs" / project_no
    research_path = output_root / "web-research.md"
    analysis_path = output_root / "detail-page-analysis.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not info_path.is_file():
        errors.append(f"missing product information file: {info_path}")
        text = ""
    else:
        text = info_path.read_text(encoding="utf-8")

    missing_fields = [label for label in REQUIRED_FIELDS if not field_value(text, label)]
    if missing_fields:
        errors.append("empty required fields: " + ", ".join(missing_fields))

    advantages = {
        number: advantage_value(text, number)
        for number in range(1, 4)
    }
    missing_advantages = [str(number) for number, value in advantages.items() if not value]
    if missing_advantages:
        errors.append("empty core advantages: " + ", ".join(missing_advantages))

    if not research_path.is_file():
        errors.append(f"missing required web research file: {research_path}")
    else:
        research_text = research_path.read_text(encoding="utf-8")
        research_date = field_value(research_text, "조사일")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", research_date):
            errors.append(f"web research needs an ISO 조사일 YYYY-MM-DD: {research_path}")
        if not field_value(research_text, "동일 제품 결론"):
            errors.append(f"web research needs a non-empty 동일 제품 결론: {research_path}")
        if field_value(research_text, "조사 상태") != "완료":
            errors.append(
                f"web research is not complete; set '조사 상태: 완료' after recording exact and similar product searches: {research_path}"
            )
        rows = research_rows(research_text)
        for row_type in ("동일 제품", "유사 제품"):
            candidates = rows.get(row_type, [])
            populated = [
                cells
                for cells in candidates
                if len(cells) >= 8
                and cells[1]
                and valid_research_location(cells[2], allow_none=True)
                and cells[3] in {"M0", "M1", "M2", "M3"}
                and cells[4] in {"E1", "E2", "E3", "E4"}
                and cells[5]
                and cells[6]
                and cells[7]
            ]
            if not populated:
                errors.append(
                    f"web research needs a complete '{row_type}' row with query, direct URL or exact '검색 결과 없음', M/E grades, use boundary, and excluded claims: {research_path}"
                )
        structure_rows = [
            cells
            for cells in rows.get("상세 구조", [])
            if len(cells) >= 8
            and cells[1]
            and valid_research_location(cells[2], allow_none=False)
            and cells[3] in {"M0", "M1", "M2", "M3"}
            and cells[4] in {"E1", "E2", "E3", "E4"}
            and cells[5]
            and cells[6]
            and cells[7]
        ]
        if len(structure_rows) < 3:
            errors.append(
                f"web research needs at least 3 populated '상세 구조' rows before planning: {research_path}"
            )
        elif len({cells[2] for cells in structure_rows}) < 3:
            errors.append(
                f"web research needs at least 3 distinct direct detail-page URLs: {research_path}"
            )

    if not analysis_path.is_file():
        errors.append(f"missing required detail-page analysis file: {analysis_path}")
    else:
        analysis_text = analysis_path.read_text(encoding="utf-8")
        if "## 공통 패턴" not in analysis_text or len(
            re.findall(r"https?://", analysis_text)
        ) < 3:
            errors.append(
                f"detail-page analysis needs a common-pattern section and at least 3 source URLs: {analysis_path}"
            )

    role_by_path = manifest_roles(skill_root, project_no)
    original_candidates = image_files(original_dir)
    web_confirmed = image_files(web_confirmed_dir)
    originals: list[Path] = []
    legacy_web_confirmed: list[Path] = []
    for candidate in original_candidates:
        relative = candidate.relative_to(skill_root).as_posix()
        role = role_by_path.get(relative, "")
        if role == "WEB_MATCH":
            web_confirmed.append(candidate)
            legacy_web_confirmed.append(candidate)
        else:
            originals.append(candidate)
    web_confirmed = sorted(set(web_confirmed))
    references = image_files(reference_dir)
    if not originals:
        errors.append(
            f"persist at least one original product image before HTML review or generation: {original_dir}"
        )
    if conversation_original_count:
        warnings.append(
            f"found {conversation_original_count} conversation-only original image(s), but they are provisional until copied into the numbered project and hashed in asset-map.md"
        )
    if legacy_web_confirmed:
        errors.append(
            "move WEB_MATCH files out of original-images/ into the numbered web-confirmed/ folder and update asset-map.md path/SHA256 before review or generation: "
            + ", ".join(path.name for path in legacy_web_confirmed)
        )
    if not references:
        warnings.append(
            f"no style reference images found; design will use product facts and requested mood: {reference_dir}"
        )

    return {
        "ok": not errors,
        "project": project_no,
        "product_info": str(info_path),
        "web_research": str(research_path),
        "detail_page_analysis": str(analysis_path),
        "original_images": [str(path) for path in originals],
        "web_confirmed_images": [str(path) for path in web_confirmed],
        "conversation_original_count": conversation_original_count,
        "style_references": [str(path) for path in references],
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify product-info.md and input images before image generation."
    )
    parser.add_argument("project", help="Project number, for example 001 or 1")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument(
        "--conversation-originals",
        type=int,
        default=0,
        metavar="COUNT",
        help="Diagnostic count of provisional conversation attachments; these do not replace persisted RAW files",
    )
    args = parser.parse_args()

    try:
        project_no = normalize_project_number(args.project)
    except ValueError as exc:
        parser.error(str(exc))

    skill_root = Path(__file__).resolve().parents[1]
    if not 0 <= args.conversation_originals <= 5:
        parser.error("--conversation-originals must be between 0 and 5")
    report = check(skill_root, project_no, args.conversation_originals)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"READY: project {project_no}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
    else:
        print(f"NOT READY: project {project_no}")
        for error in report["errors"]:
            print(f"- {error}")
        for warning in report["warnings"]:
            print(f"- warning: {warning}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
