#!/usr/bin/env python3
"""Score a LinkedIn profile snapshot against references/rubric.md.

    score.py --profile profile.json --targets targets.json \
             [--judgments judgments.json] [--label current] [--out scorecard.json]
    score.py --check-limits profile.json

Auto criteria are computed here. Judged criteria are read from
judgments.json ({"B1": {"score": 3, "evidence": "..."}, ...}); any missing
ones are listed as pending and the scorecard is marked incomplete.
Exit codes: 0 ok, 1 limit violations (--check-limits), 2 bad input.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys

RUBRIC = [
    # id, category, max, kind, name
    ("A1", "A", 6, "auto", "Target title literally in headline"),
    ("A2", "A", 4, "auto", "Current role title matches target"),
    ("A3", "A", 7, "auto", "Target-keyword coverage"),
    ("A4", "A", 5, "auto", "Skills depth and Top skills alignment"),
    ("A5", "A", 3, "auto", "Keywords in first 300 chars of About"),
    ("A6", "A", 2, "auto", "Location set"),
    ("A7", "A", 3, "auto", "Open to Work configured"),
    ("B1", "B", 4, "judged", "Simulated AI recruiter match"),
    ("B2", "B", 3, "judged", "Entity clarity"),
    ("B3", "B", 3, "judged", "Structured context per role"),
    ("B4", "B", 2, "judged", "Cross-platform consistency"),
    ("B5", "B", 3, "auto", "Public profile visible"),
    ("C1", "C", 6, "judged", "Headline quality"),
    ("C2", "C", 6, "judged", "About structure"),
    ("C3", "C", 3, "auto", "Buzzword density"),
    ("C4", "C", 3, "judged", "Voice and readability"),
    ("C5", "C", 2, "judged", "Claims consistent and backed"),
    ("D1", "D", 6, "auto", "Quantified achievements"),
    ("D2", "D", 4, "auto", "Featured section"),
    ("D3", "D", 4, "auto", "Recommendations received"),
    ("D4", "D", 3, "judged", "Relevant certifications"),
    ("D5", "D", 3, "auto", "Projects, honors, publications"),
    ("E1", "E", 3, "auto", "Profile photo"),
    ("E2", "E", 3, "judged", "Banner quality"),
    ("E3", "E", 2, "auto", "Custom URL"),
    ("E4", "E", 2, "auto", "Education"),
    ("E5", "E", 3, "auto", "Recent roles described"),
    ("E6", "E", 2, "auto", "Verification badge"),
]
CATEGORIES = {
    "A": "Recruiter Searchability",
    "B": "AI-Sourcing Readiness",
    "C": "Positioning & Copy",
    "D": "Proof & Credibility",
    "E": "Completeness & Trust",
}
LIMITS = {"headline": 220, "about": 2600, "exp_title": 100, "exp_desc": 2000,
          "skills": 100, "skill_name": 80}
BUZZWORDS = [
    "results-driven", "results-oriented", "passionate about",
    "dynamic", "synergy", "synergies", "leveraging", "comprehensive", "robust",
    "visionary", "thought leader", "seasoned professional", "proven track record",
    "go-getter", "strategic thinker", "detail-oriented", "detail oriented",
    "team player", "excited to announce", "in today's landscape", "game-changing",
    "game changer", "revolutionary", "cutting-edge", "cutting edge",
    "hardworking", "hard-working", "self-motivated", "self-starter",
    "think outside the box", "out-of-the-box", "guru", "ninja", "rockstar",
    "best-in-class", "world-class", "innovative", "motivated individual",
]
# Words and moves that make text read as model-written. Recruiters see thousands of
# AI-drafted profiles; these patterns now cost trust, not just style points.
AI_TELLS = [
    "delve", "seamless", "seamlessly", "robust", "leverage", "leveraged", "leveraging",
    "spearheaded", "showcase", "showcasing", "elevate", "elevating", "streamline", "streamlined",
    "cutting-edge", "meticulous", "tapestry", "realm", "harness", "harnessing", "foster",
    "fostering", "pivotal", "holistic", "unlock", "unlocking", "empower", "empowering",
    "navigate the", "in today's", "fast-paced", "ever-evolving", "thrilled to", "excited to",
    "happy to talk", "passionate about", "driven by a passion", "not just", "a testament to",
    "game-changer", "dive into", "deep dive", "at the intersection of", "end-to-end solutions",
]
SENIORITY = {"senior", "sr", "junior", "jr", "lead", "staff", "principal",
             "associate", "head", "chief", "ii", "iii", "i", "of", "and", "the", "-"}
NUMBER_RE = re.compile(
    r"[₹$€£]\s?\d|\d+(\.\d+)?\s?(%|x\b|×|k\b|m\b|mn\b|bn\b|l\b|lakh|lac|crore|cr\b|\+)"
    r"|\b\d{1,3}(,\d{3})+\b|\b(?!(19|20)\d\d\b)\d+\b",
    re.I)
AUTOGEN_SLUG_RE = re.compile(r"-(?=[a-z0-9]*\d)[a-z0-9]{5,}$|-\d{3,}$", re.I)


def kw_re(alias):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias.strip()) + r"(?![A-Za-z0-9])", re.I)


def has(text, aliases):
    return any(kw_re(a).search(text or "") for a in aliases if a.strip())


def keywords(t):
    return [[a for a in k.split("|") if a.strip()] for k in t.get("keywords", [])]


def title_match(text, titles):
    """2 = exact target title present, 1 = at least half of a title's core words, 0 = none."""
    if has(text, titles):
        return 2
    words = set(re.findall(r"[a-z0-9+#.]+", (text or "").lower()))
    for title in titles:
        core = [w for w in re.findall(r"[a-z0-9+#.]+", title.lower()) if w not in SENIORITY]
        if core and sum(w in words for w in core) * 2 >= len(core):
            return 1
    return 0


