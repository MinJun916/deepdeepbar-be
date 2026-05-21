# Commit Message Convention

These rules define how commit messages MUST be generated in this project.
All commit messages should be clear, concise, and consistent.

---

## Format

<type>: <summary>

---

## Allowed Types

- feat: add a new feature
- fix: fix a bug
- refactor: refactor code without changing behavior
- perf: improve performance
- docs: update documentation
- test: add or update tests
- chore: update configs, build scripts, dependencies, CI
- style: formatting or style changes without logic changes

---

## Rules

- Use lowercase for the type
- Keep the summary under 50 characters
- Do NOT end the summary with a period
- Use imperative, present tense (e.g. "add", "fix", "remove")
- Describe **what** changed, not **why**
- Base the message ONLY on staged git diff
- Do NOT invent changes that are not in the diff
- Focus on one logical change per commit

---

## Language

- Write the summary in English
- Use simple, professional wording
- Avoid vague words like "update", "change", "modify"

---

## Examples

feat: add infinite scroll to estimate list  
fix: prevent duplicate notification creation  
refactor: extract notification creation logic  
perf: reduce query execution time with index  
chore: disable automatic seed on deploy

---

## Notes

- One commit should represent one clear change
- Split unrelated changes into separate commits
- Prefer clarity over brevity
