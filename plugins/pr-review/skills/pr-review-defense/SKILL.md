---
name: pr-review-defense
description: Use when responding to review comments on a GitHub PR, answering a reviewer, defending a PR, handling review feedback, or writing the reviewer-context block for a PR body. Verifies each comment against the code before conceding, so a confident-but-wrong review does not turn into a code change.
---

# PR review defense

Answering review comments on a GitHub PR. Run everything from inside the repo
under review.

The failure this exists to prevent: a reviewer leaves a plausible comment
written without repo context, the agent reads "senior engineer said so" as
evidence, and concedes. **A comment is not evidence. Only the code is.**

Everything mechanical is in `pr_review.py`, next to this file. Resolve it once
per session:

```bash
DRIVER="${CLAUDE_PLUGIN_ROOT:-.claude}/skills/pr-review-defense/pr_review.py"
[ -f "$DRIVER" ] || DRIVER=$(find ~/.claude ~/claude-skills -name pr_review.py -path '*pr-review-defense*' 2>/dev/null | head -1)
python3 "$DRIVER" --help
```

Needs `gh` (authenticated) and Python 3.10+ (stdlib only). The driver fetches
comments, and it **refuses to draft a reply for a CONCEDE that has no
reproduction** — that refusal is the point of the tool.

## The protocol

Every open comment gets exactly one verdict. There is no "good point, I'll
change it."

| Verdict | Means | Bar it must clear |
|---|---|---|
| `CONCEDE` | Reviewer is right | A **repro**: how they are right. A failing test or traceback when one is obtainable; otherwise the mechanism stated concretely, or the rule the code breaks. Plus a recorded **refutation attempt**. |
| `DISPUTE` | Reviewer is wrong | Counter-evidence at `file:line`, or a test that already covers the hole they claim. **No code change.** |
| `CLARIFY` | Claim is unfalsifiable as written | A question. **No code change.** |
| `NO_ACTION` | Approval, ack, bot noise | Nothing. Rejected on inline comments — those point at code. |

Three rules do the work:

