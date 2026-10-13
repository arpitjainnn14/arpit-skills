# linkedin

Recruiters do not read profiles first. They search them. The search runs
Boolean queries in LinkedIn Recruiter, natural-language queries in Hiring
Assistant, and semantic queries in off-platform tools such as Juicebox,
SeekOut and hireEZ. A profile that never appears in those results does not
get read at all. A profile that does appear has about 10 seconds to say
what you do, for whom, at what level, and the proof.

## `linkedin-profile-optimizer`

- **Reads, never writes.** It captures your logged-in profile through
  Claude in Chrome. It visits about a dozen pages and does not click Save.
  You paste the drafts in yourself.
- **One fixed 100-point rubric.** It has five categories: Recruiter
  Searchability, AI-Sourcing Readiness, Positioning & Copy, Proof &
  Credibility, and Completeness & Trust.
  - `scripts/score.py` computes two-thirds of the points mechanically. These
    cover title match, keyword coverage against your target job postings,
    quantified bullets, buzzwords, and completeness.
  - The rest are judged against written anchors. Unchanged text keeps
    its score from the previous run, so trends stay honest.
- **Before, after, and over time.** Each run is a dated folder under
  `~/linkedin-audits/`.
  - It scores the live profile, then scores the drafts as a projection.
  - `scripts/report.py` draws both on one trend line, next to LinkedIn's own
    performance numbers: profile views, search appearances, impressions.
- **No invented numbers.** A missing metric becomes
  `[ADD METRIC: …]`, because a recruiter screen will test anything on the
  page.
- **Banner through Canva.** It writes a 1584×396 brief and creates the
  design through the Canva connector when you sign in.

Re-run it 2–4 weeks after applying changes. It reports which drafts you
applied and how the score and the analytics moved.
