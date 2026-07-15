#!/usr/bin/env python3
"""Deterministically calculate YouTube candidate metrics and gate statuses."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


DEFAULT_WEIGHTS = {
    "product_fit": Decimal("0.30"),
    "audience_fit": Decimal("0.20"),
    "engagement": Decimal("0.20"),
    "reach": Decimal("0.15"),
    "advertising_experience": Decimal("0.10"),
    "activity": Decimal("0.05"),
}

SCORE_FIELDS = {
    "product_fit": "product_fit",
    "audience_fit": "audience_fit",
    "engagement": "engagement_score",
    "reach": "reach_score",
    "advertising_experience": "advertising_experience_score",
    "activity": "activity_score",
}

CONTENT_TYPE_ALIASES = {
    "longform": "longform",
    "long-form": "longform",
    "video": "longform",
    "videos": "longform",
    "일반 영상": "longform",
    "동영상": "longform",
    "short": "shorts",
    "shorts": "shorts",
    "쇼츠": "shorts",
}


class InputError(ValueError):
    """Raised when input cannot be evaluated without guessing."""


def decimal_value(value: Any, field: str, *, allow_none: bool = True) -> Decimal | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool):
        raise InputError(f"{field} must be numeric, not boolean")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{field} must be numeric or null") from exc
    if not result.is_finite():
        raise InputError(f"{field} must be finite")
    return result


def integer_value(value: Any, field: str, *, minimum: int | None = None) -> int:
    number = decimal_value(value, field, allow_none=False)
    assert number is not None
    if number != number.to_integral_value():
        raise InputError(f"{field} must be an integer")
    result = int(number)
    if minimum is not None and result < minimum:
        raise InputError(f"{field} must be at least {minimum}")
    return result


def parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field} must be an ISO date string")
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise InputError(f"{field} must use ISO format") from exc


def normalize_content_type(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InputError(f"{field} must be longform or shorts")
    normalized = CONTENT_TYPE_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise InputError(
            f"{field} must be longform or shorts; evaluate all uploads as separate cohorts"
        )
    return normalized


def quantize(value: Decimal | None, places: str) -> int | float | None:
    if value is None:
        return None
    rounded = value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def score_value(candidate: dict[str, Any], field: str) -> Decimal | None:
    value = decimal_value(candidate.get(field), field)
    if value is not None and not Decimal("0") <= value <= Decimal("5"):
        raise InputError(f"{field} must be between 0 and 5 or null")
    return value


def load_weights(criteria: dict[str, Any]) -> dict[str, Decimal]:
    raw = criteria.get("weights")
    if raw is None:
        return DEFAULT_WEIGHTS.copy()
    if not isinstance(raw, dict) or set(raw) != set(DEFAULT_WEIGHTS):
        raise InputError(
            "criteria.weights must contain product_fit, audience_fit, engagement, "
            "reach, advertising_experience, and activity"
        )
    weights: dict[str, Decimal] = {}
    for key in DEFAULT_WEIGHTS:
        value = decimal_value(raw[key], f"criteria.weights.{key}", allow_none=False)
        assert value is not None
        if value < 0:
            raise InputError(f"criteria.weights.{key} cannot be negative")
        weights[key] = value
    if sum(weights.values()) != Decimal("1"):
        raise InputError("criteria.weights must sum exactly to 1")
    return weights


def video_sort_key(video: dict[str, Any]) -> tuple[int, str]:
    published = video.get("published_at")
    if not isinstance(published, str):
        return (0, "")
    try:
        parsed = parse_date(published, "published_at")
    except InputError:
        return (0, "")
    return (1, parsed.isoformat())


def derive_metrics(
    videos: list[dict[str, Any]], content_type: str, count: int
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    issues: list[str] = []
    eligible: list[dict[str, Any]] = []
    for index, video in enumerate(videos):
        if not isinstance(video, dict):
            issues.append(f"recent_videos[{index}] is not an object")
            continue
        if video.get("eligible") is False:
            if not nonempty(video.get("exclusion_reason")):
                issues.append(f"recent_videos[{index}] exclusion_reason is missing")
            continue
        try:
            video_type = normalize_content_type(
                video.get("content_type"), f"recent_videos[{index}].content_type"
            )
        except InputError as exc:
            issues.append(str(exc))
            continue
        if video_type == content_type:
            eligible.append(video)

    eligible.sort(key=video_sort_key, reverse=True)
    selected = eligible[:count]
    complete = len(selected) == count
    if not complete:
        issues.append(
            f"only {len(selected)} eligible {content_type} videos are available; {count} required"
        )

    comments: list[Decimal] = []
    views: list[Decimal] = []
    published_dates: list[date] = []
    approximate = False

    for index, video in enumerate(selected):
        comment = decimal_value(video.get("comments"), f"selected_videos[{index}].comments")
        view = decimal_value(video.get("views"), f"selected_videos[{index}].views")
        if comment is None:
            issues.append(f"selected_videos[{index}].comments is unverified")
        elif comment < 0 or comment != comment.to_integral_value():
            raise InputError(f"selected_videos[{index}].comments must be a non-negative integer")
        else:
            comments.append(comment)
        if view is None:
            issues.append(f"selected_videos[{index}].views is unverified")
        elif view < 0 or view != view.to_integral_value():
            raise InputError(f"selected_videos[{index}].views must be a non-negative integer")
        else:
            views.append(view)
        try:
            published_dates.append(
                parse_date(video.get("published_at"), f"selected_videos[{index}].published_at")
            )
        except InputError as exc:
            issues.append(str(exc))
        if video.get("comments_approximate") is True or video.get("views_approximate") is True:
            approximate = True
        if not nonempty(video.get("url")):
            issues.append(f"selected_videos[{index}].url is missing")

    if approximate:
        issues.append("selected video metrics include approximate public values")

    all_comments = complete and len(comments) == count
    all_views = complete and len(views) == count
    comment_total = sum(comments) if all_comments else None
    average_comments = comment_total / Decimal(count) if comment_total is not None else None
    view_total = sum(views) if all_views else None
    average_views = view_total / Decimal(count) if view_total is not None else None
    engagement = None
    if comment_total is not None and view_total is not None:
        if view_total > 0:
            engagement = comment_total / view_total * Decimal("100")
        else:
            issues.append("engagement_by_views is undefined because total views is zero")

    latest = max(published_dates) if published_dates else None
    metrics = {
        "metric_window_complete": complete,
        "comment_total": quantize(comment_total, "1"),
        "average_comments": quantize(average_comments, "0.01"),
        "average_views": quantize(average_views, "0.01"),
        "engagement_by_views": quantize(engagement, "0.0001"),
        "latest_upload_date": latest.isoformat() if latest else None,
    }
    return selected, metrics, issues


def add_failure(
    failures: list[dict[str, Any]],
    gate: str,
    actual: Decimal,
    required: Decimal,
    relation: str,
) -> None:
    if relation == "minimum":
        gap = (required - actual) / required if required > 0 else Decimal("1")
        message = f"{gate} is below the required minimum"
    else:
        gap = (actual - required) / required if required > 0 else Decimal("1")
        message = f"{gate} exceeds the allowed maximum"
    failures.append(
        {
            "gate": gate,
            "message": message,
            "actual": quantize(actual, "0.0001"),
            "required": quantize(required, "0.0001"),
            "gap_ratio": quantize(max(gap, Decimal("0")), "0.0001"),
            "near_eligible": True,
        }
    )


def evaluate_candidate(
    candidate: dict[str, Any], criteria: dict[str, Any], weights: dict[str, Decimal]
) -> dict[str, Any]:
    result = dict(candidate)
    failures: list[dict[str, Any]] = []
    issues: list[str] = []

    count = integer_value(criteria.get("recent_video_count", 3), "recent_video_count", minimum=1)
    content_type = normalize_content_type(
        criteria.get("recent_content_type", "longform"), "recent_content_type"
    )
    raw_videos = candidate.get("recent_videos")
    if not isinstance(raw_videos, list):
        raw_videos = []
        issues.append("recent_videos is missing or is not an array")
    selected, metrics, video_issues = derive_metrics(raw_videos, content_type, count)
    issues.extend(video_issues)
    result["selected_videos"] = selected
    result.update(metrics)

    subscriber = decimal_value(candidate.get("subscriber_count"), "subscriber_count")
    subscriber_min = decimal_value(criteria.get("subscriber_min"), "subscriber_min")
    subscriber_max = decimal_value(criteria.get("subscriber_max"), "subscriber_max")
    if subscriber is None:
        if subscriber_min is not None or subscriber_max is not None:
            issues.append("subscriber_count is unverified")
    elif subscriber < 0 or subscriber != subscriber.to_integral_value():
        raise InputError("subscriber_count must be a non-negative integer")
    else:
        if subscriber_min is not None and subscriber < subscriber_min:
            add_failure(failures, "subscriber_count", subscriber, subscriber_min, "minimum")
        if subscriber_max is not None and subscriber > subscriber_max:
            add_failure(failures, "subscriber_count", subscriber, subscriber_max, "maximum")

    numeric_gates = (
        ("comment_total", "minimum_comment_total"),
        ("average_comments", "minimum_average_comments"),
        ("average_views", "minimum_average_views"),
        ("engagement_by_views", "minimum_engagement_by_views"),
    )
    for metric_name, criterion_name in numeric_gates:
        required = decimal_value(criteria.get(criterion_name), criterion_name)
        if required is None:
            continue
        actual = decimal_value(result.get(metric_name), metric_name)
        if actual is None:
            issues.append(f"{metric_name} cannot be verified for required gate {criterion_name}")
        elif actual < required:
            add_failure(failures, metric_name, actual, required, "minimum")

    evaluation_raw = criteria.get("evaluation_date")
    evaluation_date = (
        parse_date(evaluation_raw, "evaluation_date")
        if evaluation_raw is not None
        else datetime.now().astimezone().date()
    )
    latest_raw = metrics.get("latest_upload_date")
    latest_date = parse_date(latest_raw, "latest_upload_date") if latest_raw else None
    days_since = (evaluation_date - latest_date).days if latest_date else None
    result["days_since_latest_upload"] = days_since
    recency = decimal_value(criteria.get("upload_recency_days"), "upload_recency_days")
    if recency is not None:
        if recency < 0:
            raise InputError("upload_recency_days cannot be negative")
        if days_since is None:
            issues.append("latest upload date is unverified")
        elif days_since < 0:
            issues.append("latest upload date is after evaluation_date")
        elif Decimal(days_since) > recency:
            add_failure(
                failures,
                "days_since_latest_upload",
                Decimal(days_since),
                recency,
                "maximum",
            )

    sponsored_required = criteria.get("sponsored_content_required", False)
    if not isinstance(sponsored_required, bool):
        raise InputError("sponsored_content_required must be boolean")
    sponsored_verified = candidate.get("sponsored_content_verified")
    if sponsored_required:
        if sponsored_verified is None:
            issues.append("sponsored_content_verified is unverified")
        elif sponsored_verified is not True:
            failures.append(
                {
                    "gate": "sponsored_content_required",
                    "message": "verified sponsored-content experience is required",
                    "actual": False,
                    "required": True,
                    "gap_ratio": None,
                    "near_eligible": False,
                }
            )
        elif not nonempty(candidate.get("sponsorship_evidence")):
            issues.append("sponsorship_evidence is missing")

    require_evidence = criteria.get("require_complete_evidence", True)
    if not isinstance(require_evidence, bool):
        raise InputError("require_complete_evidence must be boolean")
    if require_evidence:
        if not nonempty(candidate.get("channel_url")):
            issues.append("channel_url is missing")
        if not nonempty(candidate.get("checked_at")):
            issues.append("checked_at is missing")
        if not nonempty(candidate.get("product_relevance_evidence")):
            issues.append("product_relevance_evidence is missing")

    weighted_sum = Decimal("0")
    coverage = Decimal("0")
    missing_scores: list[str] = []
    for component, weight in weights.items():
        value = score_value(candidate, SCORE_FIELDS[component])
        if value is None:
            missing_scores.append(component)
        else:
            weighted_sum += value * weight
            coverage += weight
    result["score_coverage"] = quantize(coverage * Decimal("100"), "0.01")
    result["score_components_missing"] = missing_scores
    result["weighted_recommendation_score"] = (
        quantize(weighted_sum / Decimal("5") * Decimal("100"), "0.01")
        if not missing_scores
        else None
    )

    tolerance = decimal_value(
        criteria.get("near_match_tolerance", "0.20"), "near_match_tolerance", allow_none=False
    )
    assert tolerance is not None
    if tolerance < 0:
        raise InputError("near_match_tolerance cannot be negative")

    if issues:
        status = "UNVERIFIED"
    elif not failures:
        status = "PASS"
    elif (
        len(failures) == 1
        and failures[0]["near_eligible"]
        and failures[0]["gap_ratio"] is not None
        and Decimal(str(failures[0]["gap_ratio"])) <= tolerance
    ):
        status = "NEAR MATCH"
    else:
        status = "FAIL"

    result["status"] = status
    result["failure_reasons"] = failures
    result["verification_issues"] = list(dict.fromkeys(issues))
    return result


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    criteria = payload.get("criteria")
    candidates = payload.get("candidates")
    if not isinstance(criteria, dict):
        raise InputError("criteria must be an object")
    if not isinstance(candidates, list):
        raise InputError("candidates must be an array")
    weights = load_weights(criteria)
    evaluated: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise InputError(f"candidates[{index}] must be an object")
        try:
            evaluated.append(evaluate_candidate(candidate, criteria, weights))
        except InputError as exc:
            raise InputError(f"candidates[{index}]: {exc}") from exc

    counts = {status: 0 for status in ("PASS", "NEAR MATCH", "FAIL", "UNVERIFIED")}
    for candidate in evaluated:
        counts[candidate["status"]] += 1
    result = {
        "criteria": criteria,
        "summary": {"candidate_count": len(evaluated), "status_counts": counts},
        "candidates": evaluated,
    }
    report_metadata = payload.get("report_metadata")
    if report_metadata is not None:
        if not isinstance(report_metadata, dict):
            raise InputError("report_metadata must be an object when provided")
        result["report_metadata"] = report_metadata
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate verified YouTube influencer metrics and gate statuses."
    )
    parser.add_argument("--input", type=Path, help="JSON input file; stdin when omitted")
    parser.add_argument("--output", type=Path, help="JSON output file; stdout when omitted")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        result = evaluate(payload)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    try:
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except OSError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
