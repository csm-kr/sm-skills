#!/usr/bin/env python3
"""Insert approved Korean copy into a blank copy area with deterministic layout."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from pillow_runtime import load_pillow


FONT_CANDIDATES = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/AppleGothic.ttf",
    "/Library/Fonts/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
    "C:/Windows/Fonts/malgun.ttf",
)


def parse_box(value: str, width: int, height: int) -> tuple[int, int, int, int]:
    try:
        numbers = [float(item.strip()) for item in value.split(",")]
    except ValueError as exc:
        raise ValueError("box must be x,y,width,height") from exc
    if len(numbers) != 4:
        raise ValueError("box must contain four comma-separated numbers")
    if all(0 <= number <= 1 for number in numbers):
        x, y, box_width, box_height = numbers
        numbers = [x * width, y * height, box_width * width, box_height * height]
    x, y, box_width, box_height = [round(number) for number in numbers]
    if x < 0 or y < 0 or box_width <= 0 or box_height <= 0:
        raise ValueError("box coordinates must be non-negative and dimensions positive")
    if x + box_width > width or y + box_height > height:
        raise ValueError("box extends outside the input image")
    return x, y, box_width, box_height


def font_supports_korean(path: Path) -> bool:
    _, _, ImageFont, _ = load_pillow(install=False)
    try:
        font = ImageFont.truetype(str(path), size=40)
        signatures = []
        for character in ("가", "나", "힣"):
            mask = font.getmask(character)
            signatures.append((mask.size, bytes(mask)))
        return len(set(signatures)) == len(signatures)
    except OSError:
        return False


def find_font(explicit: str | None) -> Path:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    environment_font = os.environ.get("COUPANG_KOREAN_FONT")
    if environment_font:
        candidates.append(environment_font)
    candidates.extend(FONT_CANDIDATES)
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file() and font_supports_korean(path):
            return path

    if shutil.which("fc-match"):
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", "Noto Sans CJK KR"],
            check=False,
            capture_output=True,
            text=True,
        )
        path = Path(result.stdout.strip())
        if result.returncode == 0 and path.is_file() and font_supports_korean(path):
            return path
    raise FileNotFoundError(
        "Korean-capable font not found; pass --font /path/to/Korean-font.ttf (or .ttc)"
    )


def wrap_text(draw, text: str, font, max_width: int) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for token in paragraph.split(" "):
            proposal = token if not current else f"{current} {token}"
            if draw.textlength(proposal, font=font) <= max_width:
                current = proposal
                continue
            if current:
                lines.append(current)
                current = ""
            while token and draw.textlength(token, font=font) > max_width:
                split_at = len(token)
                while split_at > 0 and draw.textlength(token[:split_at], font=font) > max_width:
                    split_at -= 1
                if split_at == 0:
                    raise ValueError("copy box is narrower than one glyph at this font size")
                lines.append(token[:split_at])
                token = token[split_at:]
            current = token
        lines.append(current)
    return "\n".join(lines)


def fit_text(draw, text: str, font_path: Path, max_size: int, min_size: int, box_width: int, box_height: int, spacing: int):
    _, _, ImageFont, _ = load_pillow(install=False)
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        try:
            wrapped = wrap_text(draw, text, font, box_width)
        except ValueError:
            continue
        bounds = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=spacing)
        rendered_width = bounds[2] - bounds[0]
        rendered_height = bounds[3] - bounds[1]
        if rendered_width <= box_width and rendered_height <= box_height:
            return font, wrapped, rendered_width, rendered_height
    raise ValueError(
        f"approved copy does not fit the box at minimum font size {min_size}; enlarge the box or shorten approved copy"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Overlay exact approved copy on an image; installs Pillow into .runtime on first real use."
    )
    parser.add_argument("input", type=Path, help="Text-free source image")
    parser.add_argument("output", type=Path, help="New PNG output path")
    parser.add_argument("--text", required=True, help="Exact approved Korean copy")
    parser.add_argument(
        "--box",
        required=True,
        help="x,y,width,height in pixels, or 0..1 fractions such as 0.1,0.1,0.8,0.2",
    )
    parser.add_argument("--font", help="Korean .ttf/.otf/.ttc font; auto-detected when omitted")
    parser.add_argument("--font-size", type=int, default=96)
    parser.add_argument("--min-font-size", type=int, default=32)
    parser.add_argument("--color", default="#111111")
    parser.add_argument("--background", help="Optional copy-box fill color, e.g. #FFFFFF")
    parser.add_argument("--align", choices=("left", "center", "right"), default="center")
    parser.add_argument("--valign", choices=("top", "center", "bottom"), default="center")
    parser.add_argument("--spacing", type=int, default=20)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input image not found: {args.input}")
    if args.output.exists() and not args.overwrite:
        parser.error(f"output already exists (use --overwrite to replace): {args.output}")
    if args.font_size < args.min_font_size or args.min_font_size < 8:
        parser.error("font sizes must satisfy font-size >= min-font-size >= 8")

    try:
        Image, ImageDraw, _, ImageOps = load_pillow(install=True)
        font_path = find_font(args.font)
        with Image.open(args.input) as raw:
            raw.load()
            image = ImageOps.exif_transpose(raw).convert("RGB")
        x, y, box_width, box_height = parse_box(args.box, image.width, image.height)
        draw = ImageDraw.Draw(image)
        if args.background:
            draw.rectangle((x, y, x + box_width, y + box_height), fill=args.background)
        font, wrapped, text_width, text_height = fit_text(
            draw,
            args.text,
            font_path,
            args.font_size,
            args.min_font_size,
            box_width,
            box_height,
            args.spacing,
        )
        if args.align == "left":
            text_x = x
        elif args.align == "right":
            text_x = x + box_width - text_width
        else:
            text_x = x + (box_width - text_width) // 2
        if args.valign == "top":
            text_y = y
        elif args.valign == "bottom":
            text_y = y + box_height - text_height
        else:
            text_y = y + (box_height - text_height) // 2
        draw.multiline_text(
            (text_x, text_y),
            wrapped,
            font=font,
            fill=args.color,
            spacing=args.spacing,
            align=args.align,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output, format="PNG", optimize=True)
    except (FileNotFoundError, OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"OK: inserted approved copy with {font_path} -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
