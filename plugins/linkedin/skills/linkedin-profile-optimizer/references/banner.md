# Banner: brief, Claude Design, Canva

The banner is the hero image. It should say in about 3 seconds what the
headline says, plus one thing the headline cannot show: logos, a stack, or a
visual identity.

Always write the brief first. Then build it, using the first route that is
available:

1. **Claude Design.** Artifact tool, Design type. No extra sign-in. The user
   can export a PNG, or send the design to Canva from the canvas.
2. **Canva connector.** Use it when the user asks for Canva, or when the
   Artifact tool is not available.
3. **Brief only.** If neither route works, the brief is complete enough to
   build by hand in about 10 minutes.

Whichever route you use, the user uploads the banner themselves through
"Edit profile → camera icon on the banner". This run is audit-only.

## 1. Brief (always write it to `<run>/banner-brief.md`)

- **Size:** 1584 × 396 px.
- **Safe zone:**
  - On desktop, the profile photo covers the bottom-left: about the left 420 px and the bottom 200 px.
  - Mobile crops the sides.
  - Keep all text in the **centre-right**, roughly x 500–1450 and y 60–340.
- **Content (pick at most 3):**
  1. A value line of 6–10 words. Rephrase the headline, don't copy it.
  2. 3–6 stack or skill marks, written as text. Use logos only if the user has the right to use them.
  3. A proof line ("Payments at 70k orders/day", "AWS Certified"). It must be backed by the profile, because C5 applies to the banner too.
  4. A contact or CTA: personal site URL or GitHub handle.
- **Style:**
  - One accent colour plus a dark or light neutral.
  - Text needs at least 4.5:1 contrast with the background.
  - No stock photos, no quotes, no "Data is the new oil" clichés.
  - About 20 words in total, at most.
- Give **two directions**, for example "Clean typographic" and "Stack strip". Give the exact text for each.

## 2. Claude Design (preferred)

1. Call `Artifact` with `action: "quickstart"` and `intent: "design"`. Then create the canvas from the `type_url` it returns, with `title: "LinkedIn banner — <name>"`. The create result carries the Design type's own instructions. **Follow those for file shapes and the publish calls.** They change between releases, so do not rely on details remembered from an earlier run.
2. Make one artboard per direction, each **fixed at 1584 × 396**: `Main.dc.html` for direction A and `Banner-B.dc.html` for direction B.
   - Put them in a column, with 120 px between rows.
   - Expose the accent colour and the value line as `data-props` tweaks, so the user can adjust them without you.
   - Do not draw the profile-photo circle inside the artboard, or it ends up in the exported PNG. Keep the safe zone empty instead. Mark it with the canvas `guides` if the type's `format.md` supports them, or with a sticky note beside the artboard.
3. The only text allowed is facts from the profile. If a fact is missing, use a visible placeholder such as `[YOUR SITE]`. Never invent a metric or a logo.
4. Tell the user how to get the file out:
   - **Share › Export** gives a PNG.
   - **Share › Export › Send to** sends the design to Canva.
   - Then upload the PNG to LinkedIn.

   Put the canvas link in `drafts.md`, under Banner.
5. When you score the proposed profile, judge E2 from the artboards you built.

## 3. Canva connector

1. Check whether Canva's design tools are loaded. If only `mcp__claude_ai_Canva__authenticate` exists, call it. It returns a sign-in URL: give that to the user, and call `mcp__claude_ai_Canva__complete_authentication` once they confirm.
2. The real Canva tools then appear in the deferred tool list. Load them with ToolSearch (query "canva design") and read their schemas. Tool names change, so do not assume them.
3. Create a design at 1584 × 396. Use a custom size, or the "LinkedIn background/banner" preset if the tool offers one. Pass the brief's exact text, colours and layout.
4. Return the Canva edit link. Put it in `drafts.md`, under Banner.

If a Claude Design canvas already exists and the user wants it in Canva, point them to **Share › Export › Send to** on the canvas. Do not rebuild it in Canva.