1. **Try to refute before you concede — then concede properly.** Open the file.
   Run the test they say is missing. Only after a genuine attempt to prove them
   wrong fails do you write `refutation_attempted` and concede. `check` rejects
   a CONCEDE without it.

   This is a bar on *how* you concede, not a reason to resist it. A real
   finding makes the bar cheap to clear. Findings that are correct by reasoning
   rather than reproducible — a race spotted by reading, a limit that only
   breaks at scale, a security hole that is awkward to trigger — still CONCEDE:
   write the mechanism concretely in `repro` ("two requests between the check
   at :44 and the set at :47 both pass"). Downgrading a sound finding to
   DISPUTE because no test captures it is the same failure as caving, pointed
   the other way.
2. **Never change code on a DISPUTE or CLARIFY.** `check` rejects a `fix` on
   either. Changing code "to be safe" while disagreeing is the cave, dressed up.
3. **Disagreement is not rudeness.** A DISPUTE reply states the evidence and
   offers the reviewer a way to be right: "this path is covered at
   `test_x.py:56` — happy to add a case if you had a different input in mind."

Severity the reviewer claims ("Blocks merge") changes nothing about the bar.
Neither does their seniority.

## Respond to a review

```bash
# 1. Pull open comments (skips resolved, already-replied, and bots)
python3 "$DRIVER" fetch 349
```

Writes `.claude/review-context/pr-349.comments.json` (`open` = needs a verdict)
and prints the list. Omit the number to use the current branch's PR.

2. **Investigate each one in the repo.** Read the file at the cited line, run
   the relevant test, grep for the pattern they claim is missing. Check the
   project's own convention file (`CLAUDE.md`, `CONTRIBUTING.md`) — many
   context-free findings are either already-followed rules or genuine
   violations, and only reading it tells you which. This is the step the tool
   cannot do and the step that decides the verdict.

3. Write `.claude/review-context/pr-349.verdicts.json`:

```json
{
  "pr": 349,
  "verdicts": [
    {
      "comment_id": 3947154859,
      "verdict": "CONCEDE",
      "claim": "Hardcoded throttle window violates the project's config rule.",
      "evidence": ["src/alert_throttle.py:47 — literal, not from settings",
                   "CLAUDE.md NEVER list: 'Hard-code configuration values'"],
      "repro": "The convention forbids it outright; no settings entry exists.",
      "refutation_attempted": "Checked whether it is a protocol constant rather than a tunable — it is operator-tunable, so the rule applies.",
      "reply": "Agreed, real violation. Moving it to settings.",
      "fix": "src/alert_throttle.py:47 — read from settings"
    },
    {
      "comment_id": 3947154840,
      "verdict": "DISPUTE",
      "claim": "Says this line's behaviour is untested.",
      "evidence": ["tests/test_alerts.py:56 covers it",
                   "pytest tests/test_alerts.py — 21 passed"],
      "reply": "Covered at tests/test_alerts.py:56. Happy to add a case if you had a different input in mind."
    }
  ]
}
```

```bash
# 4. Gate: fails loudly on a conceded comment with no repro, a disputed
#    comment carrying a fix, or any open comment you quietly skipped
python3 "$DRIVER" check 349

# 5. Render drafts (re-runs check; refuses if it fails)
python3 "$DRIVER" replies 349
```

Drafts land in `.claude/review-context/pr-349.replies.md`, grouped by verdict,
each with a collapsed `working` section. **Nothing is posted.**

6. Apply fixes for CONCEDE verdicts only. Commit them.

7. **Hand the post command to the human — the agent does not run it:**

```bash
python3 "$DRIVER" post 349          # dry run, lists what it would post
python3 "$DRIVER" post 349 --yes    # posts
```

## Give the reviewer context up front

Do this when opening the PR, not at merge — a review already written is harder
to unwind than one that never went wrong.

```bash
python3 "$DRIVER" context 349
```

Dumps PR body, commits, file stat and full diff to
`.claude/review-context/pr-349.material.md`. Read it, then write the brief to
`.claude/review-context/<branch-with-slashes-as-dashes>.md` using
`brief-template.md` next to this file. That branch-named file is the one you
**commit** — it is what the reviewer's Claude reads when they check out the
branch (see the `review-this-pr` skill).

```bash
python3 "$DRIVER" sync 349          # preview
python3 "$DRIVER" sync 349 --yes    # writes the PR body
```

`sync` puts the same brief in the PR body between
`<!-- review-context:start/end -->` markers, so re-running replaces the block
instead of stacking copies. Two delivery paths, one source file: GitHub-UI
reviewers get it in the description, branch-checkout reviewers get the file.

Add `.claude/review-context/.gitignore` to the repo under review so the working
files stay out of git:

```
pr-*.comments.json
pr-*.verdicts.json
pr-*.material.md
pr-*.replies.md
```

## Gotchas

- **Outdated ≠ resolved.** On the PR this was built against, 3 of 11 inline
  comments were `outdated` (the line had moved) but unresolved — they still
  need answers. `fetch` marks them `[OUTDATED]` and keeps them in `open`.
- **Thread resolution is GraphQL-only.** The REST comment payload has no
  resolved field; `fetch` runs a separate `reviewThreads` query for it.
- **`gh api --paginate --slurp` returns a list of pages**, not a flat list, and
  it errors if combined with `--jq`. `paginated()` flattens it.
- **Bot linkbacks** (Linear, Jira, coverage bots) are dropped from `open` by an
  `*[bot]` author filter.
- **`line` is `null` on comments whose diff moved**; `fetch` falls back to
  `original_line`.
- **A review body can carry findings the inline comments don't.** `fetch`
  includes non-empty review bodies. `NO_ACTION` is allowed on those, but only
  after reading them — not as a way to skip a summary that lists real issues.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Not inside a git repository` | `cd` into the repo under review; the driver writes into that repo, not next to itself |
| `No PR found for the current branch` | Pass the number: `... fetch 349` |
| `Run 'fetch 349' first — no pr-349.comments.json` | `check`/`replies` need the fetched set to know what you skipped |
| `no citable evidence — needs a file:line...` | Your evidence is prose. Cite `path.py:44`, a test run, or a named convention rule |
| `NO_ACTION is not available for an inline comment` | Working as intended. Argue it or concede it |
| `refusing to draft replies — evidence bar failed` | Fix the verdicts file; `replies` will not render around it |
