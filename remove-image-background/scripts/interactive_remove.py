#!/usr/bin/env python3
"""브라우저 드래그 앤 드롭으로 배경 제거 입력 이미지를 받는다."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SKILL_DIR = Path(__file__).resolve().parents[1]
HTML_PATH = SKILL_DIR / "assets" / "drop_image.html"
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


def resolve_input_dir(
    project_root: Path | str,
    input_dir: Path | str | None = None,
) -> Path:
    project_root = Path(project_root).expanduser().resolve()
    if input_dir is not None:
        path = Path(input_dir).expanduser()
        return path.resolve() if path.is_absolute() else (project_root / path).resolve()
    config_path = project_root / "bg-remove" / "config.json"
    configured = {}
    if config_path.is_file():
        configured = json.loads(config_path.read_text(encoding="utf-8"))
    path = Path(configured.get("input_dir") or "bg-remove/inputs").expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def save_submission(payload: dict, input_dir: Path | str) -> Path:
    image = payload.get("image")
    if not isinstance(image, dict):
        raise ValueError("배경을 제거할 이미지가 필요함")
    input_dir = Path(input_dir).expanduser().resolve()
    input_dir.mkdir(parents=True, exist_ok=True)
    destination = input_dir / safe_filename(str(image.get("name") or ""))
    destination.write_bytes(decode_data_url(image.get("data_url", "")))
    return destination


class RemoveInputHandler(BaseHTTPRequestHandler):
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
        if urlparse(self.path).path != "/" or not self.token_matches():
            self.send_payload(404, b"not found", "text/plain")
            return
        submit_url = f"/submit?token={self.server.token}"
        html = self.server.html.replace("__SUBMIT_URL__", submit_url).encode("utf-8")
        self.send_payload(200, html, "text/html; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/submit" or not self.token_matches():
            self.send_payload(404, b'{"error":"not found"}', "application/json")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_payload(413, b'{"error":"request too large"}', "application/json")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.server.result = save_submission(payload, self.server.input_dir)
            body = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
            self.send_payload(200, body, "application/json; charset=utf-8")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        except Exception as error:
            body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
            self.send_payload(400, body, "application/json; charset=utf-8")


def run_server(
    input_dir: Path | str,
    port: int = 0,
    open_browser: bool = True,
) -> Path:
    server = ThreadingHTTPServer(("127.0.0.1", port), RemoveInputHandler)
    server.input_dir = Path(input_dir).expanduser().resolve()
    server.token = uuid.uuid4().hex
    server.html = HTML_PATH.read_text(encoding="utf-8")
    server.result = None
    url = f"http://127.0.0.1:{server.server_port}/?token={server.token}"
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    if server.result is None:
        raise RuntimeError("이미지 입력 없이 드롭 화면이 종료됨")
    return server.result


def main() -> int:
    parser = argparse.ArgumentParser(description="배경 제거 이미지 드롭 화면 실행")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    try:
        input_dir = resolve_input_dir(args.project_root, args.input_dir)
        print(run_server(input_dir, args.port, not args.no_open))
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
