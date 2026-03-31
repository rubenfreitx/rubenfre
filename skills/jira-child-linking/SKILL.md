---
name: jira-child-linking
description: Use this skill when the user asks to link one Jira issue as child of another. Creates issue links with Jira type Parent/Child and maps direction correctly (child issue as inward issue, parent issue as outward issue). Triggers on phrases like "child of", "hija de", "parent/child", or "vincular tareas Jira". For requests that include creating an Epic and multiple User Stories, use the jira-epic-stories skill instead.
---

# Jira Child Linking

## When to use

Use this skill when the user asks to create a Jira relation where one existing issue is child of another existing issue.

Use this skill for linking-only requests, not for bulk creation workflows.

## Delegate rule

If the request includes any of these intents, delegate to `jira-epic-stories`:
- create an Epic,
- create multiple User Stories,
- link those stories as children of the Epic.

Examples of delegation triggers:
- "Crea una epica y 5 historias hijas"
- "Create epic with stories"
- "Genera historias de usuario para esta epica"

## Required mapping

Jira link type name:
- `Parent/Child`

Direction mapping for `child of`:
- `inward_issue_key`: child issue
- `outward_issue_key`: parent issue

Example:
- Request: `MIDDARQ-12650 child of MIDDARQ-12535`
- Call:
  - `link_type`: `Parent/Child`
  - `inward_issue_key`: `MIDDARQ-12650`
  - `outward_issue_key`: `MIDDARQ-12535`

## Execution workflow

1. Parse child and parent issue keys from user request.
2. Create the link using `mcp_jira_jira_create_issue_link` with:
   - `link_type` = `Parent/Child`
   - child key as `inward_issue_key`
   - parent key as `outward_issue_key`
3. If Jira rejects link type text, query available link types and retry using `Parent/Child`.
4. Confirm result to the user with both issue keys and created relation.

## Guardrails

- Do not invert child/parent direction.
- Do not use `Child of` as link type name; use `Parent/Child`.
- Do not use this skill when the user asks to create Epic + Stories in one request; use `jira-epic-stories`.
- Keep confirmation concise and explicit.
