#!/usr/bin/env python3
"""Driver for the pr-review-defense skill.

Mechanical I/O around a GitHub PR review. All judgement is the agent's;
this script only:

  fetch    pull review comments (+ thread state) into structured JSON
  context  dump the raw material an agent needs to write a review brief
  sync     inject a written brief into the PR body (mutating, --yes)
  check    validate a verdicts file against the evidence bar
  replies  render verdicts into reply drafts (refuses on a failed check)
  post     post the drafted replies (mutating, --yes, human-run only)

The evidence bar in `check` is the point of the whole thing: a CONCEDE
that has no reproduction and no recorded refutation attempt is rejected,
so "the reviewer is senior" cannot become a code change on its own.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

def _repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit("Not inside a git repository \u2014 cd into the repo under review.")
    return Path(proc.stdout.strip())


# Output always lands in the repo under review, never next to this script.
REPO_ROOT = _repo_root()
OUT_DIR = REPO_ROOT / ".claude" / "review-context"

BRIEF_START = "<!-- review-context:start -->"
BRIEF_END = "<!-- review-context:end -->"

# NO_ACTION exists so an approval or a "👍" does not have to be argued with.
# It is deliberately unavailable for inline comments: those point at a line of
# code, so they always get a real verdict.
VERDICTS = ("CONCEDE", "DISPUTE", "CLARIFY", "NO_ACTION")


# --------------------------------------------------------------------------
# gh plumbing
# --------------------------------------------------------------------------


def gh(*args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=False
    )
    if check and proc.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def gh_json(*args: str) -> Any:
    raw = gh(*args)
    return json.loads(raw) if raw.strip() else []


def paginated(endpoint: str) -> list[dict]:
    """gh api --paginate --slurp returns a list of pages; flatten it."""
    pages = gh_json("api", "--paginate", "--slurp", endpoint)
    if pages and isinstance(pages[0], list):
        return [item for page in pages for item in page]
    return pages


def repo_slug() -> tuple[str, str]:
    slug = gh("repo", "view", "--json", "owner,name")
    data = json.loads(slug)
    return data["owner"]["login"], data["name"]


def current_pr() -> int:
    """PR number for the checked-out branch."""
    out = gh("pr", "view", "--json", "number", check=False)
    if not out.strip():
        sys.exit(
            "No PR found for the current branch. Pass one explicitly: "
            "pr_review.py fetch <pr-number>"
        )
    return json.loads(out)["number"]


# --------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------


def thread_state(pr: int) -> dict[int, dict]:
    """Map every inline comment id to its thread's resolved/outdated state."""
    owner, repo = repo_slug()
    query = """
    query($owner:String!,$repo:String!,$pr:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$pr){
          reviewThreads(first:100){
            nodes{
              id isResolved isOutdated
              comments(first:50){nodes{databaseId}}
            }
          }
        }
      }
    }
    """
    data = gh_json(
        "api",
        "graphql",
        "-f",
        f"owner={owner}",
        "-f",
        f"repo={repo}",
        "-F",
        f"pr={pr}",
        "-f",
        f"query={query}",
    )
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    if len(nodes) >= 100:
        print(
            "warning: this PR has 100+ review threads; resolution state beyond "
            "the first 100 is unknown, so some already-resolved comments may "
            "show up as open. Err toward answering them.",
            file=sys.stderr,
        )
    state: dict[int, dict] = {}
    for node in nodes:
        for comment in node["comments"]["nodes"]:
            state[comment["databaseId"]] = {
                "thread_id": node["id"],
                "resolved": node["isResolved"],
                "outdated": node["isOutdated"],
            }
    return state


