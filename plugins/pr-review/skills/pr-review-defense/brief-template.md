## Context for reviewers

<!--
Copy this to .claude/review-context/<branch-with-slashes-as-dashes>.md, fill it
in, commit it, then `pr_review.py sync <pr> --yes` to mirror it into the PR body.

Write it for someone who has never seen this subsystem. Every section below
exists to pre-empt a specific class of context-free review comment — delete a
section only when it genuinely does not apply, not to save time.
-->

**Problem.** What was broken or missing, in one or two sentences. Include how it
showed up in production or QA if it did.

**Constraints that shaped this.** The non-obvious ones — infra we cannot
provision, a vendor API's behaviour, a deadline, a rule in CLAUDE.md. This is
the section that prevents "why didn't you just use X".

**Why this shape.** The design in three or four sentences. Name the load-bearing
decision.

**Alternatives rejected.**

- _X_ — rejected because …
- _Y_ — rejected because …

**Rules this deliberately obeys.** Cite CLAUDE.md items the diff touches, e.g.
"#7 keyword extras are rendered, so no PII in `logger.info` extras" or "#2
`full_name` casing preserved". Stops a reviewer flagging a rule you already
followed.

**Already verified.** Exact commands and results — `pytest app/tests/test_x.py`
(N passed), `ruff check app/`, a manual run against the vendor VM. A reviewer
should not have to guess what was tested.

**What to actually scrutinise.** Two or three specific things you are least sure
about, at `file:line`. Giving the review a target is the single most effective
way to avoid a generic one.

**Out of scope.** What this PR deliberately does not do, and where that work
lives instead (ticket, follow-up branch).
