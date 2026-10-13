#!/usr/bin/env python3
"""Build an HTML dashboard comparing every audit run in an audits folder.

    report.py [--dir ~/linkedin-audits] [--out <dir>/report.html]

Each run is a subfolder (YYYY-MM-DD[-N]) holding scorecard.json and,
optionally, projected.json (the score the drafted profile would get).
"""
import argparse
import html
import json
import os
import sys

E = html.escape


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def runs(root):
    out = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        card = load(os.path.join(d, "scorecard.json")) if os.path.isdir(d) else None
        if card:
            out.append({"name": name, "card": card, "proj": load(os.path.join(d, "projected.json"))})
    return out


def crit(card):
    return {c["id"]: c for c in card["criteria"]} if card else {}


def fmt(c):
    if not c:
        return "—"
    if c.get("na"):
        return "n/a"
    return "…" if c.get("score") is None else f'{c["score"]:g}'


def cat_earned(card, k):
    return f'{card["categories"][k]["earned"]:g}' if card else "—"


def delta(a, b):
    if a is None or b is None:
        return ""
    d = round(a - b, 1)
    cls = "up" if d > 0 else "down" if d < 0 else "flat"
    return f'<span class="{cls}">{"+" if d > 0 else ""}{d:g}</span>'


def trend_svg(rs):
    pts = [(r["name"], r["card"]["total"], r["proj"]["total"] if r["proj"] else None) for r in rs]
    w, h, pad = 640, 200, 32
    n = max(len(pts) - 1, 1)
    x = lambda i: pad + i * (w - 2 * pad) / n
    y = lambda v: h - pad - v * (h - 2 * pad) / 100
    grid = "".join(f'<line x1="{pad}" x2="{w-pad}" y1="{y(v)}" y2="{y(v)}" class="grid"/><text x="4" y="{y(v)+4}" class="ax">{v}</text>' for v in (0, 40, 60, 75, 90, 100))
    line = " ".join(f"{x(i)},{y(v)}" for i, (_, v, _) in enumerate(pts))
    dots = "".join(f'<circle cx="{x(i)}" cy="{y(v)}" r="4" class="cur"><title>{E(nm)}: {v}</title></circle><text x="{x(i)}" y="{h-8}" class="ax" text-anchor="middle">{E(nm)}</text>' for i, (nm, v, _) in enumerate(pts))
    proj = "".join(f'<line x1="{x(i)}" x2="{x(i)}" y1="{y(v)}" y2="{y(p)}" class="projline"/><circle cx="{x(i)}" cy="{y(p)}" r="4" class="proj"><title>{E(nm)} projected: {p}</title></circle>' for i, (nm, v, p) in enumerate(pts) if p is not None)
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Profile score over time">{grid}<polyline points="{line}" class="curline"/>{proj}{dots}</svg>'


