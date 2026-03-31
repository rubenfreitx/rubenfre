---
name: jira-epic-stories
description: Use this skill when the user asks to create a Jira Epic and multiple User Stories as children (e.g. "crea una epica y 5 historias", "create epic with stories", "hijas de la epica"). Ensures correct Epic fields and linking workflow in Jira projects.
---

# Jira Epic + User Stories Creation

## When to use

Use this skill when a user asks to:
- create a new Epic,
- create several User Stories,
- and leave those stories linked as children of that Epic.

Typical triggers:
- "Crea una epica y 5 historias hijas"
- "Create an epic and child user stories"
- "Genera historias de usuario para esta epica"

## Required creation rules

### 1) Create the Epic first

Tool:
- `mcp_jira_jira_create_issue`

Parameters:
- `project_key`: target project (ask user if missing)
- `summary`: Epic title requested by user
- `issue_type`: `Épica`
- `additional_fields.customfield_11762`: must contain the same Epic name as `summary`

Example:
```json
{
  "project_key": "MIDDARQ",
  "summary": "RUBENFREPRUEBA",
  "issue_type": "Épica",
  "additional_fields": {
    "customfield_11762": "RUBENFREPRUEBA"
  }
}
```

### 2) Create User Stories

Tool:
- `mcp_jira_jira_create_issue`

Parameters per story:
- `project_key`: same as Epic
- `summary`: story title
- `issue_type`: `Historia`

## Linking rules (critical)

For Story -> Epic relation in this workflow, use Epic Link:
- Update each story with `fields.customfield_11760 = <EPIC_KEY>`

Tool:
- `mcp_jira_jira_update_issue`

Example:
```json
{
  "issue_key": "MIDDARQ-12657",
  "fields": {
    "customfield_11760": "MIDDARQ-12656"
  }
}
```

Note:
- Do not rely on `fields.parent` for Story -> Epic in classic Jira Epic workflows.
- If `parent` update succeeds but relation is not visible, set `customfield_11760` explicitly.

## Verification checklist

After linking, verify each story has the Epic key:
- `mcp_jira_jira_get_issue` with fields: `summary,customfield_11760`
- Expected: `customfield_11760.value == <EPIC_KEY>`

## Execution workflow

1. Parse requested project key, Epic name, and number of stories.
2. Create Epic using `Épica` + `customfield_11762`.
3. Create all stories as `Historia`.
4. Link every story to Epic using `customfield_11760`.
5. Verify links on all stories.
6. Return concise result: Epic key + list of story keys.

## Guardrails

- Never use `Epic` if Jira mapping requires `Épica`.
- Keep Epic name and `customfield_11762` aligned.
- If project key is not given, ask before creating issues.
- Confirm final output with actual created issue keys, not placeholders.
