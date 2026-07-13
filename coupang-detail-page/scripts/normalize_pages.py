#!/usr/bin/env python3
"""Normalize page-01..page-10 to 780x3000 using Pillow or macOS sips."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pillow_runtime import load_pillow
from validate_pages import TARGET_HEIGHT, TARGET_WIDTH, image_size, validate


TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT
SOURCE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".avif"}


def find_pages(directory: Path) -> list[Path]:
    pages: list[Path] = []
    for number in range(1, 11):
        matches = [
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in SOURCE_EXTENSIONS
            and path.stem == f"page-{number:02d}"
        ]
        if len(matches) != 1:
            raise ValueError(
                f"page-{number:02d}: expected exactly one source image, found {len(matches)}"
            )
        pages.append(matches[0])
    return pages


def crop_box(width: int, height: int) -> tuple[int, int, int, int]:
    ratio = width / height
    if ratio > TARGET_RATIO:
        crop_width = round(height * TARGET_RATIO)
        left = (width - crop_width) // 2
        return left, 0, left + crop_width, height
    crop_height = round(width / TARGET_RATIO)
    top = (height - crop_height) // 2
    return 0, top, width, top + crop_height


def normalize_with_pillow(source: Path, destination: Path, allow_crop: bool) -> None:
    from PIL import Image, ImageOps

    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert("RGB")
        ratio_error = abs((image.width / image.height) - TARGET_RATIO) / TARGET_RATIO
        if ratio_error > 0.02:
            if not allow_crop:
                raise ValueError(
                    f"{source.name}: aspect ratio differs by {ratio_error:.1%}; inspect and regenerate or use --allow-center-crop"
                )
            image = image.crop(crop_box(image.width, image.height))
        image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        image.save(destination, format="PNG", optimize=True)


def run_sips(arguments: list[str]) -> None:
    subprocess.run(["sips", *arguments], check=True, stdout=subprocess.DEVNULL)


def normalize_with_sips(source: Path, destination: Path, allow_crop: bool) -> None:
    width, height = image_size(source)
    ratio_error = abs((width / height) - TARGET_RATIO) / TARGET_RATIO
    with tempfile.TemporaryDirectory(prefix="coupang-page-") as temp_dir:
        working = source
        if ratio_error > 0.02:
            if not allow_crop:
                raise ValueError(
                    f"{source.name}: aspect ratio differs by {ratio_error:.1%}; inspect and regenerate or use --allow-center-crop"
                )
            left, top, right, bottom = crop_box(width, height)
            crop_width = right - left
            crop_height = bottom - top
            cropped = Path(temp_dir) / "cropped.png"
            run_sips(["-c", str(crop_height), str(crop_width), str(source), "--out", str(cropped)])
            working = cropped
        run_sips(
            [
                "-s",
                "format",
                "png",
                "-z",
                str(TARGET_HEIGHT),
                str(TARGET_WIDTH),
                str(working),
                "--out",
                str(destination),
            ]
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create exact 780x3000 PNGs from page-01..page-10 source images."
    )
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--allow-center-crop",
        action="store_true",
        help="Center-crop mismatched ratios only after visually confirming the central safe area",
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        parser.error(f"not a directory: {args.source_dir}")
    if args.source_dir.resolve() == args.output_dir.resolve():
        parser.error("source_dir and output_dir must be different")

    try:
        pages = find_pages(args.source_dir)
    except ValueError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    try:
        load_pillow(install=False)
        backend = "Pillow"
        normalizer = normalize_with_pillow
    except ImportError:
        if shutil.which("sips"):
            backend = "sips"
            normalizer = normalize_with_sips
        else:
            try:
                load_pillow(install=True)
                backend = "Pillow (isolated runtime)"
                normalizer = normalize_with_pillow
            except (ImportError, OSError, subprocess.CalledProcessError) as exc:
                print(f"FAILED: could not prepare image runtime: {exc}", file=sys.stderr)
                return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    placeholder = args.output_dir / ".gitkeep"
    existing_entries = [
        entry
        for entry in args.output_dir.iterdir()
        if entry != placeholder or not entry.is_file()
    ]
    if existing_entries:
        print(
            "FAILED: output_dir must be empty; use a new directory to avoid overwriting existing work.",
            file=sys.stderr,
        )
        return 1

    created: list[Path] = []
    try:
        for number, source in enumerate(pages, start=1):
            destination = args.output_dir / f"page-{number:02d}.png"
            created.append(destination)
            normalizer(source, destination, args.allow_center_crop)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        for path in created:
            path.unlink(missing_ok=True)
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    report = validate(args.output_dir)
    if not report["ok"]:
        for path in created:
            path.unlink(missing_ok=True)
        print("FAILED after normalization:", file=sys.stderr)
        for error in report["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1

    placeholder.unlink(missing_ok=True)
    print(f"OK: normalized 10 pages with {backend}; every image is 780x3000.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
