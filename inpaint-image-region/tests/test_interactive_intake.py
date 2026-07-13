import base64
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "interactive_intake.py"
HTML_PATH = SKILL_DIR / "assets" / "inpaint_selector.html"


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


if __name__ == "__main__":
    unittest.main()
