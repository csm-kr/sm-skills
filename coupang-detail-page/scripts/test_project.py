#!/usr/bin/env python3
"""Tests for numbered project initialization and input readiness checks."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from check_project import check
from init_project import choose_number, initialize, prepare
from normalize_pages import (
    build_parser,
    normalize_with_pillow,
    pad_to_target_ratio,
)
from pillow_runtime import load_pillow, runtime_site_packages
from run_overlay_copy import wrap_text
from validate_pages import image_size, validate


COMPLETE_PRODUCT_INFO = """# 상품 정보

프로젝트 번호: 001
상품명: 테스트 텀블러
카테고리: 주방용품
브랜드명: 없음
1. 휴대하기 쉬운 크기
2. 단순한 사용 방법
3. 세척하기 편한 구조
타깃 고객: 출퇴근 직장인
대표 불편: 일회용 컵 사용이 번거로움
사용 상황: 사무실과 이동 중
사용 방법: 음료를 담아 사용
구성품: 텀블러 본체와 뚜껑
소재/재질: 스테인리스
색상: 흰색
사이즈: 미제공
중량: 미제공
제조국: 미제공
관리/세탁/보관 방법: 사용 후 세척
주의사항: 뜨거운 음료 사용 시 주의
경쟁 제품 대비 검증된 차별점: 별도 근거 없음
강조할 분위기: 깔끔하고 실용적
객관적인 수치/인증/시험 정보: 없음
사용하면 안 되는 표현: 100%, 완벽, 최고
"""

COMPLETE_WEB_RESEARCH = """# 웹 리서치

프로젝트 번호: 001
조사일: 2026-07-13
조사 상태: 완료
동일 제품 결론: 검색 결과 없음

| 유형 | 검색어 | URL 또는 검색 결과 없음 | 동일성 | 출처 | 확인한 내용 | 기획 사용 범위 | 제외할 주장 |
|---|---|---|---|---|---|---|---|
| 동일 제품 | 테스트 텀블러 모델명 | 검색 결과 없음 | M0 | E4 | 동일 제품 미확인 | 결과 없음 기록 | 모든 상품 사실 |
| 유사 제품 | 흰색 휴대용 텀블러 | https://example.com/similar | M3 | E4 | 카테고리 구성 | 장면 아이디어만 | 기능·수치 |
| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 |
| 상세 구조 | 텀블러 상세페이지 B | https://example.com/b | M3 | E4 | 디테일 캡션 | 구조만 | 상품 사실 |
| 상세 구조 | 패션 상세페이지 C | https://example.com/c | M3 | E4 | 타이포 계층 | 구조만 | 상품 사실 |
"""

COMPLETE_DETAIL_PAGE_ANALYSIS = """# 상세페이지 비교 분석

## 비교한 페이지

- https://example.com/a
- https://example.com/b
- https://example.com/c

## 공통 패턴

