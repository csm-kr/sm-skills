#!/usr/bin/env python3
"""Create verifiable ComfyUI endpoint or workflow evidence receipts."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


RECEIPT_SCHEMA = "coupang-detail-page/comfyui-evidence/v1"
RECEIPT_TOOL = "coupang-detail-page/scripts/comfyui_receipt.py@1"
MAX_PROBE_BYTES = 8 * 1024 * 1024


def normalize_project_number(value: str) -> str:
    if not value.isdigit() or not 1 <= int(value) <= 999:
        raise ValueError("project number must be between 001 and 999")
    return f"{int(value):03d}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def endpoint_kind(hostname: str) -> str:
    host = hostname.casefold().rstrip(".")
    if host == "localhost":
        return "LOCALHOST"
    try:
        if ipaddress.ip_address(host).is_loopback:
            return "LOCALHOST"
    except ValueError:
        pass
    return "EXPLICIT_REMOTE"


def normalize_endpoint(value: str) -> tuple[str, str]:
    endpoint = value.strip().rstrip("/")
    parsed = urlsplit(endpoint)
    if parsed.scheme.casefold() not in {"http", "https"}:
        raise ValueError("ComfyUI endpoint must use http:// or https://")
    if not parsed.netloc or not parsed.hostname:
        raise ValueError("ComfyUI endpoint must include an explicit hostname")
    if parsed.username or parsed.password:
        raise ValueError("ComfyUI endpoint must not embed credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("ComfyUI endpoint must not contain a query or fragment")
    if parsed.hostname.casefold().rstrip(".") in {"0.0.0.0", "::", "*"}:
        raise ValueError("ComfyUI endpoint must name localhost or an explicit host, not a wildcard")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("ComfyUI endpoint has an invalid port") from exc
    return endpoint, endpoint_kind(parsed.hostname)


def receipt_id_for(payload: dict[str, object]) -> str:
    status = str(payload.get("status", ""))
    common = {
        "schema": payload.get("schema"),
        "tool": payload.get("tool"),
        "status": status,
        "checked_at": payload.get("checked_at"),
        "nonce": payload.get("nonce"),
    }
    if status == "CONNECTED":
        common.update(
            {
                "endpoint": payload.get("endpoint"),
                "endpoint_kind": payload.get("endpoint_kind"),
                "probe_url": payload.get("probe_url"),
                "probe_ok": payload.get("probe_ok"),
                "http_status": payload.get("http_status"),
                "response_bytes": payload.get("response_bytes"),
                "response_fingerprint_sha256": payload.get(
                    "response_fingerprint_sha256"
                ),
                "response_identity_sha256": payload.get(
                    "response_identity_sha256"
                ),
            }
        )
    elif status == "WORKFLOW_PROVIDED":
        common.update(
            {
                "workflow_path": payload.get("workflow_path"),
                "workflow_sha256": payload.get("workflow_sha256"),
                "workflow_kind": payload.get("workflow_kind"),
            }
        )
    canonical = json.dumps(
        common, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def comfy_workflow_kind(payload: object) -> str | None:
    """Return a supported ComfyUI workflow representation, never generic JSON."""

    if not isinstance(payload, dict) or not payload:
        return None

    nodes = payload.get("nodes")
    links = payload.get("links")
    if isinstance(nodes, list) and nodes and isinstance(links, list):
        valid_nodes = all(
            isinstance(node, dict)
            and isinstance(node.get("id"), (int, str))
            and bool(str(node.get("type", "")).strip())
            for node in nodes
        )
        if valid_nodes:
            return "UI_WORKFLOW"

    valid_api_nodes = all(
        isinstance(node_id, str)
        and bool(re.fullmatch(r"\d+", node_id))
        and isinstance(node, dict)
        and bool(str(node.get("class_type", "")).strip())
        and isinstance(node.get("inputs"), dict)
        for node_id, node in payload.items()
    )
    if valid_api_nodes:
        return "API_PROMPT_GRAPH"
    return None


def comfy_response_identity(payload: object) -> str:
    """Hash stable ComfyUI system/device identity while excluding live counters."""

    if not isinstance(payload, dict):
        raise ValueError("ComfyUI identity source must be a JSON object")
    volatile_markers = (
        "free",
        "used",
        "usage",
        "allocated",
        "reserved",
        "available",
        "timestamp",
        "uptime",
    )

    def stable(value: object) -> object:
        if isinstance(value, dict):
            return {
                str(key): stable(child)
                for key, child in sorted(value.items(), key=lambda item: str(item[0]))
                if not any(marker in str(key).casefold() for marker in volatile_markers)
            }
        if isinstance(value, list):
            return [stable(child) for child in value]
        return value

    identity = {
        key: stable(payload[key])
        for key in ("system", "devices")
        if key in payload
    }
    if not identity:
        raise ValueError("ComfyUI identity source lacks system/devices")
    canonical = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def connected_receipt(endpoint_value: str, timeout: float = 5.0) -> dict[str, object]:
    endpoint, kind = normalize_endpoint(endpoint_value)
    probe_url = endpoint + "/system_stats"
    request = Request(
        probe_url,
        headers={
            "Accept": "application/json",
            "User-Agent": RECEIPT_TOOL,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_PROBE_BYTES + 1)
        status = int(response.status)
    if len(body) > MAX_PROBE_BYTES:
        raise ValueError("ComfyUI probe response exceeds the 8 MiB safety limit")
    if not 200 <= status < 300:
        raise ValueError(f"ComfyUI probe returned HTTP {status}")
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ComfyUI /system_stats did not return valid UTF-8 JSON") from exc
    if not (
        isinstance(decoded, dict)
        and isinstance(decoded.get("system"), dict)
        and isinstance(decoded.get("devices"), list)
    ):
        raise ValueError(
            "ComfyUI /system_stats JSON needs a system object and devices list"
        )
    payload: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "tool": RECEIPT_TOOL,
        "status": "CONNECTED",
        "checked_at": utc_now_iso(),
        "endpoint": endpoint,
        "endpoint_kind": kind,
        "probe_url": probe_url,
        "probe_ok": True,
        "http_status": status,
        "response_bytes": len(body),
        "response_fingerprint_sha256": hashlib.sha256(body).hexdigest(),
        "response_identity_sha256": comfy_response_identity(decoded),
        "nonce": secrets.token_hex(16),
    }
    payload["receipt_id"] = receipt_id_for(payload)
    return payload


def project_relative_file(
    skill_root: Path, project_no: str, value: str | Path, label: str
) -> tuple[Path, str]:
    root_resolved = skill_root.resolve()
    raw = Path(value)
    if raw.is_absolute():
        source_absolute = Path(os.path.abspath(raw))
        root_absolute = Path(os.path.abspath(skill_root))
        try:
            nominal = root_resolved / source_absolute.relative_to(root_absolute)
        except ValueError:
            nominal = source_absolute
    else:
        nominal = Path(os.path.abspath(root_resolved / raw))

    try:
        path = nominal.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{label} path cannot be resolved safely: {exc}") from exc
    if path != nominal:
        raise ValueError(f"{label} path contains a symlink component")
    try:
        relative = path.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the skill root") from exc
    allowed_nominal_roots = (
        root_resolved / "inputs" / project_no / "evidence",
        root_resolved / "outputs" / project_no,
    )
    for allowed_root in allowed_nominal_roots:
        try:
            resolved_allowed_root = allowed_root.resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError(
                f"{label} canonical project root cannot be resolved safely: {exc}"
            ) from exc
        if resolved_allowed_root != allowed_root:
            raise ValueError(f"{label} canonical project root contains a symlink")
    if not any(
        path == root or root in path.parents for root in allowed_nominal_roots
    ):
        raise ValueError(f"{label} must live in the numbered project evidence/output tree")
    return path, relative.as_posix()


def workflow_receipt(
    skill_root: Path, project_no: str, workflow_value: str | Path
) -> dict[str, object]:
    path, relative = project_relative_file(
        skill_root, project_no, workflow_value, "ComfyUI workflow"
    )
    if path.suffix.casefold() != ".json" or not path.is_file():
        raise ValueError("ComfyUI workflow must be an existing local .json file")
    try:
        workflow_payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("ComfyUI workflow is not valid JSON") from exc
    workflow_kind = comfy_workflow_kind(workflow_payload)
    if workflow_kind is None:
        raise ValueError(
            "ComfyUI workflow must be an API prompt graph (numeric node IDs with class_type/inputs) "
            "or a UI workflow (non-empty nodes plus a links list, with node id/type)"
        )
    payload: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "tool": RECEIPT_TOOL,
        "status": "WORKFLOW_PROVIDED",
        "checked_at": utc_now_iso(),
        "workflow_path": relative,
        "workflow_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "workflow_kind": workflow_kind,
        "nonce": secrets.token_hex(16),
    }
    payload["receipt_id"] = receipt_id_for(payload)
    return payload


def write_receipt(
    skill_root: Path,
    project_no: str,
    payload: dict[str, object],
    output_value: str | Path | None = None,
) -> Path:
    default_name = (
        "comfyui-connected-receipt.json"
        if payload.get("status") == "CONNECTED"
        else "comfyui-workflow-receipt.json"
    )
    output_value = output_value or (
        Path("inputs") / project_no / "evidence" / default_name
    )
    path, _ = project_relative_file(
        skill_root, project_no, output_value, "ComfyUI receipt"
    )
    if path.suffix.casefold() != ".json":
        raise ValueError("ComfyUI receipt output must use a .json suffix")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe ComfyUI or hash a workflow and persist a project receipt."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    probe = subparsers.add_parser("probe", help="Probe /system_stats on a live endpoint")
    probe.add_argument("project", help="Project number, for example 003 or 3")
    probe.add_argument("--endpoint", required=True, help="Explicit ComfyUI base http(s) URL")
    probe.add_argument("--timeout", type=float, default=5.0)
    probe.add_argument("--output")
    workflow = subparsers.add_parser("workflow", help="Hash a local ComfyUI workflow")
    workflow.add_argument("project", help="Project number, for example 003 or 3")
    workflow.add_argument("--workflow", required=True, dest="workflow_path")
    workflow.add_argument("--output")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    try:
        project_no = normalize_project_number(args.project)
        if args.command == "probe":
            if args.timeout <= 0 or args.timeout > 60:
                raise ValueError("probe timeout must be greater than 0 and at most 60 seconds")
            payload = connected_receipt(args.endpoint, timeout=args.timeout)
        else:
            payload = workflow_receipt(skill_root, project_no, args.workflow_path)
        path = write_receipt(skill_root, project_no, payload, args.output)
    except Exception as exc:  # argparse should surface network/JSON/filesystem failures uniformly.
        parser.error(str(exc))
    print(path.relative_to(skill_root).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
