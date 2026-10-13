# Profile Score rubric (100 points)

`scripts/score.py` scores every `auto` criterion. You score every `judged`
criterion in `judgments.json`, using the anchors below. One rubric, one
scorer, and one fixed `targets.json` make two runs comparable. If any of
the three changes, the comparison is no longer valid.

If a criterion does not apply, it is marked `n/a` and taken out of the
denominator. The total is always `earned / possible × 100`.

## Grade bands

| Score | Grade | Meaning |
|---|---|---|
| 90–100 | A | Stands out. Shows up in recruiter searches and wins the 10-second skim. |
| 75–89 | B | Strong. Findable, with a few gaps in proof or polish. |
| 60–74 | C | Visible but forgettable. Shows up in search but does not convert. |
| 40–59 | D | Hard to find. Missing keywords, structure, or sections. |
| 0–39 | F | Working against the goal. |

Most real profiles score 35–60 the first time they are audited. Expect that. Do not round up to be kind.

## A. Recruiter Searchability (30). All auto.

Recruiters search with Boolean and keyword queries on titles, headline and skills. They also filter by location and Open to Work status. Recent roles count more than old ones.

| ID | Criterion | Max | Rule |
|---|---|---|---|
| A1 | Target title literally in headline | 6 | Any target title, exact match → 6. At least half of the title's core words → 3. Otherwise 0. |
| A2 | Current role title matches target | 4 | Exact → 4. Partial → 2. No current role → 0 (n/a when `between_roles: true`). |
| A3 | Target-keyword coverage | 7 | 7 × the share of `targets.keywords` found anywhere in headline, About, experience or skills. |
| A4 | Skills depth and Top skills alignment | 5 | Up to 3 points for skill count: 30+ skills → 3, 15–29 → 2, 5–14 → 1. Up to 2 more if the Top 5 skills hold target keywords: 3 or more keywords → 2, 1–2 → 1. |
| A5 | Keywords in first 300 chars of About | 3 | One point per distinct target keyword, max 3. This is the text a recruiter sees before "see more". |
| A6 | Location set | 2 | Present → 2. |
| A7 | Open to Work configured | 3 | 1 point for On. 1 more for job titles. 1 more if the locations cover the target market, including Remote whenever `targets.market` has it. Off → 0. n/a when `open_to_work_applicable: false`. |

## B. AI-Sourcing Readiness (15)

LinkedIn Hiring Assistant and tools like Juicebox, SeekOut and hireEZ match profiles to natural-language queries such as "senior backend engineer, fintech, Kafka at scale, open to remote". They reward explicit, structured context and penalise vague prose.

| ID | Criterion | Max | Kind | Anchors |
|---|---|---|---|---|
| B1 | Simulated AI recruiter match | 4 | judged (write `"queries_met": n`; the script converts it to points) | Run each `targets.ai_queries` query (3 of them) against **headline + first 300 chars of About + current role** only. Count the queries the profile *clearly* satisfies: every hard requirement is stated, not inferred. 3/3 → 4, 2/3 → 3, 1/3 → 1, 0 → 0. For each query, write in the evidence which requirement is missing. |
| B2 | Entity clarity | 3 | judged | 3: the first 300 chars of About name the role, the specialty and the domain/audience in a sentence a model could quote ("Backend engineer who builds payment systems for Indian fintechs"). 2: two of the three. 1: a role only. 0: generic ("passionate technologist"). |
| B3 | Structured context per role | 3 | judged | Each of the last 3 roles states the domain/industry, the stack or method, and the scale (users, revenue, team size, data volume). 3: all roles have all three. 2: most do. 1: some. 0: none. |
| B4 | Cross-platform consistency | 2 | judged | 2: GitHub, portfolio or website is linked from the profile, and its positioning matches the headline. 1: linked, but the positioning differs or the link is stale. 0: nothing linked. |
| B5 | Public profile visible | 3 | auto | Public visibility is on → 3. Off or not captured → 0. Off-platform AI sourcing tools can only see the public profile. |

## C. Positioning and Copy (20)

