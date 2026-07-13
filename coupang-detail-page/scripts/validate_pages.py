#!/usr/bin/env python3
"""Validate ten final PNGs by fully decoding every image."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from pillow_runtime import load_pillow


TARGET_WIDTH = 780
TARGET_HEIGHT = 3000
EXTENSIONS = {".png"}
DISCOVERABLE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def png_header_size(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    return None


def jpeg_size(path: Path) -> tuple[int, int] | None:
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    with path.open("rb") as stream:
        if stream.read(2) != b"\xff\xd8":
            return None
        while True:
            byte = stream.read(1)
            if not byte:
                return None
            if byte != b"\xff":
                continue
            while byte == b"\xff":
                byte = stream.read(1)
            marker = byte[0]
            if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
                continue
            raw_length = stream.read(2)
            if len(raw_length) != 2:
                return None
            length = struct.unpack(">H", raw_length)[0]
            if length < 2:
                return None
            if marker in sof_markers:
                payload = stream.read(5)
                if len(payload) != 5:
                    return None
                height, width = struct.unpack(">HH", payload[1:5])
                return width, height
            stream.seek(length - 2, 1)


def webp_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height
    return None


def _decode_with_pillow(path: Path, required_format: str | None) -> tuple[int, int]:
    Image, _, _, _ = load_pillow(install=False)
    with Image.open(path) as image:
        detected_format = image.format
        image.load()
        size = image.size
    if required_format and detected_format != required_format:
        raise ValueError(
            f"expected decoded format {required_format}, got {detected_format or 'unknown'}"
        )
    return size


def _decode_with_sips(path: Path, required_format: str | None) -> tuple[int, int]:
    if required_format == "PNG" and not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("expected decoded format PNG")
    with tempfile.TemporaryDirectory(prefix="coupang-decode-") as temp_dir:
        probe = Path(temp_dir) / "decoded.png"
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(path), "--out", str(probe)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not probe.is_file():
            message = (result.stderr or result.stdout).strip().splitlines()
            detail = message[-1] if message else f"sips exit {result.returncode}"
            raise ValueError(f"image decode failed: {detail}")
        data = probe.read_bytes()
        size = png_header_size(data)
        if not size:
            raise ValueError("image decode produced an invalid PNG")
    if required_format and path.suffix.lower() != f".{required_format.lower()}":
        raise ValueError(f"expected {required_format} filename extension")
    return size


def image_size(path: Path, required_format: str | None = None) -> tuple[int, int]:
    """Fully decode an image and return its dimensions; never trust headers alone."""

    try:
        return _decode_with_pillow(path, required_format)
    except ImportError:
        pass
    if shutil.which("sips"):
        return _decode_with_sips(path, required_format)
    try:
        load_pillow(install=True)
        return _decode_with_pillow(path, required_format)
    except (ImportError, OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(
            "cannot fully decode images; Pillow runtime setup failed and macOS sips is unavailable"
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
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
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
        description="Validate exactly ten page-01..page-10 images at 780x3000."
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
        print("OK: 10 images found; every image is 780x3000.")
    else:
        print("FAILED:")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