def roles(p):
    return p.get("experience") or []


def bullets(desc):
    out = []
    for line in (desc or "").splitlines():
        line = line.strip().lstrip("•-*–·▪◦ ").strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", line) if len(line) > 200 else [line]
        out += [s for s in parts if len(s) >= 20]
    return out


def skill_names(p):
    return [s["name"] if isinstance(s, dict) else s for s in p.get("skills") or []]


def corpus(p):
    parts = [p.get("headline"), p.get("about")]
    for r in roles(p):
        parts += [r.get("title"), r.get("description")] + (r.get("skills") or [])
    parts += skill_names(p) + (p.get("top_skills") or [])
    return "\n".join(x for x in parts if x)


def score_auto(cid, p, t):
    """Return (score, evidence) or (None, reason) when n/a."""
    titles = t.get("titles") or []
    kws = keywords(t)
    about = p.get("about") or ""
    rs = roles(p)
    recent = rs[:3]

    if cid == "A1":
        m = title_match(p.get("headline"), titles)
        return [0, 3, 6][m], f"headline {'contains a target title' if m == 2 else 'partially matches' if m else 'has no target title'}: {p.get('headline')!r}"
    if cid == "A2":
        cur = next((r for r in rs if r.get("current")), None)
        if not cur:
            if t.get("between_roles"):
                return None, "between roles"
            return 0, "no current role listed"
        m = title_match(cur.get("title"), titles)
        return [0, 2, 4][m], f"current title {cur.get('title')!r}"
    if cid == "A3":
        if not kws:
            return 0, "targets.keywords is empty"
        text = corpus(p)
        missing = [k[0] for k in kws if not has(text, k)]
        cov = 1 - len(missing) / len(kws)
        return round(7 * cov), f"{len(kws) - len(missing)}/{len(kws)} keywords found; missing: {', '.join(missing[:12]) or 'none'}"
    if cid == "A4":
        names = skill_names(p)
        n = len(names)
        base = 3 if n >= 30 else 2 if n >= 15 else 1 if n >= 5 else 0
        top = p.get("top_skills") or names[:5]
        hit = sum(1 for k in kws if has("\n".join(top), k))
        bonus = 2 if hit >= 3 else 1 if hit >= 1 else 0
        return base + bonus, f"{n} skills; {hit} target keywords in Top skills {top}"
    if cid == "A5":
        head = about[:300]
        hit = [k[0] for k in kws if has(head, k)]
        return min(3, len(hit)), f"keywords in first 300 chars: {hit or 'none'}"
    if cid == "A6":
        return (2, f"location {p['location']!r}") if p.get("location") else (0, "no location")
    if cid == "A7":
        if t.get("open_to_work_applicable") is False:
            return None, "not job seeking"
        otw = p.get("open_to_work") or {}
        if not otw.get("enabled"):
            return 0, "off"
        wants_remote = any("remote" in m.lower() for m in t.get("market") or [])
        where = " ".join((otw.get("locations") or []) + (otw.get("workplace") or [])).lower()
        covers = bool(otw.get("locations")) and (not wants_remote or "remote" in where)
        miss = [] if otw.get("titles") else ["no job titles"]
        if not covers:
            miss.append("Remote missing from locations/workplace" if wants_remote and otw.get("locations") else "no locations")
        return 1 + bool(otw.get("titles")) + covers, f"on ({otw.get('visibility', '?')})" + (f"; {', '.join(miss)}" if miss else f", titles {otw['titles']}")
    if cid == "B5":
        vis = (p.get("public_profile") or {}).get("visible")
        return (3, "public profile visible") if vis is True else (0, "public profile hidden" if vis is False else "not captured — check linkedin.com/public-profile/settings")
    if cid == "C3":
        text = "\n".join(x for x in [p.get("headline"), about] + [r.get("description") for r in rs] if x)
        found = [b for b in BUZZWORDS for _ in kw_re(b).findall(text)]
        n = len(found)
        s = 3 if n == 0 else 2 if n <= 2 else 1 if n <= 4 else 0
        return s, f"{n} buzzwords: {sorted(set(found)) or 'none'}"
    if cid == "D1":
        bs = [b for r in recent for b in bullets(r.get("description"))]
        if not bs:
            return 0, "no bullets in the last 3 roles"
        q = sum(1 for b in bs if NUMBER_RE.search(b))
        ratio = q / len(bs)
        depth = min(1.0, len(bs) / 6)  # three bullets in total is thin evidence, however well quantified
        return min(6, round(6 * min(1.0, ratio / 0.6) * depth)), f"{q}/{len(bs)} bullets quantified ({ratio:.0%}); {len(bs)} bullets across recent roles (full credit needs 6+)"
    if cid == "D2":
        n = len(p.get("featured") or [])
        return (4 if 3 <= n <= 6 else 3 if n > 6 else 2 if n else 0), f"{n} featured items"
    if cid == "D3":
        n = p.get("recommendations_received")
        if n is None:
            n = len(p.get("recommendations") or [])
        return (4 if n >= 3 else 2 if n else 0), f"{n} recommendations received"
    if cid == "D5":
        n = sum(len(p.get(k) or []) for k in ("projects", "honors", "publications"))
        return (3 if n >= 2 else 2 if n else 0), f"{n} projects/honors/publications"
    if cid == "E1":
        return (3, "photo present") if p.get("photo") else (0, "no photo")
    if cid == "E3":
        slug = (p.get("custom_url") or "").rstrip("/").split("/")[-1]
        if not slug:
            return 0, "URL not captured"
        return (0, f"auto-generated slug {slug!r}") if AUTOGEN_SLUG_RE.search(slug) else (2, f"custom slug {slug!r}")
    if cid == "E4":
        return (2, "education listed") if p.get("education") else (0, "no education")
    if cid == "E5":
        if not recent:
            return 0, "no roles"
        good = sum(1 for r in recent if len(r.get("description") or "") >= 200)
        return round(3 * good / len(recent)), f"{good}/{len(recent)} recent roles have 200+ char descriptions"
    if cid == "E6":
        return (2, "verified") if p.get("verified") else (0, "not verified")
    raise KeyError(cid)


