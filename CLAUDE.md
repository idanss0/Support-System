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
