---
name: text-editor
description: Set up, publish and run a rich-text editor artifact for a project's user-facing texts (a registry of every text, a live preview drawn by the project's own code, bold / italic / underline / colours / icons / line breaks, edits saved to the artifact's db), then apply the user's edits to the project. Use when the user wants to edit or review an app's texts, tooltips or copy themselves, or asks where a text lives.
---

Read and apply the [canonical skill](../../../tools/agent-skills/text-editor/SKILL.md) before performing this workflow. Its templates, kits and workflow files sit beside it in `tools/agent-skills/text-editor/`; resolve every path it gives relative to that folder.

This discovery adapter does not own the skill: Claude (`.claude/skills/`) and Codex (`.agents/skills/`) share the one canonical copy, so edit it there.