def ym(s):
    """'2023-03' / '2023' / None -> months since year 0, or None."""
    m = re.match(r"(\d{4})(?:-(\d{1,2}))?", str(s or ""))
    return int(m.group(1)) * 12 + int(m.group(2) or 1) - 1 if m else None


def facts(p):
    """Derived facts the drafts must agree with, plus red flags for the user."""
    now = ym((p.get("captured_at") or dt.date.today().isoformat())[:7])
    spans = sorted((ym(r.get("start")), now if r.get("current") else ym(r.get("end")) or ym(r.get("start")))
                   for r in roles(p) if ym(r.get("start")) is not None)
    months, flags, cur_end = 0, [], None
    for a, b in spans:
        if cur_end is not None and a - cur_end > 6:
            flags.append(f"{a - cur_end}-month gap between roles ending {cur_end // 12}-{cur_end % 12 + 1:02d}")
        lo = max(a, cur_end) if cur_end is not None else a
        months += max(0, b - lo)
        cur_end = b if cur_end is None else max(cur_end, b)
    if cur_end is not None and not any(r.get("current") for r in roles(p)) and now - cur_end > 3:
        flags.append(f"no current role: {now - cur_end} months since the last role ended — explain it (About, Open to Work, or a current entry for study/freelance/projects)")
    claim_text = "\n".join(x for x in [p.get("headline"), p.get("about")] if x)
    certs = " ".join(c.get("name", "") + " " + (c.get("issuer") or "") for c in p.get("certifications") or [])
    for m in re.finditer(r"([A-Z][\w+.-]*(?:[ \t]+[A-Z][\w+.-]*){0,3})[ \t]+Certified|Certified[ \t]+([A-Z][\w+.-]*(?:[ \t]+[A-Z][\w+.-]*){0,3})", claim_text):
        vendor = (m.group(1) or m.group(2)).split()[0]
        if not re.search(re.escape(vendor), certs, re.I):
            flags.append(f"headline/About claims '{m.group(0)}' but no matching certification is listed")
    total_years = round(months / 12, 1)
    words = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
    num = r"(\d+|" + "|".join(words) + r")"
    # Only claims about the career length count. "Grew ARR 3x in 2 years" is not one.
    # A qualified claim ("7 years of teaching experience", "the last 5 years") may be a
    # subset of the career, so it is flagged only when it overclaims.
    for m in re.finditer(r"\b" + num + r"(\+)?[ \t]+years?(?:'|’)?[ \t]+(?:of[ \t]+)?(\w+[ \t]+)?experience\b"
                         r"|\b(?:last|past)[ \t]+" + num + r"[ \t]+years\b"
                         r"|\b" + num + r"\+[ \t]+years\b", claim_text, re.I):
        raw = m.group(1) or m.group(4) or m.group(5)
        n = int(raw) if raw.isdigit() else words[raw.lower()]
        subset = bool(m.group(3)) or bool(m.group(4)) or bool(m.group(2)) or bool(m.group(5))
        if total_years and (n > total_years + 0.5 if subset else abs(n - total_years) >= 1):
            flags.append(f"text says {m.group(0)!r} but listed roles add up to {total_years} years")
    ends = [ym(e.get("end")) for e in p.get("education") or [] if ym(e.get("end"))]
    student = re.search(r"\b(pursuing|currently (?:studying|enrolled)|final[- ]year|student at|undergrad(?:uate)?)\b",
                        claim_text, re.I)
    if student and ends and max(ends) < now:
        flags.append(f"text says {student.group(0)!r} but education ended {max(ends) // 12}-{max(ends) % 12 + 1:02d}: "
                     "it reads as a current student, so update it to the finished degree")
    otw = p.get("open_to_work") or {}
    if otw.get("enabled") and otw.get("visibility") == "recruiters" and re.search(
            r"\bopen[ \t]+to\b[\s\S]{0,80}?\b(roles?|opportunit\w*|positions?|jobs?)\b", claim_text, re.I):
        flags.append("Open to Work is recruiters-only, but the headline/About publicly says 'open to … roles'. "
                     "Anyone, the current employer included, can read it. Keep it only if that is fine")
    edu = sorted((ym(e.get("start")) or ym(e.get("end")), (ym(e.get("end")) or ym(e.get("start"))) + 5)
                 for e in p.get("education") or [] if ym(e.get("start")) or ym(e.get("end")))
    first_role = spans[0][0] if spans else None
    if edu and first_role is not None:
        covered = [(a, b) for a, b in edu if a < first_role]
        end = covered[0][1] if covered else None
        for a, b in covered[1:] + [(first_role, first_role)]:
            if end is not None and a - end > 12:
                flags.append(f"{(a - end) // 12}+ years between education ending {end // 12} and the next entry ({a // 12}) are unaccounted for — list that work, or the profile reads as less experience than you have")
            end = max(end, b) if end is not None else b
    return {"experience_years": total_years,
            "headline_chars": len(p.get("headline") or ""),
            "about_chars": len(p.get("about") or "")}, flags


