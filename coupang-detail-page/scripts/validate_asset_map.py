#!/usr/bin/env python3
"""Validate RAW→evidence→reference principle→page lineage for a project."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ASSET_ROLES = {
    "RAW_PRIMARY",
    "RAW_DETAIL",
    "RAW_MEASUREMENT",
    "RAW_DEMO",
    "WEB_MATCH",
    "REF_STRUCTURE",
    "REF_MOOD",
    "REF_TYPO",
    "REF_PHOTO",
    "GENERATED",
}
REFERENCE_ROLES = {role for role in ASSET_ROLES if role.startswith("REF_")}
RAW_ROLES = {role for role in ASSET_ROLES if role.startswith("RAW_")}
LOCAL_ROLE_ROOTS = {
    "RAW_PRIMARY": ("inputs", "{project_no}", "original-images"),
    "RAW_DETAIL": ("inputs", "{project_no}", "original-images"),
    "RAW_MEASUREMENT": ("inputs", "{project_no}", "evidence"),
    "RAW_DEMO": ("inputs", "{project_no}", "evidence"),
    "WEB_MATCH": ("inputs", "{project_no}", "web-confirmed"),
    "REF_STRUCTURE": ("inputs", "{project_no}", "real-references"),
    "REF_MOOD": ("inputs", "{project_no}", "real-references"),
    "REF_TYPO": ("inputs", "{project_no}", "real-references"),
    "REF_PHOTO": ("inputs", "{project_no}", "real-references"),
    "GENERATED": ("outputs", "{project_no}"),
}
ORIGINS = {"USER", "OFFICIAL", "MARKETPLACE", "WEB", "AI"}
PRODUCT_MATCHES = {"USER", "M0", "M1", "M2", "M3"}
SOURCE_GRADES = {"USER", "E1", "E2", "E3", "E4"}
EVIDENCE_TYPES = {
    "OBSERVED_RAW",
    "USER_DECLARED_SPEC",
    "OFFICIAL_SPEC",
    "REAL_TEST",
    "WEB_SUPPORT",
}
CLAIM_CLASSES = {
    "IDENTITY",
    "STRUCTURE",
    "SPEC",
    "FUNCTION_NAME",
    "PERFORMANCE",
    "USE",
    "PACKAGE_VISIBLE",
    "PACKAGE_SALE",
    "SAFETY",
    "CONTEXT",
    "BOUNDARY",
}
STRENGTHS = {
    "DIRECT_OBSERVED",
    "USER_CONFIRMED",
    "USER_CONFIRMED_NO_PHOTO",
    "OFFICIAL_MODEL_MATCH",
    "TESTED",
    "SUPPORT_ONLY",
}
REFERENCE_TYPES = {"STRUCTURE", "MOOD", "TYPO", "PHOTO"}
DECISION_STAGES = {"NOTICE", "UNDERSTAND", "VERIFY", "FIT", "USE", "DECIDE"}
PROOF_MODES = {
    "RAW_CROP",
    "USER_DECLARATION",
    "OFFICIAL_DIAGRAM",
    "REAL_DEMO",
    "REAL_TEST",
    "AI_ILLUSTRATION",
    "COMPOSITE_LAYOUT",
}
EMPTY_VALUES = {"", "-", "미정", "미확인", "작성 필요"}
DIRECT_IMAGE_SUFFIXES = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}


def normalize_project_number(value: str) -> str:
    if not value.isdigit() or not 1 <= int(value) <= 999:
        raise ValueError("project number must be between 001 and 999")
    return f"{int(value):03d}"


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def rows_by_pattern(text: str, pattern: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = table_cells(line)
        if cells and re.fullmatch(pattern, cells[0], re.IGNORECASE):
            rows.append(cells)
    return rows


def table_dict_rows(text: str, required: set[str]) -> list[dict[str, str]]:
    """Return rows from the first Markdown table containing all required headers."""

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
        row_index = index + 2
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            cells = table_cells(lines[row_index])
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
            row_index += 1
        return rows
    return []


def labeled_field(text: str, label: str) -> str:
    match = re.search(
        rf"^{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)$", text, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def token_ids(value: str, prefix: str) -> set[str]:
    return {
        token.upper()
        for token in re.findall(rf"\b{re.escape(prefix)}\d{{2,}}\b", value, re.IGNORECASE)
    }


def fact_ids(value: str) -> set[str]:
    return token_ids(value, "F")


def asset_ids(value: str) -> set[str]:
    return token_ids(value, "A")


def proof_ids(value: str) -> set[str]:
    return token_ids(value, "P")


def principle_ids(value: str) -> set[str]:
    return {
        token.upper()
        for token in re.findall(r"\bRP\d{2,}\b", value, re.IGNORECASE)
    }


def source_tokens(value: str) -> set[str]:
    return set(re.findall(r"\b[A-Z][A-Z0-9_]*\b", value.upper()))


def page_ids(value: str) -> set[str]:
    return {f"{int(item):02d}" for item in re.findall(r"(?<!\d)\d{1,2}(?!\d)", value)}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nominal_role_root(skill_root: Path, project_no: str, role: str) -> Path | None:
    """Return the symlink-free nominal root authorized for an asset role."""

    parts = LOCAL_ROLE_ROOTS.get(role)
    if parts is None:
        return None
    return skill_root.resolve().joinpath(
        *(project_no if part == "{project_no}" else part for part in parts)
    )


def nominal_local_path(skill_root: Path, source: str) -> Path:
    """Build an absolute, dot-normalized path without resolving inner symlinks."""

    root_resolved = skill_root.resolve()
    source_path = Path(source)
    if not source_path.is_absolute():
        return Path(os.path.abspath(root_resolved / source_path))

    source_absolute = Path(os.path.abspath(source_path))
    root_absolute = Path(os.path.abspath(skill_root))
    try:
        relative_source = source_absolute.relative_to(root_absolute)
    except ValueError:
        return source_absolute
    return root_resolved / relative_source


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def ledger_ids(skill_root: Path, project_no: str) -> set[str]:
    path = skill_root / "outputs" / project_no / "fact-ledger.md"
    if not path.is_file():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = table_cells(line)
        if cells and re.fullmatch(r"F\d{2,}", cells[0], re.IGNORECASE):
            ids.add(cells[0].upper())
    return ids


def plan_rows(skill_root: Path, project_no: str) -> dict[str, list[str]]:
    path = skill_root / "outputs" / project_no / "plan-gate.md"
    if not path.is_file():
        return {}
    rows: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = table_cells(line)
        if cells and re.fullmatch(r"\d{1,2}", cells[0]):
            rows[f"{int(cells[0]):02d}"] = cells
    return rows


def normalize_text(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def valid_iso_date(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_direct_image_url(value: str) -> bool:
    """Return whether a source URL names an image object rather than an HTML page."""

    path = urlsplit(value).path.casefold()
    return any(path.endswith(suffix) for suffix in DIRECT_IMAGE_SUFFIXES)


def web_research_asset_links(
    skill_root: Path, project_no: str
) -> tuple[dict[str, str], list[str]]:
    """Read persisted web-asset → direct-source links from web-research.md."""

    path = skill_root / "outputs" / project_no / "web-research.md"
    if not path.is_file():
        return {}, [f"missing web research file for local web assets: {path}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    research_date = labeled_field(text, "조사일")
    if not valid_iso_date(research_date):
        errors.append("web-research.md needs a valid ISO 조사일 YYYY-MM-DD for asset lineage")
    rows = table_dict_rows(
        text,
        {
            "ASSET_ID",
            "URL 또는 검색 결과 없음",
        },
    )
    if not rows:
        return {}, errors + [
            "web-research.md search table needs an ASSET_ID column for downloaded web assets"
        ]

    links: dict[str, str] = {}
    for row in rows:
        raw_asset_id = row.get("ASSET_ID", "").strip().upper()
        if raw_asset_id in {"", "-", "NONE", "해당 없음"}:
            continue
        if not re.fullmatch(r"A\d{2,}", raw_asset_id):
            errors.append(
                "web-research.md must map exactly one ASSET_ID per canonical source row: "
                + raw_asset_id
            )
            continue
        asset_id = raw_asset_id
        location = row.get("URL 또는 검색 결과 없음", "").strip().strip("<>")
        if not re.fullmatch(r"https?://\S+", location, re.IGNORECASE):
            errors.append(
                "web-research.md ASSET_ID rows must cite a direct http(s) source URL: "
                + asset_id
            )
            continue
        if asset_id in links:
            errors.append(
                f"web-research.md maps {asset_id} more than once; keep one canonical source row"
            )
        else:
            links[asset_id] = location
    return links, errors


def validate(skill_root: Path, project_no: str) -> dict[str, object]:
    path = skill_root / "outputs" / project_no / "asset-map.md"
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "ok": False,
            "project": project_no,
            "path": str(path),
            "errors": [f"missing asset map file: {path}"],
            "warnings": warnings,
        }

    text = path.read_text(encoding="utf-8")
    if labeled_field(text, "검증 상태") != "완료":
        errors.append("set '검증 상태: 완료' only after all four lineage tables are filled")

    asset_row_list = rows_by_pattern(text, r"A\d{2,}")
    evidence_row_list = rows_by_pattern(text, r"P\d{2,}")
    principle_row_list = rows_by_pattern(text, r"RP\d{2,}")
    page_row_list = rows_by_pattern(text, r"\d{1,2}")

    assets: dict[str, list[str]] = {}
    local_web_asset_ids: set[str] = set()
    for cells in asset_row_list:
        asset_id = cells[0].upper()
        if asset_id in assets:
            errors.append(f"duplicate ASSET_ID: {asset_id}")
            continue
        assets[asset_id] = cells
        if len(cells) < 11:
            errors.append(f"asset {asset_id} needs all 11 columns")
            continue
        _, role, origin, source, match, grade, sha256, observed, allowed, forbidden, status = cells[:11]
        if role not in ASSET_ROLES:
            errors.append(f"asset {asset_id} has unsupported ROLE '{role}'")
        if origin not in ORIGINS:
            errors.append(f"asset {asset_id} has unsupported ORIGIN '{origin}'")
        if match not in PRODUCT_MATCHES:
            errors.append(f"asset {asset_id} has unsupported PRODUCT_MATCH '{match}'")
        if grade not in SOURCE_GRADES:
            errors.append(f"asset {asset_id} has unsupported SOURCE_GRADE '{grade}'")
        for label, value in (
            ("PATH_OR_URL", source),
            ("OBSERVABLE_FACTS", observed),
            ("ALLOWED_USE", allowed),
            ("FORBIDDEN_TRANSFER", forbidden),
        ):
            if value.casefold() in EMPTY_VALUES:
                errors.append(f"asset {asset_id} has empty {label}")
        if status != "READY":
            errors.append(f"asset {asset_id} STATUS must be READY or the asset must be omitted")

        is_url = bool(re.match(r"https?://", source))
        if role in RAW_ROLES:
            if origin != "USER" or match != "USER" or grade != "USER":
                errors.append(
                    f"RAW asset {asset_id} must use ORIGIN=USER, PRODUCT_MATCH=USER, SOURCE_GRADE=USER"
                )
            if is_url:
                errors.append(f"RAW asset {asset_id} must be a persisted local user file, not a URL")
        if role == "WEB_MATCH":
            if origin not in {"OFFICIAL", "MARKETPLACE", "WEB"}:
                errors.append(
                    f"WEB_MATCH asset {asset_id} must come from OFFICIAL, MARKETPLACE, or WEB"
                )
            if match not in {"M1", "M2"} or grade not in {"E1", "E2", "E3"}:
                errors.append(
                    f"WEB_MATCH asset {asset_id} must be M1/M2 with E1/E2/E3; similar M3 material belongs in REF_*"
                )
        if role in REFERENCE_ROLES and origin == "AI":
            errors.append(
                f"reference asset {asset_id} cannot use ORIGIN=AI; record generated material as GENERATED"
            )
        if role == "GENERATED":
            if origin != "AI":
                errors.append(f"GENERATED asset {asset_id} must use ORIGIN=AI")
        if is_url:
            if sha256 != "REMOTE":
                errors.append(f"remote asset {asset_id} SHA256 must be REMOTE")
        else:
            root_resolved = skill_root.resolve()
            local_nominal = nominal_local_path(skill_root, source)
            role_nominal = nominal_role_root(skill_root, project_no, role)
            path_is_authorized = True
            local_path: Path | None = None
            role_root: Path | None = None
            if role_nominal is None:
                errors.append(
                    f"asset {asset_id} has no canonical local root for unsupported ROLE '{role}'"
                )
                path_is_authorized = False
            else:
                try:
                    role_root = role_nominal.resolve()
                except (OSError, RuntimeError) as exc:
                    errors.append(
                        f"asset {asset_id} canonical role root cannot be resolved safely: {exc}"
                    )
                    path_is_authorized = False
                else:
                    if role_root != role_nominal:
                        errors.append(
                            f"asset {asset_id} canonical role root contains a symlink: {role_nominal}"
                        )
                        path_is_authorized = False
                    if not is_within(role_root, root_resolved):
                        errors.append(
                            f"asset {asset_id} canonical role root escapes the skill root: {role_root}"
                        )
                        path_is_authorized = False

            try:
                local_path = local_nominal.resolve()
            except (OSError, RuntimeError) as exc:
                errors.append(
                    f"asset {asset_id} local path cannot be resolved safely: {source}: {exc}"
                )
                path_is_authorized = False
            else:
                if local_path != local_nominal:
                    errors.append(
                        f"asset {asset_id} local path contains a symlink component: {source}"
                    )
                    path_is_authorized = False

            if local_path is not None and not is_within(local_path, root_resolved):
                errors.append(f"asset {asset_id} local path escapes the skill root: {source}")
                path_is_authorized = False
            if (
                local_path is not None
                and role_root is not None
                and not is_within(local_path, role_root)
            ):
                expected = (
                    role_root.relative_to(root_resolved)
                    if is_within(role_root, root_resolved)
                    else role_root
                )
                errors.append(
                    f"{role} asset {asset_id} must resolve under its canonical role root {expected}/"
                )
                path_is_authorized = False

            # Fail closed: never inspect or hash a file until both the skill-root and
            # role-root boundaries have passed after resolving '..' and symlinks.
            if path_is_authorized and local_path is not None and not local_path.is_file():
                errors.append(f"asset {asset_id} local file does not exist: {source}")
            elif (
                path_is_authorized
                and local_path is not None
                and not re.fullmatch(r"[0-9a-f]{64}", sha256)
            ):
                errors.append(f"asset {asset_id} needs a lowercase 64-character SHA256")
            elif path_is_authorized and local_path is not None:
                actual = file_sha256(local_path)
                if actual != sha256:
                    errors.append(f"asset {asset_id} SHA256 mismatch: expected {sha256}, found {actual}")
            if (
                role == "WEB_MATCH" or role in REFERENCE_ROLES
            ) and origin in {"OFFICIAL", "MARKETPLACE", "WEB"}:
                local_web_asset_ids.add(asset_id)

    if local_web_asset_ids:
        research_links, research_errors = web_research_asset_links(
            skill_root, project_no
        )
        errors.extend(research_errors)
        missing_research_links = sorted(local_web_asset_ids - set(research_links))
        if missing_research_links:
            errors.append(
                "local WEB_MATCH/REF assets need a direct URL row and ASSET_ID in "
                "web-research.md: " + ", ".join(missing_research_links)
            )
        dangling_research_links = sorted(set(research_links) - set(assets))
        if dangling_research_links:
            errors.append(
                "web-research.md maps unknown ASSET_ID values: "
                + ", ".join(dangling_research_links)
            )
        wrong_role_links = sorted(
            asset_id
            for asset_id in set(research_links) & set(assets)
            if len(assets[asset_id]) > 1
            and assets[asset_id][1] != "WEB_MATCH"
            and assets[asset_id][1] not in REFERENCE_ROLES
        )
        if wrong_role_links:
            errors.append(
                "web-research.md ASSET_ID links may identify only WEB_MATCH/REF assets: "
                + ", ".join(wrong_role_links)
            )

        direct_image_sources: dict[str, list[tuple[str, str]]] = {}
        for asset_id in sorted(local_web_asset_ids & set(research_links)):
            source_url = research_links[asset_id]
            asset_row = assets.get(asset_id, [])
            asset_sha = asset_row[6] if len(asset_row) > 6 else ""
            if is_direct_image_url(source_url) and re.fullmatch(
                r"[0-9a-f]{64}", asset_sha
            ):
                direct_image_sources.setdefault(source_url, []).append(
                    (asset_id, asset_sha)
                )
        for source_url, source_assets in direct_image_sources.items():
            if len({sha for _, sha in source_assets}) > 1:
                errors.append(
                    "different local SHA256 assets cannot share one direct image URL: "
                    + source_url
                    + " -> "
                    + ", ".join(
                        f"{asset_id}={sha}" for asset_id, sha in source_assets
                    )
                )

    ledger_path = skill_root / "outputs" / project_no / "fact-ledger.md"
    ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.is_file() else ""
    known_fact_ids = ledger_ids(skill_root, project_no)
    manifest_rows = table_dict_rows(ledger_text, {"장", "근거 Fact ID"})
    manifest_facts: dict[str, set[str]] = {}
    manifest_info_ids: dict[str, str] = {}
    for row in manifest_rows:
        raw_page = row.get("장", "")
        if not raw_page.isdigit():
            continue
        page = f"{int(raw_page):02d}"
        if page in manifest_facts:
            errors.append(f"duplicate approved copy manifest page: {page}")
            continue
        row_fact_ids = fact_ids(row.get("근거 Fact ID", ""))
        manifest_facts[page] = row_fact_ids
        manifest_info_ids[page] = row.get("INFO_ID", "").strip().upper()
        if not row_fact_ids:
            errors.append(f"copy manifest page {page} needs at least one Fact ID")
        missing_manifest_facts = sorted(row_fact_ids - known_fact_ids)
        if missing_manifest_facts:
            errors.append(
                f"copy manifest page {page} uses unknown Fact IDs: {', '.join(missing_manifest_facts)}"
            )
    evidence: dict[str, list[str]] = {}
    evidence_facts: dict[str, set[str]] = {}
    evidence_sources: dict[str, set[str]] = {}
    evidence_types: dict[str, str] = {}
    evidence_strengths: dict[str, str] = {}
    evidence_claim_classes: dict[str, str] = {}
    for cells in evidence_row_list:
        proof_id = cells[0].upper()
        if proof_id in evidence:
            errors.append(f"duplicate PROOF_ID: {proof_id}")
            continue
        evidence[proof_id] = cells
        if len(cells) < 10:
            errors.append(f"proof {proof_id} needs all 10 columns")
            continue
        _, facts, claim_class, evidence_type, sources, strength, sku_scope, allowed, forbidden, status = cells[:10]
        row_facts = fact_ids(facts)
        row_assets = asset_ids(sources)
        row_source_tokens = source_tokens(sources)
        evidence_facts[proof_id] = row_facts
        evidence_sources[proof_id] = row_assets
        evidence_types[proof_id] = evidence_type
        evidence_strengths[proof_id] = strength
        evidence_claim_classes[proof_id] = claim_class
        if not row_facts:
            errors.append(f"proof {proof_id} needs at least one Fact ID")
        missing_facts = sorted(row_facts - known_fact_ids)
        if missing_facts:
            errors.append(f"proof {proof_id} uses unknown Fact IDs: {', '.join(missing_facts)}")
        if claim_class not in CLAIM_CLASSES:
            errors.append(f"proof {proof_id} has unsupported CLAIM_CLASS '{claim_class}'")
        if evidence_type not in EVIDENCE_TYPES:
            errors.append(f"proof {proof_id} has unsupported EVIDENCE_TYPE '{evidence_type}'")
        if strength not in STRENGTHS:
            errors.append(f"proof {proof_id} has unsupported STRENGTH '{strength}'")
        for label, value in (
            ("SKU_OPTION_SCOPE", sku_scope),
            ("ALLOWED_COPY", allowed),
            ("FORBIDDEN_EXPANSION", forbidden),
        ):
            if value.casefold() in EMPTY_VALUES:
                errors.append(f"proof {proof_id} has empty {label}")
        if status != "APPROVED":
            errors.append(f"proof {proof_id} STATUS must be APPROVED")
        if evidence_type == "USER_DECLARED_SPEC":
            if "PRODUCT_INFO" not in row_source_tokens:
                errors.append(f"proof {proof_id} USER_DECLARED_SPEC must cite PRODUCT_INFO")
        elif not row_assets:
            errors.append(f"proof {proof_id} must cite at least one ASSET_ID")
        missing_assets = sorted(row_assets - set(assets))
        if missing_assets:
            errors.append(f"proof {proof_id} cites unknown assets: {', '.join(missing_assets)}")
        for source_id in row_assets & set(assets):
            source_role = assets[source_id][1] if len(assets[source_id]) > 1 else ""
            if source_role in REFERENCE_ROLES or source_role == "GENERATED":
                errors.append(f"proof {proof_id} cannot use {source_role} asset {source_id} as evidence")
            if evidence_type == "WEB_SUPPORT" and source_role == "WEB_MATCH":
                source_match = assets[source_id][4] if len(assets[source_id]) > 4 else ""
                source_grade = assets[source_id][5] if len(assets[source_id]) > 5 else ""
                if claim_class in {"SPEC", "PERFORMANCE", "PACKAGE_SALE", "SAFETY"} and (
                    source_match != "M1" or source_grade not in {"E1", "E2"}
                ):
                    errors.append(
                        f"proof {proof_id} needs M1+E1/E2 for {claim_class}; {source_id} is {source_match}+{source_grade}"
                    )
        source_roles = {
            assets[source_id][1]
            for source_id in row_assets & set(assets)
            if len(assets[source_id]) > 1
        }
        if evidence_type == "OBSERVED_RAW":
            if not row_assets or not source_roles or not source_roles.issubset(RAW_ROLES):
                errors.append(f"proof {proof_id} OBSERVED_RAW must cite only RAW_* assets")
            if strength != "DIRECT_OBSERVED":
                errors.append(f"proof {proof_id} OBSERVED_RAW requires DIRECT_OBSERVED strength")
        elif evidence_type == "USER_DECLARED_SPEC":
            if strength not in {"USER_CONFIRMED", "USER_CONFIRMED_NO_PHOTO"}:
                errors.append(
                    f"proof {proof_id} USER_DECLARED_SPEC requires USER_CONFIRMED or USER_CONFIRMED_NO_PHOTO"
                )
        elif evidence_type == "OFFICIAL_SPEC":
            if strength != "OFFICIAL_MODEL_MATCH":
                errors.append(f"proof {proof_id} OFFICIAL_SPEC requires OFFICIAL_MODEL_MATCH strength")
            for source_id in row_assets & set(assets):
                source_row = assets[source_id]
                if not (
                    len(source_row) >= 6
                    and source_row[1] == "WEB_MATCH"
                    and source_row[2] == "OFFICIAL"
                    and source_row[4] == "M1"
                    and source_row[5] == "E1"
                ):
                    errors.append(
                        f"proof {proof_id} OFFICIAL_SPEC source {source_id} must be OFFICIAL WEB_MATCH M1+E1"
                    )
        elif evidence_type == "REAL_TEST":
            if "RAW_DEMO" not in source_roles:
                errors.append(f"proof {proof_id} REAL_TEST must cite a RAW_DEMO asset")
            if strength != "TESTED":
                errors.append(f"proof {proof_id} REAL_TEST requires TESTED strength")
        elif evidence_type == "WEB_SUPPORT":
            if not row_assets or not source_roles or not source_roles.issubset({"WEB_MATCH"}):
                errors.append(f"proof {proof_id} WEB_SUPPORT must cite only WEB_MATCH assets")
            if strength not in {"SUPPORT_ONLY", "OFFICIAL_MODEL_MATCH"}:
                errors.append(
                    f"proof {proof_id} WEB_SUPPORT requires SUPPORT_ONLY or OFFICIAL_MODEL_MATCH strength"
                )
        if claim_class == "PACKAGE_SALE" and evidence_type == "OBSERVED_RAW":
            errors.append(f"proof {proof_id} cannot infer sales package quantity from visible RAW count")
        if claim_class == "PERFORMANCE" and evidence_type not in {"REAL_TEST", "OFFICIAL_SPEC"}:
            errors.append(f"proof {proof_id} PERFORMANCE needs REAL_TEST or OFFICIAL_SPEC")

    principles: dict[str, list[str]] = {}
    principle_targets: dict[str, set[str]] = {}
    for cells in principle_row_list:
        principle_id = cells[0].upper()
        if principle_id in principles:
            errors.append(f"duplicate REF_PRINCIPLE_ID: {principle_id}")
            continue
        principles[principle_id] = cells
        if len(cells) < 8:
            errors.append(f"reference principle {principle_id} needs all 8 columns")
            continue
        _, asset_id, ref_type, abstract, target_pages, do_not_copy, status, rejection = cells[:8]
        asset_id = asset_id.upper()
        targets = page_ids(target_pages)
        principle_targets[principle_id] = targets
        if asset_id not in assets:
            errors.append(f"reference principle {principle_id} cites unknown asset {asset_id}")
        elif len(assets[asset_id]) > 1 and assets[asset_id][1] not in REFERENCE_ROLES:
            errors.append(f"reference principle {principle_id} asset {asset_id} is not a REF_* asset")
        if ref_type not in REFERENCE_TYPES:
            errors.append(f"reference principle {principle_id} has unsupported REFERENCE_TYPE '{ref_type}'")
        if abstract.casefold() in EMPTY_VALUES or do_not_copy.casefold() in EMPTY_VALUES:
            errors.append(f"reference principle {principle_id} needs an abstract principle and DO_NOT_COPY boundary")
        if status not in {"USED", "REJECTED"}:
            errors.append(f"reference principle {principle_id} STATUS must be USED or REJECTED")
        if status == "USED" and not targets:
            errors.append(f"used reference principle {principle_id} needs TARGET_PAGE_IDS")
        if status == "REJECTED" and rejection.casefold() in EMPTY_VALUES:
            errors.append(f"rejected reference principle {principle_id} needs REJECTION_REASON")

    plan = plan_rows(skill_root, project_no)
    pages: dict[str, list[str]] = {}
    page_facts: dict[str, set[str]] = {}
    used_proofs: dict[str, str] = {}
    exclusive_gains: dict[str, str] = {}
    drop_tests: dict[str, str] = {}
    for cells in page_row_list:
        page = f"{int(cells[0]):02d}"
        if page in pages:
            errors.append(f"duplicate page source row: {page}")
            continue
        pages[page] = cells
        if len(cells) < 11:
            errors.append(f"page {page} source contract needs all 11 columns")
            continue
        _, info_id, stage, raw_assets, ref_principles, proof_id, facts, proof_mode, gain, drop_test, boundary = cells[:11]
        info_id = info_id.upper()
        proof_id = proof_id.upper()
        row_raw_assets = asset_ids(raw_assets)
        row_principles = principle_ids(ref_principles)
        row_facts = fact_ids(facts)
        page_facts[page] = row_facts
        plan_cells = plan.get(page)
        if plan_cells is None:
            errors.append(f"page {page} exists in asset-map.md but not plan-gate.md")
        elif len(plan_cells) > 6:
            plan_info = plan_cells[6].strip().upper()
            plan_facts = fact_ids(plan_cells[5])
            if info_id != plan_info:
                errors.append(f"page {page} INFO_ID mismatch: asset map {info_id}, plan {plan_info}")
            if row_facts != plan_facts:
                errors.append(
                    f"page {page} PRIMARY_FACT_IDS must match plan-gate.md: asset map {sorted(row_facts)}, plan {sorted(plan_facts)}"
                )
        if not re.fullmatch(r"I\d{2,}", info_id):
            errors.append(f"page {page} INFO_ID must look like I01")
        if stage not in DECISION_STAGES:
            errors.append(f"page {page} has unsupported DECISION_STAGE '{stage}'")
        if raw_assets != "NO_PRODUCT" and not row_raw_assets:
            errors.append(f"page {page} needs RAW_ASSET_IDS or NO_PRODUCT")
        if raw_assets == "NO_PRODUCT" and page != "01":
            errors.append(f"NO_PRODUCT is allowed only for page 01 problem imagery")
        missing_raw = sorted(row_raw_assets - set(assets))
        if missing_raw:
            errors.append(f"page {page} cites unknown RAW assets: {', '.join(missing_raw)}")
        for raw_id in row_raw_assets & set(assets):
            role = assets[raw_id][1] if len(assets[raw_id]) > 1 else ""
            if role not in RAW_ROLES:
                errors.append(
                    f"page {page} RAW_ASSET_IDS must contain persisted RAW_* assets, not {role} asset {raw_id}"
                )
        if ref_principles != "NONE" and not row_principles:
            errors.append(f"page {page} REF_PRINCIPLE_IDS must cite RP IDs or NONE")
        missing_principles = sorted(row_principles - set(principles))
        if missing_principles:
            errors.append(f"page {page} cites unknown reference principles: {', '.join(missing_principles)}")
        for principle_id in row_principles & set(principles):
            if page not in principle_targets.get(principle_id, set()):
                errors.append(f"reference principle {principle_id} does not target page {page}")
        if proof_id not in evidence:
            errors.append(f"page {page} cites unknown PROOF_ID {proof_id}")
        else:
            missing_proof_facts = row_facts - evidence_facts.get(proof_id, set())
            if missing_proof_facts:
                errors.append(
                    f"page {page} PROOF_ID {proof_id} does not cover PRIMARY_FACT_IDS: {', '.join(sorted(missing_proof_facts))}"
                )
        if proof_id in used_proofs:
            errors.append(f"duplicate PROOF_ID across pages {used_proofs[proof_id]} and {page}: {proof_id}")
        else:
            used_proofs[proof_id] = page
        if proof_mode not in PROOF_MODES:
            errors.append(f"page {page} has unsupported PROOF_MODE '{proof_mode}'")
        elif proof_id in evidence:
            evidence_type = evidence_types.get(proof_id, "")
            source_roles = {
                assets[source_id][1]
                for source_id in evidence_sources.get(proof_id, set()) & set(assets)
                if len(assets[source_id]) > 1
            }
            if proof_mode == "RAW_CROP" and evidence_type != "OBSERVED_RAW":
                errors.append(f"page {page} RAW_CROP requires OBSERVED_RAW evidence")
            if proof_mode in {"RAW_CROP", "REAL_DEMO", "REAL_TEST"} and not (
                row_raw_assets & evidence_sources.get(proof_id, set())
            ):
                errors.append(
                    f"page {page} {proof_mode} must use a RAW_ASSET_ID cited by its proof"
                )
            if proof_mode == "USER_DECLARATION" and evidence_type != "USER_DECLARED_SPEC":
                errors.append(f"page {page} USER_DECLARATION requires USER_DECLARED_SPEC evidence")
            if proof_mode == "OFFICIAL_DIAGRAM" and evidence_type != "OFFICIAL_SPEC":
                errors.append(f"page {page} OFFICIAL_DIAGRAM requires OFFICIAL_SPEC evidence")
            if proof_mode == "REAL_DEMO" and not (
                evidence_type == "OBSERVED_RAW" and "RAW_DEMO" in source_roles
            ):
                errors.append(f"page {page} REAL_DEMO requires OBSERVED_RAW evidence from RAW_DEMO")
            if proof_mode == "REAL_TEST" and not (
                evidence_type == "REAL_TEST" and "RAW_DEMO" in source_roles
            ):
                errors.append(f"page {page} REAL_TEST requires REAL_TEST evidence from RAW_DEMO")
            if (
                proof_mode == "AI_ILLUSTRATION"
                and evidence_claim_classes.get(proof_id) == "PERFORMANCE"
            ):
                errors.append(f"page {page} AI_ILLUSTRATION cannot serve a PERFORMANCE claim")
        for label, value, registry in (
            ("EXCLUSIVE_GAIN", gain, exclusive_gains),
            ("DROP_TEST", drop_test, drop_tests),
        ):
            normalized = normalize_text(value)
            if not normalized:
                errors.append(f"page {page} has empty {label}")
            elif normalized in registry:
                errors.append(f"duplicate {label}: pages {registry[normalized]} and {page}")
            else:
                registry[normalized] = page
        if boundary.casefold() in EMPTY_VALUES:
            errors.append(f"page {page} has empty CLAIM_BOUNDARY")

    plan_pages = set(plan)
    source_pages = set(pages)
    if source_pages != plan_pages:
        missing = sorted(plan_pages - source_pages)
        extra = sorted(source_pages - plan_pages)
        if missing:
            errors.append("asset-map.md is missing selected pages: " + ", ".join(missing))
        if extra:
            errors.append("asset-map.md has unselected pages: " + ", ".join(extra))

    manifest_pages = set(manifest_facts)
    if manifest_pages != source_pages:
        missing = sorted(source_pages - manifest_pages)
        extra = sorted(manifest_pages - source_pages)
        if missing:
            errors.append("copy manifest is missing selected pages: " + ", ".join(missing))
        if extra:
            errors.append("copy manifest has unselected pages: " + ", ".join(extra))
    for page in sorted(source_pages & manifest_pages):
        if manifest_facts[page] != page_facts.get(page, set()):
            errors.append(
                f"copy manifest Fact IDs must match page {page} source contract: "
                f"manifest {sorted(manifest_facts[page])}, source {sorted(page_facts.get(page, set()))}"
            )
        manifest_info = manifest_info_ids.get(page, "")
        if manifest_info and len(pages.get(page, [])) > 1:
            source_info = pages[page][1].strip().upper()
            if manifest_info != source_info:
                errors.append(
                    f"copy manifest INFO_ID mismatch on page {page}: {manifest_info} vs {source_info}"
                )

    ordered_pages = sorted(page_facts)
    for index, page_a in enumerate(ordered_pages):
        for page_b in ordered_pages[index + 1 :]:
            facts_a = page_facts[page_a]
            facts_b = page_facts[page_b]
            union = facts_a | facts_b
            if not union:
                continue
            jaccard = len(facts_a & facts_b) / len(union)
            if jaccard > 0.33:
                errors.append(
                    f"page Fact-set overlap is too high: {page_a} vs {page_b} Jaccard={jaccard:.2f}"
                )

    used_assets = set().union(*(asset_ids(cells[3]) for cells in pages.values() if len(cells) > 3))
    used_assets |= set().union(*(evidence_sources.values()), set())
    used_ref_assets = {
        cells[1].upper()
        for principle_id, cells in principles.items()
        if len(cells) > 6 and cells[6] == "USED"
    }
    used_assets |= used_ref_assets
    unused_ready = sorted(set(assets) - used_assets)
    if unused_ready:
        warnings.append("READY assets not used by an approved page lineage: " + ", ".join(unused_ready))

    return {
        "ok": not errors,
        "project": project_no,
        "path": str(path),
        "assets": sorted(assets),
        "proofs": sorted(evidence),
        "reference_principles": sorted(principles),
        "pages": sorted(pages),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate product asset, evidence, reference-principle, and page lineage."
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
        print(
            f"ASSET LINEAGE READY: project {project_no} "
            f"({len(report['assets'])} assets, {len(report['pages'])} pages)"
        )
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
    else:
        print(f"ASSET LINEAGE NOT READY: project {project_no}")
        for error in report["errors"]:
            print(f"- {error}")
        for warning in report["warnings"]:
            print(f"- warning: {warning}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
