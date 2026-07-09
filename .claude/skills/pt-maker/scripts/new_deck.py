#!/usr/bin/env python3
"""pt-maker: 다음 순번의 덱 폴더를 스캐폴딩한다.

사용:
  python new_deck.py "<slug>" [--date YYYYMMDD] [--root <작업공간>]

output/ 의 기존 최대 순번 +1 을 계산해
  output/NN_<slug>_<date>/{deck.html, assets/}
를 만들고, 스킬의 assets/template.html 을 deck.html 로 복사한다.
생성된 덱 폴더 경로를 마지막 줄에 출력한다.
표준 라이브러리만 사용.
"""
import argparse, datetime, re, shutil, sys
from pathlib import Path

SEQ_RE = re.compile(r"^(\d{2,})_")


def next_seq(output_dir: Path) -> int:
    mx = 0
    if output_dir.is_dir():
        for p in output_dir.iterdir():
            if p.is_dir():
                m = SEQ_RE.match(p.name)
                if m:
                    mx = max(mx, int(m.group(1)))
    return mx + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    output_dir = root / "output"
    template = Path(__file__).resolve().parent.parent / "assets" / "template.html"
    if not template.is_file():
        sys.exit(f"ERROR: 템플릿을 찾을 수 없음: {template}")

    seq = next_seq(output_dir)
    deck_dir = output_dir / f"{seq:02d}_{args.slug}_{args.date}"
    if deck_dir.exists():
        sys.exit(f"ERROR: 이미 존재함: {deck_dir}")
    (deck_dir / "assets").mkdir(parents=True)
    shutil.copyfile(template, deck_dir / "deck.html")
    print(f"OK: 덱 폴더 생성 (seq={seq:02d}, date={args.date})")
    print(deck_dir)


if __name__ == "__main__":
    main()
