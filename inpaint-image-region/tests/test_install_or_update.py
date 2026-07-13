import importlib.util
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "install_or_update.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("install_or_update", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstallOrUpdateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def test_resolves_codex_and_claude_project_targets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            self.assertEqual(
                self.module.default_target(root, "codex"),
                root / ".codex" / "skills" / "inpaint-image-region",
            )
            self.assertEqual(
                self.module.default_target(root, "claude"),
                root / ".claude" / "skills" / "inpaint-image-region",
            )

    def test_copy_skill_installs_and_updates_without_cache_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "target"
            (source / "scripts" / "__pycache__").mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (source / "scripts" / "run.py").write_text("print('new')", encoding="utf-8")
            (source / "scripts" / "__pycache__" / "run.pyc").write_bytes(b"cache")
            target.mkdir()
            (target / "SKILL.md").write_text("old", encoding="utf-8")

            installed = self.module.copy_skill(source, target)

            self.assertEqual(installed, target.resolve())
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertTrue((target / "scripts" / "run.py").is_file())
            self.assertFalse((target / "scripts" / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
