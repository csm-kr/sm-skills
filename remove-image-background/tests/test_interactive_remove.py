import base64
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "interactive_remove.py"
HTML_PATH = SKILL_DIR / "assets" / "drop_image.html"


def load_script_module():
    spec = importlib.util.spec_from_file_location("interactive_remove", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InteractiveRemoveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def test_saves_dragged_image_to_input_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "inputs"
            encoded = base64.b64encode(b"image-bytes").decode()

            saved = self.module.save_submission(
                {
                    "image": {
                        "name": "../product.png",
                        "data_url": f"data:image/png;base64,{encoded}",
                    }
                },
                input_dir,
            )

            self.assertEqual(saved, input_dir / "product.png")
            self.assertEqual(saved.read_bytes(), b"image-bytes")
            html = HTML_PATH.read_text(encoding="utf-8")
            self.assertIn("dragover", html)
            self.assertIn("배경 제거", html)

    def test_uses_input_directory_from_project_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "bg-remove" / "config.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps({"input_dir": "custom input"}),
                encoding="utf-8",
            )

            resolved = self.module.resolve_input_dir(project_root)

            self.assertEqual(resolved, project_root / "custom input")


if __name__ == "__main__":
    unittest.main()
