#!/usr/bin/env python3
"""브라우저에서 원본·박스·프롬프트·선택적 레퍼런스를 입력받는다."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import mimetypes
import sys
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SKILL_DIR = Path(__file__).resolve().parents[1]
HTML_PATH = SKILL_DIR / "assets" / "inpaint_selector.html"
RUNNER_PATH = SKILL_DIR / "scripts" / "run_inpainting.py"
MAX_REQUEST_BYTES = 100 * 1024 * 1024


def safe_filename(name: str) -> str:
    filename = Path(name.replace("\\", "/")).name
    if not filename or filename in {".", ".."}:
        raise ValueError("유효한 이미지 파일명이 필요함")
    return filename


def decode_data_url(data_url: str) -> bytes:
    if not data_url.startswith("data:image/") or ";base64," not in data_url:
        raise ValueError("이미지 data URL 형식이 아님")
    return base64.b64decode(data_url.split(",", 1)[1], validate=True)


def normalize_box(value) -> str:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("박스 좌표는 네 개여야 함")
    x1, y1, x2, y2 = (int(round(float(item))) for item in value)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    if right - left < 2 or bottom - top < 2:
        raise ValueError("박스의 너비와 높이는 2픽셀 이상이어야 함")
    return f"{left},{top},{right},{bottom}"


def save_image(item: dict, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decode_data_url(item.get("data_url", "")))
    return destination.resolve()


def resolve_input_dir(
    project_root: Path,
    input_dir: Path | str | None = None,
) -> Path:
    if input_dir is not None:
        path = Path(input_dir).expanduser()
        return path.resolve() if path.is_absolute() else (project_root / path).resolve()
    config_path = project_root / "inpainting" / "config.json"
    configured = {}
    if config_path.is_file():
        configured = json.loads(config_path.read_text(encoding="utf-8"))
    path = Path(configured.get("input_dir") or "inpainting/inputs").expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def save_submission(
    payload: dict,
    project_root: Path | str,
    input_dir: Path | str | None = None,
) -> Path:
    project_root = Path(project_root).expanduser().resolve()
    input_dir = resolve_input_dir(project_root, input_dir)
    source = payload.get("source")
    if not isinstance(source, dict):
        raise ValueError("원본 이미지가 필요함")

    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("변경 프롬프트가 필요함")

    source_path = save_image(
        source,
        input_dir / safe_filename(str(source.get("name") or "")),
    )
    reference = payload.get("reference")
    reference_path = None
    if isinstance(reference, dict):
        reference_path = save_image(
            reference,
            input_dir / f"reference-{safe_filename(str(reference.get('name') or ''))}",
        )

    manifest = {
        "source_path": str(source_path),
        "reference_path": str(reference_path) if reference_path else None,
        "prompt": prompt,
        "box": normalize_box(payload.get("box")),
        "mode": "reference" if reference_path else "text_only",
    }
    manifest_path = project_root / "inpainting" / "session.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path.resolve()


def load_runner_module():
    spec = importlib.util.spec_from_file_location("inpaint_skill_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("인페인팅 실행 스크립트를 불러올 수 없음")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def enhance_manifest(
    manifest_path: Path | str,
    enhanced_prompt: str,
) -> Path:
    manifest_path = Path(manifest_path).expanduser().resolve()
    prompt = enhanced_prompt.strip()
    if not prompt:
        raise ValueError("agent가 보강한 영어 프롬프트가 필요함")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["original_prompt"] = manifest.get("original_prompt") or manifest["prompt"]
    manifest["prompt"] = prompt
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def run_manifest(
    manifest_path: Path | str,
    project_root: Path | str,
    runner=None,
) -> Path:
    project_root = Path(project_root).expanduser().resolve()
    manifest_path = Path(manifest_path).expanduser().resolve()
    runner = runner or load_runner_module()
    settings = runner.resolve_settings(project_root)
    results = runner.run_inpainting(
        manifest_path,
        settings.output_dir,
        settings.server,
    )
    if not results:
        raise RuntimeError("ComfyUI 인페인팅 결과가 없음")
    return Path(results[0]).resolve()


def image_data_url(path: Path | str) -> str:
    path = Path(path)
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


class IntakeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_payload(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def token_matches(self) -> bool:
        query = parse_qs(urlparse(self.path).query)
        return query.get("token") == [self.server.token]

    def do_GET(self):
        request_path = urlparse(self.path).path
        if not self.token_matches():
            self.send_payload(404, b"not found", "text/plain")
            return
        if request_path == "/status":
            payload = {
                "state": self.server.state,
                "original_prompt": self.server.original_prompt,
                "enhanced_prompt": self.server.enhanced_prompt,
                "error": self.server.error,
            }
            if self.server.result is not None:
                payload.update(
                    {
                        "result_name": self.server.result.name,
                        "result_data_url": image_data_url(self.server.result),
                    }
                )
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_payload(200, body, "application/json; charset=utf-8")
            return
        if request_path != "/":
            self.send_payload(404, b"not found", "text/plain")
            return
        submit_url = f"/submit?token={self.server.token}"
        status_url = f"/status?token={self.server.token}"
        regenerate_url = f"/regenerate?token={self.server.token}"
        execute_url = f"/execute?token={self.server.token}"
        close_url = f"/close?token={self.server.token}"
        html = self.server.html.replace("__SUBMIT_URL__", submit_url)
        html = html.replace("__STATUS_URL__", status_url)
        html = html.replace("__REGENERATE_URL__", regenerate_url)
        html = html.replace("__EXECUTE_URL__", execute_url)
        html = html.replace("__CLOSE_URL__", close_url).encode("utf-8")
        self.send_payload(200, html, "text/html; charset=utf-8")

    def request_agent_prompt(self, event: str) -> None:
        enhance_url = (
            f"http://127.0.0.1:{self.server.server_port}"
            f"/enhance?token={self.server.token}"
        )
        request = {
            "manifest": str(self.server.manifest),
            "prompt": self.server.original_prompt,
            "current_enhanced_prompt": self.server.enhanced_prompt,
            "mode": self.server.mode,
            "enhance_url": enhance_url,
        }
        self.server.state = "waiting_agent"
        print(f"[{event}] " + json.dumps(request, ensure_ascii=False), flush=True)

    def do_POST(self):
        request_path = urlparse(self.path).path
        if not self.token_matches():
            self.send_payload(404, b'{"error":"not found"}', "application/json")
            return
        if request_path == "/close":
            self.send_payload(200, b'{"ok":true}', "application/json")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if request_path == "/regenerate":
            if self.server.manifest is None:
                self.send_payload(
                    400,
                    b'{"error":"submit first"}',
                    "application/json",
                )
                return
            self.request_agent_prompt("AGENT_REGENERATE")
            self.send_payload(
                200,
                b'{"ok":true,"state":"waiting_agent"}',
                "application/json",
            )
            return
        if request_path == "/execute":
            if self.server.manifest is None or not self.server.enhanced_prompt:
                self.send_payload(
                    400,
                    b'{"error":"enhanced prompt required"}',
                    "application/json",
                )
                return
            try:
                self.server.state = "running"
                self.server.result = run_manifest(
                    self.server.manifest,
                    self.server.project_root,
                )
                self.server.state = "complete"
                self.send_payload(
                    200,
                    b'{"ok":true,"state":"complete"}',
                    "application/json",
                )
            except Exception as error:
                self.server.state = "error"
                self.server.error = str(error)
                body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
                self.send_payload(400, body, "application/json; charset=utf-8")
            return
        if request_path not in {"/submit", "/enhance"}:
            self.send_payload(404, b'{"error":"not found"}', "application/json")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_payload(413, b'{"error":"request too large"}', "application/json")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if request_path == "/submit":
                self.server.manifest = save_submission(
                    payload,
                    self.server.project_root,
                    self.server.input_dir,
                )
                self.server.result = None
                self.server.error = None
                self.server.enhanced_prompt = None
                self.server.original_prompt = str(payload.get("prompt") or "").strip()
                self.server.mode = "reference" if payload.get("reference") else "text_only"
                self.request_agent_prompt("AGENT_PROMPT")
            else:
                if self.server.manifest is None:
                    raise RuntimeError("먼저 사용자 입력을 제출해야 함")
                self.server.enhanced_prompt = str(payload.get("prompt") or "").strip()
                enhance_manifest(self.server.manifest, self.server.enhanced_prompt)
                self.server.state = "ready"
            body = json.dumps({"ok": True, "state": self.server.state}).encode("utf-8")
            self.send_payload(200, body, "application/json; charset=utf-8")
        except Exception as error:
            self.server.state = "error"
            self.server.error = str(error)
            body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
            self.send_payload(400, body, "application/json; charset=utf-8")


def run_server(
    project_root: Path | str,
    input_dir: Path | str | None = None,
    port: int = 0,
    open_browser: bool = True,
) -> Path:
    server = ThreadingHTTPServer(("127.0.0.1", port), IntakeHandler)
    server.project_root = Path(project_root).expanduser().resolve()
    server.input_dir = input_dir
    server.token = uuid.uuid4().hex
    server.html = HTML_PATH.read_text(encoding="utf-8")
    server.result = None
    server.manifest = None
    server.enhanced_prompt = None
    server.original_prompt = None
    server.mode = None
    server.error = None
    server.state = "idle"
    url = f"http://127.0.0.1:{server.server_port}/?token={server.token}"
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    if server.result is None:
        raise RuntimeError("사용자 입력 없이 선택 화면이 종료됨")
    return server.result


def main() -> int:
    parser = argparse.ArgumentParser(description="인페인팅 영역 선택 화면 실행")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    try:
        print(
            run_server(
                args.project_root,
                args.input_dir,
                args.port,
                not args.no_open,
            )
        )
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
