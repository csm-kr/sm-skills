#!/usr/bin/env python3
"""Tests for numbered project initialization and input readiness checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_project import check
from init_project import choose_number, initialize, prepare
from pillow_runtime import load_pillow
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


class ProjectWorkflowTest(unittest.TestCase):
    def test_initialize_and_choose_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            self.assertTrue((input_root / "product-info.md").is_file())
            self.assertTrue((input_root / "original-images").is_dir())
            self.assertTrue((output_root / "raw" / "retries").is_dir())
            self.assertTrue((output_root / "final").is_dir())
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
            input_root, _ = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (input_root / "original-images" / "front.png").write_bytes(b"fixture")
            report = check(root, "001")
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(len(report["original_images"]), 1)

    def test_check_accepts_conversation_only_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, _ = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            report = check(root, "001", conversation_original_count=1)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["conversation_original_count"], 1)
            self.assertFalse(report["original_images"])

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

    def test_validate_rejects_truncated_png_with_claimed_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            final = Path(temp_dir)
            fake_header = (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + (780).to_bytes(4, "big")
                + (3000).to_bytes(4, "big")
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
            Image.new("RGB", (780, 3000), "white").save(path, format="PNG")
            data = path.read_bytes()
            path.write_bytes(data[: len(data) // 2])
            with self.assertRaises((OSError, ValueError)):
                image_size(path, required_format="PNG")

    def test_wrap_text_rejects_box_narrower_than_one_glyph(self) -> None:
        class AlwaysWideDraw:
            @staticmethod
            def textlength(_text, font=None):
                return 100

        with self.assertRaises(ValueError):
            wrap_text(AlwaysWideDraw(), "승", object(), 10)


if __name__ == "__main__":
    unittest.main()
