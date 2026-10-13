# pr-review

Two halves of the same problem: reviews written without repo context, and
agents that concede to them.

## `pr-review-defense` — the author's side

A reviewer leaves a plausible comment. Your agent reads "senior engineer said
so" as evidence and changes the code. That is the failure this prevents.

Every open comment gets exactly one verdict, and `pr_review.py check` enforces
the bar structurally rather than by asking nicely:

- `CONCEDE` needs a **repro** (failing test, traceback, cited convention rule)
  *and* a recorded **refutation attempt** — what you tried in order to prove
  the reviewer wrong, and why it failed.
- `DISPUTE` / `CLARIFY` may not carry a code change. Changing code while
  disagreeing is the cave in disguise.
- Evidence must be citable — `file:line`, a test invocation, a named rule — not
  prose.
- Skipping a comment is an error, not an omission.
- `NO_ACTION` is unavailable on inline comments; those point at code.

`replies` re-runs the gate and refuses to render around a failure. Nothing is
ever posted without `--yes`, and the skill tells the agent to hand that command
to a human.

## `review-this-pr` — the reviewer's side

Loads the author's committed brief and the project's convention file before the
diff, and holds findings to a matching bar: locate it, show the failure, check
it isn't already handled, check the brief didn't already answer it.

## Context delivery

`pr_review.py context` dumps the diff and commits; you write a brief from
`brief-template.md`; `sync` mirrors it into the PR body between
`<!-- review-context:start/end -->` markers while the committed copy lives at
`.claude/review-context/<branch>.md`. One source, two paths — GitHub-UI
reviewers read the description, branch-checkout reviewers get the file and the
`review-this-pr` skill that points at it.

## Requirements

`gh` (authenticated) and Python 3.10+. Stdlib only, no pip install.