SENIORITY_WORDS = re.compile(r"\b(senior|sr\.?|lead|staff|principal|head|manager|director|vp|chief|architect)\b", re.I)


def title_inflation(live, proposed):
    """A drafted Experience title may add a standard title, never a level the person did not hold."""
    out = []
    old = {(r.get("company") or "").lower(): r.get("title") or "" for r in roles(live)}
    for r in roles(proposed):
        before = old.get((r.get("company") or "").lower())
        if before is None:
            continue
        gained = {w.lower().rstrip(".") for w in SENIORITY_WORDS.findall(r.get("title") or "")} - \
                 {w.lower().rstrip(".") for w in SENIORITY_WORDS.findall(before)}
        if gained:
            out.append(f"Experience title at {r.get('company')} gains {sorted(gained)}: {before!r} -> {r.get('title')!r}. "
                       "A title field must state the level actually held; put the target level in the headline or Open to Work")
    return out


def style_tells(text):
    """Patterns that read as machine-written. Returns a list of short findings."""
    out = []
    t = text or ""
    found = sorted({w for w in AI_TELLS if kw_re(w).search(t)})
    if found:
        out.append(f"AI-sounding words: {', '.join(found)}")
    dashes = t.count("\u2014")
    if dashes > 1:
        out.append(f"{dashes} em dashes; use commas, full stops or brackets (at most one per block)")
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    # Real bullets only: "• x", "- x", "* x". Not "**Label:**" lines or "- [ ]" tick boxes.
    bullets = [l for l in lines if l[:1] in "\u2022\u25aa" or (l[:2] in ("- ", "* ") and not l.startswith("- ["))]
    colon_led = [b for b in bullets if ":" in b[:70]]
    if len(bullets) >= 3 and len(colon_led) * 2 >= len(bullets):
        out.append(f"{len(colon_led)}/{len(bullets)} bullets use the 'thing: result' colon pattern; vary them")
    caps = [l for l in lines if len(l) > 3 and l.upper() == l and any(c.isalpha() for c in l)]
    if len(caps) > 2:
        out.append(f"{len(caps)} ALL-CAPS headers ({', '.join(caps[:4])}); keep at most two, or none")
    starts = [b.lstrip("\u2022-*\u25aa ").split(" ")[0].lower() for b in bullets]
    if len(bullets) >= 4 and len(set(starts)) <= len(bullets) // 2:
        out.append("bullets keep opening with the same few verbs; vary the openings")
    return out


