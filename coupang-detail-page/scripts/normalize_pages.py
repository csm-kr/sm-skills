#!/usr/bin/env python3
"""Normalize page-01..page-10 to 800x2400 using strict Pillow decoding."""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

from pillow_runtime import load_pillow
from validate_pages import TARGET_HEIGHT, TARGET_WIDTH, validate


TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT
TARGET_UNIT_GCD = math.gcd(TARGET_WIDTH, TARGET_HEIGHT)
TARGET_RATIO_WIDTH = TARGET_WIDTH // TARGET_UNIT_GCD
TARGET_RATIO_HEIGHT = TARGET_HEIGHT // TARGET_UNIT_GCD
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


def padded_canvas_size(width: int, height: int) -> tuple[int, int]:
    """Return the smallest exact 1:3 canvas that contains the source."""

    scale = math.ceil(
        max(width / TARGET_RATIO_WIDTH, height / TARGET_RATIO_HEIGHT)
    )
    return TARGET_RATIO_WIDTH * scale, TARGET_RATIO_HEIGHT * scale


def sample_corner_background(image) -> tuple[int, int, int]:
    """Estimate a conservative solid background color from four corner patches."""

    from PIL import ImageStat

    patch_size = max(1, min(64, image.width // 10, image.height // 10))
    boxes = (
        (0, 0, patch_size, patch_size),
        (image.width - patch_size, 0, image.width, patch_size),
        (0, image.height - patch_size, patch_size, image.height),
        (
            image.width - patch_size,
            image.height - patch_size,
            image.width,
            image.height,
        ),
    )
    means = [ImageStat.Stat(image.crop(box)).mean[:3] for box in boxes]
    channels: list[int] = []
    for channel in range(3):
        values = sorted(mean[channel] for mean in means)
        channels.append(round((values[1] + values[2]) / 2))
    return tuple(channels)


def pad_to_target_ratio(image):
    """Center the full source on a sampled-color canvas without cropping it."""

    from PIL import Image

    canvas_width, canvas_height = padded_canvas_size(image.width, image.height)
    canvas = Image.new(
        "RGB",
        (canvas_width, canvas_height),
        sample_corner_background(image),
    )
    left = (canvas_width - image.width) // 2
    top = (canvas_height - image.height) // 2
    canvas.paste(image, (left, top))
    return canvas


def normalize_with_pillow(
    source: Path,
    destination: Path,
    allow_crop: bool = False,
    allow_background_pad: bool = False,
) -> None:
    from PIL import Image, ImageOps

    if allow_crop and allow_background_pad:
        raise ValueError(
            "--allow-center-crop and --allow-background-pad cannot be used together"
        )

    with Image.open(source) as probe:
        probe.verify()
    with Image.open(source) as raw:
        raw.load()
        image = ImageOps.exif_transpose(raw).convert("RGB")
        ratio_error = abs((image.width / image.height) - TARGET_RATIO) / TARGET_RATIO
        if ratio_error > 0.02:
            if allow_background_pad:
                image = pad_to_target_ratio(image)
            elif allow_crop:
                image = image.crop(crop_box(image.width, image.height))
            else:
                raise ValueError(
                    f"{source.name}: aspect ratio differs by {ratio_error:.1%}; "
                    "inspect and regenerate, use --allow-background-pad, or use --allow-center-crop"
                )
        image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        image.save(destination, format="PNG", optimize=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create exact 800x2400 PNGs from page-01..page-10 source images."
    )
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    ratio_mode = parser.add_mutually_exclusive_group()
    ratio_mode.add_argument(
        "--allow-center-crop",
        action="store_true",
        help="Center-crop mismatched ratios only after visually confirming the central safe area",
    )
    ratio_mode.add_argument(
        "--allow-background-pad",
        action="store_true",
        help="Preserve the full image and pad to 1:3 with a color sampled from its corners",
    )
    return parser


def main() -> int:
    parser = build_parser()
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
        load_pillow(install=True)
        backend = "Pillow"
        normalizer = normalize_with_pillow
    except (ImportError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"FAILED: could not prepare strict image runtime: {exc}", file=sys.stderr)
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
            normalizer(
                source,
                destination,
                allow_crop=args.allow_center_crop,
                allow_background_pad=args.allow_background_pad,
            )
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
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
    print(f"OK: normalized 10 pages with {backend}; every image is 800x2400.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
