#!/usr/bin/env python3
"""Validate ten final PNGs by fully decoding every image."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from pillow_runtime import load_pillow


TARGET_WIDTH = 800
TARGET_HEIGHT = 2400
EXTENSIONS = {".png"}
DISCOVERABLE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


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


def validate(directory: Path) -> dict[str, object]:
    errors: list[str] = []
    pages: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    image_files = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in DISCOVERABLE_IMAGE_EXTENSIONS
    )

    expected: set[Path] = set()
    for number in range(1, 11):
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

    extras = [path.name for path in image_files if path not in expected]
    if extras:
        errors.append("unexpected final image files: " + ", ".join(extras))

    return {
        "ok": not errors,
        "directory": str(directory.resolve()),
        "expected_count": 10,
        "actual_image_count": len(image_files),
        "target_size": [TARGET_WIDTH, TARGET_HEIGHT],
        "pages": pages,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate exactly ten page-01..page-10 images at 800x2400."
    )
    parser.add_argument("directory", type=Path, help="Final image directory")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")

    report = validate(args.directory)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print("OK: 10 images found; every image is 800x2400.")
    else:
        print("FAILED:")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