def anchor_warnings(p, crit):
    """Judged scores that contradict a hard anchor in rubric.md."""
    s = {c["id"]: c["score"] for c in crit}
    w = []
    about = (p.get("about") or "").strip()
    if s.get("C2") == 6 and not 1200 <= len(about) <= 2600:
        w.append(f"C2=6 but About is {len(about)} chars (anchor: 1,200–2,600)")
    if s.get("C2") == 6 and re.match(r"(hi|hello|hey)\b|(i am|i'm)\s+(a\s+|an\s+)?(passionate|motivated|dedicated|driven|"
                                     r"results|hard[- ]?working|enthusiastic|aspiring)", about, re.I):
        w.append("C2=6 but About opens with a greeting or a self-applied adjective (anchor: subtract 1)")
    if s.get("C1") == 6 and s.get("A1") != 6:
        w.append("C1=6 but the headline lacks a literal target title (A1 < 6)")
    tells = style_tells("\n".join(x for x in [p.get("headline"), p.get("about")] +
                                   [r.get("description") for r in roles(p)] if x))
    if s.get("C4") == 3 and tells:
        w.append("C4=3 but the text reads as machine-written: " + "; ".join(tells))
    if (s.get("E2") or 0) > 0 and p.get("banner") != "custom":
        w.append("E2 > 0 but banner is default")
    if s.get("B4") == 2 and not ((p.get("contact") or {}).get("github") or (p.get("contact") or {}).get("website")):
        w.append("B4=2 but no GitHub/website in contact info")
    return w


