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
- The hook that updates Obsidian automatically is not set up yet. Until it is, update the notes as part of each change.
