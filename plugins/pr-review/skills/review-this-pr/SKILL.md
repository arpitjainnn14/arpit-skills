---
name: review-this-pr
description: Use when reviewing a pull request, reviewing a branch, doing code review, or checking someone's changes. Loads the author's committed review brief first so the review is grounded in the project's real constraints instead of generic advice.
---

# Review a PR

You are reviewing someone else's branch. Run from inside the repo.

## 1. Read the brief before the diff

Authors using the companion `pr-review-defense` skill commit a context brief
for the branch under review:

```bash
git rev-parse --abbrev-ref HEAD          # e.g. feat/vendor-startup
ls .claude/review-context/*.md
```

The brief is the branch name with `/` replaced by `-`, e.g.
`.claude/review-context/feat-vendor-startup.md`. The same text is in the PR
description between `<!-- review-context:start -->` markers:

```bash
gh pr view --json body --jq .body
```

**Read it first.** It states the constraints, the alternatives already
rejected, what was verified, and where the author wants scrutiny. A finding the
brief already answers is noise, and it costs the author a round trip.

If there is no brief, say so in the review and ask for one — do not substitute
guesses about intent.

## 2. Read the project's conventions

`CLAUDE.md`, `CONTRIBUTING.md`, `.cursor/rules`, the linter config — whichever
the repo has. These are binding house style, not suggestions. Violations of
them are real findings. Style preferences that *contradict* them are not, no
matter how strongly you hold them.

```bash
ls CLAUDE.md CONTRIBUTING.md 2>/dev/null
```

## 3. Review against an evidence bar

Before writing a finding, clear it:

- **Locate it.** `file:line` in the diff. No finding without a location.
- **Show the failure.** Concrete input or state → wrong output, exception, or
  violated rule. "This could be a problem" is not a finding.
- **Check it isn't already handled.** Read the surrounding function and the
  tests. Most context-free findings die here.
- **Check the brief didn't answer it.** If the author rejected your suggestion
  with a reason, engage with the reason or drop it.

Then label each finding honestly: **Blocking** (defect or convention
violation), **Worth reconsidering** (a real trade-off, author's call), or
**Nit** (say so, and don't block on it). Mislabelling a nit as blocking is the
fastest way to have the whole review discounted.

Run what you can rather than speculating — the repo's own test and lint
commands, as documented in its README or convention file.

## 4. Expect to be argued with

The author answers each comment with a verdict backed by evidence. If they
dispute your finding with a `file:line` or a passing test, **check it**. If
they are right, say so plainly and withdraw the comment — a withdrawn finding
costs nothing; a defended wrong one costs everyone a day.

Symmetrically: do not withdraw a finding just because the author pushed back
confidently. Withdraw it when their evidence shows it is wrong.