def check_limits(p):
    v = []
    if len(p.get("headline") or "") > LIMITS["headline"]:
        v.append(f"headline {len(p['headline'])}/{LIMITS['headline']} chars")
    if len(p.get("about") or "") > LIMITS["about"]:
        v.append(f"about {len(p['about'])}/{LIMITS['about']} chars")
    for r in roles(p):
        name = f"{r.get('title')} @ {r.get('company')}"
        if len(r.get("title") or "") > LIMITS["exp_title"]:
            v.append(f"title of {name}: {len(r['title'])}/{LIMITS['exp_title']} chars")
        if len(r.get("description") or "") > LIMITS["exp_desc"]:
            v.append(f"description of {name}: {len(r['description'])}/{LIMITS['exp_desc']} chars")
    names = skill_names(p)
    if len(names) > LIMITS["skills"]:
        v.append(f"{len(names)}/{LIMITS['skills']} skills")
    v += [f"skill {s!r} over {LIMITS['skill_name']} chars" for s in names if len(s) > LIMITS["skill_name"]]
    slug = (p.get("custom_url") or "").rstrip("/").split("/")[-1]
    if slug and not re.fullmatch(r"[A-Za-z0-9-]{3,100}", slug):
        v.append(f"custom URL slug {slug!r} must be 3-100 letters, digits, hyphens")
    return v


