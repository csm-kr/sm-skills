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
모델명/SKU:
제품 라벨 표기:
검색 식별 키워드:

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

WEB_RESEARCH_TEMPLATE = """# 웹 리서치

프로젝트 번호: {project_no}
조사일:
조사 상태: 미완료
동일 제품 결론:

## 근거 등급

- 동일성: M1 확정 / M2 유력 / M3 유사 / M0 불일치·확인 불가
- 출처: E1 공식 / E2 신뢰 판매처 / E3 마켓플레이스·개인 판매 / E4 카테고리 자료

## 검색 기록

| 유형 | 검색어 | URL 또는 검색 결과 없음 | 동일성 | 출처 | 확인한 내용 | 기획 사용 범위 | 제외할 주장 |
|---|---|---|---|---|---|---|---|
| 동일 제품 |  |  | M0 |  |  |  |  |
| 유사 제품 |  |  | M3 | E4 |  |  |  |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  |

## 기획에 채택한 연구 인사이트

1.
2.
3.
"""

FACT_LEDGER_TEMPLATE = """# 사실·카피 원장

프로젝트 번호: {project_no}

## allowed facts

## approved copy manifest

| 장 | 설득 목적 | 후킹 각도 | EYEBROW | H1 | BODY | CARD·CHIP·CAPTION | CTA | 근거 Fact ID | 읽는 순서 |
|---|---|---|---|---|---|---|---|---|---|

## forbidden claims
"""

PROMPT_SET_TEMPLATE = """# image_gen 프롬프트 세트

프로젝트 번호: {project_no}

## COPY_SYSTEM

- 카피 매니페스트: EYEBROW / H1 / BODY / CARD·CHIP / CAPTION / CTA
- 정보 밀도: 한 장당 3~6개 세로 정보 구역, 구역마다 한 메시지
- 정확성: 모든 승인 문자열을 직접 조판하고 누락·축약·의역·추가 금지

## TYPOGRAPHY_SYSTEM

- 800px 원본: H1 72~104px / H2 44~64px / BODY 32~40px / 라벨·캡션 최소 32px
- 10장 동일한 한국어 산세리프 한 계열과 굵기 토큰

## DESIGN_SYSTEM

## 10장 프롬프트와 실행 기록

| 장 | 역할·정보 구역 | 카피 매니페스트 | 입력 경로 | 최종 프롬프트 | 시도 | raw 출력 | 상태 |
|---|---|---|---|---|---|---|---|
"""

DETAIL_PAGE_ANALYSIS_TEMPLATE = """# 상세페이지 비교 분석

프로젝트 번호: {project_no}
조사일:

## 접근 상태

- 차단된 URL과 확인하지 못한 범위를 기록한다.

## 비교한 페이지

| 페이지 | 확인한 구조 | 채택할 패턴 | 가져오지 않는 것 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

## 공통 패턴

1.
2.
3.

## 프로젝트 적용 결정

- 한 장당 3~6개 세로 정보 구역
- H1 72~104px / H2 44~64px / BODY 32~40px / 라벨·캡션 최소 32px
"""

QA_REPORT_TEMPLATE = """# 장별 QA 보고서

프로젝트 번호: {project_no}

| 장 | 시도 | TEXT | PRODUCT | LAYOUT | CLAIMS | 판정 | 실패 사유 | 최종 파일 |
|---|---|---|---|---|---|---|---|---|
"""

MOTION_PLAN_TEMPLATE = """# GIF·영상·ComfyUI 모션 계획

프로젝트 번호: {project_no}
ComfyUI 상태: HANDOFF_ONLY

| 장 | 정지/GIF/영상 | 추천 이유 | 움직임 아이디어 | 시작·끝 프레임 | 길이/FPS/루프 | 입력 경로 | 제품 불변 요소 | 상태 |
|---|---|---|---|---|---|---|---|---|
"""

OUTPUT_TEMPLATES = {
    "web-research.md": WEB_RESEARCH_TEMPLATE,
    "detail-page-analysis.md": DETAIL_PAGE_ANALYSIS_TEMPLATE,
    "fact-ledger.md": FACT_LEDGER_TEMPLATE,
    "prompt-set.md": PROMPT_SET_TEMPLATE,
    "qa-report.md": QA_REPORT_TEMPLATE,
    "motion-plan.md": MOTION_PLAN_TEMPLATE,
}


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
    for filename, template in OUTPUT_TEMPLATES.items():
        (output_root / filename).write_text(
            template.format(project_no=project_no), encoding="utf-8"
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
    for filename, template in OUTPUT_TEMPLATES.items():
        path = output_root / filename
        if not path.exists():
            path.write_text(template.format(project_no=project_no), encoding="utf-8")
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
