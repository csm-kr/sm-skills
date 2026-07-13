import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "remove_background.py"
WORKFLOW_PATH = SKILL_DIR / "assets" / "birefnet_remove_background.json"


def load_script_module():
    spec = importlib.util.spec_from_file_location("remove_background", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeComfyHandler(BaseHTTPRequestHandler):
    png_bytes = b"\x89PNG\r\n\x1a\ntransparent-result"
    received_prompt = None
    uploaded_image = False

    def log_message(self, format, *args):
        pass

    def _send(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)

        if self.path == "/upload/image":
            type(self).uploaded_image = b"source.png" in body and b"image-bytes" in body
            response = {"name": "uploaded-source.png", "subfolder": "", "type": "input"}
            self._send(200, json.dumps(response).encode())
            return

        if self.path == "/prompt":
            type(self).received_prompt = json.loads(body.decode())["prompt"]
            self._send(200, b'{"prompt_id": "prompt-1", "node_errors": {}}')
            return

        self._send(404, b"{}")

    def do_GET(self):
        if self.path == "/object_info":
            response = {
                name: {}
                for name in (
                    "LoadImage",
                    "LoadBackgroundRemovalModel",
                    "RemoveBackground",
                    "InvertMask",
                    "JoinImageWithAlpha",
                    "SaveImage",
                )
            }
            response["LoadBackgroundRemovalModel"] = {
                "input": {
                    "required": {
                        "bg_removal_name": [
                            "COMBO",
                            {"options": ["birefnet.safetensors"]},
                        ]
                    }
                }
            }
            self._send(200, json.dumps(response).encode())
            return

        if self.path == "/history/prompt-1":
            response = {
                "prompt-1": {
                    "status": {"completed": True, "status_str": "success"},
                    "outputs": {
                        "6": {
                            "images": [
                                {
                                    "filename": "source_background_removed_00001_.png",
                                    "subfolder": "background_removed",
                                    "type": "output",
                                }
                            ]
                        }
                    },
                }
            }
            self._send(200, json.dumps(response).encode())
            return

        if self.path.startswith("/view?"):
            self._send(200, self.png_bytes, "image/png")
            return

        self._send(404, b"{}")


class RemoveBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def setUp(self):
        FakeComfyHandler.received_prompt = None
        FakeComfyHandler.uploaded_image = False

    def test_patch_workflow_sets_uploaded_image_and_output_prefix(self):
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": "old.png"}},
            "6": {"class_type": "SaveImage", "inputs": {"filename_prefix": "old"}},
        }

        self.module.patch_workflow(
            workflow,
            uploaded_image="inputs/new.png",
            filename_prefix="background_removed/new_background_removed",
        )

        self.assertEqual(workflow["1"]["inputs"]["image"], "inputs/new.png")
        self.assertEqual(
            workflow["6"]["inputs"]["filename_prefix"],
            "background_removed/new_background_removed",
        )

    def test_end_to_end_uploads_runs_and_saves_to_requested_directory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeComfyHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "source.png"
                source.write_bytes(b"image-bytes")
                output_dir = root / "results"

                saved = self.module.run_background_removal(
                    input_path=source,
                    output_dir=output_dir,
                    server=f"http://127.0.0.1:{server.server_port}",
                    workflow_path=WORKFLOW_PATH,
                    timeout=1,
                    poll_interval=0,
                )

                expected = output_dir / "source-rmbg.png"
                self.assertEqual(saved, [expected])
                self.assertEqual(expected.read_bytes(), FakeComfyHandler.png_bytes)
                self.assertTrue(FakeComfyHandler.uploaded_image)
                self.assertEqual(
                    FakeComfyHandler.received_prompt["1"]["inputs"]["image"],
                    "uploaded-source.png",
                )
                self.assertEqual(
                    FakeComfyHandler.received_prompt["6"]["inputs"]["filename_prefix"],
                    "background_removed/source-rmbg",
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_default_batch_processes_images_from_project_input_directory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeComfyHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                input_dir = project_root / "bg-remove" / "inputs"
                input_dir.mkdir(parents=True)
                (input_dir / "source.png").write_bytes(b"image-bytes")
                (input_dir / "ignore.txt").write_text("not an image")

                saved = self.module.run_default_batch(
                    project_root=project_root,
                    server=f"http://127.0.0.1:{server.server_port}",
                    timeout=1,
                    poll_interval=0,
                )

                expected = project_root / "bg-remove" / "outputs" / "source-rmbg.png"
                self.assertEqual(saved, [expected])
                self.assertEqual(expected.read_bytes(), FakeComfyHandler.png_bytes)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_stage_inputs_copies_given_image_into_default_input_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source = project_root / "source.png"
            source.write_bytes(b"image-bytes")

            staged = self.module.stage_inputs([source], project_root / "bg-remove" / "inputs")

            expected = project_root / "bg-remove" / "inputs" / "source.png"
            self.assertEqual(staged, [expected])
            self.assertEqual(expected.read_bytes(), b"image-bytes")

    def test_cli_uses_requested_comfyui_server_by_default(self):
        args = self.module.build_parser().parse_args([])

        self.assertIsNone(args.server)

    def test_settings_use_portable_defaults_and_round_trip_project_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with mock.patch.dict(os.environ, {}, clear=True):
                defaults = self.module.resolve_settings(project_root)

            self.assertEqual(defaults.server, "http://127.0.0.1:8188")
            self.assertEqual(defaults.input_dir, project_root / "bg-remove" / "inputs")
            self.assertEqual(defaults.output_dir, project_root / "bg-remove" / "outputs")

            configured = self.module.Settings(
                server="http://comfy.example:8188",
                input_dir=project_root / "images in",
                output_dir=project_root / "images out",
            )
            config_path = self.module.save_config(project_root, configured)
            loaded = self.module.resolve_settings(project_root)

            self.assertEqual(config_path, project_root / "bg-remove" / "config.json")
            self.assertEqual(loaded, configured)

    def test_environment_can_override_configured_server(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            configured = self.module.Settings(
                server="http://configured:8188",
                input_dir=project_root / "in",
                output_dir=project_root / "out",
            )
            self.module.save_config(project_root, configured)

            with mock.patch.dict(
                os.environ,
                {"COMFYUI_SERVER": "http://environment:8188/"},
                clear=True,
            ):
                loaded = self.module.resolve_settings(project_root)

            self.assertEqual(loaded.server, "http://environment:8188")

    def test_preflight_reports_missing_birefnet_model(self):
        object_info = {
            name: {}
            for name in (
                "LoadImage",
                "LoadBackgroundRemovalModel",
                "RemoveBackground",
                "InvertMask",
                "JoinImageWithAlpha",
                "SaveImage",
            )
        }
        object_info["LoadBackgroundRemovalModel"] = {
            "input": {
                "required": {
                    "bg_removal_name": ["COMBO", {"options": []}],
                }
            }
        }

        with mock.patch.object(self.module, "get_json", return_value=object_info):
            with self.assertRaisesRegex(RuntimeError, "birefnet.safetensors"):
                self.module.preflight("http://127.0.0.1:8188")


if __name__ == "__main__":
    unittest.main()
