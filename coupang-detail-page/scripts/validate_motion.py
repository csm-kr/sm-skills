#!/usr/bin/env python3
"""Validate proof-hook scoring and real-capture boundaries for motion plans."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


AXES = (
    "동작 필요성",
    "주장 안전성",
    "전환 관련성",
    "제작 실행성",
    "제품 안정성",
    "고유 소구 선명도",
    "실증 후킹력",
)
CAPTURE_MODES = {
    "REAL_TEST",
    "REAL_DEMO",
    "AI_ILLUSTRATION",
    "NO_PROOF_HOOK",
}
REAL_REQUIRED_FIELDS = (
    "증명 상태",
    "검증할 구매 의심",
    "허용 주장",
    "도전 조건·과업",
    "통제 조건",
    "판정 기준",
    "실사 원본 클립 경로",
    "편집 정책",
)
AI_PROOF_TERMS = re.compile(r"(?:테스트|입증|검증 완료|버틴다|PASS|성능을 증명)")


def normalize_project_number(value: str) -> str:
    if not value.isdigit():
        raise ValueError("project number must contain digits only")
    number = int(value)
    if not 1 <= number <= 999:
        raise ValueError("project number must be between 001 and 999")
    return f"{number:03d}"


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index + 1 < len(lines):
        if lines[index].lstrip().startswith("|") and is_separator(lines[index + 1]):
            header = split_row(lines[index])
            rows: list[list[str]] = []
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
                rows.append(split_row(lines[cursor]))
                cursor += 1
            tables.append((header, rows))
            index = cursor
        else:
            index += 1
    return tables


def plain_int(value: str) -> int | None:
    match = re.fullmatch(r"\*{0,2}\s*(\d{1,3})\s*\*{0,2}", value.strip())
    return int(match.group(1)) if match else None


def line_value(text: str, label: str) -> str:
    match = re.search(
        rf"^(?:-[ \t]*)?{re.escape(label)}[ \t]*:[ \t]*(.+?)\s*$",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def motion_section(text: str, motion_id: str) -> str:
    match = re.search(
        rf"^##[ \t]+{re.escape(motion_id)}\b.*?(?=^##[ \t]+motion-\d+\b|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(0) if match else ""


def registered_raw_demo_paths(skill_root: Path, project_no: str) -> set[str]:
    path = skill_root / "outputs" / project_no / "asset-map.md"
    if not path.is_file():
        return set()
    result: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if len(cells) >= 4 and re.fullmatch(r"A\d{2,}", cells[0], re.IGNORECASE):
            if cells[1] == "RAW_DEMO" and not re.match(r"https?://", cells[3]):
                result.add(cells[3].lstrip("./"))
    return result


def media_decode_errors(path: Path) -> list[str]:
    errors: list[str] = []
    if path.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm", ".gif"}:
        return [f"unsupported motion evidence format: {path.suffix or 'none'}"]
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return ["ffprobe is required to verify actual motion evidence"]
    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,nb_frames,duration:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return ["motion evidence cannot be decoded by ffprobe"]
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return ["motion evidence probe returned invalid metadata"]
    streams = [
        stream
        for stream in payload.get("streams", [])
        if stream.get("codec_type") == "video"
    ]
    if not streams:
        return ["motion evidence has no decodable video stream"]
    stream = streams[0]
    if int(stream.get("width") or 0) <= 0 or int(stream.get("height") or 0) <= 0:
        errors.append("motion evidence has invalid frame dimensions")
    duration_value = stream.get("duration") or payload.get("format", {}).get("duration")
    try:
        duration = float(duration_value)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0.1:
        errors.append("motion evidence duration must exceed 0.1 seconds")
    frame_value = stream.get("nb_frames")
    if isinstance(frame_value, str) and frame_value.isdigit() and int(frame_value) < 2:
        errors.append("motion evidence must contain at least two frames")
    return errors


def validate(
    skill_root: Path,
    project_no: str,
    execution: bool = False,
    selected_ids: set[str] | None = None,
) -> dict[str, object]:
    output_root = skill_root / "outputs" / project_no
    motion_path = output_root / "motion-plan.md"
    video_path = output_root / "video-plan.md"
    errors: list[str] = []
    warnings: list[str] = []
    raw_demo_paths = registered_raw_demo_paths(skill_root, project_no)

    if not motion_path.is_file():
        errors.append(f"missing motion plan: {motion_path}")
        motion_text = ""
    else:
        motion_text = motion_path.read_text(encoding="utf-8")

    if not video_path.is_file():
        errors.append(f"missing video plan: {video_path}")
        video_text = ""
    else:
        video_text = video_path.read_text(encoding="utf-8")

    hook = line_value(motion_text, "가장 영상이 필요한 소구점")
    if not hook:
        errors.append("motion plan needs a non-empty '가장 영상이 필요한 소구점'")

    score_table: tuple[list[str], list[list[str]]] | None = None
    for header, rows in markdown_tables(motion_text):
        if "MOTION_ID" in header and "CAPTURE_MODE" in header:
            score_table = (header, rows)
            break
    if score_table is None:
        errors.append("motion plan needs the 7-axis table with MOTION_ID and CAPTURE_MODE")
        return {
            "ok": False,
            "project": project_no,
            "motion_plan": str(motion_path),
            "video_plan": str(video_path),
            "hook": hook,
            "rows": [],
            "errors": errors,
            "warnings": warnings,
        }

    header, raw_rows = score_table
    required_columns = (
        "순위",
        "MOTION_ID",
        "형식",
        "CAPTURE_MODE",
        *AXES,
        "총점",
        "판정",
    )
    missing_columns = [column for column in required_columns if column not in header]
    if missing_columns:
        errors.append("motion score table is missing columns: " + ", ".join(missing_columns))

    index = {name: header.index(name) for name in header}
    parsed_rows: list[dict[str, object]] = []
    for raw in raw_rows:
        if len(raw) < len(header):
            continue
        motion_id = raw[index["MOTION_ID"]].strip()
        if not re.fullmatch(r"motion-\d{2}", motion_id):
            continue
        capture_mode = raw[index["CAPTURE_MODE"]].strip()
        output_format = raw[index["형식"]].strip()
        if capture_mode not in CAPTURE_MODES:
            errors.append(f"{motion_id}: invalid CAPTURE_MODE '{capture_mode}'")

        scores: dict[str, int] = {}
        for axis in AXES:
            score = plain_int(raw[index[axis]])
            if score is None or not 0 <= score <= 20:
                errors.append(f"{motion_id}: {axis} must be an integer from 0 to 20")
                continue
            scores[axis] = score

        total = plain_int(raw[index["총점"]])
        if total is None:
            errors.append(f"{motion_id}: 총점 must be an integer")
        elif len(scores) == len(AXES) and total != sum(scores.values()):
            errors.append(
                f"{motion_id}: 총점 {total} does not equal 7-axis sum {sum(scores.values())}"
            )

        proof_score = scores.get("실증 후킹력")
        if capture_mode == "AI_ILLUSTRATION" and proof_score is not None and proof_score > 5:
            errors.append(f"{motion_id}: AI_ILLUSTRATION 실증 후킹력 cannot exceed 5")

        parsed_rows.append(
            {
                "motion_id": motion_id,
                "capture_mode": capture_mode,
                "format": output_format,
                "scores": scores,
                "total": total,
                "verdict": raw[index["판정"]].strip(),
            }
        )

    if not parsed_rows:
        errors.append("motion score table needs at least one populated motion row")

    top1 = next((row for row in parsed_rows if row["motion_id"] == "motion-01"), None)
    no_proof = hook == "NO_PROOF_HOOK"
    if top1 is None:
        errors.append("motion score table needs motion-01")
    elif no_proof:
        if top1["capture_mode"] != "NO_PROOF_HOOK":
            errors.append("NO_PROOF_HOOK selection must use CAPTURE_MODE NO_PROOF_HOOK")
        if "실사 촬영 필요: 예" not in video_text:
            errors.append("NO_PROOF_HOOK video plan must state '실사 촬영 필요: 예'")
    else:
        top1_mode = str(top1["capture_mode"])
        top1_scores = top1["scores"]
        if top1_mode not in {"REAL_TEST", "REAL_DEMO"}:
            errors.append("motion-01 must be REAL_TEST or REAL_DEMO to qualify as a proof hook")
        if isinstance(top1_scores, dict):
            if top1_scores.get("고유 소구 선명도", 0) < 12:
                errors.append("motion-01 고유 소구 선명도 must be at least 12")
            if top1_scores.get("실증 후킹력", 0) < 12:
                errors.append("motion-01 실증 후킹력 must be at least 12")

    for row in parsed_rows:
        motion_id = str(row["motion_id"])
        capture_mode = str(row["capture_mode"])
        section = motion_section(video_text, motion_id)
        if not section:
            errors.append(f"video plan is missing section for {motion_id}")
            continue
        section_mode = line_value(section, "CAPTURE_MODE")
        if section_mode != capture_mode:
            errors.append(
                f"{motion_id}: CAPTURE_MODE differs between motion plan ({capture_mode}) and video plan ({section_mode or 'missing'})"
            )

        if capture_mode in {"REAL_TEST", "REAL_DEMO"}:
            for field in REAL_REQUIRED_FIELDS:
                if not line_value(section, field):
                    errors.append(f"{motion_id}: video plan needs non-empty '{field}'")
            status = line_value(section, "증명 상태")
            source = line_value(section, "실사 원본 클립 경로")
            if status == "VERIFIED" and source in {"", "PENDING_CAPTURE", "없음"}:
                errors.append(f"{motion_id}: VERIFIED evidence needs a real original clip path")
            if execution and (selected_ids is None or motion_id in selected_ids):
                if status != "VERIFIED":
                    errors.append(
                        f"{motion_id}: actual motion generation requires 증명 상태 VERIFIED"
                    )
                normalized_source = source.strip().strip("`").lstrip("./")
                if normalized_source not in raw_demo_paths:
                    errors.append(
                        f"{motion_id}: actual motion generation requires a clip registered as RAW_DEMO in asset-map.md"
                    )
                elif not (skill_root / normalized_source).is_file():
                    errors.append(
                        f"{motion_id}: registered RAW_DEMO clip does not exist: {normalized_source}"
                    )
                else:
                    for media_error in media_decode_errors(skill_root / normalized_source):
                        errors.append(f"{motion_id}: {media_error}")
            if capture_mode == "REAL_TEST" and "무편집" not in line_value(section, "편집 정책"):
                errors.append(f"{motion_id}: REAL_TEST must keep the core test segment unedited")
        elif capture_mode == "AI_ILLUSTRATION":
            allowed_claim = line_value(section, "허용 주장")
            if not allowed_claim:
                errors.append(f"{motion_id}: AI_ILLUSTRATION needs a bounded '허용 주장'")
            elif AI_PROOF_TERMS.search(allowed_claim):
                errors.append(
                    f"{motion_id}: AI_ILLUSTRATION allowed claim uses proof/test language"
                )
        elif (
            capture_mode == "NO_PROOF_HOOK"
            and execution
            and (selected_ids is None or motion_id in selected_ids)
        ):
            errors.append(
                f"{motion_id}: NO_PROOF_HOOK cannot be generated as an approved motion output"
            )

    known_motion_ids = {str(row["motion_id"]) for row in parsed_rows}
    if selected_ids is not None:
        unknown_selected = sorted(selected_ids - known_motion_ids)
        if unknown_selected:
            errors.append("unknown selected motion IDs: " + ", ".join(unknown_selected))
        if execution and not selected_ids:
            errors.append("actual motion generation needs at least one selected motion ID")

    return {
        "ok": not errors,
        "project": project_no,
        "motion_plan": str(motion_path),
        "video_plan": str(video_path),
        "hook": hook,
        "rows": parsed_rows,
        "errors": errors,
        "warnings": warnings,
        "execution": execution,
        "selected_ids": sorted(selected_ids) if selected_ids is not None else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate 7-axis proof-hook scoring and capture-mode evidence boundaries."
    )
    parser.add_argument("project", help="Project number, for example 003 or 3")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument(
        "--execution",
        action="store_true",
        help="Require VERIFIED local RAW_DEMO clips for actual motion generation",
    )
    args = parser.parse_args()

    try:
        project_no = normalize_project_number(args.project)
    except ValueError as exc:
        parser.error(str(exc))

    skill_root = Path(__file__).resolve().parents[1]
    report = validate(skill_root, project_no, execution=args.execution)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"MOTION READY: project {project_no}")
    else:
        print(f"MOTION NOT READY: project {project_no}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
