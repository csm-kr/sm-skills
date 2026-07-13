#!/usr/bin/env python3
"""Validate a contiguous 3..10 page PNG set by fully decoding every image."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from pillow_runtime import load_pillow


TARGET_WIDTH = 800
TARGET_HEIGHT = 2400
MIN_PAGE_COUNT = 3
MAX_PAGE_COUNT = 10
EXTENSIONS = {".png"}
DISCOVERABLE_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".heic",
    ".avif",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
}
PAGE_STEM_PATTERN = re.compile(r"^page-(\d{2})$")


def page_count(value: str) -> int:
    """Parse a CLI page count constrained to the supported range."""

    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("page count must be an integer") from exc
    if not MIN_PAGE_COUNT <= count <= MAX_PAGE_COUNT:
        raise argparse.ArgumentTypeError(
            f"page count must be between {MIN_PAGE_COUNT} and {MAX_PAGE_COUNT}"
        )
    return count


def _resolved_count(
    image_files: list[Path], expected_count: int | None
) -> tuple[int, list[str]]:
    """Resolve the requested or highest numbered page count."""

    errors: list[str] = []
    if expected_count is not None:
        if not MIN_PAGE_COUNT <= expected_count <= MAX_PAGE_COUNT:
            errors.append(
                f"expected count must be between {MIN_PAGE_COUNT} and {MAX_PAGE_COUNT}, "
                f"got {expected_count}"
            )
        return expected_count, errors

    numbers = [
        int(match.group(1))
        for path in image_files
        if (match := PAGE_STEM_PATTERN.fullmatch(path.stem))
    ]
    detected_count = max(numbers, default=0)
    if not MIN_PAGE_COUNT <= detected_count <= MAX_PAGE_COUNT:
        errors.append(
            f"auto-detected page count must be between {MIN_PAGE_COUNT} and "
            f"{MAX_PAGE_COUNT}, got {detected_count}"
        )
    return detected_count, errors


def _decode_with_pillow(path: Path, required_format: str | None) -> tuple[int, int]:
    Image, _, _, _ = load_pillow(install=False)
    with Image.open(path) as probe:
        detected_format = probe.format
        probe.verify()
    with Image.open(path) as image:
        image.load()
        size = image.size
    if required_format and detected_format != required_format:
        raise ValueError(
            f"expected decoded format {required_format}, got {detected_format or 'unknown'}"
        )
    return size


def image_size(path: Path, required_format: str | None = None) -> tuple[int, int]:
    """Fully decode an image and return its dimensions; never trust headers alone."""

    try:
        load_pillow(install=True)
        return _decode_with_pillow(path, required_format)
    except (ImportError, RuntimeError) as exc:
        raise ValueError(
            "cannot fully decode images; install Pillow or ensure python3 -m pip is available"
        ) from exc


def validate(directory: Path, expected_count: int | None = None) -> dict[str, object]:
    errors: list[str] = []
    pages: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    image_files = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in DISCOVERABLE_IMAGE_EXTENSIONS
    )

    resolved_count, count_errors = _resolved_count(image_files, expected_count)
    errors.extend(count_errors)

    numbered: dict[int, list[Path]] = {}
    for path in image_files:
        match = PAGE_STEM_PATTERN.fullmatch(path.stem)
        if match:
            numbered.setdefault(int(match.group(1)), []).append(path)

    for number, matches in sorted(numbered.items()):
        if len(matches) > 1:
            errors.append(
                f"page-{number:02d}: duplicate page number: "
                + ", ".join(path.name for path in matches)
            )

    expected: set[Path] = set()
    for number in range(1, resolved_count + 1):
        expected_name = f"page-{number:02d}.png"
        matches = [path for path in image_files if path.name == expected_name]
        if len(matches) != 1:
            errors.append(
                f"page-{number:02d}: expected exactly one {expected_name}, found {len(matches)}"
            )
            continue
        path = matches[0]
        expected.add(path)
        try:
            width, height = image_size(path, required_format="PNG")
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        ok = (width, height) == (TARGET_WIDTH, TARGET_HEIGHT)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        pages.append(
            {
                "page": number,
                "path": str(path.resolve()),
                "width": width,
                "height": height,
                "size_ok": ok,
                "sha256": digest,
            }
        )
        if not ok:
            errors.append(
                f"{path.name}: expected {TARGET_WIDTH}x{TARGET_HEIGHT}, got {width}x{height}"
            )
        if digest in hashes:
            errors.append(f"{path.name}: exact duplicate of {hashes[digest]}")
        else:
            hashes[digest] = path.name

    extras = [
        path.name
        for path in image_files
        if path not in expected
        and not (
            (match := PAGE_STEM_PATTERN.fullmatch(path.stem))
            and 1 <= int(match.group(1)) <= resolved_count
            and len(numbered.get(int(match.group(1)), [])) > 1
        )
    ]
    if extras:
        errors.append("unexpected final image files: " + ", ".join(extras))

    return {
        "ok": not errors,
        "directory": str(directory.resolve()),
        "expected_count": resolved_count,
        "actual_image_count": len(image_files),
        "target_size": [TARGET_WIDTH, TARGET_HEIGHT],
        "pages": pages,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a contiguous page-01..page-NN PNG set at 800x2400 "
            f"({MIN_PAGE_COUNT}..{MAX_PAGE_COUNT} pages)."
        )
    )
    parser.add_argument("directory", type=Path, help="Final image directory")
    parser.add_argument(
        "--expected-count",
        type=page_count,
        help="Require this many contiguous pages instead of auto-detecting the count",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")

    report = validate(args.directory, expected_count=args.expected_count)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(
            f"OK: {report['expected_count']} images found; "
            f"every image is {TARGET_WIDTH}x{TARGET_HEIGHT}."
        )
    else:
        print("FAILED:")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
