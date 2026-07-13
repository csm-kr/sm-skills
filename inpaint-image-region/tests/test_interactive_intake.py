import base64
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "interactive_intake.py"
HTML_PATH = SKILL_DIR / "assets" / "inpaint_selector.html"
SKILL_PATH = SKILL_DIR / "SKILL.md"


def load_script_module():
    spec = importlib.util.spec_from_file_location("interactive_intake", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def image_payload(name, content):
    encoded = base64.b64encode(content).decode()
    return {"name": name, "data_url": f"data:image/png;base64,{encoded}"}


class InteractiveIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def test_saves_source_box_and_prompt_as_text_only_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = {
                "source": image_payload("../source.png", b"source-image"),
                "reference": None,
                "prompt": "  replace the shirt with a blue jacket  ",
                "box": [300, 400, 100, 200],
            }

            manifest_path = self.module.save_submission(payload, root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["mode"], "text_only")
            self.assertEqual(manifest["prompt"], "replace the shirt with a blue jacket")
            self.assertEqual(manifest["box"], "100,200,300,400")
            self.assertIsNone(manifest["reference_path"])
            self.assertEqual(Path(manifest["source_path"]).name, "source.png")
            self.assertEqual(Path(manifest["source_path"]).read_bytes(), b"source-image")

    def test_saves_optional_reference_and_selector_contains_drop_ui(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = {
                "source": image_payload("source.png", b"source-image"),
                "reference": image_payload("reference.png", b"reference-image"),
                "prompt": "use the referenced fabric",
                "box": [10, 20, 110, 220],
            }

            manifest_path = self.module.save_submission(payload, root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            html = HTML_PATH.read_text(encoding="utf-8")

            self.assertEqual(manifest["mode"], "reference")
            self.assertEqual(Path(manifest["reference_path"]).read_bytes(), b"reference-image")
            self.assertIn("<canvas", html)
            self.assertIn("레퍼런스", html)
            self.assertIn("dragover", html)
            self.assertIn('addEventListener("wheel"', html)
            self.assertIn("바로 인페인팅 실행", html)
            self.assertIn("한국어는 짧게 번역하고, 명확한 영어는 그대로 사용합니다", html)
            self.assertIn("__STATUS_URL__", html)
            self.assertIn('id="enhancedPromptInput"', html)
            self.assertIn('id="regenerate"', html)
            self.assertIn('id="execute"', html)
            self.assertIn('id="beforeImage"', html)
            self.assertIn('id="afterImage"', html)
            self.assertIn('id="compareSlider"', html)
            self.assertIn('id="clearSource"', html)
            self.assertIn('id="clearReference"', html)
            self.assertIn('id="clearResult"', html)
            self.assertIn('aria-label="원본 이미지 삭제"', html)
            self.assertIn('aria-label="레퍼런스 이미지 삭제"', html)
            self.assertIn('aria-label="결과 이미지 삭제"', html)
            self.assertIn("변경할 내용", html)
            self.assertIn("원본", html)
            self.assertIn("결과", html)

    def test_uses_configured_input_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "custom input"
            payload = {
                "source": image_payload("source.png", b"source-image"),
                "reference": None,
                "prompt": "make it blue",
                "box": [10, 20, 110, 220],
            }

            manifest_path = self.module.save_submission(payload, root, input_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(Path(manifest["source_path"]), input_dir / "source.png")

    def test_skill_keeps_clear_english_edit_prompt_unchanged(self):
        instructions = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("영어 원문이 이미 짧고 명확하면 그대로 사용한다", instructions)
        self.assertIn("`change the hat to bald head`", instructions)
        self.assertNotIn("Replace the flat cap with a natural bald scalp", instructions)

    def test_submission_runs_comfyui_and_returns_result_for_same_window(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            calls = []

            class FakeRunner:
                @staticmethod
                def resolve_settings(project_root):
                    return SimpleNamespace(
                        server="http://comfy.example:8188",
                        output_dir=project_root / "inpainting" / "outputs",
                    )

                @staticmethod
                def run_inpainting(manifest_path, output_dir, server):
                    calls.append((manifest_path, output_dir, server))
                    output_dir.mkdir(parents=True)
                    result = output_dir / "source-inpaint.png"
                    result.write_bytes(b"result-image")
                    return [result]

            payload = {
                "source": image_payload("source.png", b"source-image"),
                "reference": None,
                "prompt": "make it blue",
                "box": [10, 20, 110, 220],
            }

            manifest_path = self.module.save_submission(payload, root)
            self.module.enhance_manifest(
                manifest_path,
                "Replace the selected item with a blue version while preserving the subject and background.",
            )
            result = self.module.run_manifest(manifest_path, root, runner=FakeRunner)

            self.assertEqual(result.read_bytes(), b"result-image")
            self.assertEqual(calls[0][2], "http://comfy.example:8188")
            self.assertEqual(calls[0][0], root / "inpainting" / "session.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["original_prompt"], "make it blue")
            self.assertTrue(manifest["prompt"].startswith("Replace the selected item"))
            data_url = self.module.image_data_url(result)
            self.assertTrue(data_url.startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