def grade(total):
    return "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F"


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: cannot read {path}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--targets")
    ap.add_argument("--judgments")
    ap.add_argument("--label", default="current")
    ap.add_argument("--out")
    ap.add_argument("--check-limits", metavar="PROFILE")
    ap.add_argument("--baseline", metavar="LIVE_PROFILE",
                    help="the live profile.json; flags drafted Experience titles that gain a seniority word")
    a = ap.parse_args()

    if a.check_limits:
        v = check_limits(load(a.check_limits))
        print("\n".join(v) if v else "all within LinkedIn limits")
        sys.exit(1 if v else 0)
    if not (a.profile and a.targets):
        ap.error("--profile and --targets are required")

    p, t = load(a.profile), load(a.targets)
    j = load(a.judgments) if a.judgments else {}
    criteria, pending, bad = [], [], []
    for cid, cat, mx, kind, name in RUBRIC:
        c = {"id": cid, "category": cat, "name": name, "max": mx, "kind": kind}
        if kind == "auto":
            s, ev = score_auto(cid, p, t)
        else:
            entry = j.get(cid)
            if entry is None:
                s, ev = None, "pending judgment"
                pending.append(cid)
            elif entry.get("na"):
                s, ev = None, entry.get("evidence", "n/a")
            elif cid == "B1" and isinstance(entry.get("queries_met"), int):
                # Deterministic: the judgment is the count of satisfied queries, the points follow the rubric.
                n = max(0, min(3, entry["queries_met"]))
                s, ev = [0, 1, 3, 4][n], f"{n}/3 queries met. " + entry.get("evidence", "")
            else:
                s, ev = entry.get("score"), entry.get("evidence", "")
                if not isinstance(s, (int, float)) or not 0 <= s <= mx:
                    bad.append(f"{cid} score {s!r} not in 0..{mx}")
        c.update(score=s, evidence=ev, na=s is None and cid not in pending)
        criteria.append(c)
    if bad:
        sys.exit("error: " + "; ".join(bad))

    cats = {}
    for k, label in CATEGORIES.items():
        rows = [c for c in criteria if c["category"] == k and not c["na"] and c["score"] is not None]
        earned = sum(c["score"] for c in rows)
        possible = sum(c["max"] for c in rows)
        cats[k] = {"name": label, "earned": earned, "possible": possible,
                   "pct": round(100 * earned / possible, 1) if possible else None}
    earned = sum(c["earned"] for c in cats.values())
    possible = sum(c["possible"] for c in cats.values())
    total = round(100 * earned / possible, 1) if possible else 0.0

    fct, flags = facts(p)
    if a.baseline:
        flags += title_inflation(load(a.baseline), p)
    warns = anchor_warnings(p, criteria)
    perf = dict(p.get("analytics") or {})
    for k in ("connections", "followers"):
        if p.get(k) is not None:
            perf[k] = p[k]

    card = {
        "label": a.label,
        "scored_at": dt.datetime.now().isoformat(timespec="seconds"),
        "profile_captured_at": p.get("captured_at"),
        "targets_hash": hashlib.sha256(json.dumps(t, sort_keys=True).encode()).hexdigest()[:12],
        "targets_titles": t.get("titles"),
        "complete": not pending,
        "pending": pending,
        "total": total,
        "grade": grade(total),
        "categories": cats,
        "criteria": criteria,
        "limit_violations": check_limits(p),
        "facts": fct,
        "flags": flags,
        "anchor_warnings": warns,
        "performance": perf,
    }
    if a.out:
        with open(a.out, "w") as f:
            json.dump(card, f, indent=2, ensure_ascii=False)

    print(f"{a.label}: {total}/100 ({card['grade']})" if not pending else f"{a.label}: provisional {total}/100 over auto criteria only — pending {', '.join(pending)}")
    for k, c in cats.items():
        print(f"  {k} {c['name']:<26} {c['earned']:>4}/{c['possible']:<3}")
    for c in criteria:
        s = "n/a" if c["na"] else "…" if c["score"] is None else c["score"]
        print(f"  {c['id']} {c['name']:<40} {s!s:>4}/{c['max']:<2} {c['evidence']}")
    for v in card["limit_violations"]:
        print(f"  LIMIT: {v}")
    print("  FACT: " + ", ".join(f"{k}={v}" for k, v in fct.items()))
    for f in flags:
        print(f"  FLAG: {f}")
    for w in warns:
        print(f"  ANCHOR: {w}")
    for t_ in style_tells("\n".join(x for x in [p.get("headline"), p.get("about")] +
                                     [r.get("description") for r in roles(p)] if x)):
        print(f"  STYLE: {t_}")


if __name__ == "__main__":
    main()
