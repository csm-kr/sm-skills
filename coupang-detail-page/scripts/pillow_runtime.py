#!/usr/bin/env python3
"""Load Pillow from the system or an isolated skill-local runtime."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


PILLOW_REQUIREMENT = "Pillow>=10.0,<13"


def runtime_site_packages() -> Path:
    return Path(__file__).resolve().parents[1] / ".runtime" / "pillow"


def _import_image_modules():
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    return Image, ImageDraw, ImageFont, ImageOps


def load_pillow(*, install: bool):
    """Return Pillow modules, optionally installing into .runtime/pillow."""

    try:
        return _import_image_modules()
    except ImportError:
        pass

    target = runtime_site_packages()
    if str(target) not in sys.path:
        sys.path.insert(0, str(target))
    importlib.invalidate_caches()
    try:
        return _import_image_modules()
    except ImportError:
        if not install:
            raise

    target.mkdir(parents=True, exist_ok=True)
    pip_probe = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    if pip_probe.returncode != 0:
        raise RuntimeError(
            "Pillow is unavailable and this Python has no pip; install pip or run `python3 -m pip install -r requirements.txt` with a Python that provides pip"
        )
    print(
        f"Preparing isolated image runtime at {target} ({PILLOW_REQUIREMENT})...",
        file=sys.stderr,
    )
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--target",
                str(target),
                PILLOW_REQUIREMENT,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"isolated Pillow installation failed with exit {exc.returncode}") from exc
    importlib.invalidate_caches()
    try:
        return _import_image_modules()
    except ImportError as exc:
        raise RuntimeError("Pillow installation completed but could not be imported") from exc
