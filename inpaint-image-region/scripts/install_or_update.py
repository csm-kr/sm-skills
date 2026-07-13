#!/usr/bin/env python3
"""GitHub의 최신 인페인팅 스킬을 Codex 또는 Claude 프로젝트에 설치한다."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_NAME = "inpaint-image-region"
DEFAULT_REPO = "https://github.com/csm-kr/sm-skills.git"


def default_target(project_root: Path | str, tool: str) -> Path:
    project_root = Path(project_root).expanduser().resolve()
    folder = ".codex" if tool == "codex" else ".claude"
    return project_root / folder / "skills" / SKILL_NAME


def ignore_cache(directory, names):
    return {
        name
        for name in names
        if name == "__pycache__" or name.endswith((".pyc", ".pyo"))
    }


def copy_skill(source: Path | str, target: Path | str) -> Path:
    source = Path(source).expanduser().resolve()
    target = Path(target).expanduser().resolve()
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"스킬 원본을 찾을 수 없음: {source}")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=ignore_cache,
    )
    return target


def download_skill(repo: str, ref: str, temp_root: Path) -> Path:
    checkout = temp_root / "sm-skills"
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            "--branch",
            ref,
            repo,
            str(checkout),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(checkout), "sparse-checkout", "set", SKILL_NAME],
        check=True,
    )
    return checkout / SKILL_NAME


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="inpaint-image-region 스킬 설치 또는 업데이트"
    )
    parser.add_argument("--tool", choices=("codex", "claude"), default="codex")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--target", type=Path)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--source", type=Path, help="GitHub 대신 복사할 로컬 스킬 폴더")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target = args.target or default_target(args.project_root, args.tool)
    try:
        if args.source:
            installed = copy_skill(args.source, target)
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                source = download_skill(args.repo, args.ref, Path(temp_dir))
                installed = copy_skill(source, target)
        print(installed)
    except Exception as error:
        print(f"[실패] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