1. 훅 다음에 설명과 카드가 이어진다.
2. 디테일마다 캡션이 있다.
3. 같은 타이포 계층을 유지한다.
"""


class ProjectWorkflowTest(unittest.TestCase):
    def test_initialize_and_choose_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            self.assertTrue((input_root / "product-info.md").is_file())
            self.assertTrue((input_root / "original-images").is_dir())
            self.assertTrue((output_root / "raw" / "retries").is_dir())
            self.assertTrue((output_root / "final").is_dir())
            for filename in (
                "web-research.md",
                "detail-page-analysis.md",
                "fact-ledger.md",
                "prompt-set.md",
                "qa-report.md",
                "motion-plan.md",
            ):
                self.assertTrue((output_root / filename).is_file())
            self.assertEqual(choose_number(root, None), 2)
            with self.assertRaises(FileExistsError):
                choose_number(root, 1)

    def test_check_rejects_blank_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize(root, 1)
            report = check(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(report["errors"])

    def test_check_accepts_complete_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "web-research.md").write_text(
                COMPLETE_WEB_RESEARCH, encoding="utf-8"
            )
            (output_root / "detail-page-analysis.md").write_text(
                COMPLETE_DETAIL_PAGE_ANALYSIS, encoding="utf-8"
            )
            (input_root / "original-images" / "front.png").write_bytes(b"fixture")
            report = check(root, "001")
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(len(report["original_images"]), 1)

    def test_check_accepts_conversation_only_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "web-research.md").write_text(
                COMPLETE_WEB_RESEARCH, encoding="utf-8"
            )
            (output_root / "detail-page-analysis.md").write_text(
                COMPLETE_DETAIL_PAGE_ANALYSIS, encoding="utf-8"
            )
            report = check(root, "001", conversation_original_count=1)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["conversation_original_count"], 1)
            self.assertFalse(report["original_images"])

    def test_check_rejects_project_without_completed_web_research(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, _ = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (input_root / "original-images" / "front.png").write_bytes(b"fixture")
            report = check(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("web research" in error for error in report["errors"]),
                report["errors"],
            )

    def test_check_rejects_more_than_five_conversation_originals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize(root, 1)
            with self.assertRaises(ValueError):
                check(root, "001", conversation_original_count=6)

    def test_prepare_is_idempotent_and_preserves_product_info(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, _, created = prepare(root, 1)
            self.assertTrue(created)
            info_path = input_root / "product-info.md"
            info_path.write_text("private facts", encoding="utf-8")
            _, _, created_again = prepare(root, 1)
            self.assertFalse(created_again)
            self.assertEqual(info_path.read_text(encoding="utf-8"), "private facts")

    def test_pillow_runtime_is_isolated_by_python_abi(self) -> None:
        self.assertIn(
            sys.implementation.cache_tag,
            runtime_site_packages().name,
        )

    def test_validate_rejects_truncated_png_with_claimed_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            final = Path(temp_dir)
            fake_header = (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + (800).to_bytes(4, "big")
                + (2400).to_bytes(4, "big")
            )
            for number in range(1, 11):
                (final / f"page-{number:02d}.png").write_bytes(
                    fake_header + bytes([number])
                )
            report = validate(final)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    "decode" in error
                    or "corrupt" in error
                    or "truncated" in error.lower()
                    for error in report["errors"]
                ),
                report["errors"],
            )

    def test_validate_rejects_non_png_final_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            final = Path(temp_dir)
            for number in range(1, 11):
                (final / f"page-{number:02d}.jpg").write_bytes(b"not an image")
            report = validate(final)
            self.assertFalse(report["ok"])
            self.assertTrue(any("unexpected" in error for error in report["errors"]))

    def test_strict_decode_rejects_half_truncated_png(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "truncated.png"
            Image, _, _, _ = load_pillow(install=True)
            Image.new("RGB", (800, 2400), "white").save(path, format="PNG")
            data = path.read_bytes()
            path.write_bytes(data[: len(data) // 2])
            with self.assertRaises((OSError, ValueError)):
                image_size(path, required_format="PNG")

    def test_background_padding_preserves_full_source_on_exact_ratio_canvas(self) -> None:
        Image, ImageDraw, _, _ = load_pillow(install=True)
        source = Image.new("RGB", (100, 100), "white")
        ImageDraw.Draw(source).rectangle((25, 25, 74, 74), fill="black")

        padded = pad_to_target_ratio(source)

        self.assertEqual(padded.size, (100, 300))
        self.assertEqual(padded.width * 3, padded.height)
        self.assertEqual(padded.getpixel((50, 150)), (0, 0, 0))
        self.assertEqual(padded.getpixel((0, 0)), (255, 255, 255))

    def test_normalize_requires_explicit_ratio_policy_and_accepts_padding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.png"
            destination = root / "destination.png"
            Image, _, _, _ = load_pillow(install=True)
            Image.new("RGB", (200, 100), "white").save(source, format="PNG")

            with self.assertRaisesRegex(ValueError, "aspect ratio differs"):
                normalize_with_pillow(source, destination)

            normalize_with_pillow(
                source,
                destination,
                allow_background_pad=True,
            )
            self.assertEqual(
                image_size(destination, required_format="PNG"),
                (800, 2400),
            )

    def test_ratio_adjustment_options_are_mutually_exclusive(self) -> None:
        parser = build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(
                    [
                        "source",
                        "output",
                        "--allow-center-crop",
                        "--allow-background-pad",
                    ]
                )

    def test_wrap_text_rejects_box_narrower_than_one_glyph(self) -> None:
        class AlwaysWideDraw:
            @staticmethod
            def textlength(_text, font=None):
                return 100

        with self.assertRaises(ValueError):
            wrap_text(AlwaysWideDraw(), "승", object(), 10)


if __name__ == "__main__":
    unittest.main()
