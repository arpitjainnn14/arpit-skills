---
name: linkedin-profile-optimizer
description: Audit, score and rewrite a LinkedIn profile so recruiters and AI sourcing tools (LinkedIn Recruiter, Hiring Assistant, Juicebox, SeekOut, hireEZ) find it and it stands out. Reads the logged-in profile through Claude in Chrome (read-only), scores it on a fixed 100-point rubric, drafts copy-paste rewrites for headline, About, experience, skills, Featured, certifications and settings, designs the banner in Claude Design or Canva, and tracks scores over time in an HTML dashboard. Use this whenever the user mentions their LinkedIn profile, headline, About/summary, banner, recruiter visibility, "nobody views my profile", job hunting on LinkedIn, profile score or audit, or wants to re-check progress, even if they don't say "optimize".
---

# LinkedIn profile optimizer

Turn a LinkedIn profile into something a recruiter's search returns, and
that a person or a model can understand in 10 seconds: **what you do, for
whom, at what level, and the proof**.

The skill reads the profile, scores it, drafts rewrites, and stops there.
The user pastes the changes in. **Never edit the live profile.** Never
click Save, Post, Send, Connect, Endorse or Apply. The user chose
audit-and-drafts mode: an edit they did not review can notify their whole
network, and they cannot take it back.

## Files

- `references/rubric.md`: the 100-point rubric, grade bands, judging anchors. Read it before scoring.
- `references/capture.md`: how to read the profile in Chrome, and the `profile.json` schema.
- `references/sections.md`: per-section best practices, hard limits, India and remote notes. Read it before drafting.
- `references/banner.md`: the banner brief, the Claude Design canvas, and the Canva connector.
- `scripts/score.py`: scores a profile snapshot and checks LinkedIn character limits.
- `scripts/report.py`: builds `report.html`, comparing all runs.
- `scripts/build_writeup.py`: renders the click-by-click corrections checklist from `edits.json` and fails on over-limit pastes and AI-sounding text.
- `scripts/check_drafts.py`: re-measures every stated count in `drafts.md` (character counts, Add/Remove/Keep list sizes). It must pass before anything reaches the user.

`SKILL_DIR` below means the folder this file is in.

## Run folder

Every audit is a dated folder, so runs can be compared:

```
~/linkedin-audits/                 # or a folder the user names
  report.html                      # rebuilt every run
  2026-10-12/                      # one run (add -2, -3 for same-day reruns)
    targets.json                   # what we optimise for (reused across runs)
    profile.json                   # captured live profile
    judgments.json                 # your scores for judged criteria
    scorecard.json                 # score of the live profile
    proposed-profile.json          # profile.json with drafts applied
    proposed-judgments.json
    projected.json                 # score if drafts are applied
    drafts.md                      # the copy-paste deliverable
    banner-brief.md
```

Before you start, list the existing run folders. The latest one is the
**previous run**.

## Workflow

### 1. Targets

Scores are only comparable when the targets stay the same. If a previous
`targets.json` exists, show its titles and keywords, and ask whether
anything has changed. The default is to reuse it unchanged.

If no previous targets exist, ask in one message:
- The target job titles (1–3), seniority, and industry or domain.
- Market: India, remote/global, or both.
- Whether they are actively looking (this decides whether Open to Work is scored), and whether they are between roles.
- Sources:
  - a resume/CV path
  - a GitHub username
  - 2–5 target job postings (URLs or pasted text)

  Job postings make the keyword list real instead of guessed, so push for at least two.

Read the job postings. LinkedIn job URLs need Chrome (`get_page_text`). For other URLs use WebFetch. Then write `targets.json`:

```json
{
  "titles": ["Senior Backend Engineer", "Backend Engineer"],
  "keywords": ["Go|Golang", "Kubernetes|K8s", "PostgreSQL|Postgres", "Kafka", "microservices", "AWS|Amazon Web Services", "system design", "distributed systems"],
  "ai_queries": [
    "Senior backend engineer with Go and Kafka who has run payment or high-throughput systems in production",
    "Backend engineer in India open to remote roles, 5+ years, Kubernetes and AWS",
    "Engineer who has scaled a fintech backend and led a small team"
  ],
  "market": ["India", "Remote"],
  "open_to_work_applicable": true,
  "between_roles": false
}
```