def build(rs):
    latest, prev = rs[-1], (rs[-2] if len(rs) > 1 else None)
    cur, proj = latest["card"], latest["proj"]
    pcard = prev["card"] if prev else None
    warn = ""
    if pcard and pcard.get("targets_hash") != cur.get("targets_hash"):
        warn += '<p class="warn">Targets changed since the previous run, so the run-over-run deltas compare different goals.</p>'
    if not cur.get("complete"):
        warn += f'<p class="warn">Latest scorecard is incomplete: pending {E(", ".join(cur.get("pending", [])))}.</p>'
    if cur.get("limit_violations"):
        warn += "<p class=\"warn\">Over LinkedIn limits: " + E("; ".join(cur["limit_violations"])) + "</p>"
    if proj and proj.get("limit_violations"):
        warn += "<p class=\"warn\">Drafts over LinkedIn limits: " + E("; ".join(proj["limit_violations"])) + "</p>"

    proj_v = f'{proj["total"]:g}<small>/100 · {proj["grade"]}</small>' if proj else "—"
    tiles = f'''<div class="tiles">
  <div class="tile"><div class="k">Profile score</div><div class="v">{cur["total"]:g}<small>/100 · {cur["grade"]}</small></div><div class="s">{delta(cur["total"], pcard["total"]) + " vs " + E(prev["name"]) if pcard else "first audit"}</div></div>
  <div class="tile"><div class="k">Projected with drafts</div><div class="v">{proj_v}</div><div class="s">{delta(proj["total"], cur["total"]) + " if applied" if proj else "no projected.json"}</div></div>
  <div class="tile"><div class="k">Targets</div><div class="v sm">{E(", ".join(cur.get("targets_titles") or []))}</div><div class="s">{len(rs)} run(s) on record</div></div>
</div>'''

    cat_rows = "".join(
        f'<tr><td>{E(c["name"])}</td><td>{c["earned"]:g}/{c["possible"]}</td>'
        f'<td>{cat_earned(pcard, k)}</td><td>{cat_earned(proj, k)}</td>'
        f'<td><div class="bar"><i style="width:{c["pct"] or 0}%"></i></div></td></tr>'
        for k, c in cur["categories"].items())

    pc, cc, jc = crit(pcard), crit(cur), crit(proj)
    gap = sorted((c for c in cur["criteria"] if not c.get("na") and c.get("score") is not None),
                 key=lambda c: c["score"] - c["max"])
    fixes = "".join(f'<li><b>{E(c["id"])} {E(c["name"])}</b> — losing {c["max"] - c["score"]:g} pts. {E(c["evidence"])}</li>'
                    for c in gap[:7] if c["max"] > c["score"])
    crit_rows = "".join(
        f'<tr><td>{E(c["id"])}</td><td>{E(c["name"])}<span class="kind">{E(c["kind"])}</span></td><td>{c["max"]}</td>'
        f'<td>{fmt(pc.get(c["id"]))}</td><td><b>{fmt(c)}</b></td><td>{fmt(jc.get(c["id"]))}</td><td class="ev">{E(str(c["evidence"]))}</td></tr>'
        for c in cur["criteria"])

    keys = []
    for r in rs:
        for k in (r["card"].get("performance") or {}):
            if k not in keys:
                keys.append(k)
    perf = ""
    if keys:
        head = "".join(f"<th>{E(r['name'])}</th>" for r in rs)
        body = "".join("<tr><td>" + E(k) + "</td>" + "".join(f'<td>{E(str((r["card"].get("performance") or {}).get(k, "—")))}</td>' for r in rs) + "</tr>" for k in keys)
        perf = f'<h2>Performance</h2><p class="note">LinkedIn analytics captured at each run. These are outcomes, not inputs. Expect them to move 2–6 weeks after changes go live.</p><div class="scroll"><table><tr><th>Metric</th>{head}</tr>{body}</table></div>'

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LinkedIn Profile Audit</title><style>
:root{{--bg:#f7f7f5;--card:#fff;--fg:#1d1d1b;--mut:#6b6b66;--line:#e3e2dc;--acc:#0a66c2;--proj:#c27c0a;--up:#1a7f37;--down:#c0392b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--card:#1f1f1d;--fg:#ecebe6;--mut:#a09f98;--line:#33332f;--acc:#5aa2ef;--proj:#e0a54a;--up:#4cc26a;--down:#ef6b5b}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:17px;margin:32px 0 8px}}
.note{{color:var(--mut);font-size:13px;margin:0 0 8px}}.warn{{background:color-mix(in srgb,var(--proj) 15%,transparent);border-left:3px solid var(--proj);padding:8px 12px;border-radius:4px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:16px 0}}.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px}}
.k{{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}}.v{{font-size:32px;font-weight:650}}.v small{{font-size:14px;color:var(--mut);font-weight:400}}.v.sm{{font-size:15px;font-weight:500}}.s{{font-size:13px;color:var(--mut)}}
.up{{color:var(--up);font-weight:600}}.down{{color:var(--down);font-weight:600}}.flat{{color:var(--mut)}}
svg{{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}}.grid{{stroke:var(--line)}}.ax{{fill:var(--mut);font-size:10px}}
.curline{{fill:none;stroke:var(--acc);stroke-width:2}}.cur{{fill:var(--acc)}}.proj{{fill:var(--proj)}}.projline{{stroke:var(--proj);stroke-dasharray:3 3}}
.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px;font-size:14px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:12px;color:var(--mut);font-weight:600}}
.ev{{color:var(--mut);font-size:13px;min-width:240px}}.kind{{margin-left:6px;font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:3px;padding:0 4px}}
.bar{{background:var(--line);height:8px;border-radius:4px;min-width:80px}}.bar i{{display:block;height:100%;background:var(--acc);border-radius:4px}}
ol li{{margin-bottom:6px}}</style></head><body><main>
<h1>LinkedIn Profile Audit</h1><p class="note">Latest run {E(latest["name"])} · scored {E(cur.get("scored_at", ""))} · rubric: references/rubric.md</p>
{warn}{tiles}
<h2>Score over time</h2><p class="note">Blue is the scored live profile. Amber is the score the drafts from that run would get if applied.</p>{trend_svg(rs)}
<h2>Categories</h2><div class="scroll"><table><tr><th>Category</th><th>Now</th><th>Previous</th><th>Projected</th><th></th></tr>{cat_rows}</table></div>
<h2>Biggest gaps right now</h2><ol>{fixes or "<li>No gaps.</li>"}</ol>
<h2>All criteria</h2><div class="scroll"><table><tr><th>ID</th><th>Criterion</th><th>Max</th><th>Prev</th><th>Now</th><th>Projected</th><th>Evidence (now)</th></tr>{crit_rows}</table></div>
{perf}
</main></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/linkedin-audits"))
    ap.add_argument("--out")
    a = ap.parse_args()
    rs = runs(a.dir) if os.path.isdir(a.dir) else []
    if not rs:
        sys.exit(f"error: no run folders with scorecard.json under {a.dir}")
    out = a.out or os.path.join(a.dir, "report.html")
    with open(out, "w") as f:
        f.write(build(rs))
    print(out)


if __name__ == "__main__":
    main()
