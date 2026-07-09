#!/usr/bin/env python3
"""pt-maker: reveal.js .html → .pdf.

사용:
  python export_pdf.py deck.html [out.pdf] [--decktape]

기본: 이미 설치된 browser CLI(Chromium)로 ?print-pdf 렌더 후 PDF 저장 (다운로드 없음).
browser CLI가 없거나 --decktape: npx decktape 사용 (최초 1회 Chromium 다운로드).
주의: 브라우저 도구는 작업공간 아래의 파일만 안정적으로 열 수 있으므로 deck.html은 프로젝트 폴더에 둔다.
"""
import argparse, os, shutil, subprocess, sys
from pathlib import Path


def find_browse():
    names = ["browse.exe", "browse"] if os.name == "nt" else ["browse", "browse.exe"]
    found = shutil.which("browse")
    if found:
        return found
    roots = [
        Path.cwd() / ".gstack/browse/dist",
        Path.cwd() / ".codex/plugins/gstack/browse/dist",
        Path.home() / ".codex/plugins/gstack/browse/dist",
        Path.home() / ".claude/skills/gstack/browse/dist",
    ]
    for root in roots:
        for n in names:
            p = root / n
            if p.exists():
                return str(p)
    return None


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
    return r


def run_media_guard(html: Path):
    guard = Path(__file__).with_name("qa_media_guard.py")
    r = subprocess.run([sys.executable, str(guard), str(html)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
        sys.exit("ERROR: qa_media_guard.py blocked PDF export. Fix media/map P0 findings first.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--decktape", action="store_true")
    args = ap.parse_args()

    html = Path(args.html).resolve()
    if not html.is_file():
        sys.exit(f"ERROR: 파일 없음: {html}")
    out = Path(args.out).resolve() if args.out else html.with_suffix(".pdf")
    run_media_guard(html)
    file_url = html.as_uri()

    browse = None if args.decktape else find_browse()
    if browse:
        run([browse, "goto", file_url + "?print-pdf"])
        run([browse, "wait", "--networkidle"])
        r = run([browse, "pdf", str(out), "--print-background", "--prefer-css-page-size"])
        if r.returncode == 0 and out.is_file():
            print(f"OK: {out}")
            return
        sys.stderr.write("browser CLI PDF 실패 → decktape로 폴백합니다.\n")

    npx = shutil.which("npx") or ("npx.cmd" if os.name == "nt" else "npx")
    r = run([npx, "-y", "decktape", "reveal", file_url, str(out), "--size", "1280x720"])
    if r.returncode == 0 and out.is_file():
        print(f"OK: {out} (decktape)")
    else:
        sys.exit("ERROR: PDF 생성 실패. browser CLI 또는 node/npx 환경을 확인하세요.")


if __name__ == "__main__":
    main()
