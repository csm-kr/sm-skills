#!/usr/bin/env python3
"""공식 BiRefNet 모델을 ComfyUI 모델 폴더에 설치한다."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from urllib.request import Request, urlopen


MODEL_URL = (
    "https://huggingface.co/Comfy-Org/BiRefNet/resolve/main/"
    "background_removal/birefnet.safetensors"
)
MODEL_SHA256 = "9ab37426bf4de0567af6b5d21b16151357149139362e6e8992021b8ce356a154"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_model(
    comfyui_root: Path | str,
    url: str = MODEL_URL,
    expected_sha256: str = MODEL_SHA256,
) -> Path:
    comfyui_root = Path(comfyui_root).expanduser().resolve()
    destination = (
        comfyui_root / "models" / "background_removal" / "birefnet.safetensors"
    )
    if destination.is_file():
        if file_sha256(destination) == expected_sha256:
            return destination
        raise RuntimeError(f"기존 모델의 SHA-256이 일치하지 않음: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".safetensors.part")
    digest = hashlib.sha256()
    try:
        with urlopen(Request(url), timeout=60) as response, temporary.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise RuntimeError("다운로드한 모델의 SHA-256이 일치하지 않음")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="공식 BiRefNet 모델을 ComfyUI/models/background_removal에 설치"
    )
    parser.add_argument("comfyui_root", type=Path, help="ComfyUI 설치 루트 폴더")
    args = parser.parse_args()
    try:
        print(install_model(args.comfyui_root))
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
