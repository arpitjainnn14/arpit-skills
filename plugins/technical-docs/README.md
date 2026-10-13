# technical-docs

A handoff fails in two ways: the diagram is unreadable, or the prose is so
smooth that the reader never learns what will actually break. This plugin
fixes both, and it is opinionated about how.

## `technical-doc`

Produces a published HTML artifact — not a markdown file — from a skeleton
that carries the palette, type scale, section furniture, and working Mermaid
boilerplate.

**C4 is the model. `flowchart` is the notation.** Mermaid's `C4Context` /
`C4Container` DSL is explicitly banned: it renders generic blue boxes, dead
whitespace, and arrow labels that sit on top of the shapes. Plain `flowchart`
and `sequenceDiagram` carry the same C4 levels and look finished. The
discipline comes from three semantic classes applied identically on every
figure — green `ours`, grey `ext`, tan `person` — announced once in Figure 1's
caption and never changed.

**Simplified Technical English, applied where it pays.** Active voice, short
sentences, one name per thing. But applied uniformly, STE deletes the
judgment that makes a handoff worth reading, so the skill scopes it to steps,
warnings, and config values, and tells you to keep a precise idiom when it is
the shortest true phrase.

Three structural devices do most of the work:

- A **status note** at the top listing what has *not* run yet, ending "read
  this document as the design, and not as a report of a system in operation."
  A document that quietly implies everything works is the main way these
  mislead.
- **`.note` callouts** labelled for the trap — `THE ONE IRREVERSIBLE ACTION`.
  Every system has an action nobody can undo. Find it, give it a callout, and
  write the exact recovery.
- **State tables** with severity tags and a Recovery column where `None` is
  valid and blank is not.

The skill also documents two measured Mermaid theme traps that silently drop
content: `labelTextColor` must be white or the `alt` tab is dark-on-dark, and
`loopTextColor` must be set explicitly or every `alt`/`else` condition renders
invisible while the diagram still looks complete.

## Install

```
/plugin install technical-docs@claude-skills
```

## Reference

The style this plugin encodes: **Tally Invoice Sync** —
https://claude.ai/code/artifact/f8e0f043-6c45-4812-8e43-2a7f2f2bd9b3