def cmd_fetch(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    me = json.loads(gh("api", "user"))["login"]

    inline = paginated(f"repos/{{owner}}/{{repo}}/pulls/{pr}/comments?per_page=100")
    reviews = paginated(f"repos/{{owner}}/{{repo}}/pulls/{pr}/reviews?per_page=100")
    issues = paginated(f"repos/{{owner}}/{{repo}}/issues/{pr}/comments?per_page=100")
    threads = thread_state(pr)

    items: list[dict] = []
    for comment in inline:
        cid = comment["id"]
        meta = threads.get(cid, {})
        items.append(
            {
                "id": cid,
                "kind": "inline",
                "author": comment["user"]["login"],
                "is_mine": comment["user"]["login"] == me,
                "path": comment["path"],
                "line": comment.get("line") or comment.get("original_line"),
                "in_reply_to": comment.get("in_reply_to_id"),
                "resolved": meta.get("resolved", False),
                "outdated": meta.get("outdated", False),
                "url": comment["html_url"],
                "diff_hunk": comment["diff_hunk"],
                "body": comment["body"],
            }
        )
    for review in reviews:
        if not (review.get("body") or "").strip():
            continue
        items.append(
            {
                "id": review["id"],
                "kind": "review",
                "author": review["user"]["login"],
                "is_mine": review["user"]["login"] == me,
                "state": review["state"],
                "resolved": False,
                "outdated": False,
                "url": review["html_url"],
                "body": review["body"],
            }
        )
    for comment in issues:
        items.append(
            {
                "id": comment["id"],
                "kind": "issue",
                "author": comment["user"]["login"],
                "is_mine": comment["user"]["login"] == me,
                "resolved": False,
                "outdated": False,
                "url": comment["html_url"],
                "body": comment["body"],
            }
        )

    # Anything you already replied to under a comment counts as handled.
    replied_to = {
        item["in_reply_to"] for item in items if item["is_mine"] and item.get("in_reply_to")
    }
    open_items = [
        item
        for item in items
        if not item["is_mine"]
        and not item["author"].endswith("[bot]")
        and not item["resolved"]
        and item["id"] not in replied_to
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"pr-{pr}.comments.json"
    path.write_text(
        json.dumps({"pr": pr, "all": items, "open": open_items}, indent=2) + "\n"
    )

    print(f"PR #{pr}: {len(items)} comments, {len(open_items)} needing a verdict")
    print(f"written: {path.relative_to(REPO_ROOT)}\n")
    for item in open_items:
        where = (
            f"{item['path']}:{item['line']}"
            if item["kind"] == "inline"
            else item["kind"]
        )
        flag = " [OUTDATED]" if item["outdated"] else ""
        first = item["body"].strip().splitlines()[0][:90]
        print(f"  {item['id']}  {item['author']:<22} {where}{flag}\n      {first}")
    return 0


# --------------------------------------------------------------------------
# context
# --------------------------------------------------------------------------


def cmd_context(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    meta = json.loads(
        gh(
            "pr",
            "view",
            str(pr),
            "--json",
            "number,title,body,headRefName,baseRefName,files,commits,url",
        )
    )
    base = meta["baseRefName"]
    subprocess.run(["git", "fetch", "-q", "origin", base], check=False)
    diff = gh("pr", "diff", str(pr))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"pr-{pr}.material.md"
    lines = [
        f"# Raw material for PR #{pr} — {meta['title']}",
        "",
        f"branch `{meta['headRefName']}` -> `{base}` · {meta['url']}",
        "",
        "## Existing PR body",
        "",
        meta["body"] or "_(empty)_",
        "",
        "## Commits",
        "",
    ]
    for commit in meta["commits"]:
        lines.append(f"- {commit['oid'][:8]} {commit['messageHeadline']}")
    lines += ["", "## Files", ""]
    for file in meta["files"]:
        lines.append(
            f"- {file['path']} (+{file['additions']} -{file['deletions']})"
        )
    lines += ["", "## Diff", "", "```diff", diff, "```", ""]
    path.write_text("\n".join(lines))

    print(f"written: {path.relative_to(REPO_ROOT)}")
    print(f"branch: {meta['headRefName']}")
    print(
        "next: write the brief to "
        f".claude/review-context/{meta['headRefName'].replace('/', '-')}.md, "
        f"then `pr_review.py sync {pr} --yes`"
    )
    return 0


def brief_path_for(branch: str) -> Path:
    return OUT_DIR / f"{branch.replace('/', '-')}.md"


# --------------------------------------------------------------------------
# sync
# --------------------------------------------------------------------------


def cmd_sync(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    meta = json.loads(gh("pr", "view", str(pr), "--json", "body,headRefName"))
    brief = Path(args.brief) if args.brief else brief_path_for(meta["headRefName"])
    if not brief.exists():
        sys.exit(f"No brief at {brief}. Run `context` and write it first.")

    block = f"{BRIEF_START}\n{brief.read_text().strip()}\n{BRIEF_END}"
    body = meta["body"] or ""
    if BRIEF_START in body:
        new_body = re.sub(
            re.escape(BRIEF_START) + r".*?" + re.escape(BRIEF_END),
            block,
            body,
            flags=re.S,
        )
        action = "replaced"
    else:
        new_body = (body.rstrip() + "\n\n" + block).lstrip()
        action = "appended"

    if not args.yes:
        print(f"--- would have {action} the brief in PR #{pr} body ---")
        print(new_body)
        print("\nre-run with --yes to write it")
        return 0

    gh("pr", "edit", str(pr), "--body", new_body)
    print(f"{action} the review-context block in PR #{pr}")
    return 0


# --------------------------------------------------------------------------
# check — the evidence bar
# --------------------------------------------------------------------------


def load_verdicts(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"No verdicts file at {path}")
    return json.loads(path.read_text())


def check_verdicts(pr: int, data: dict) -> list[str]:
    comments_path = OUT_DIR / f"pr-{pr}.comments.json"
    if not comments_path.exists():
        sys.exit(f"Run `fetch {pr}` first — no {comments_path.name}")
    fetched = json.loads(comments_path.read_text())
    open_ids = {item["id"] for item in fetched["open"]}
    by_id = {item["id"]: item for item in fetched["all"]}

    errors: list[str] = []
    seen: set[int] = set()

    for verdict in data.get("verdicts", []):
        cid = verdict.get("comment_id")
        tag = f"comment {cid}"
        if cid not in by_id:
            errors.append(f"{tag}: not a comment on PR #{pr}")
            continue
        seen.add(cid)

        kind = verdict.get("verdict")
        if kind not in VERDICTS:
            errors.append(f"{tag}: verdict must be one of {VERDICTS}, got {kind!r}")
            continue
        if not (verdict.get("claim") or "").strip():
            errors.append(f"{tag}: missing `claim` (restate what the reviewer asserted)")

        if kind == "NO_ACTION":
            if by_id[cid]["kind"] == "inline":
                errors.append(
                    f"{tag}: NO_ACTION is not available for an inline comment — it "
                    "points at a line of code, so argue it or concede it"
                )
            if (verdict.get("fix") or "").strip():
                errors.append(f"{tag}: NO_ACTION carries a `fix`")
            continue

        if not (verdict.get("reply") or "").strip():
            errors.append(f"{tag}: missing `reply` text")

        evidence = [e for e in verdict.get("evidence", []) if e.strip()]
        if not evidence:
            errors.append(f"{tag}: needs at least one `evidence` entry")
        if kind in ("CONCEDE", "DISPUTE") and not any(
            re.search(r"\S+\.\w+:\d+|pytest|ruff|mypy|CLAUDE\.md", e)
            for e in evidence
        ):
            errors.append(
                f"{tag}: no citable evidence — needs a file:line, a test/tool "
                "invocation, or a CLAUDE.md rule, not prose"
            )

        if kind == "CONCEDE":
            if not (verdict.get("repro") or "").strip():
                errors.append(
                    f"{tag}: CONCEDE needs `repro` — how the reviewer is right. A "
                    "failing test or traceback when you can get one; otherwise the "
                    "mechanism spelled out concretely (inputs or interleaving -> "
                    "wrong result), or the rule it breaks. Reasoning counts. "
                    "Deference does not"
                )
            if not (verdict.get("refutation_attempted") or "").strip():
                errors.append(
                    f"{tag}: CONCEDE needs `refutation_attempted` — what you tried "
                    "in order to prove the reviewer wrong, and why it failed"
                )
        else:
            if (verdict.get("fix") or "").strip():
                errors.append(
                    f"{tag}: {kind} carries a `fix` — you do not change code on a "
                    "comment you did not concede"
                )
            if kind == "CLARIFY" and "?" not in (verdict.get("reply") or ""):
                errors.append(f"{tag}: CLARIFY reply asks no question")

    for missing in sorted(open_ids - seen):
        item = by_id[missing]
        where = item.get("path") or item["kind"]
        errors.append(f"comment {missing} ({item['author']}, {where}): no verdict")

    return errors


def cmd_check(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    data = load_verdicts(Path(args.verdicts or OUT_DIR / f"pr-{pr}.verdicts.json"))
    errors = check_verdicts(pr, data)
    if errors:
        print(f"evidence bar FAILED — {len(errors)} problem(s):\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    counts: dict[str, int] = {}
    for verdict in data["verdicts"]:
        counts[verdict["verdict"]] = counts.get(verdict["verdict"], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"evidence bar PASSED — {summary}")
    return 0


# --------------------------------------------------------------------------
# replies
# --------------------------------------------------------------------------


def cmd_replies(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    path = Path(args.verdicts or OUT_DIR / f"pr-{pr}.verdicts.json")
    data = load_verdicts(path)
    errors = check_verdicts(pr, data)
    if errors:
        print("refusing to draft replies — evidence bar failed:\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1

    fetched = json.loads((OUT_DIR / f"pr-{pr}.comments.json").read_text())
    by_id = {item["id"]: item for item in fetched["all"]}

    out = [f"# Reply drafts — PR #{pr}", "", "Nothing below is posted. Review, edit, then:", "", f"`python3 .claude/skills/pr-review-defense/pr_review.py post {pr} --yes`", ""]
    for kind in ("CONCEDE", "DISPUTE", "CLARIFY"):
        group = [v for v in data["verdicts"] if v["verdict"] == kind]
        if not group:
            continue
        out += [f"## {kind} ({len(group)})", ""]
        for verdict in group:
            item = by_id[verdict["comment_id"]]
            where = (
                f"{item['path']}:{item['line']}"
                if item["kind"] == "inline"
                else item["kind"]
            )
            out += [
                f"### {verdict['comment_id']} — {item['author']} · {where}",
                "",
                f"> {verdict['claim']}",
                "",
                verdict["reply"].strip(),
                "",
                "<details><summary>working</summary>",
                "",
                "evidence:",
                *[f"- {e}" for e in verdict["evidence"]],
            ]
            if verdict.get("repro"):
                out += ["", f"repro: {verdict['repro']}"]
            if verdict.get("refutation_attempted"):
                out += ["", f"tried to refute: {verdict['refutation_attempted']}"]
            if verdict.get("fix"):
                out += ["", f"fix: {verdict['fix']}"]
            out += ["", "</details>", "", item["url"], "", "---", ""]

    dest = OUT_DIR / f"pr-{pr}.replies.md"
    dest.write_text("\n".join(out))
    print(f"written: {dest.relative_to(REPO_ROOT)}")
    print("NOT posted. Read it, edit the wording, then run `post`.")
    return 0


# --------------------------------------------------------------------------
# post
# --------------------------------------------------------------------------


def cmd_post(args: argparse.Namespace) -> int:
    pr = args.pr or current_pr()
    data = load_verdicts(Path(args.verdicts or OUT_DIR / f"pr-{pr}.verdicts.json"))
    errors = check_verdicts(pr, data)
    if errors:
        sys.exit("evidence bar failed — run `check` and fix it before posting")

    fetched = json.loads((OUT_DIR / f"pr-{pr}.comments.json").read_text())
    by_id = {item["id"]: item for item in fetched["all"]}

    postable = [v for v in data["verdicts"] if v["verdict"] != "NO_ACTION"]

    if not args.yes:
        print(f"would post {len(postable)} replies to PR #{pr}:")
        for verdict in postable:
            item = by_id[verdict["comment_id"]]
            print(f"  -> {item['url']}")
        print("\nre-run with --yes to post")
        return 0

    for verdict in postable:
        cid = verdict["comment_id"]
        item = by_id[cid]
        body = verdict["reply"].strip()
        if item["kind"] == "inline":
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/pulls/{pr}/comments",
                "-f",
                f"body={body}",
                "-F",
                f"in_reply_to={cid}",
            )
        else:
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/issues/{pr}/comments",
                "-f",
                f"body={body}",
            )
        print(f"posted reply to {cid}")
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(prog="pr_review.py", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add(name: str, func, verdicts: bool = False):
        p = sub.add_parser(name, help=func.__doc__ or name)
        p.add_argument("pr", nargs="?", type=int, help="PR number (default: current branch)")
        if verdicts:
            p.add_argument("--verdicts", help="path to the verdicts JSON")
        p.set_defaults(func=func)
        return p

    add("fetch", cmd_fetch)
    add("context", cmd_context)
    p_sync = add("sync", cmd_sync)
    p_sync.add_argument("--brief", help="path to the brief markdown")
    p_sync.add_argument("--yes", action="store_true", help="actually edit the PR body")
    add("check", cmd_check, verdicts=True)
    add("replies", cmd_replies, verdicts=True)
    p_post = add("post", cmd_post, verdicts=True)
    p_post.add_argument("--yes", action="store_true", help="actually post")

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
