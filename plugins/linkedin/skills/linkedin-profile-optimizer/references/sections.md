# Section playbook

Use this when you draft rewrites. Treat the profile as a landing page: in
10 seconds a recruiter, or a model summarising the profile for one, should
know **what you do, for whom, at what level, and the proof**.

## Contents
1. Hard limits
2. Headline
3. About
4. Experience
5. Skills and Top skills
6. Featured
7. Certifications, projects, honors
8. Education
9. Photo and banner
10. Custom URL, location, Open to Work, public visibility
11. Recommendations and endorsements
12. Market notes: India and remote/global
13. Outdated advice to never give
14. Sound like a person, not a model

## 1. Hard limits

| Field | Limit |
|---|---|
| Headline | 220 chars |
| About | 2,600 chars. About 300 show before "see more" (fewer on mobile) |
| Experience title / company | 100 chars each |
| Experience description | 2,000 chars per role |
| Skills | 100 max, 80 chars each |
| Custom URL | 3–100 chars, letters/digits/hyphens. Can be changed about 5 times in 6 months |
| Banner | 1584 × 396 px, under 8 MB |

Run `score.py --check-limits proposed-profile.json` before you hand over drafts. Text over a limit cannot be pasted into LinkedIn.

## 2. Headline

Recruiter search treats the headline as high-weight text. The headline is
also the first line a model reads.

**Formula:** `<Target title> | <1–2 differentiating skills> | <domain or audience> | <one proof point>`

- Put the target title in **word for word**, in the form the market uses. Recruiter search matches the exact string, so a close synonym does not count.
  - The headline is a self-description, not a title field. If the user already works at the target level under an odd internal title ("SDE-2" with 6 years of experience, "Member of Technical Staff 2"), lead with the standard title.
  - If the target is a real step up, keep it honest and still searchable: "Backend Engineer (SDE-2) | Open to Senior Backend Engineer roles".
  - Either way, the exact target string appears. Never put a step-up title in an Experience title field.
  - **Career switchers** (no paid role in the target field yet): never lead with the target title alone as an identity. Pair it with the real current role:
    - "Mathematics Teacher → UX Designer | …" when the user is openly switching.
    - "Mathematics Teacher & UX Designer | Google UX Certificate | …" when they are discreet and have real UX work to point to.
  - **Discretion is about phrasing, not about the title.** "Senior Backend Engineer | Go, Kafka | Payments at scale" is a self-description, and a discreet headline still leads with the standard target title whenever the user already works at that level. Only phrases that announce a search ("Open to …", "seeking", "looking for") give the user away.
  - The Open to Work job titles are visible to recruiters only, so they always carry the exact target titles. That is where a discreet user is most searchable.
  - **Discretion beats points** only for the announcing phrases. If the user is employed and has not said they are openly looking, an "Open to <title> roles" line in public text can reach their employer. In that case:
    - Draft a discreet default, and let Open to Work (recruiters only) carry the target titles.
    - Offer the "openly looking" variant next to it, with the trade-off: about 3–6 points of A1, against the employer seeing it.
    - Ask which one they want.
- Pick proof that only you can claim: a named employer, a metric, a credential, or an open-source project with stars.
- Write three variants. Recommend one and say why.
  - **A, searchable-first:** title and keywords lead.
  - **B, outcome-first:** "Cut checkout latency 40% at X".
  - **C, niche:** "Payments infra for Indian fintechs".
