#!/usr/bin/env python3
"""Extract every Mermaid block from a document and render it, so a broken
diagram is caught before the page is published.

    python3 check_diagrams.py PAGE.html [--png OUTDIR] [--keep]

Handles both containers:
  - HTML:     <pre class="mermaid"> ... </pre>
  - Markdown: ```mermaid ... ```

Exit 0 = every diagram rendered. Exit 1 = at least one failed.

Rendering exit 0 only means Mermaid drew something. Pass --png and look at
the images; a diagram can render and still have lost its branch labels.
"""

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

BLOCK_RE = re.compile(
    r'<pre[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>'
    r'|^[ \t]*```[ \t]*mermaid[ \t]*\n(.*?)^[ \t]*```',
    re.S | re.M,
)


def extract(text: str) -> list[str]:
    out = []
    for m in BLOCK_RE.finditer(text):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        # HTML blocks carry entities (&gt; in --> arrows, &amp; in labels).
        out.append(html.unescape(body).strip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--png", metavar="OUTDIR",
                    help="write a PNG per diagram so you can look at them")
    ap.add_argument("--keep", action="store_true",
                    help="keep the extracted .mmd files next to the PNGs")
    args = ap.parse_args()

    src = pathlib.Path(args.page)
    if not src.is_file():
        print(f"no such file: {src}", file=sys.stderr)
        return 2

    if shutil.which("npx") is None:
        print("npx not found — install Node 18+", file=sys.stderr)
        return 2

    blocks = extract(src.read_text(encoding="utf-8"))
    if not blocks:
        print(f"{src.name}: no mermaid blocks found", file=sys.stderr)
        return 1

    outdir = pathlib.Path(args.png) if args.png else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="checkdiag-"))
    stem = src.stem.replace(" ", "-")
    failed = 0

    for i, body in enumerate(blocks, 1):
        mmd = (outdir if (outdir and args.keep) else tmp) / f"{stem}-{i}.mmd"
        mmd.write_text(body + "\n", encoding="utf-8")
        png = (outdir / f"{stem}-{i}.png") if outdir else (tmp / f"{i}.png")
        proc = subprocess.run(
            ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd),
             "-o", str(png)],
            capture_output=True, text=True,
        )
        kind = body.lstrip().splitlines()
        kind = next(
            (ln.strip() for ln in kind if not ln.strip().startswith("%%")),
            "?",
        ).split()[0]
        if proc.returncode == 0:
            where = f"  -> {png}" if outdir else ""
            print(f"  figure {i}  {kind:16} ok{where}")
        else:
            failed += 1
            err = [
                ln for ln in (proc.stderr or proc.stdout).splitlines()
                if "rror" in ln
            ]
            print(f"  figure {i}  {kind:16} FAILED")
            for ln in err[:3]:
                print(f"      {ln.strip()}")

    if not (outdir and args.keep):
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(blocks)
    print(f"\n{total - failed}/{total} rendered"
          + ("" if outdir else "  (pass --png OUTDIR to look at them)"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
