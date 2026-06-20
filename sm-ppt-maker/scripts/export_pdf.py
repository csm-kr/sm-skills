#!/usr/bin/env python3
"""sm-ppt-maker: reveal.js .html → .pdf.

사용:
  python export_pdf.py deck.html [out.pdf] [--decktape]

기본: 이미 설치된 gstack browse(Chromium)로 ?print-pdf 렌더 후 PDF 저장 (다운로드 없음).
browse가 없거나 --decktape: npx decktape 사용 (최초 1회 Chromium 다운로드).
주의: browse는 cwd 또는 TEMP 아래의 파일만 열 수 있으므로 deck.html은 프로젝트 폴더에 둔다.
"""
import argparse, os, shutil, subprocess, sys
from pathlib import Path


def find_browse():
    names = ["browse.exe", "browse"] if os.name == "nt" else ["browse", "browse.exe"]
    roots = [Path.cwd() / ".claude/skills/gstack/browse/dist",
             Path.home() / ".claude/skills/gstack/browse/dist"]
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
    file_url = html.as_uri()

    browse = None if args.decktape else find_browse()
    if browse:
        run([browse, "goto", file_url + "?print-pdf"])
        run([browse, "wait", "--networkidle"])
        r = run([browse, "pdf", str(out), "--print-background", "--prefer-css-page-size"])
        if r.returncode == 0 and out.is_file():
            print(f"OK: {out}")
            return
        sys.stderr.write("browse PDF 실패 → decktape로 폴백합니다.\n")

    npx = shutil.which("npx") or ("npx.cmd" if os.name == "nt" else "npx")
    r = run([npx, "-y", "decktape", "reveal", file_url, str(out), "--size", "1280x720"])
    if r.returncode == 0 and out.is_file():
        print(f"OK: {out} (decktape)")
    else:
        sys.exit("ERROR: PDF 생성 실패. gstack browse 또는 node/npx 환경을 확인하세요.")


if __name__ == "__main__":
    main()
