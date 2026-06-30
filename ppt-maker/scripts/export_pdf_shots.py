#!/usr/bin/env python3
"""ppt-maker: reveal.js .html → .pdf — HTML 렌더 스샷을 그대로 합쳐 화면과 1:1.

언제 쓰나: 기본 export_pdf.py(reveal `?print-pdf` 경로)는 print용 pdf.css + Chromium
인쇄 엔진 + 폰트 로드 타이밍 때문에 화면(paper.css)보다 줄간격이 좁게 나올 수 있다.
화면 그대로를 PDF로 보장하려면 이 스크립트로 각 슬라이드를 고해상도 스샷 떠서 합친다.

사용:
  python export_pdf_shots.py deck.html ["<주제>.pdf"] [--width 2048]
  - out 생략 시 deck.pdf. 산출물은 주제 이름으로 저장 권장(예: "커피의 기원.pdf").

의존성: gstack browse(스샷) + pymupdf(합치기). browse 없으면 export_pdf.py를 쓴다.
"""
import argparse, os, re, subprocess, sys, tempfile
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    sys.exit("ERROR: pip install pymupdf 후 다시 실행하세요.")


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
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--width", type=int, default=2048, help="스샷 가로 px(16:9). reveal maxScale 1.6 → 1280*1.6=2048 권장")
    args = ap.parse_args()

    html = Path(args.html).resolve()
    if not html.is_file():
        sys.exit(f"ERROR: 파일 없음: {html}")
    out = Path(args.out).resolve() if args.out else html.with_suffix(".pdf")

    b = find_browse()
    if not b:
        sys.exit("ERROR: gstack browse가 없습니다. 기본 export_pdf.py(print-pdf)를 쓰세요.")

    w = args.width
    h = round(w * 9 / 16)
    run([b, "viewport", f"{w}x{h}"])
    run([b, "goto", html.as_uri()])
    run([b, "wait", "--networkidle"])
    run([b, "js", "Reveal.configure({transition:'none'})"])
    r = run([b, "js", "Reveal.getTotalSlides()"])
    m = re.search(r"\d+", r.stdout or "")
    if not m:
        sys.exit(f"ERROR: 슬라이드 수 파악 실패: {r.stdout!r}")
    n = int(m.group())

    tmp = Path(tempfile.mkdtemp(prefix="pptshots_"))
    pngs = []
    for i in range(n):
        run([b, "js", f"Reveal.slide({i})"])
        run([b, "js", "1"])  # 렌더 settle
        p = tmp / f"pg_{i:02d}.png"
        run([b, "screenshot", "--viewport", str(p)])
        pngs.append(p)

    doc = fitz.open()
    for p in pngs:
        img = fitz.open(str(p))
        pdfb = img.convert_to_pdf()
        img.close()
        src = fitz.open("pdf", pdfb)
        page = doc.new_page(width=1280, height=720)  # 16:9
        page.show_pdf_page(page.rect, src, 0)
        src.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"OK: {out} ({doc.page_count} pages, from {n} HTML shots)")


if __name__ == "__main__":
    main()