- **Keywords:** 15–30 of them, ranked by how often they appear across the postings. Use `|` to separate aliases. Prefer the wording the postings use. With no postings, derive keywords from the titles and the market, and tell the user the list is a guess.
- **ai_queries:** exactly 3, written the way a recruiter would type into Hiring Assistant or Juicebox. One should be strict on stack, one on domain or seniority, one on location or work mode.

### 2. Capture

Follow `references/capture.md` and write `profile.json`. If Chrome or the
login is not available, ask the user for the profile PDF ("More → Save to
PDF") or pasted text instead. Do not give up on the audit.

Then gather the other sources:
- The resume: use Read, or the pdf/docx skill.
- GitHub: `gh api users/<u>` and `gh api "users/<u>/repos?sort=pushed&per_page=30"`, or WebFetch if `gh` is not available.

These are where the missing metrics, projects and skills come from.

### 3. Score the live profile

```bash
python3 SKILL_DIR/scripts/score.py --profile RUN/profile.json --targets RUN/targets.json
```

This prints the auto scores and the pending judged criteria. Next, write
`judgments.json` (`{"B1": {"score": 3, "evidence": "…"}, …}`) for B1, B2,
B3, B4, C1, C2, C4, C5, D4 and E2, using the anchors in `rubric.md`.
For B1, write `{"queries_met": 0-3, "evidence": "<per query: met, or the requirement missing>"}`
and let the script convert it to points. A query is met only when every hard
requirement is stated, not inferred. Evidence must
quote or point to the actual text, so the user can see why. If a previous
run exists, follow the consistency rule at the bottom of `rubric.md`. Then
run:

```bash
python3 SKILL_DIR/scripts/score.py --profile RUN/profile.json --targets RUN/targets.json \
  --judgments RUN/judgments.json --label current --out RUN/scorecard.json
```

The script also prints:
- `FACT:` lines, such as the computed `experience_years`. Use these in every draft, never your own arithmetic.
- `FLAG:` lines: red flags such as employment gaps, unbacked "Certified" claims, a years-of-experience mismatch, or public "open to roles" text when the user wants discretion. Every flag goes into C5 and into the **Red flags** part of your reply, even if it costs no points.
  - The checks are heuristics. If a flag is wrong (the claim is true and the regex misread it), say so in the reply and in the C5 evidence.
  - **Never reword true text just to silence a flag.** Rewording to beat the checker hides the very thing the user should see, and it teaches nothing.
- `ANCHOR:` warnings: a judged score that contradicts a hard anchor. Fix the judgment and re-run.

Score honestly. First audits usually land at 35–60. A flattering number
makes the before/after comparison worthless, and it is the comparison the
user asked for.

### 4. Fill the fact gaps

Rewrites are only as good as the facts behind them. List what the drafts
need that you don't have. Common gaps:
- metrics for the last 3 roles
- team size and scale (users, requests, data, revenue)
- the products shipped
- certifications in progress
- who could write a recommendation

First check whether the resume or GitHub already answers each gap. Then
ask the user what is left, in **one** message with at most 8 specific
questions, each tied to a role ("At Acme, roughly how many orders a day did
the checkout service handle?"). Accept "don't know". In that case the draft
keeps a placeholder. Also ask whether any employer numbers (revenue,
volumes, client names) are confidential. If they are, rewrite them as
ranges or relative figures ("~3× throughput") instead of dropping the
proof.

### 5. Draft

Read `references/sections.md`. Then write `drafts.md` in the order the
LinkedIn edit screens use:

```markdown
# LinkedIn drafts — <date>
Score now: <total> (<grade>) → projected <total> (<grade>) if all applied.

## Apply in this order
<numbered list: goal blockers first, then by points recoverable (from the scorecard), each with the rubric IDs it moves and a rough time cost>

## Red flags
<every FLAG line, with the fix. Example: "Headline says AWS Certified but no certification is listed: add it under Licenses & certifications with the credential URL, or drop the claim.">

## Headline
Current: "<current>"
**Recommended (A)** — <n>/220 chars
<copy-paste text>
Alternatives: (B) … (C) …
Why: <one or two sentences, rubric IDs>

## About
**Proposed** — <n>/2600 chars
<copy-paste text>
Why: …

## Experience
### <Title> · <Company>
Title: <standard title, if it changes>
**Description** — <n>/2000 chars
<copy-paste text>
Skills to attach: a, b, c, d, e

## Skills
Top 5: …
Add: …
Remove: …

## Featured
<3–6 items: what to add, its title, why>

## Certifications / Projects / Honors
## Settings checklist
<first: turn off "Share profile updates with your network". Then custom URL, location, Open to Work fields, public visibility, contact info. Exact values to enter.>

## Recommendation requests
<one ready-to-send message per suggested colleague, under 600 chars. The user sends them.>

## Banner
<pointer to banner-brief.md and the Canva link>
```

Rules for every draft:
- **No fabrication.** Every claim, metric, title and skill must come from the profile, the resume, GitHub or the user's answers. If a number is missing, write `[ADD METRIC: what to measure]`. A recruiter screen will test anything on the profile, and an invented number is worse than none.
- Use keywords only where they are true. Spread the target keywords across headline, About (3 or more in the first 300 chars), experience and skills. Never write a keyword-stuffed list in prose.
- Keep the user's voice, and make it sound like them, not like a model (`sections.md` §14). Reuse their own phrasing from their answers. `score.py` prints `STYLE:` lines for AI tells (stock words, em-dash runs, colon-pattern bullets, ALL-CAPS header stacks). Clear them in the drafts, and judge C4 as no higher than 2 while any remain.
- Placeholders name what to measure and never carry a realistic example value: `[ADD METRIC: uptime %]`, not `[e.g. 99.9%]`. An example value gets pasted as fact.
- Give every text block its character count, including recommendation requests and project descriptions, computed with code (`python3 -c "print(len(open('x').read()))"` or `score.py --check-limits`), never by eye. The text must paste without hitting a limit.
- One number, one meaning. If the same figure describes different things ("40,000 businesses", "40,000 merchants"), flag it and ask which is right.
- Build the Skills section from `proposed-profile.json`: list the Top 5, then the final full list with its count, then what to add and remove. The Top 5 must be in the final list, and add + keep must equal the count.
- Headlines for career switchers, and the discreet-versus-openly-looking choice, follow `sections.md` §2. When the user is employed and hasn't said how open the search is, give both variants and ask.

Then make `proposed-profile.json`: a copy of `profile.json` with the drafted
text applied. Apply only changes the user can make on their own: text,
skills, settings, Featured items they already have, and a banner they will
upload. Leave recommendations and verification as they are, because those
depend on other people. Write `proposed-judgments.json` by judging the
drafts with the same anchors, and just as strictly. Text that is still an
`[ADD …]` placeholder earns nothing: score it as if it were blank.
Otherwise the projection promises points that only the user's missing facts
could earn. A projected 6/6 on an
About under 1,200 chars is a broken promise, and the next re-audit will
expose it. If `score.py` prints any `ANCHOR:` or `FLAG:` line for the
proposed profile, fix the draft or the judgment. Then run:

```bash
python3 SKILL_DIR/scripts/score.py --check-limits RUN/proposed-profile.json
python3 SKILL_DIR/scripts/score.py --profile RUN/proposed-profile.json --targets RUN/targets.json \
  --judgments RUN/proposed-judgments.json --baseline RUN/profile.json \
  --label projected --out RUN/projected.json
```

Fix any limit violation before moving on. Then verify the drafts themselves:

```bash
python3 SKILL_DIR/scripts/check_drafts.py RUN/drafts.md
```

Every count `MISMATCH` is a number you wrote by hand; every `STYLE` line is text that reads as machine-written. Recount it with code, fix
it in `drafts.md`, and re-run until it prints `0 wrong`. The user should never
have to find a wrong count: a write-up that says "288 characters" next to a
282-character block makes them distrust every other number in it.

If the projected score is still
under 75, say which criteria are still losing points, and whether the fix
needs the user to act (get recommendations, earn a certification, publish a
project) rather than better wording.

### 6. Banner

Follow `references/banner.md`. Write the brief, then build two banner directions as a Claude Design canvas (Artifact tool, Design type). The user can export a PNG or send it to Canva from there. Use the Canva connector directly only if the user asks for it or the Artifact tool is not available.

### 7. Report

```bash
python3 SKILL_DIR/scripts/report.py --dir ~/linkedin-audits && open ~/linkedin-audits/report.html
```

### 8. The write-up (always; do not wait to be asked)

A full audit always ends with a corrections checklist the user can follow
while editing. Nobody should have to ask for it, or ask for it to be fixed.
It is not a report: no scores, rubric IDs, point gains or reasoning. Those
live in `drafts.md` and `report.html`.

1. Write `RUN/edits.json`: one step per LinkedIn screen, in the order the
   user would edit:
   - turn off update sharing
   - headline
   - About + Top skills
   - each Experience role
   - Skills
   - Featured
   - projects (removals as their own step)
   - certifications
   - Open to Work
   - contact info
   - banner and photo

   Each step has `where` (the exact clicks), `first` lines (title changes,
   "the box is empty, so just paste"), `delete` (the current text, quoted
   short), `paste_file` (the verified text file behind `drafts.md`),
   `limit`, then `lines` (skills to attach, dates to fix). Put off-LinkedIn
   items (resume fixes, GitHub bio) and recommendation requests in `tail`.
2. Build and check it:

   ```bash
   python3 SKILL_DIR/scripts/build_writeup.py RUN/edits.json
   ```

   It renders `RUN/writeup.md` and fails on any paste over its limit, or any
   text that reads as machine-written. Fix and rebuild until it reports
   `0 problems`.
3. Publish `writeup.md`. Where a first-party document connector is
   available (Claude Docs: `Artifact` quickstart, `intent: "document"`),
   make it a doc titled "LinkedIn edits for <first name>", one step group
   per call. Otherwise publish it as an HTML artifact with copy buttons.
   Failing both, hand over the file.

Write it the way a friend who knows LinkedIn would: short plain sentences,
"Where / Delete / Paste" and a tick box for each step, no em-dash chains, no
ALL-CAPS, no "at a glance" or "key takeaways". If the user edits the doc,
their edit wins. Re-check it with the same scripts, never overwrite it.

## Re-audit ("check my progress", "re-score my LinkedIn")

Use the same flow, with five differences:
1. Reuse `targets.json`.
2. After capture, compare `profile.json` with the previous run's `proposed-profile.json`. Tell the user which drafted changes they applied, which they partly applied, and which they skipped.
3. Re-check anything carried over from the previous drafts against the current rules before you reuse it. Earlier drafts can be wrong. The `--baseline` flag catches one case: a drafted Experience title that gains a level the user never held.
4. Draft only what still loses points. Keep the summary centred on the delta: "62 → 81. Applied headline, About and skills. Experience bullets still need metrics."
5. End with step 8's write-up as usual, covering only what's left: a "done" table of the applied changes, then current versus replacement for the rest.

## Quick score only

If the user only wants a score ("rate my profile", "how bad is it?"), do
steps 1–3 and 7 (skip step 8: a quick score's reply is the write-up). Then reply with:
- the score and grade, with one line per category
- red flags (every `FLAG:` line)
- the top 5 fixes. **Goal blockers come first**, whatever their points: anything that hides the profile from the search the user described. Examples: Remote missing from Open to Work when they want remote, Open to Work off while job seeking, the target title absent from the headline. The rest follow **sorted by points recoverable, highest first**. Take
  each fix's points from the scorecard (`max − score` of the criteria it
  moves). Do not estimate them. If two fixes tie, put the faster one first.
- one ready-to-paste headline, as a preview of what drafting would give
- an offer to draft the rest
