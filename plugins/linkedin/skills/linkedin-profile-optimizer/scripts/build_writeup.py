#!/usr/bin/env python3
"""Render the click-by-click corrections checklist from RUN/edits.json.

    build_writeup.py RUN/edits.json [--out RUN/writeup.md]

edits.json:
{
  "title": "LinkedIn edits for Arpit",
  "lead": "Work through these top to bottom. ...",
  "steps": [
    {"title": "Headline",
     "where": "your profile → pencil icon on the top card → Headline",
     "delete": "SDE-1 @ Hexalog | ...",          # optional
     "paste": "Backend Engineer (SDE-1) | ...",  # optional; or "paste_file": "text/headline_A.txt"
     "limit": 220,                              # optional; checked against the paste
     "first": ["**Title:** change …"],          # optional lines before Delete/Paste
     "lines": ["**Skills:** add FastAPI, ..."],  # optional lines after the paste
     "check": "Saved"}                          # optional; tick-box label (default "Done")
  ],
  "tail": ["## Outside LinkedIn\\n\\n- [ ] ..."]   # optional free sections after the steps
}

Fails (exit 1) when a paste is over its limit or any text reads as
machine-written (score.style_tells). Exit 2 = bad input.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import style_tells  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edits")
    ap.add_argument("--out")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.edits))
    try:
        plan = json.load(open(a.edits, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    out, problems, prose = [f"# {plan['title']}", plan.get("lead", "")], [], [plan.get("lead", "")]
    for n, st in enumerate(plan["steps"], 1):
        paste = st.get("paste")
        if st.get("paste_file"):
            paste = open(os.path.join(base, st["paste_file"]), encoding="utf-8").read().rstrip("\n")
        part = [f"## {n}. {st['title']}"]
        if st.get("why"):
            part.append(st["why"])
            prose.append(st["why"])
        part.append(f"**Where:** {st['where']}")
        for line in st.get("first", []):
            part.append(line)
            prose.append(line)
        if st.get("delete"):
            part.append(f"**Delete:** {st['delete']}")
        if paste:
            part.append("**Paste:**")
            part.append(f"```\n{paste}\n```")
            if st.get("limit") and len(paste) > st["limit"]:
                problems.append(f"step {n} ({st['title']}): paste is {len(paste)} chars, limit {st['limit']}")
            problems += [f"step {n} ({st['title']}) paste: {t}" for t in style_tells(paste)]
        for line in st.get("lines", []):
            part.append(line)
            prose.append(line)
        part.append(f"- [ ] {st.get('check', 'Done')}")
        out.append("\n\n".join(part))
    out += plan.get("tail", [])
    prose += plan.get("tail", [])
    problems += [f"write-up prose: {t}" for t in style_tells("\n".join(prose))]

    md = "\n\n".join(x for x in out if x) + "\n"
    dest = a.out or os.path.join(base, "writeup.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(md)
    for p in problems:
        print("PROBLEM:", p)
    print(f"{dest}: {len(plan['steps'])} steps, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
