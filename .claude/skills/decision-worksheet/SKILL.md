---
name: decision-worksheet
description: Build and publish an interactive decisions worksheet (a claude.ai artifact where the user taps an option per question, adds comments, and the answers save to the artifact's database for Claude to read back). Use whenever a reply would ask the user more than 5 decisions or questions; 5 or fewer stay a numbered text message.
---

Read and apply the [canonical skill](../../../tools/agent-skills/decision-worksheet/SKILL.md) before performing this workflow. Its templates, kits and workflow files sit beside it in `tools/agent-skills/decision-worksheet/`; resolve every path it gives relative to that folder.

This discovery adapter does not own the skill: Claude (`.claude/skills/`) and Codex (`.agents/skills/`) share the one canonical copy, so edit it there.