- Bad: "Passionate software engineer | Learner | Dreamer". Bad: "Software Engineer at Acme" (LinkedIn's default).

## 3. About

Structure (2,000–2,600 chars is the sweet spot for keyword coverage):

1. **Hook (first 300 chars).** Who you are, what you build, for whom, plus one proof point. This block must contain 3–5 target keywords, ideally the same ones the headline leads with, because it is what search snippets, Hiring Assistant summaries and the "see more" preview show. Never open with a greeting ("Hi, I'm Arpit") or a self-applied adjective ("I am a passionate…"). "I'm a backend engineer at Hexalog…" is fine: it puts role and specialty in the first five words.
2. **Credibility.** Domains, company types, problem types and scale.
3. **Proof.** 3–5 bullet wins, each with a number.
4. **Stack / toolkit line.** A plain comma-separated list of tools. AI parsers and Boolean search both pick it up, and it reads fine to humans.
5. **What you are looking for and the CTA.** Role type, work mode (remote/hybrid, time zone), how to reach you. **Only if the user is openly looking.** If they are employed and want discretion, this line is public and undoes "Recruiters only". Use a neutral CTA instead ("Happy to talk payments infra: email …"), and let the Open to Work settings carry the job-search signal. Example: "Open to Staff/Senior backend roles, remote (IST, 4h overlap with EU) — email me at …".

Use short paragraphs. One or two plain labels are fine ("Recent work", "Stack"); a stack of ALL-CAPS headers is a template giveaway. Write in first person, the way the user talks (§14).

## 4. Experience

- Use the **market-standard title**. If the real title differs, write "Senior Software Engineer (internal: SDE-3)" or put the standard title in the first description line. Never claim a title you did not hold.
- First line: a one-sentence scope summary. Include team, product, users and scale, which covers rubric B3.
- Then 3–6 bullets in the shape **verb + what + metric + how**: "Cut p99 API latency 820→190 ms by moving hot reads to Redis and batching writes". Keep each bullet to about 25 words.
- Use the target keywords where they are true. Do not add a keyword the person cannot back up in an interview.
- Attach up to 5 skills to each role. Recruiter filters read role-attached skills.
- For older or minor roles (5+ years ago, or under a year), write 1–2 honest lines from facts you have. Placeholders are for metrics that would materially change a recent role. A pasted description that is mostly `[ADD …]` brackets looks worse than a short true one.
- If a number is missing, write `[ADD METRIC: e.g. % latency drop, users served]`. Never invent one.

## 5. Skills and Top skills

- Aim for 30–50 skills, all relevant. Add a skill only if the resume, GitHub, an experience entry or the user backs it, and it is either a target keyword or an established tool in the user's stack. Generic fillers ("Scalability", "Caching", "Software Design", "Problem Solving") dilute the list. Use LinkedIn's own taxonomy names: pick from the autocomplete wording ("Amazon Web Services (AWS)", not "aws cloud").
- The **Top skills** (up to 5, shown in About) should be the 5 most important target keywords.
- Order the drafts as: Top 5, then the rest grouped by priority. Mark which ones to **remove** (outdated or irrelevant skills dilute the profile).
- Endorsements matter less than whether the skill is listed. Do not chase them.

## 6. Featured

3–6 items in this order: the strongest proof of work (case study, repo, talk, article) first, then evidence of impact, then a contact or "work with me" item. Give each item a benefit-led title. For engineers: pinned GitHub repo, tech blog post, conference talk, demo video.

## 7. Certifications, projects, honors

- **Certifications.** Keep the current ones that are relevant to the target. Fill in issuer, date and credential ID or URL, because verified credentials count as a trust signal. Suggest 1–2 high-signal certifications for the target only if the gap is real (e.g. AWS SA Associate for cloud roles, CKA for platform roles).
- **Projects.** Side projects and open source, each with a link and a one-line outcome. Call out tutorial-grade projects that thousands of profiles share: Titanic, Iris, MNIST, Superstore dashboard, Netflix/Spotify clone, to-do app. Suggest replacing them with one project built on a real problem or real data.
- **Honors and awards.** Hackathons, spot awards, ranks. These are underused and cheap credibility.

## 8. Education

Degree, institution and years. Activities only if they are relevant. Leave out grades unless they are strong and recent.

## 9. Photo and banner

- **Photo.** Face takes up about 60% of the frame, recent, plain background, good light. Profiles with photos get far more views.
- **Banner.** A custom 1584×396 banner works as the hero image. See `banner.md` for the Canva flow.

## 10. Custom URL, location, Open to Work, public visibility

- **Custom URL.** `linkedin.com/in/firstname-lastname`, or add the role if that is taken. Remove the auto-generated suffix.
- **Location.** Use the real city. Recruiters filter on geography. If you want remote roles, keep your city and say "Remote" in Open to Work.
- **Open to Work.** Set it to **Recruiters only** unless you are openly between jobs. Fill in up to 5 job titles (standard names), locations including "Remote", workplace types, start date ("Immediately" or a date) and employment types. Recruiter filters and Hiring Assistant read all of these.
- **Public profile.** Turn on visibility, and turn on every section in public-profile settings. Off-platform AI sourcing tools (Juicebox, SeekOut, hireEZ) see only the public view.
- **Contact info.** Add an email recruiters can use, a website or portfolio, and GitHub.
- **Before editing:** turn off "Share profile updates with your network" (in the edit-intro dialog, or under Settings → Visibility). Without that, every pasted section can announce itself to the user's employer and network.

## 11. Recommendations and endorsements

- Target 3 or more recent recommendations from managers, tech leads or clients. Each should name a specific outcome.
- Draft personal request messages (under 600 chars). Each one names the colleague, the shared project, and the 1–2 strengths you would like them to mention. Offer to write one back. The user sends these; never send them yourself.

## 12. Market notes: India and remote/global

- **India.** Recruiters search with both product-company titles ("SDE 2", "SDE-II") and standard titles ("Software Engineer II", "Senior Software Engineer"). Use the standard title in the headline and add the internal one in the experience entry. Notice period is not a LinkedIn field. The Open to Work start date covers it, and an "Immediate joiner" line in About works if it is true. Never put CTC or salary on the profile.
- **Remote / global.** State the time zone and overlap ("IST, flexible overlap with EU/US"). Use US/EU title conventions ("Senior", "Staff", "Principal"). Name async and remote experience if the person has it (distributed teams, open source). Add "Remote" to the Open to Work locations.
- Writing for both markets: a standard title, a keyword-dense first 300 chars, and a clear work-mode line serve both.

## 13. Outdated advice to never give

- "Turn on Creator mode." LinkedIn removed it in March 2024.
- "Add profile hashtags." Removed along with Creator mode.
- "Headline limit is 120 chars." It has been 220 since 2020.
- "Collect as many endorsements as possible." Low weight. Listed and attached skills matter more.

## 14. Sound like a person, not a model

Recruiters now read hundreds of AI-drafted profiles a week, and they spot the
pattern in seconds. A profile that sounds generated loses trust even when every
fact is true. The same goes for the write-up you hand the user: it should read
like notes from a sharp colleague, not a report generator.

**Tells to remove.** `score.py` prints them as `STYLE:` and `check_drafts.py` fails on them.
- Stock words: delve, seamless, robust, leverage, spearheaded, showcase, elevate, streamline, cutting-edge, passionate about, fast-paced, "happy to talk", "not just X but Y", "at the intersection of".
- More than one em dash in a block. Use a comma, a full stop or brackets.
- Every bullet in the same "Did X: result Y" colon shape, or opening with the same few verbs.
- A stack of ALL-CAPS section headers. Perfectly parallel triplets everywhere.
- A closing line that could end anyone's About ("Happy to connect!", "Let's build something great").

**Do instead.**
- Borrow the user's own words from their answers and resume ("the finance team used to put the data into Tally by hand" beats "eliminated manual data entry").
- Vary the shape. One bullet can be a short sentence, another can lead with the number, a third can say why it mattered.
- Mix sentence lengths. Use contractions where the user would. Keep one plain, slightly specific detail an AI couldn't invent: the tool, the team, the reason.
- End on something concrete: what they want to work on next, or the one link worth clicking.
- Read it aloud as the user. If they wouldn't say it to a recruiter on a call, rewrite it.

