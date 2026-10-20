# Working Rules

## Planning
- Before planning, grill me with questions until the requirements are clear.
- Always plan first, then execute. Do not write code before the plan is approved.
- Use Opus 5.5 for planning and Sonnet 5 for execution.

## Git and GitHub
- The project lives in a GitHub repository: https://github.com/idanss0/Support-System
- Every new feature is developed on its own new branch, never directly on main.

## Testing
After every implementation, run and report the actual results:
- E2E tests on the full user flow
- Regression tests, to confirm existing features still work
- Edge cases (empty, missing, very long or invalid input)

## Security
- After every stage of execution, run a security review: injection, prompt injection, input validation, and secrets or API keys in code.

## Documentation
- Keep the project notes in Obsidian up to date after every change.
- The source of the notes is in the repo: `docs/*.md` (converted automatically) and `obsidian/*.md` (the hub note and the decisions note, edited by hand). When a decision or a document changes, update `obsidian/` in the same change.
- On the Windows machine, a Stop hook in `.claude/settings.local.json` runs `tools/obsidian_sync.py` after every response and copies the notes to `C:\Obsidian_Vault\מערכת מעקב תמיכה טכנית\`. The hook does not run in cloud sessions; there, run the script by hand or rely on the next local session.
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A documentation repo, not an application. It holds Hebrew MVP specs for a "Support Control Tower": Spotfire Cloud dashboards over Salesforce Service Cloud, RingCentral, TFS (Tier 4 / R&D) and an existing shared corporate DW. There is no app code, build or test suite. The only code is the Word export script in `tools/`.

## Layout

- `docs/MVP-Support-Control-Tower.md`: the full spec (v1.0). Chapter 13 holds per-team work packages, chapter 9 the dashboard illustrations, chapter 17 the points for approval.
- `docs/MVP-Short.md`: the narrowed MVP (a live screen for team leads, built by an external Spotfire consultant, maintained by IT).
- `docs/MVP-Mobile.md`: the mobile MVP.
- Each `.md` has a committed `.docx` and `.pdf` twin with the same name. When a `.md` changes, its `.docx` (and the `.pdf`) must be rebuilt and committed with it.
- `docs/dashboards/index.html` and `mobile.html`: standalone mockups with synthetic data (inline CSS/JS, CSS-variable theme with dark mode). `docs/dashboards/img/*.png` are screenshots of them, embedded in the specs. Change a mockup, then retake the matching screenshot.

## Building the Word files

```
cd tools && npm install
node md-to-docx.js ../docs/MVP-Support-Control-Tower.md ../docs/MVP-Support-Control-Tower.docx
node md-to-docx.js ../docs/MVP-Short.md ../docs/MVP-Short.docx --no-breaks
```

`md-to-docx.js` is a hand-rolled converter, not a general Markdown parser. It supports only what the specs use:
- `#`/`##`/`###` (title, H1, H2), tables, `>` callouts, `-` bullets (two-space indent for level 2), `1.` numbered lists, fenced code (kept left-to-right), `**bold**` and `` `code` `` inline, and `---` (dropped).
- Images must be PNG on a line of their own: `![caption|80](dashboards/img/x.png)`. The `|80` suffix is the width in percent; the caption gets "(נתונים מומצאים)" appended.
- `<div dir="rtl">` wrapper lines are stripped; every doc starts and ends with one so GitHub renders it right-to-left.
- Page breaks are hardcoded before H2 headings numbered 5, 8, 9, 13 and 16, which is tuned for the full spec. Pass `--no-breaks` to turn them off for a document where they don't fit.
- After packing, it patches `styles.xml` and `document.xml` with JSZip to make the whole document RTL. Keep that step when editing the script.

The repo has no PDF build script; PDFs were exported from the `.docx`.

## Writing conventions

- Spec text is Hebrew, in short plain sentences. Product and object names stay in English (Salesforce `Case`, `Request`, `CaseMilestone`, `CaseHistory`, Spotfire, DW, P1, SLA, QARA).
- Commit messages are English: a short subject, then a body that states what changed in the scope or plan.
