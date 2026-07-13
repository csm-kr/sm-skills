#!/usr/bin/env python3
"""ComfyUI BiRefNet 워크플로로 이미지 배경을 제거한다."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import sys
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_SERVER = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = (
    Path(__file__).resolve().parents[1] / "assets" / "birefnet_remove_background.json"
)
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
REQUIRED_NODES = {
    "InvertMask",
    "JoinImageWithAlpha",
    "LoadBackgroundRemovalModel",
    "LoadImage",
    "RemoveBackground",
    "SaveImage",
}


class Settings(NamedTuple):
    server: str
    input_dir: Path
    output_dir: Path


def normalize_server(server: str) -> str:
    return server.strip().rstrip("/")


def config_path(project_root: Path) -> Path:
    return project_root / "bg-remove" / "config.json"


def resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def load_config(project_root: Path) -> dict:
    path = config_path(project_root)
    if not path.is_file():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"설정 파일의 최상위 값은 객체여야 함: {path}")
    return loaded


def resolve_settings(
    project_root: Path | str,
    server: str | None = None,
    input_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> Settings:
    project_root = Path(project_root).expanduser().resolve()
    configured = load_config(project_root)
    resolved_server = (
        server
        or os.environ.get("COMFYUI_SERVER")
        or configured.get("server")
        or DEFAULT_SERVER
    )
    resolved_input = input_dir or configured.get("input_dir") or "bg-remove/inputs"
    resolved_output = output_dir or configured.get("output_dir") or "bg-remove/outputs"
    return Settings(
        server=normalize_server(str(resolved_server)),
        input_dir=resolve_path(project_root, resolved_input),
        output_dir=resolve_path(project_root, resolved_output),
    )


def portable_path(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def save_config(project_root: Path | str, settings: Settings) -> Path:
    project_root = Path(project_root).expanduser().resolve()
    path = config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    settings.input_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "server": normalize_server(settings.server),
        "input_dir": portable_path(project_root, settings.input_dir.resolve()),
        "output_dir": portable_path(project_root, settings.output_dir.resolve()),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def http_json(request: Request, timeout: float = 30) -> dict:
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return http_json(request)


def get_json(url: str) -> dict:
    return http_json(Request(url))


def get_bytes(url: str) -> bytes:
    with urlopen(Request(url), timeout=120) as response:
        return response.read()


def preflight(server: str) -> None:
    object_info = get_json(f"{normalize_server(server)}/object_info")
    missing_nodes = sorted(REQUIRED_NODES - set(object_info))
    if missing_nodes:
        raise RuntimeError(
            "필요한 ComfyUI 노드가 없음: "
            + ", ".join(missing_nodes)
            + ". 최신 ComfyUI로 업데이트 필요"
        )

    model_spec = (
        object_info["LoadBackgroundRemovalModel"]
        .get("input", {})
        .get("required", {})
        .get("bg_removal_name", [])
    )
    options = (
        model_spec[1].get("options", [])
        if len(model_spec) > 1 and isinstance(model_spec[1], dict)
        else model_spec[0] if model_spec and isinstance(model_spec[0], list) else []
    )
    if "birefnet.safetensors" not in options:
        raise RuntimeError(
            "birefnet.safetensors 모델이 없음. "
            "ComfyUI/models/background_removal에 공식 모델 설치 필요"
        )


def encode_upload(input_path: Path, remote_name: str) -> tuple[bytes, str]:
    boundary = f"----codex-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(input_path.name)[0] or "application/octet-stream"
    chunks = [
        f"--{boundary}\r\n".encode(),
        (
            'Content-Disposition: form-data; name="image"; '
            f'filename="{remote_name}"\r\n'
        ).encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        input_path.read_bytes(),
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="type"\r\n\r\ninput\r\n',
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="overwrite"\r\n\r\nfalse\r\n',
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def upload_image(server: str, input_path: Path) -> str:
    remote_name = f"codex-bg-{uuid.uuid4().hex}-{input_path.name}"
    body, content_type = encode_upload(input_path, remote_name)
    request = Request(
        f"{server}/upload/image",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    uploaded = http_json(request, timeout=120)
    name = uploaded.get("name")
    if not name:
        raise RuntimeError(f"이미지 업로드 응답에 name이 없음: {uploaded}")
    subfolder = uploaded.get("subfolder") or ""
    return str(PurePosixPath(subfolder) / name) if subfolder else name


def patch_workflow(workflow: dict, uploaded_image: str, filename_prefix: str) -> None:
    load_nodes = [
        node for node in workflow.values() if node.get("class_type") == "LoadImage"
    ]
    save_nodes = [
        node for node in workflow.values() if node.get("class_type") == "SaveImage"
    ]
    if len(load_nodes) != 1 or len(save_nodes) != 1:
        raise ValueError("워크플로에는 LoadImage와 SaveImage 노드가 각각 하나씩 있어야 함")
    load_nodes[0]["inputs"]["image"] = uploaded_image
    save_nodes[0]["inputs"]["filename_prefix"] = filename_prefix


def wait_for_history(
    server: str,
    prompt_id: str,
    timeout: float,
    poll_interval: float,
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        entry = get_json(f"{server}/history/{prompt_id}").get(prompt_id)
        if entry is not None:
            status = entry.get("status") or {}
            if status.get("completed") or status.get("status_str") in {"success", "error"}:
                return entry
        time.sleep(poll_interval)
    raise TimeoutError(f"{timeout:g}초 안에 ComfyUI 실행이 완료되지 않음")


def collect_images(history: dict) -> list[dict]:
    status = history.get("status") or {}
    if status.get("status_str") == "error":
        raise RuntimeError(f"ComfyUI 워크플로 실행 실패: {status.get('messages') or status}")

    images = []
    for output in (history.get("outputs") or {}).values():
        images.extend(output.get("images") or [])
    if not images:
        raise RuntimeError("ComfyUI 실행 결과에 이미지가 없음")
    return images


def download_images(
    server: str,
    images: list[dict],
    output_dir: Path,
    input_stem: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for index, image in enumerate(images, start=1):
        query = urlencode(
            {
                "filename": image["filename"],
                "subfolder": image.get("subfolder") or "",
                "type": image.get("type") or "output",
            }
        )
        suffix = "" if index == 1 else f"_{index}"
        destination = output_dir / f"{input_stem}-rmbg{suffix}.png"
        destination.write_bytes(get_bytes(f"{server}/view?{query}"))
        saved.append(destination)
    return saved


def run_background_removal(
    input_path: Path | str,
    output_dir: Path | str,
    server: str = DEFAULT_SERVER,
    workflow_path: Path | str = DEFAULT_WORKFLOW,
    timeout: float = 600,
    poll_interval: float = 1.5,
) -> list[Path]:
    input_path = Path(input_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    workflow_path = Path(workflow_path).expanduser().resolve()
    server = server.rstrip("/")

    if not input_path.is_file():
        raise FileNotFoundError(f"입력 이미지를 찾을 수 없음: {input_path}")

    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    uploaded_image = upload_image(server, input_path)
    output_prefix = f"background_removed/{input_path.stem}-rmbg"
    patch_workflow(workflow, uploaded_image, output_prefix)

    queued = post_json(
        f"{server}/prompt",
        {"prompt": workflow, "client_id": str(uuid.uuid4())},
    )
    prompt_id = queued.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"큐 등록 응답에 prompt_id가 없음: {queued}")

    history = wait_for_history(server, prompt_id, timeout, poll_interval)
    images = collect_images(history)
    return download_images(server, images, output_dir, input_path.stem)


def stage_inputs(input_paths: list[Path | str], input_dir: Path) -> list[Path]:
    input_dir.mkdir(parents=True, exist_ok=True)
    staged = []
    for input_path in input_paths:
        source = Path(input_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"입력 이미지를 찾을 수 없음: {source}")
        destination = (input_dir / source.name).resolve()
        if source != destination:
            shutil.copy2(source, destination)
        staged.append(destination)
    return staged


def discover_inputs(input_dir: Path) -> list[Path]:
    input_dir.mkdir(parents=True, exist_ok=True)
    return sorted(
        path.resolve()
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def run_default_batch(
    project_root: Path | str,
    input_paths: list[Path | str] | None = None,
    input_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    server: str = DEFAULT_SERVER,
    workflow_path: Path | str = DEFAULT_WORKFLOW,
    timeout: float = 600,
    poll_interval: float = 1.5,
) -> list[Path]:
    project_root = Path(project_root).expanduser().resolve()
    input_dir = (
        Path(input_dir).expanduser().resolve()
        if input_dir
        else project_root / "bg-remove" / "inputs"
    )
    default_output_dir = project_root / "bg-remove" / "outputs"
    default_output_dir.mkdir(parents=True, exist_ok=True)
    preflight(server)

    images = (
        stage_inputs(input_paths, input_dir)
        if input_paths
        else discover_inputs(input_dir)
    )
    if not images:
        raise FileNotFoundError(f"배경을 제거할 이미지가 없음: {input_dir}")

    destination_dir = Path(output_dir).expanduser().resolve() if output_dir else default_output_dir
    saved = []
    for image in images:
        saved.extend(
            run_background_removal(
                input_path=image,
                output_dir=destination_dir,
                server=server,
                workflow_path=workflow_path,
                timeout=timeout,
                poll_interval=poll_interval,
            )
        )
    return saved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ComfyUI BiRefNet으로 이미지 배경을 제거하고 투명 PNG를 저장"
    )
    parser.add_argument(
        "input_images",
        type=Path,
        nargs="*",
        help="bg-remove/inputs에 복사한 뒤 처리할 이미지. 생략하면 inputs의 모든 이미지를 처리",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="bg-remove 폴더를 만들 프로젝트 루트",
    )
    parser.add_argument("--input-dir", type=Path, help="설정된 기본값 대신 사용할 입력 폴더")
    parser.add_argument("--output-dir", type=Path, help="설정된 기본값 대신 사용할 출력 폴더")
    parser.add_argument("--server", help="ComfyUI 서버 URL")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="서버와 입출력 폴더를 검증해 bg-remove/config.json에 저장",
    )
    parser.add_argument("--timeout", type=float, default=600, help="완료 대기 최대 초")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        settings = resolve_settings(
            project_root=args.project_root,
            server=args.server,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        if args.configure:
            preflight(settings.server)
            saved_config = save_config(args.project_root, settings)
            print(saved_config)
            return 0

        saved = run_default_batch(
            project_root=args.project_root,
            input_paths=args.input_images,
            input_dir=settings.input_dir,
            output_dir=settings.output_dir,
            server=settings.server,
            timeout=args.timeout,
        )
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1

    for path in saved:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
