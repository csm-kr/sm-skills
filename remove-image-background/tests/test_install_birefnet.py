import hashlib
import importlib.util
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "install_birefnet.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("install_birefnet", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModelHandler(BaseHTTPRequestHandler):
    payload = b"fake-safetensors-model"

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)


class InstallBiRefNetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def test_downloads_and_verifies_model_in_comfyui_model_directory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                result = self.module.install_model(
                    comfyui_root=root,
                    url=f"http://127.0.0.1:{server.server_port}/model",
                    expected_sha256=hashlib.sha256(ModelHandler.payload).hexdigest(),
                )

                expected = root / "models" / "background_removal" / "birefnet.safetensors"
                self.assertEqual(result, expected)
                self.assertEqual(expected.read_bytes(), ModelHandler.payload)
                self.assertFalse(expected.with_suffix(".safetensors.part").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