| ID | Criterion | Max | Kind | Anchors |
|---|---|---|---|---|
| C1 | Headline quality | 6 | judged | 6: target title + 1–2 differentiating skills + domain/audience + one proof point (named employer, metric, credential), ≤220 chars, and no other candidate could use it verbatim. 4: title + skills, but generic. 2: title only, or "X at Company". 0: empty, or slogan-only. |
| C2 | About structure | 6 | judged | 6: a hook that states role and specialty up front ("I'm a backend engineer at Hexalog, building…" is fine), never a greeting ("Hi, I'm Arpit") or a self-applied adjective ("I am a passionate…"); credibility (domains, companies, problem types); proof with numbers; a CTA or contact line; scannable (short paragraphs or sub-headers); 1,200–2,600 chars. Subtract 1 for each missing element. 0 if About is empty. |
| C3 | Buzzword density | 3 | auto | 0 buzzwords → 3. 1–2 → 2. 3–4 → 1. More than 4 → 0. The list is in `score.py`. |
| C4 | Voice and readability | 3 | judged | 3: sounds like the person, not a model (no `STYLE:` lines from `score.py`), with active verbs, short lines, consistent person and no walls of text. 2: mostly good. 1: mixed. 0: dense blocks, or duties written in the passive "Responsible for…". |
| C5 | Claims consistent and backed | 2 | judged | Start from the `FLAG:` lines that `score.py` prints. 2: no flags, and every credential, title and metric in the headline and About is backed by a section (Certifications, Experience). 1: one minor mismatch (e.g. About says 5 years, roles add up to 6; "Pursuing a degree" after the education end date; resume and LinkedIn dates disagree). 0: an unbacked credential ("AWS Certified" with no certification listed), an inflated title, or an unexplained gap of 6+ months. A recruiter treats an unbacked claim as a red flag, not a typo. |

## D. Proof and Credibility (20)

| ID | Criterion | Max | Kind | Rule / anchors |
|---|---|---|---|---|
| D1 | Quantified achievements | 6 | auto | Share of bullets in the last 3 roles that contain a number. 60% or more scores 6, and the score scales linearly below that. A bare year does not count. The score is then scaled by depth: fewer than 6 bullets in total is thin evidence (3 bullets earn at most half). |
| D2 | Featured section | 4 | auto | 3–6 items → 4. More than 6 → 3. 1–2 → 2. 0 → 0. |
| D3 | Recommendations received | 4 | auto | 3 or more → 4. 1–2 → 2. 0 → 0. |
| D4 | Relevant certifications | 3 | judged | 3: 2 or more certifications that are relevant to the target role and current (not expired, from a recognised issuer). 2: 1 relevant. 1: only tangential ones. 0: none. |
| D5 | Projects, honors, publications | 3 | auto | Count across the three sections. 2 or more → 3. 1 → 2. 0 → 0. |

## E. Completeness and Trust (15). Auto, except E2.

| ID | Criterion | Max | Rule |
|---|---|---|---|
| E1 | Profile photo | 3 | Present → 3. |
| E2 | Banner quality | 3 | **judged.** 3: custom banner that carries a value line or proof, matches the headline, and keeps the text out of the photo's area. 2: custom and on-topic, but generic. 1: custom but cliché (stock laptop, "Data is the new oil", a quote) or off-topic. 0: default LinkedIn banner. For a proposed profile, score the banner in `banner-brief.md`. |
| E3 | Custom URL | 2 | Slug has no auto-generated suffix (e.g. `-a1b2c3`, `-123456`) → 2. |
| E4 | Education | 2 | At least one entry → 2. |
| E5 | Recent roles described | 3 | 3 × the share of the last 3 roles that have a description of 200 chars or more. |
| E6 | Verification badge | 2 | Verified → 2. |

## Performance (tracked, not scored)

These are captured on each run and shown as trends in the report. They are
outcomes, not inputs, so they stay out of the score. A profile with a
better score should see them rise over the following 2–6 weeks.

- `profile_views_90d`: profile views in the last 90 days.
- `search_appearances_7d`: search appearances in the last 7 days.
- `post_impressions_7d`: post impressions in the last 7 days.
- `connections`, `followers`.
- `last_post_days_ago`: days since your last post.

## Guards the script enforces

`score.py` prints `ANCHOR:` warnings when a judged score contradicts a hard
anchor. Examples: C2=6 for an About under 1,200 chars; C1=6 when the
headline has no target title; E2>0 on a default banner. Fix the judgment
before you save the scorecard. A projection is only honest if the drafts
are judged as strictly as the live profile.

## Judging consistently across runs

When a previous run exists, read its `judgments.json` before you write the
new one. For each judged criterion, compare the text you are judging now
with the text that was judged then. If that text has not changed, keep the
same score. If it has changed, re-score it and say what changed in the
evidence. Without this rule, re-rolled judgments make scores drift and the
trend line stops meaning anything.
