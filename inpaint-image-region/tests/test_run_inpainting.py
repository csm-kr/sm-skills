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
SCRIPT_PATH = SKILL_DIR / "scripts" / "run_inpainting.py"
WORKFLOW_PATH = SKILL_DIR / "assets" / "klein_inpaint_box.json"


def load_script_module():
    spec = importlib.util.spec_from_file_location("run_inpainting", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeComfyHandler(BaseHTTPRequestHandler):
    png_bytes = b"\x89PNG\r\n\x1a\n-inpainted"
    received_prompt = None
    upload_count = 0

    def log_message(self, format, *args):
        pass

    def _send(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path == "/upload/image":
            type(self).upload_count += 1
            name = "uploaded-reference.png" if b"reference.png" in body else "uploaded-source.png"
            response = {"name": name, "subfolder": "", "type": "input"}
            self._send(200, json.dumps(response).encode())
            return
        if self.path == "/prompt":
            type(self).received_prompt = json.loads(body.decode())["prompt"]
            self._send(200, b'{"prompt_id":"prompt-1","node_errors":{}}')
            return
        self._send(404, b"{}")

    def do_GET(self):
        if self.path == "/object_info":
            response = {
                "SMInpaintSquareCrop": {},
                "SMInpaintSquareStitch": {},
                "CFGGuider": {},
                "EmptyFlux2LatentImage": {},
                "Flux2Scheduler": {},
                "GetImageSize": {},
                "ImageScaleToTotalPixels": {},
                "KSamplerSelect": {},
                "RandomNoise": {},
                "ReferenceLatent": {},
                "SamplerCustomAdvanced": {},
                "UNETLoader": {
                    "input": {"required": {"unet_name": [["flux-2-klein-9b.safetensors"]]}}
                },
                "CLIPLoader": {
                    "input": {"required": {"clip_name": [["qwen_3_8b_fp8mixed.safetensors"]]}}
                },
                "VAELoader": {
                    "input": {"required": {"vae_name": [["flux2-vae.safetensors"]]}}
                },
            }
            self._send(200, json.dumps(response).encode())
            return
        if self.path == "/history/prompt-1":
            response = {
                "prompt-1": {
                    "status": {"completed": True, "status_str": "success"},
                    "outputs": {
                        "SMI:19": {
                            "images": [
                                {
                                    "filename": "source-inpaint_00001_.png",
                                    "subfolder": "inpainting",
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


class RunInpaintingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script_module()

    def setUp(self):
        FakeComfyHandler.received_prompt = None
        FakeComfyHandler.upload_count = 0

    def test_text_only_removes_external_reference_chain(self):
        workflow = {
            f"SMI:{number}": {"inputs": {}}
            for number in range(1, 35)
        }
        workflow["SMI:18"]["inputs"]["positive"] = ["SMI:33", 0]
        workflow["SMI:18"]["inputs"]["negative"] = ["SMI:34", 0]

        self.module.patch_workflow(
            workflow=workflow,
            source_image="source.png",
            reference_image=None,
            prompt="make it blue",
            box="10,20,110,220",
            filename_prefix="inpainting/source-inpaint",
            seed=42,
        )

        for node_id in ("SMI:30", "SMI:31", "SMI:32", "SMI:33", "SMI:34"):
            self.assertNotIn(node_id, workflow)
        self.assertEqual(workflow["SMI:18"]["inputs"]["positive"], ["SMI:11", 0])
        self.assertEqual(workflow["SMI:18"]["inputs"]["negative"], ["SMI:12", 0])

    def test_reference_mode_patches_source_reference_prompt_and_box(self):
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))

        self.module.patch_workflow(
            workflow=workflow,
            source_image="source.png",
            reference_image="reference.png",
            prompt="use the reference fabric",
            box="10,20,110,220",
            filename_prefix="inpainting/source-inpaint",
            seed=42,
        )

        self.assertEqual(workflow["SMI:7"]["inputs"]["image"], "source.png")
        self.assertEqual(workflow["SMI:30"]["inputs"]["image"], "reference.png")
        self.assertEqual(workflow["SMI:5"]["inputs"]["text"], "use the reference fabric")
        self.assertEqual(workflow["SMI:8"]["inputs"]["box"], "10,20,110,220")
        self.assertEqual(workflow["SMI:16"]["inputs"]["noise_seed"], 42)
        self.assertEqual(workflow["SMI:8"]["inputs"]["context_expand"], 1.0)
        self.assertEqual(workflow["SMI:15"]["class_type"], "Flux2Scheduler")
        self.assertEqual(workflow["SMI:15"]["inputs"]["steps"], 4)
        self.assertEqual(workflow["SMI:17"]["inputs"]["sampler_name"], "euler")
        self.assertEqual(workflow["SMI:19"]["class_type"], "SamplerCustomAdvanced")
        self.assertEqual(workflow["SMI:21"]["inputs"]["color_match"], "mean_std")
        self.assertEqual(workflow["SMI:18"]["inputs"]["positive"], ["SMI:33", 0])
        self.assertEqual(workflow["SMI:18"]["inputs"]["negative"], ["SMI:34", 0])

    def test_settings_use_portable_defaults_and_round_trip_project_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with mock.patch.dict(os.environ, {}, clear=True):
                defaults = self.module.resolve_settings(project_root)

            self.assertEqual(defaults.server, "http://127.0.0.1:8188")
            self.assertEqual(defaults.input_dir, project_root / "inpainting" / "inputs")
            self.assertEqual(defaults.output_dir, project_root / "inpainting" / "outputs")

            configured = self.module.Settings(
                server="http://comfy.example:8188",
                input_dir=project_root / "custom input",
                output_dir=project_root / "custom output",
            )
            config_path = self.module.save_config(project_root, configured)
            loaded = self.module.resolve_settings(project_root)

            self.assertEqual(config_path, project_root / "inpainting" / "config.json")
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

    def test_preflight_reports_missing_required_model(self):
        object_info = {
            name: {}
            for name in self.module.REQUIRED_NODES
        }
        object_info["UNETLoader"] = {
            "input": {"required": {"unet_name": [["another-model.safetensors"]]}}
        }
        object_info["CLIPLoader"] = {
            "input": {"required": {"clip_name": [["qwen_3_8b_fp8mixed.safetensors"]]}}
        }
        object_info["VAELoader"] = {
            "input": {"required": {"vae_name": [["flux2-vae.safetensors"]]}}
        }

        with mock.patch.object(self.module, "get_json", return_value=object_info):
            with self.assertRaisesRegex(RuntimeError, "flux-2-klein-9b.safetensors"):
                self.module.preflight("http://comfy.example:8188")

    def test_end_to_end_uploads_both_images_and_downloads_result(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeComfyHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "source.png"
                reference = root / "reference.png"
                source.write_bytes(b"source-image")
                reference.write_bytes(b"reference-image")
                manifest = root / "session.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "source_path": str(source),
                            "reference_path": str(reference),
                            "prompt": "use the reference fabric",
                            "box": "10,20,110,220",
                            "mode": "reference",
                        }
                    ),
                    encoding="utf-8",
                )

                saved = self.module.run_inpainting(
                    manifest_path=manifest,
                    output_dir=root / "outputs",
                    server=f"http://127.0.0.1:{server.server_port}",
                    workflow_path=WORKFLOW_PATH,
                    timeout=1,
                    poll_interval=0,
                    seed=42,
                )

                expected = root / "outputs" / "source-inpaint.png"
                self.assertEqual(saved, [expected])
                self.assertEqual(expected.read_bytes(), FakeComfyHandler.png_bytes)
                self.assertEqual(FakeComfyHandler.upload_count, 2)
                self.assertEqual(
                    FakeComfyHandler.received_prompt["SMI:30"]["inputs"]["image"],
                    "uploaded-reference.png",
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
