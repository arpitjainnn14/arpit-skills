#!/usr/bin/env python3
"""Verify every count stated in drafts.md before it reaches the user.

    check_drafts.py RUN/drafts.md

Checks:
  * each fenced block's stated length — the nearest preceding line that says
    "N/LIMIT", "N of LIMIT" or "N characters" — matches len(block), and N <= LIMIT;
  * each "Add (N): a, b, c" / "Remove (N): …" / "Keep (N): …" list has N items;
  * no paste-ready block reads as machine-written (score.style_tells).
Exit 0 = all counts true; 1 = mismatches listed; 2 = bad input.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import style_tells  # noqa: E402

LEN_RE = re.compile(r"\(?\b(\d[\d,]*)\s*(?:/|of)\s*(\d[\d,]*)\b|\b(\d[\d,]*)\s*(?:chars?|characters)\b", re.I)
LIST_RE = re.compile(r"\*\*(Add|Remove|Keep)\s*\((\d+)\)[:\s]*\*\*\s*:?\s*(.+)", re.I)


def num(s):
    return int(s.replace(",", ""))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_drafts.py RUN/drafts.md")
    try:
        lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    problems, checked, i = [], 0, 0
    while i < len(lines):
        m = LIST_RE.search(lines[i])
        if m:
            items = [x for x in re.split(r",\s*", m.group(3).strip().rstrip(".")) if x]
            checked += 1
            if len(items) != int(m.group(2)):
                problems.append(f"line {i + 1}: '{m.group(1)} ({m.group(2)})' lists {len(items)} items")
        if lines[i].startswith("```"):
            start = i
            i += 1
            body = []
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            text = "\n".join(body)
            for t in style_tells(text):
                checked += 1
                problems.append(f"line {start + 2}: STYLE: {t}")
            # nearest non-empty line above the fence that states a length
            j = start - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            stated = LEN_RE.search(lines[j]) if j >= 0 else None
            if stated:
                checked += 1
                n = num(stated.group(1) or stated.group(3))
                limit = num(stated.group(2)) if stated.group(2) else None
                if n != len(text):
                    problems.append(f"line {j + 1}: says {n} chars, block is {len(text)}: {text[:50]!r}…")
                if limit and len(text) > limit:
                    problems.append(f"line {j + 1}: block is {len(text)} chars, over the {limit} limit")
        i += 1

    for p in problems:
        print("MISMATCH:", p)
    print(f"{checked} checks, {len(problems)} wrong")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
