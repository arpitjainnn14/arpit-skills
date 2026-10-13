# claude-skills

Claude Code skills, packaged as a plugin marketplace. One plugin per concern;
add more under `plugins/` over time.

| Plugin | Skills | What it's for |
|---|---|---|
| [`pr-review`](plugins/pr-review) | `pr-review-defense`, `review-this-pr` | Answering PR review comments without caving to ones that are wrong, and handing reviewers real context before they write a generic review. |
| [`technical-docs`](plugins/technical-docs) | `technical-doc` | Handoffs and design docs as published artifacts: C4 diagrams drawn with Mermaid `flowchart` (never the C4 DSL), prose in Simplified Technical English. |
| [`linkedin`](plugins/linkedin) | `linkedin-profile-optimizer` | Auditing a LinkedIn profile against a fixed 100-point rubric, drafting rewrites so recruiter search and AI sourcing tools find it, and tracking the score across runs. Reads the profile, never writes to it. |

## Install

```bash
/plugin marketplace add arpitjainnn14/claude-skills
/plugin install pr-review@claude-skills
/plugin install technical-docs@claude-skills
/plugin install linkedin@claude-skills
```

Or point at a local clone while iterating:

```bash
/plugin marketplace add ~/claude-skills
```

## Layout

```
.claude-plugin/marketplace.json     # lists every plugin in this repo
plugins/
  <plugin>/
    .claude-plugin/plugin.json      # plugin manifest
    skills/
      <skill-name>/
        SKILL.md                    # frontmatter name + description drive auto-load
        <driver>                    # any script the skill shells out to
```

## Adding a skill

1. `mkdir -p plugins/<plugin>/skills/<skill-name>` and write `SKILL.md`. The
   frontmatter `description` is what Claude scans to decide whether to load it
   — put the verbs someone would actually type in it.
2. If the skill needs to *do* something rather than just advise, commit the
   script beside `SKILL.md` and have the skill resolve it via
   `${CLAUDE_PLUGIN_ROOT}`.
3. New plugin? Add a `.claude-plugin/plugin.json` and an entry in
   `.claude-plugin/marketplace.json`.

Every command in a `SKILL.md` here should be one that was actually run.
