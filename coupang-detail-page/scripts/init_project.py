#!/usr/bin/env python3
"""Create the next numbered Coupang detail-page input/output project."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_PATTERN = re.compile(r"^[0-9]{3}$")
PRODUCT_INFO_TEMPLATE = """# 상품 정보

프로젝트 번호: {project_no}

## 기본 정보

상품명:
카테고리:
브랜드명:

## 핵심 장점 3가지

1.
2.
3.

## 고객과 사용

타깃 고객:
대표 불편:
사용 상황:
사용 방법:

## 상품 사양

구성품:
소재/재질:
색상:
사이즈:
중량:
제조국:
관리/세탁/보관 방법:
주의사항:

## 광고 근거

경쟁 제품 대비 검증된 차별점:
강조할 분위기:
객관적인 수치/인증/시험 정보: 없음
사용하면 안 되는 표현:

## 입력 이미지

- 원본 상품 이미지: `original-images/`
- 실제 스타일 레퍼런스: `real-references/`
"""


def existing_numbers(skill_root: Path) -> set[int]:
    numbers: set[int] = set()
    for folder_name in ("inputs", "outputs"):
        base = skill_root / folder_name
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if child.is_dir() and PROJECT_PATTERN.fullmatch(child.name):
                numbers.add(int(child.name))
    return numbers


def choose_number(skill_root: Path, requested: int | None) -> int:
    used = existing_numbers(skill_root)
    if requested is not None:
        if not 1 <= requested <= 999:
            raise ValueError("project number must be between 1 and 999")
        if requested in used:
            raise FileExistsError(f"project {requested:03d} already exists")
        return requested
    number = max(used, default=0) + 1
    if number > 999:
        raise ValueError("no project numbers remain in the 001-999 range")
    return number


def initialize(skill_root: Path, number: int) -> tuple[Path, Path]:
    project_no = f"{number:03d}"
    input_root = skill_root / "inputs" / project_no
    output_root = skill_root / "outputs" / project_no

    if input_root.exists() or output_root.exists():
        raise FileExistsError(f"project {project_no} already exists")

    empty_directories = (
        input_root / "original-images",
        input_root / "real-references",
        output_root / "raw" / "retries",
        output_root / "final",
    )
    for directory in empty_directories:
        directory.mkdir(parents=True)
        (directory / ".gitkeep").touch()
    (input_root / "product-info.md").write_text(
        PRODUCT_INFO_TEMPLATE.format(project_no=project_no), encoding="utf-8"
    )
    return input_root, output_root


def prepare(skill_root: Path, number: int) -> tuple[Path, Path, bool]:
    """Idempotently prepare a starter/runtime project without overwriting data."""

    if not 1 <= number <= 999:
        raise ValueError("project number must be between 1 and 999")
    project_no = f"{number:03d}"
    input_root = skill_root / "inputs" / project_no
    output_root = skill_root / "outputs" / project_no
    empty_directories = (
        input_root / "original-images",
        input_root / "real-references",
        output_root / "raw" / "retries",
        output_root / "final",
    )
    for directory in empty_directories:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)
    info_path = input_root / "product-info.md"
    created = not info_path.exists()
    if created:
        info_path.write_text(
            PRODUCT_INFO_TEMPLATE.format(project_no=project_no), encoding="utf-8"
        )
    return input_root, output_root, created


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create inputs/NNN and outputs/NNN for a new detail-page project."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--number",
        type=int,
        help="Explicit project number from 1 to 999; default is max existing number plus one",
    )
    group.add_argument(
        "--prepare",
        type=int,
        metavar="NUMBER",
        help="Idempotently prepare an existing starter project without overwriting it",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    try:
        if args.prepare is not None:
            input_root, output_root, created = prepare(skill_root, args.prepare)
            print(f"PROJECT={args.prepare:03d}")
            print(f"PRODUCT_INFO={'CREATED' if created else 'PRESERVED'}")
            print(f"INPUTS={input_root}")
            print(f"OUTPUTS={output_root}")
            return 0
        number = choose_number(skill_root, args.number)
        input_root, output_root = initialize(skill_root, number)
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"PROJECT={number:03d}")
    print(f"INPUTS={input_root}")
    print(f"OUTPUTS={output_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
