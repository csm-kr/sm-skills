#!/usr/bin/env python3
"""Block static or motion generation until recorded user approvals are complete."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import html as html_lib
import json
import re
import sys
from pathlib import Path

from build_plan_review import planning_digest, planning_files
from check_project import check as check_project
from comfyui_receipt import (
    RECEIPT_SCHEMA,
    RECEIPT_TOOL,
    comfy_workflow_kind,
    connected_receipt,
    endpoint_kind,
    normalize_endpoint,
    project_relative_file,
    receipt_id_for,
)
from validate_asset_map import validate as validate_asset_map
from validate_motion import validate as validate_motion
from validate_plan import (
    EXPECTED_ROLES,
    normalize_project_number,
    table_rows,
    validate as validate_plan,
)
from validate_production_docs import validate as validate_production_docs


STATIC_SCOPES = {
    "STATIC_ONLY",
    "STATIC_PLUS_GIF",
    "STATIC_PLUS_VIDEO",
    "STATIC_PLUS_GIF_VIDEO",
    "STATIC_PLUS_MOTION_HANDOFF",
}
MOTION_SCOPES = {"STATIC_PLUS_GIF", "STATIC_PLUS_VIDEO", "STATIC_PLUS_GIF_VIDEO"}
HANDOFF_SCOPES = {"STATIC_PLUS_MOTION_HANDOFF"}
COMFY_STATES = {"CONNECTED", "WORKFLOW_PROVIDED", "HANDOFF_ONLY", "NOT_REQUIRED"}
RECEIPT_COMFY_STATES = {"CONNECTED", "WORKFLOW_PROVIDED"}
LIVE_COMFY_STATES = {"CONNECTED"}
CONNECTED_RECEIPT_MAX_AGE = timedelta(hours=24)
RECEIPT_FUTURE_TOLERANCE = timedelta(minutes=5)
APPROVAL_TIMEZONE = timezone(timedelta(hours=9), "Asia/Seoul")
GATE_LABELS = (
    "프로젝트 번호",
    "기획 리뷰 HTML",
    "기획 검토 상태",
    "사용자 승인 기록",
    "승인한 기획 소스 해시",
    "승인한 리뷰 HTML 해시",
    "제작 범위",
    "선정 모션 ID",
    "환경 선택 기록",
    "ComfyUI 상태",
    "ComfyUI 증빙 JSON",
    "정적 이미지 생성 승인",
    "GIF·영상 생성 승인",
    "최종 생성 승인 기록",
)


def clean(value: str) -> str:
    return value.strip().strip("`").replace("**", "").strip()


def fields(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for label in GATE_LABELS:
        match = re.search(
            rf"^{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)$",
            text,
            re.MULTILINE,
        )
        result[label] = clean(match.group(1)) if match else ""
    return result


def validate_gate_field_shape(text: str) -> list[str]:
    """Require one unambiguous top-level value for every generation-gate field."""

    errors: list[str] = []
    for label in GATE_LABELS:
        count = len(
            re.findall(rf"^{re.escape(label)}[ \t]*:", text, re.MULTILINE)
        )
        if count != 1:
            errors.append(
                f"generation-gate.md must contain exactly one '{label}:' field; found {count}"
            )
    return errors


def selected_motion_ids(value: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"\bmotion-\d{2}\b", value, re.IGNORECASE)
    }


def canonical_motion_selection(value: str) -> bool:
    if value == "해당 없음":
        return True
    if not re.fullmatch(r"motion-\d{2}(?:,[ \t]*motion-\d{2})*", value):
        return False
    tokens = re.findall(r"motion-\d{2}", value)
    return len(tokens) == len(set(tokens))


def parse_iso_day(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def valid_iso_day(value: str) -> bool:
    return parse_iso_day(value) is not None


def motion_record_token(selected_ids: set[str]) -> str:
    return ",".join(sorted(selected_ids)) if selected_ids else "NONE"


def validate_approval_records(
    gate_fields: dict[str, str], scope: str, selected_ids: set[str], comfy: str
) -> list[str]:
    """Reject empty, contradictory, or free-text approval records."""

    errors: list[str] = []
    approval_days = {}
    plan_match = re.fullmatch(
        r"(?P<date>\d{4}-\d{2}-\d{2}) · APPROVE_PLAN · ANSWER=1",
        gate_fields["사용자 승인 기록"],
    )
    if not plan_match or not valid_iso_day(plan_match.group("date")):
        errors.append(
            "user approval record must use 'YYYY-MM-DD · APPROVE_PLAN · ANSWER=1'"
        )
    else:
        approval_days["plan"] = parse_iso_day(plan_match.group("date"))

    motion_token = motion_record_token(selected_ids)
    environment_match = re.fullmatch(
        r"(?P<date>\d{4}-\d{2}-\d{2}) · SELECT_ENV · "
        r"SCOPE=(?P<scope>[A-Z_]+) · "
        r"MOTION=(?P<motion>NONE|motion-\d{2}(?:,motion-\d{2})*) · "
        r"COMFY=(?P<comfy>[A-Z_]+)",
        gate_fields["환경 선택 기록"],
    )
    if not environment_match or not valid_iso_day(environment_match.group("date")):
        errors.append(
            "environment selection record must use the exact dated SELECT_ENV token contract"
        )
    else:
        approval_days["environment"] = parse_iso_day(environment_match.group("date"))
        if environment_match.group("scope") != scope:
            errors.append("environment selection record SCOPE does not match 제작 범위")
        if environment_match.group("motion") != motion_token:
            errors.append("environment selection record MOTION does not match 선정 모션 ID")
        if environment_match.group("comfy") != comfy:
            errors.append("environment selection record COMFY does not match ComfyUI 상태")

    final_match = re.fullmatch(
        r"(?P<date>\d{4}-\d{2}-\d{2}) · APPROVE_EXECUTION · "
        r"SCOPE=(?P<scope>[A-Z_]+) · "
        r"MOTION=(?P<motion>NONE|motion-\d{2}(?:,motion-\d{2})*) · "
        r"COMFY=(?P<comfy>[A-Z_]+)",
        gate_fields["최종 생성 승인 기록"],
    )
    if not final_match or not valid_iso_day(final_match.group("date")):
        errors.append(
            "final generation approval record must use the exact dated APPROVE_EXECUTION token contract"
        )
    else:
        approval_days["final"] = parse_iso_day(final_match.group("date"))
        if final_match.group("scope") != scope:
            errors.append("final generation approval record SCOPE does not match 제작 범위")
        if final_match.group("motion") != motion_token:
            errors.append("final generation approval record MOTION does not match 선정 모션 ID")
        if final_match.group("comfy") != comfy:
            errors.append("final generation approval record COMFY does not match ComfyUI 상태")

    today = datetime.now(APPROVAL_TIMEZONE).date()
    for stage, approval_day in approval_days.items():
        if approval_day is not None and approval_day > today:
            errors.append(
                f"{stage} approval date cannot be in the future in Asia/Seoul: {approval_day}"
            )
    if set(approval_days) == {"plan", "environment", "final"}:
        plan_day = approval_days["plan"]
        environment_day = approval_days["environment"]
        final_day = approval_days["final"]
        if not (plan_day <= environment_day <= final_day):
            errors.append(
                "approval record dates must satisfy plan <= environment <= final"
            )
    return errors


def validate_comfy_receipt(
    skill_root: Path, project_no: str, state: str, receipt_value: str
) -> list[str]:
    errors: list[str] = []
    if state not in RECEIPT_COMFY_STATES:
        return errors
    value = receipt_value.strip().strip("`")
    if not value or value in {"미제공", "미확인", "해당 없음"}:
        return ["actual ComfyUI execution requires a persisted evidence JSON path"]
    try:
        receipt_path, normalized_receipt = project_relative_file(
            skill_root, project_no, value, "ComfyUI evidence JSON"
        )
    except ValueError as exc:
        return [str(exc)]
    if value != normalized_receipt:
        errors.append("ComfyUI evidence JSON path must be skill-root relative")
    if receipt_path.suffix.lower() != ".json" or not receipt_path.is_file():
        return errors + ["ComfyUI evidence JSON does not exist or is not a .json file"]
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return errors + ["ComfyUI evidence JSON is unreadable or invalid"]
    if not isinstance(payload, dict):
        return errors + ["ComfyUI evidence JSON must contain an object"]
    if payload.get("schema") != RECEIPT_SCHEMA:
        errors.append("ComfyUI evidence has an unsupported or missing receipt schema")
    if payload.get("tool") != RECEIPT_TOOL:
        errors.append("ComfyUI evidence lacks the approved receipt helper marker")
    if payload.get("status") != state:
        errors.append("ComfyUI evidence status does not match generation-gate.md")
    checked_at = str(payload.get("checked_at", "")).strip()
    checked_time: datetime | None = None
    try:
        checked_time = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
        if checked_time.tzinfo is None:
            raise ValueError
        checked_time = checked_time.astimezone(timezone.utc)
    except ValueError:
        errors.append("ComfyUI evidence needs a timezone-aware ISO checked_at")
    nonce = str(payload.get("nonce", ""))
    if not re.fullmatch(r"[0-9a-f]{32,128}", nonce):
        errors.append("ComfyUI evidence needs a helper-generated hexadecimal nonce")
    expected_receipt_id = receipt_id_for(payload)
    if payload.get("receipt_id") != expected_receipt_id:
        errors.append("ComfyUI evidence receipt_id is missing or does not match its fields")
    if checked_time is not None:
        now = datetime.now(timezone.utc)
        if checked_time - now > RECEIPT_FUTURE_TOLERANCE:
            errors.append("ComfyUI evidence checked_at is implausibly in the future")
    if state == "CONNECTED":
        endpoint = str(payload.get("endpoint", ""))
        try:
            normalized_endpoint, expected_kind = normalize_endpoint(endpoint)
        except ValueError as exc:
            normalized_endpoint, expected_kind = "", ""
            errors.append(f"CONNECTED evidence has an invalid explicit http(s) endpoint: {exc}")
        if normalized_endpoint and normalized_endpoint != endpoint:
            errors.append("CONNECTED evidence endpoint is not in canonical helper form")
        if expected_kind and payload.get("endpoint_kind") != expected_kind:
            errors.append("CONNECTED evidence endpoint_kind does not match its hostname")
        expected_probe_url = normalized_endpoint + "/system_stats" if normalized_endpoint else ""
        if payload.get("probe_url") != expected_probe_url:
            errors.append("CONNECTED evidence must record the exact /system_stats probe URL")
        if payload.get("probe_ok") is not True:
            errors.append("CONNECTED evidence needs probe_ok=true from an actual probe")
        status_code = payload.get("http_status")
        if not isinstance(status_code, int) or not 200 <= status_code < 300:
            errors.append("CONNECTED evidence needs a successful 2xx http_status")
        response_bytes = payload.get("response_bytes")
        if not isinstance(response_bytes, int) or response_bytes <= 0:
            errors.append("CONNECTED evidence needs a positive response_bytes value")
        if not re.fullmatch(
            r"[0-9a-f]{64}", str(payload.get("response_fingerprint_sha256", ""))
        ):
            errors.append("CONNECTED evidence needs a response SHA256 fingerprint")
        if not re.fullmatch(
            r"[0-9a-f]{64}", str(payload.get("response_identity_sha256", ""))
        ):
            errors.append("CONNECTED evidence needs a stable endpoint identity SHA256")
        if checked_time is not None:
            now = datetime.now(timezone.utc)
            if now - checked_time > CONNECTED_RECEIPT_MAX_AGE:
                errors.append("CONNECTED evidence probe receipt is older than 24 hours")
        if normalized_endpoint:
            try:
                live_payload = connected_receipt(normalized_endpoint, timeout=3.0)
            except Exception as exc:
                errors.append(
                    "CONNECTED evidence failed the generation-time live /system_stats re-probe: "
                    + str(exc)
                )
            else:
                if (
                    live_payload.get("response_identity_sha256")
                    != payload.get("response_identity_sha256")
                ):
                    errors.append(
                        "CONNECTED endpoint identity changed since the persisted receipt"
                    )
    else:
        workflow_value = str(payload.get("workflow_path", "")).strip().strip("`")
        try:
            workflow_path, normalized_workflow = project_relative_file(
                skill_root, project_no, workflow_value, "ComfyUI workflow"
            )
        except ValueError as exc:
            workflow_path, normalized_workflow = Path("__invalid__"), ""
            errors.append(str(exc))
        if normalized_workflow and workflow_value != normalized_workflow:
            errors.append("WORKFLOW_PROVIDED workflow_path must be skill-root relative")
        if not workflow_value or workflow_path.suffix.lower() != ".json" or not workflow_path.is_file():
            errors.append("WORKFLOW_PROVIDED evidence needs an existing workflow_path JSON")
        else:
            try:
                workflow_payload = json.loads(workflow_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                workflow_payload = None
                errors.append("WORKFLOW_PROVIDED workflow_path is not valid JSON")
            actual_kind = comfy_workflow_kind(workflow_payload)
            if actual_kind is None:
                errors.append(
                    "WORKFLOW_PROVIDED needs a ComfyUI API prompt graph or UI workflow, not generic JSON"
                )
            if payload.get("workflow_kind") != actual_kind:
                errors.append("ComfyUI workflow_kind is missing or does not match its graph")
            expected_sha = str(payload.get("workflow_sha256", ""))
            actual_sha = hashlib.sha256(workflow_path.read_bytes()).hexdigest()
            if expected_sha != actual_sha:
                errors.append("ComfyUI workflow SHA256 is missing or does not match")
    return errors


def selected_motion_contract(
    motion_report: dict[str, object], selected_ids: set[str], scope: str
) -> tuple[list[str], set[str], list[str]]:
    errors: list[str] = []
    selected_rows = [
        row
        for row in motion_report.get("rows", [])
        if str(row.get("motion_id", "")) in selected_ids
    ]
    selected_modes = {str(row.get("capture_mode", "")) for row in selected_rows}
    selected_formats = [str(row.get("format", "")) for row in selected_rows]
    gif_capable = ["gif" in value.casefold() for value in selected_formats]
    video_capable = [
        bool(re.search(r"영상|video|mp4|mov", value, re.IGNORECASE))
        for value in selected_formats
    ]
    if scope == "STATIC_PLUS_GIF" and selected_formats and not all(gif_capable):
        errors.append("STATIC_PLUS_GIF selected motions must all declare a GIF format")
    if scope == "STATIC_PLUS_VIDEO" and selected_formats and not all(video_capable):
        errors.append("STATIC_PLUS_VIDEO selected motions must all declare a video format")
    if scope == "STATIC_PLUS_GIF_VIDEO" and selected_formats and not (
        any(gif_capable) and any(video_capable)
    ):
        errors.append(
            "STATIC_PLUS_GIF_VIDEO needs selected motion formats covering both GIF and video"
        )
    return errors, selected_modes, selected_formats


def validate(skill_root: Path, project_no: str, target: str = "static") -> dict[str, object]:
    project_no = normalize_project_number(project_no)
    output_root = skill_root / "outputs" / project_no
    gate_path = output_root / "generation-gate.md"
    review_path = output_root / "plan-review.html"
    errors: list[str] = []
    warnings: list[str] = []
    motion_report: dict[str, object] | None = None
    project_report = check_project(skill_root, project_no)
    asset_report = validate_asset_map(skill_root, project_no)
    production_report = validate_production_docs(skill_root, project_no)

    if not project_report["ok"]:
        errors.append(
            "project research/input validation failed; run check_project.py first"
        )
    plan_report = validate_plan(skill_root, project_no)
    if not plan_report["ok"]:
        errors.append("plan validation failed; run validate_plan.py first")
    if not asset_report["ok"]:
        errors.append("asset lineage validation failed; run validate_asset_map.py first")
    if not production_report["ok"]:
        errors.append(
            "production document validation failed; run validate_production_docs.py first"
        )

    if not gate_path.is_file():
        return {
            "ok": False,
            "project": project_no,
            "target": target,
            "errors": errors + [f"missing generation gate: {gate_path}"],
            "warnings": warnings,
            "project_validation": project_report,
            "asset_validation": asset_report,
            "production_validation": production_report,
        }
    gate_text = gate_path.read_text(encoding="utf-8")
    errors.extend(validate_gate_field_shape(gate_text))
    gate_fields = fields(gate_text)
    if gate_fields["프로젝트 번호"] != project_no:
        errors.append("generation-gate.md project number does not match the requested project")
    if gate_fields["기획 리뷰 HTML"] != "plan-review.html":
        errors.append("generation-gate.md must name the canonical plan-review.html")

    if not review_path.is_file():
        errors.append("missing plan-review.html; run build_plan_review.py")
    else:
        review_text = review_path.read_text(encoding="utf-8")
        review_sha256 = hashlib.sha256(review_path.read_bytes()).hexdigest()
        if 'data-review-kind="coupang-detail-page-plan"' not in review_text:
            errors.append("plan-review.html does not contain the expected review signature")
        if f'data-project="{project_no}"' not in review_text:
            errors.append("plan-review.html data-project does not match the requested project")
        for role_id, _, _ in EXPECTED_ROLES.values():
            if f'data-role="{role_id}"' not in review_text:
                errors.append(f"plan-review.html is missing role {role_id}")
        if 'data-asset-lineage="complete"' not in review_text:
            errors.append("plan-review.html does not contain a complete R2P asset lineage")
        render_digest_match = re.search(
            r'data-render-digest="([0-9a-f]{64})"', review_text
        )
        card_payload_match = re.search(
            r'<div class="pages">(.*)</div></section>\s*<section class="grid">',
            review_text,
            re.DOTALL,
        )
        if not render_digest_match or not card_payload_match:
            errors.append("plan-review.html is missing its rendered page-card integrity contract")
        else:
            actual_render_digest = hashlib.sha256(
                card_payload_match.group(1).encode("utf-8")
            ).hexdigest()
            if render_digest_match.group(1) != actual_render_digest:
                errors.append("plan-review.html page-card content was modified after rendering")

        production_digest_match = re.search(
            r'data-production-digest="([0-9a-f]{64})"', review_text
        )
        production_payload_match = re.search(
            r'<pre id="production-contract" class="source-contract">(.*?)</pre>',
            review_text,
            re.DOTALL,
        )
        paths_for_contract = planning_files(skill_root, project_no)
        try:
            expected_production_contract = (
                "=== prompt-set.md ===\n"
                + paths_for_contract["prompt"].read_text(encoding="utf-8")
                + "\n=== font-plan.md ===\n"
                + paths_for_contract["font"].read_text(encoding="utf-8")
            )
        except OSError as exc:
            expected_production_contract = ""
            errors.append(f"cannot read production contract sources: {exc}")
        if not production_digest_match or not production_payload_match:
            errors.append("plan-review.html is missing its visible production contract")
        else:
            rendered_production_contract = html_lib.unescape(
                production_payload_match.group(1)
            )
            actual_production_digest = hashlib.sha256(
                rendered_production_contract.encode("utf-8")
            ).hexdigest()
            expected_production_digest = hashlib.sha256(
                expected_production_contract.encode("utf-8")
            ).hexdigest()
            if production_digest_match.group(1) != actual_production_digest:
                errors.append("plan-review.html visible production contract was modified")
            if actual_production_digest != expected_production_digest:
                errors.append("plan-review.html does not show the current prompt/font contract")

        plan_path = planning_files(skill_root, project_no)["plan"]
        try:
            expected_rows = table_rows(plan_path.read_text(encoding="utf-8"))
        except OSError as exc:
            expected_rows = {}
            errors.append(f"cannot read selected page contract: {exc}")
        expected_cards = [
            (page, cells[1], cells[6])
            for page, cells in sorted(expected_rows.items(), key=lambda item: int(item[0]))
            if len(cells) >= 7
        ]
        actual_cards = re.findall(
            r'<article class="page-card" data-page="([^"]+)" data-role="([^"]+)" data-info="([^"]+)">',
            review_text,
        )
        if actual_cards != expected_cards:
            errors.append("plan-review.html page cards do not exactly match the selected plan")

        digest_match = re.search(r'data-source-digest="([0-9a-f]{64})"', review_text)
        try:
            current_digest = planning_digest(planning_files(skill_root, project_no))
        except OSError as exc:
            current_digest = ""
            errors.append(f"cannot compute planning source digest: {exc}")
        if not digest_match:
            errors.append("plan-review.html is missing the planning source digest")
        elif current_digest and digest_match.group(1) != current_digest:
            errors.append("planning sources changed after plan-review.html was built; rebuild and reapprove")
        if current_digest and gate_fields["승인한 기획 소스 해시"] != current_digest:
            errors.append(
                "approved planning source digest is missing or stale; copy the HTML digest after user approval"
            )
        if gate_fields["승인한 리뷰 HTML 해시"] != review_sha256:
            errors.append(
                "approved review HTML digest is missing or stale; record the exact approved HTML file hash"
            )

    if gate_fields["기획 검토 상태"] != "승인":
        errors.append("user has not approved the plan review HTML")

    scope = gate_fields["제작 범위"]
    comfy = gate_fields["ComfyUI 상태"]
    selected_motion_value = gate_fields["선정 모션 ID"]
    if not canonical_motion_selection(selected_motion_value):
        errors.append(
            "선정 모션 ID must be exactly '해당 없음' or a comma-separated motion-NN list"
        )
    selected_ids = selected_motion_ids(selected_motion_value)
    errors.extend(validate_approval_records(gate_fields, scope, selected_ids, comfy))
    if scope not in STATIC_SCOPES:
        errors.append("production scope is not selected")
    if comfy not in COMFY_STATES:
        errors.append("ComfyUI availability has not been recorded")
    if comfy in {"NOT_REQUIRED", "HANDOFF_ONLY"} and gate_fields[
        "ComfyUI 증빙 JSON"
    ] != "해당 없음":
        errors.append(f"{comfy} must use ComfyUI 증빙 JSON: 해당 없음")
    if gate_fields["정적 이미지 생성 승인"] != "승인":
        errors.append("static image generation is not approved")
    if scope == "STATIC_ONLY":
        if comfy != "NOT_REQUIRED":
            errors.append("STATIC_ONLY requires ComfyUI 상태: NOT_REQUIRED")
        if gate_fields["GIF·영상 생성 승인"] != "해당 없음":
            errors.append("STATIC_ONLY requires GIF·영상 생성 승인: 해당 없음")
    elif scope in MOTION_SCOPES | HANDOFF_SCOPES:
        if gate_fields["GIF·영상 생성 승인"] != "승인":
            errors.append(
                "the selected motion or handoff scope is missing its separate approval"
            )
    errors.extend(
        validate_comfy_receipt(
            skill_root, project_no, comfy, gate_fields["ComfyUI 증빙 JSON"]
        )
    )

    planning_motion_report: dict[str, object] | None = None
    planning_selected_modes: set[str] = set()
    if scope in MOTION_SCOPES | HANDOFF_SCOPES:
        planning_motion_report = validate_motion(
            skill_root,
            project_no,
            selected_ids=selected_ids,
        )
        if not planning_motion_report["ok"]:
            errors.append(
                "selected motion planning contract is invalid; run validate_motion.py first"
            )
        contract_errors, planning_selected_modes, _ = selected_motion_contract(
            planning_motion_report, selected_ids, scope
        )
        errors.extend(contract_errors)
        if scope in MOTION_SCOPES:
            if "NO_PROOF_HOOK" in planning_selected_modes:
                errors.append(
                    "NO_PROOF_HOOK cannot be selected for an actual GIF/video production scope"
                )
            if (
                "AI_ILLUSTRATION" in planning_selected_modes
                and comfy not in LIVE_COMFY_STATES
            ):
                errors.append(
                    "selected AI_ILLUSTRATION actual motion requires a live-reprobed "
                    "CONNECTED ComfyUI before static generation"
                )
            real_only = planning_selected_modes and planning_selected_modes.issubset(
                {"REAL_TEST", "REAL_DEMO"}
            )
            if real_only and comfy not in LIVE_COMFY_STATES | {"NOT_REQUIRED"}:
                errors.append(
                    "selected REAL_TEST/REAL_DEMO motions require NOT_REQUIRED or a live CONNECTED ComfyUI state"
                )

    if target == "static":
        if scope == "STATIC_ONLY" and selected_ids:
            errors.append("STATIC_ONLY must use 선정 모션 ID: 해당 없음")
        if scope in MOTION_SCOPES | HANDOFF_SCOPES and not selected_ids:
            errors.append("the selected production scope requires at least one 선정 모션 ID")
    elif target == "motion":
        motion_report = validate_motion(
            skill_root,
            project_no,
            execution=True,
            selected_ids=selected_ids,
        )
        if not motion_report["ok"]:
            errors.append("motion validation failed; run validate_motion.py first")
        if scope not in MOTION_SCOPES:
            errors.append("production scope does not authorize actual GIF/video generation")
        selected_modes = {
            str(row.get("capture_mode", ""))
            for row in motion_report.get("rows", [])
            if str(row.get("motion_id", "")) in selected_ids
        }
        contract_errors, _, _ = selected_motion_contract(
            motion_report, selected_ids, scope
        )
        errors.extend(contract_errors)
        if "AI_ILLUSTRATION" in selected_modes and comfy not in LIVE_COMFY_STATES:
            errors.append(
                "selected AI_ILLUSTRATION motion requires live-reprobed CONNECTED ComfyUI"
            )
        if selected_modes and "AI_ILLUSTRATION" not in selected_modes and comfy not in (
            LIVE_COMFY_STATES | {"NOT_REQUIRED"}
        ):
            errors.append(
                "real-capture motion requires NOT_REQUIRED or live CONNECTED ComfyUI"
            )
    elif target == "handoff":
        motion_report = validate_motion(
            skill_root, project_no, selected_ids=selected_ids
        )
        if not motion_report["ok"]:
            errors.append("motion validation failed; run validate_motion.py first")
        if not selected_ids:
            errors.append("motion handoff requires at least one 선정 모션 ID")
        if scope not in HANDOFF_SCOPES or comfy not in {"HANDOFF_ONLY", "WORKFLOW_PROVIDED"}:
            errors.append(
                "motion handoff requires STATIC_PLUS_MOTION_HANDOFF with HANDOFF_ONLY or a validated WORKFLOW_PROVIDED receipt"
            )
    else:
        raise ValueError("target must be static, motion, or handoff")

    if comfy == "NOT_REQUIRED" and scope == "STATIC_PLUS_MOTION_HANDOFF":
        errors.append(
            "motion handoff requires HANDOFF_ONLY or WORKFLOW_PROVIDED instead of NOT_REQUIRED"
        )
    if scope == "STATIC_PLUS_MOTION_HANDOFF" and comfy not in {
        "HANDOFF_ONLY",
        "WORKFLOW_PROVIDED",
    }:
        errors.append(
            "STATIC_PLUS_MOTION_HANDOFF requires HANDOFF_ONLY or WORKFLOW_PROVIDED"
        )
    if comfy == "HANDOFF_ONLY" and scope != "STATIC_PLUS_MOTION_HANDOFF":
        errors.append("HANDOFF_ONLY requires STATIC_PLUS_MOTION_HANDOFF")
    if comfy == "WORKFLOW_PROVIDED" and scope != "STATIC_PLUS_MOTION_HANDOFF":
        errors.append(
            "WORKFLOW_PROVIDED is a validated workflow handoff state and requires STATIC_PLUS_MOTION_HANDOFF; actual AI rendering requires CONNECTED"
        )

    return {
        "ok": not errors,
        "project": project_no,
        "target": target,
        "gate": str(gate_path),
        "review": str(review_path),
        "motion_validation": motion_report,
        "planning_motion_validation": planning_motion_report,
        "project_validation": project_report,
        "asset_validation": asset_report,
        "production_validation": production_report,
        "fields": gate_fields,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate user approval before generation.")
    parser.add_argument("project", help="Project number, for example 003 or 3")
    parser.add_argument(
        "--target", choices=("static", "motion", "handoff"), default="static"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        report = validate(skill_root, args.project, args.target)
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"GENERATION READY: project {report['project']} target={report['target']}")
    else:
        print(f"GENERATION BLOCKED: project {report['project']} target={report['target']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
