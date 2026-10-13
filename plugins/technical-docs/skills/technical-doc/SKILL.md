---
name: technical-doc
description: Write or rewrite a technical handoff, design doc, runbook, architecture note, or vendor document. Produces a published HTML artifact with C4 layout diagrams in Mermaid and ASD-STE100 Simplified Technical English. Use for "write a handoff", "document this system", "add a C4 diagram", "draw the architecture", "simplify this doc", "write up the design".
---

# Technical documents

Start from the skeleton. Copy it, replace the content, publish it with the
`Artifact` tool. It carries the palette, the type scale, the section
furniture, and working Mermaid boilerplate for all three diagram kinds.

```bash
SKELETON="${CLAUDE_PLUGIN_ROOT:-.claude}/skills/technical-doc/skeleton.html"
cp "$SKELETON" "/tmp/My Document Name.html"
```

Name the file what the page should be called, and change the `<title>` to
match — both feed the artifact's name.

The reference implementation of everything below is **Tally Invoice Sync**:
https://claude.ai/code/artifact/f8e0f043-6c45-4812-8e43-2a7f2f2bd9b3

## Diagrams: C4 is the model, `flowchart` is the notation

**Do not use Mermaid's `C4Context` / `C4Container` DSL.** It renders generic
blue boxes with huge dead whitespace, arrow labels that overlap the shapes,
and no usable layout control. It looks unfinished.

Use plain `flowchart` and `sequenceDiagram`, and get the C4 discipline from
how you name and colour things:

| C4 level | Notation | Shows |
|---|---|---|
| 1 — context | `flowchart LR` | the system, who uses it, what it touches |
| 2 — container | `flowchart TB` with `subgraph` boundaries | the runnable parts |
| dynamic | `sequenceDiagram` with `autonumber` | one scenario, in order |

Three semantic classes, applied on every diagram. This is the convention that
makes the set readable as a set:

```
classDef ours   fill:#1a5c50,stroke:#12433a,color:#ffffff;
classDef ext    fill:#e8ece9,stroke:#8c9a94,color:#16241f;
classDef person fill:#f4e7d4,stroke:#9a5b12,color:#16241f;
class SYS ours;
class ST,TP,SL ext;
class FN person;
```

Green is ours. Grey is external. Tan is a person. Say so in the caption of
the first figure — `Figure 1 — C4 level 1. Green is ours.` — and never
recolour later.

Other rules that hold across the set:

- **Two lines per node:** `API["OMS<br/><small>holds all state</small>"]`.
  Name on top, the one fact that matters underneath.
- **Every arrow carries a noun:** `-- "sales voucher" -->`, not a bare arrow.
  What moves, not what the caller does.
- **Boundaries are `subgraph`**, named for the real thing: `AWS`,
  `Windows VM`.
- **Copy the `%%{init:...}%%` block from the skeleton** onto every diagram.
  Without it the diagram uses Mermaid's default blue and fights the page.
- Keep a diagram to about 8 nodes. Past that, split it.

Two `sequenceDiagram` theme traps, both measured — the skeleton already has
them right, so copy its init block rather than writing one:

- **`labelTextColor` must be white.** The `alt` / `loop` tab takes its fill
  from `actorBkg` (dark green) and ignores `labelBoxBkg`, so dark label text
  is invisible.
- **`loopTextColor` must be set explicitly.** Leave it out and Mermaid emits
  no fill rule for `.loopText`, so every `alt` / `else` condition —
  `[it refuses]`, `[it accepts]` — renders invisible. The diagram looks
  complete and has silently lost its branch labels.

Every figure goes in `<figure>` with a `<figcaption>` numbered
`<b>Figure N</b>`, and the caption states the level and the point the picture
proves — not what it contains.

## Prose: STE, applied where it pays

Active voice, short sentences, one instruction per step, one name per thing,
no filler. Applied uniformly it also strips out the judgment that makes a
document worth reading, so apply it hardest to steps, warnings, config
values, and anything the reader will type.

Where a phrase is the most precise available, keep it. The reference uses
"fails quietly" twice, once as a callout heading, because that is exactly
what the setting does and no plainer phrase is shorter.

What the reference actually sounds like:

> Tally accepts data only from its own machine. The VM can start a connection
> to the internet, but nothing on the internet can start a connection to the
> VM. OMS therefore cannot call the VM. A connector runs on the VM instead,
> and the connector starts every connection.

Four sentences, each under 20 words, each carrying one fact, ending in the
design decision the constraint forces. Note `therefore` — the prose argues,
it does not just list.

- **Give the reason, not only the rule.** "The schedule is outside the API
  for one reason. OMS scales automatically…" A reader who knows why will not
  undo it later.
- **One name per thing.** If it is the `connector`, it is never the
  `service`, the `agent`, or the `job`.
- **Prefer the negative fact when it is the load-bearing one.** "OMS never
  calls the VM." "The connector keeps no record after a restart."
- Body copy caps at 60ch — the skeleton already does this. Do not widen it.

## Structure

Header with a one-sentence standfirst · status note · numbered sections ·
states table · alerting · footer.

Three devices carry most of the weight:

**The status note, first thing on the page.** Say what has not run yet, as a
list, then: *"Read this document as the design, and not as a report of a
system in operation."* A handoff that quietly implies everything works is the
main way these documents mislead.

**`.note` callouts for the things that bite.** Give each a label:
`THE ONE IRREVERSIBLE ACTION`, `AN EMPTY RECIPIENT LIST FAILS QUIETLY`. Every
system has an action nobody can undo. Find it, and give it its own callout
with the exact recovery steps.

**State tables with severity tags** — `t-ok`, `t-warn`, `t-crit` — and a
`Recovery` column on every row. `None` is a valid recovery. An empty cell is
not.

Numbered sections (`<span class="no">1</span>`) only because these documents
get referenced in Slack as "section 5.1". If nobody will cite it, drop the
numbers rather than decorate with them.

## Do not darken `--plate`

The diagrams hardcode light fills and dark text, so the figure plate stays
**light in dark mode** — `--plate: #e7ebe8` while `--surface` goes to
`#161e1b`. That looks like a mistake in the dark palette and is not one.
Darken it and every diagram becomes dark-on-dark.

## Check the diagrams before publishing

Mermaid is unforgiving of small syntax slips, and the diagrams live inside
the page, so there is no `.mmd` file to point a renderer at. This script
pulls every block out and renders it:

```bash
CHECK="${CLAUDE_PLUGIN_ROOT:-.claude}/skills/technical-doc/check_diagrams.py"
python3 "$CHECK" "/tmp/My Document Name.html" --png /tmp/figs
```

```
  figure 1  flowchart        ok  -> /tmp/figs/My-Document-Name-1.png
  figure 2  flowchart        ok  -> /tmp/figs/My-Document-Name-2.png
  figure 3  sequenceDiagram  ok  -> /tmp/figs/My-Document-Name-3.png

3/3 rendered
```

It reads both `<pre class="mermaid">` and ```` ```mermaid ```` fences, and
unescapes HTML entities first, so `--&gt;` in the page source still parses.
Exit 1 means at least one diagram failed, and it prints the parse error with
its line number.

**Exit 0 only means Mermaid drew something.** Open the PNGs. A diagram can
render perfectly and still have dropped its `alt` / `else` labels — that is
what the two theme traps above do.

Then publish with the `Artifact` tool. It renders `<pre class="mermaid">`
natively, so nothing needs exporting and the PNGs are for your eyes only.
