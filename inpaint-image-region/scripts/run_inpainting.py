#!/usr/bin/env python3
"""선택 manifest를 ComfyUI Klein 인페인팅 워크플로로 실행한다."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import random
import sys
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_SERVER = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = Path(__file__).resolve().parents[1] / "assets" / "klein_inpaint_box.json"
REQUIRED_NODES = {
    "CFGGuider",
    "CLIPLoader",
    "EmptyFlux2LatentImage",
    "Flux2Scheduler",
    "GetImageSize",
    "ImageScaleToTotalPixels",
    "KSamplerSelect",
    "RandomNoise",
    "ReferenceLatent",
    "SamplerCustomAdvanced",
    "SMInpaintSquareCrop",
    "SMInpaintSquareStitch",
    "UNETLoader",
    "VAELoader",
}
REQUIRED_MODELS = {
    ("UNETLoader", "unet_name"): "flux-2-klein-9b.safetensors",
    ("CLIPLoader", "clip_name"): "qwen_3_8b_fp8mixed.safetensors",
    ("VAELoader", "vae_name"): "flux2-vae.safetensors",
}


class Settings(NamedTuple):
    server: str
    input_dir: Path
    output_dir: Path


def normalize_server(server: str) -> str:
    return server.strip().rstrip("/")


def config_path(project_root: Path) -> Path:
    return project_root / "inpainting" / "config.json"


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
    resolved_input = input_dir or configured.get("input_dir") or "inpainting/inputs"
    resolved_output = output_dir or configured.get("output_dir") or "inpainting/outputs"
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def http_json(request: Request, timeout: float = 30) -> dict:
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    return http_json(
        Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    )


def get_json(url: str) -> dict:
    return http_json(Request(url))


def get_bytes(url: str) -> bytes:
    with urlopen(Request(url), timeout=120) as response:
        return response.read()


def input_choices(object_info: dict, node: str, field: str) -> list[str]:
    spec = (
        object_info.get(node, {})
        .get("input", {})
        .get("required", {})
        .get(field, [])
    )
    if spec and isinstance(spec[0], list):
        return spec[0]
    if len(spec) > 1 and isinstance(spec[1], dict):
        return spec[1].get("options", [])
    return []


def preflight(server: str) -> None:
    object_info = get_json(f"{normalize_server(server)}/object_info")
    missing_nodes = sorted(REQUIRED_NODES - set(object_info))
    if missing_nodes:
        raise RuntimeError("필요한 ComfyUI 노드가 없음: " + ", ".join(missing_nodes))
    missing_models = [
        model
        for (node, field), model in REQUIRED_MODELS.items()
        if model not in input_choices(object_info, node, field)
    ]
    if missing_models:
        raise RuntimeError("필요한 ComfyUI 모델이 없음: " + ", ".join(missing_models))


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
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def upload_image(server: str, input_path: Path) -> str:
    remote_name = f"codex-inpaint-{uuid.uuid4().hex}-{input_path.name}"
    body, content_type = encode_upload(input_path, remote_name)
    uploaded = http_json(
        Request(
            f"{server}/upload/image",
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        ),
        timeout=120,
    )
    name = uploaded.get("name")
    if not name:
        raise RuntimeError(f"이미지 업로드 응답에 name이 없음: {uploaded}")
    subfolder = uploaded.get("subfolder") or ""
    return str(PurePosixPath(subfolder) / name) if subfolder else name


def patch_workflow(
    workflow: dict,
    source_image: str,
    reference_image: str | None,
    prompt: str,
    box: str,
    filename_prefix: str,
    seed: int,
) -> None:
    workflow["SMI:7"]["inputs"]["image"] = source_image
    workflow["SMI:5"]["inputs"]["text"] = prompt
    workflow["SMI:8"]["inputs"]["box"] = box
    workflow["SMI:16"]["inputs"]["noise_seed"] = seed
    workflow["SMI:22"]["inputs"]["filename_prefix"] = filename_prefix

    if reference_image is None:
        for node_id in ("SMI:30", "SMI:31", "SMI:32", "SMI:33", "SMI:34"):
            workflow.pop(node_id, None)
        workflow["SMI:18"]["inputs"]["positive"] = ["SMI:11", 0]
        workflow["SMI:18"]["inputs"]["negative"] = ["SMI:12", 0]
    else:
        workflow["SMI:30"]["inputs"]["image"] = reference_image
        workflow["SMI:18"]["inputs"]["positive"] = ["SMI:33", 0]
        workflow["SMI:18"]["inputs"]["negative"] = ["SMI:34", 0]


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    source = Path(manifest["source_path"]).expanduser()
    if not source.is_absolute():
        source = (path.parent / source).resolve()
    reference_value = manifest.get("reference_path")
    reference = Path(reference_value).expanduser() if reference_value else None
    if reference is not None and not reference.is_absolute():
        reference = (path.parent / reference).resolve()
    if not source.is_file() or (reference is not None and not reference.is_file()):
        raise FileNotFoundError("manifest가 가리키는 입력 이미지를 찾을 수 없음")
    return {
        "source": source.resolve(),
        "reference": reference.resolve() if reference else None,
        "prompt": str(manifest["prompt"]).strip(),
        "box": str(manifest["box"]),
    }


def wait_for_history(server: str, prompt_id: str, timeout: float, poll_interval: float) -> dict:
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
        raise RuntimeError(f"ComfyUI 인페인팅 실패: {status.get('messages') or status}")
    images = []
    for output in (history.get("outputs") or {}).values():
        images.extend(output.get("images") or [])
    if not images:
        raise RuntimeError("ComfyUI 인페인팅 결과 이미지가 없음")
    return images


def run_inpainting(
    manifest_path: Path | str,
    output_dir: Path | str,
    server: str = DEFAULT_SERVER,
    workflow_path: Path | str = DEFAULT_WORKFLOW,
    timeout: float = 600,
    poll_interval: float = 1.5,
    seed: int | None = None,
) -> list[Path]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    server = server.rstrip("/")
    preflight(server)
    data = load_manifest(manifest_path)
    source_upload = upload_image(server, data["source"])
    reference_upload = (
        upload_image(server, data["reference"]) if data["reference"] else None
    )
    workflow = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
    seed = seed if seed is not None else random.randint(0, 2**63 - 1)
    prefix = f"inpainting/{data['source'].stem}-inpaint"
    patch_workflow(
        workflow,
        source_upload,
        reference_upload,
        data["prompt"],
        data["box"],
        prefix,
        seed,
    )
    queued = post_json(
        f"{server}/prompt",
        {"prompt": workflow, "client_id": str(uuid.uuid4())},
    )
    prompt_id = queued.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"큐 등록 응답에 prompt_id가 없음: {queued}")
    images = collect_images(wait_for_history(server, prompt_id, timeout, poll_interval))

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
        destination = output_dir / f"{data['source'].stem}-inpaint{suffix}.png"
        destination.write_bytes(get_bytes(f"{server}/view?{query}"))
        saved.append(destination)
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description="선택한 박스를 ComfyUI Klein으로 인페인팅")
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--server")
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    try:
        settings = resolve_settings(
            args.project_root,
            server=args.server,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        if args.configure:
            preflight(settings.server)
            print(save_config(args.project_root, settings))
            return 0
        manifest = args.manifest or args.project_root / "inpainting" / "session.json"
        for path in run_inpainting(
            manifest,
            settings.output_dir,
            settings.server,
            timeout=args.timeout,
            seed=args.seed,
        ):
            print(path)
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
