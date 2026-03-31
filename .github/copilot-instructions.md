# Copilot Instructions

When user asks to create multiple JIRA stories and link them to an Epic, use the skill:

- `.github/skills/jira-epic-linking/SKILL.md`

Expected trigger phrases include:
- "crear historias en epica"
- "enlazar historias a epica"
- "bulk create stories in epic"
- "Epic Link automation"

Execution rule:
- Use two steps: create issues first, then update each issue with `additional_fields.parent`.
- Do not use issue-link relation type for this specific epic-link workflow.
