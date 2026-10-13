# Capturing the profile with Claude in Chrome

This step is read-only. You read pages. You never type into LinkedIn, and you
never click Save, Post, Send, Connect, Follow, Endorse, Apply, or any
edit-pencil "Done" button. If you open a dialog to read it, close it with
Escape or Cancel. The user approved an audit, not changes. A stray click
can also notify their whole network ("X updated their profile").

## Setup

1. Invoke the `claude-in-chrome` skill. Load the tools in one ToolSearch call: `tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `get_page_text`, `read_page`, `find`, `computer`, `tabs_close_mcp`.
2. Call `tabs_context_mcp`, then open one new tab and use it for the whole capture.
3. Navigate to `https://www.linkedin.com/in/me/`. If the page lands on `/login`, `/checkpoint`, `/authwall` or a sign-in form, stop. Ask the user to log in to LinkedIn in Chrome, and continue when they confirm. Never type credentials.
4. Note the resolved profile URL (`/in/<slug>/`). That slug is `custom_url`.

## Pages to read

Use `get_page_text` for text, because it is cheap and does not depend on
LinkedIn's DOM. Use a screenshot (`computer` → screenshot) only for the
photo, the banner and the Open-to-Work frame. Allow a second or two between
navigations. LinkedIn rate-limits fast automated browsing, and this capture
needs about 12 page loads, not 50.

| What | URL |
|---|---|
| Top card, About, Featured preview, Top skills, activity | `/in/<slug>/` (scroll to the bottom once so lazy sections load) |
| Experience (full descriptions) | `/in/<slug>/details/experience/` |
| Education | `/in/<slug>/details/education/` |
| Skills (all) | `/in/<slug>/details/skills/` |
| Certifications | `/in/<slug>/details/certifications/` |
| Projects | `/in/<slug>/details/projects/` |
| Honors | `/in/<slug>/details/honors/` |
| Featured (all) | `/in/<slug>/details/featured/` |
| Recommendations received | `/in/<slug>/details/recommendations/` (the "Received" tab) |
| Public visibility | `https://www.linkedin.com/public-profile/settings` |
| Analytics | `https://www.linkedin.com/dashboard/` (profile views, search appearances, post impressions) |

A `/details/...` page that 404s, or redirects back to the profile, means the section is empty. Record `[]`.

Experience descriptions on the main page are cut off at "…see more". The `/details/experience/` page usually shows them in full. If a description still ends in "…see more", click that link to expand it (that click is read-only) and re-read.

**Open to Work.** If the top card shows an "Open to work" box, read the titles and locations shown. The preferences dialog (the pencil icon on that box) shows visibility (recruiters only or all members), workplace types and start date. You may open it to read, then close it with Escape. Never press Save.

**Photo and banner.** Take one screenshot of the top card. Note whether a real photo is present and whether the banner is LinkedIn's default (plain blue-grey gradient or abstract pattern) or custom. Describe what the custom banner says. The drafts will critique it.

**Verification.** A shield or check badge next to the name means `verified: true`.

## profile.json schema

Write the capture to `<run>/profile.json`. Use `null` for anything you could not see, and never guess. Keep the text exactly as written: the scorer counts characters and keywords.

```json
{
  "captured_at": "2026-10-12T10:30:00",
  "source": "chrome",
  "name": "…",
  "headline": "…",
  "location": "Bengaluru, Karnataka, India",
  "custom_url": "https://www.linkedin.com/in/slug/",
  "photo": true,
  "banner": "default | custom",
  "banner_description": "what the banner says/shows, or null",
  "verified": false,
  "about": "full About text",
  "top_skills": ["…"],
  "open_to_work": {"enabled": true, "visibility": "recruiters | public", "titles": ["…"], "locations": ["…"], "workplace": ["remote"], "start": "immediately"},
  "public_profile": {"visible": true},
  "contact": {"email": true, "website": "…", "github": "…"},
  "featured": [{"title": "…", "type": "link | post | media"}],
  "experience": [
    {"title": "…", "company": "…", "start": "2023-04", "end": null, "current": true,
     "location": "…", "description": "full text with line breaks", "skills": ["…"]}
  ],
  "education": [{"school": "…", "degree": "…", "start": "…", "end": "…"}],
  "certifications": [{"name": "…", "issuer": "…", "date": "…", "credential_url": null}],
  "skills": [{"name": "…", "endorsements": 3}],
  "projects": [{"name": "…", "description": "…"}],
  "honors": [{"title": "…", "issuer": "…"}],
  "publications": [],
  "recommendations_received": 2,
  "recommendations": [{"from": "…", "relationship": "managed me", "date": "2024-05"}],
  "connections": 500,
  "followers": 812,
  "analytics": {"profile_views_90d": 140, "search_appearances_7d": 33, "post_impressions_7d": 410, "last_post_days_ago": 60}
}
```

List experience in the order LinkedIn shows it (most recent first). The scorer treats the first three entries as "recent".

If Chrome is not available or the user prefers not to use it, accept a pasted profile or the PDF from "More → Save to PDF" on the profile, and set `"source": "paste"` or `"pdf"`. The PDF has no analytics, banner, photo or Open to Work data, so record those as `null`.
