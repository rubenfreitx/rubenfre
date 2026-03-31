---
name: jira-epic-linking
description: Create multiple JIRA User Stories and link them to an Epic with a reliable two-step workflow. Use when users ask to create stories inside an epic, bulk create user stories, link stories to epic, enlazar historias a epica, or Epic Link automation.
---

# JIRA Epic Linking

Use this skill for bulk creation of JIRA stories inside a target epic.

## Required inputs

- project_key
- parent_epic_key
- stories: list of story titles (or environments to expand into titles)

## Optional inputs

- issue_type (default: User Story)
- priority (default: C(Menor) if not provided)
- description
- assignee
- components

## Critical rule

Do NOT create story-to-epic relation with `jira_create_issue_link` for this workflow.
Use the two-step workflow below.

## Workflow

1. Create every story WITHOUT parent
- Tool: `mcp_jira_jira_create_issue`
- Include summary/title, issue_type, description, priority, and other fields as needed.
- Do not send parent in creation for User Story.

2. Link each created story to epic via parent field
- Tool: `mcp_jira_jira_update_issue`
- Use `additional_fields` with:

```json
{
  "parent": "<PARENT_EPIC_KEY>"
}
```

3. Verify output
- Confirm each created issue key
- Confirm each issue now references the epic parent

## Naming helper

If user gives an environment list, build titles with this pattern:

`[SAP][$ENTORNO] Recreacion LBs con configuracion para BTP`

Example environments:
- BW
- S4
- HCM
- TM
- GRC

## Epic creation note

If creating an Epic itself in this JIRA instance, include Epic Name custom field when required by project configuration (example: `customfield_11762`).
