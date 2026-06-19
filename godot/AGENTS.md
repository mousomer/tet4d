# godot/AGENTS.md

This directory is the Godot product shell.

Rules:

- UI, menus, scenes, input, animation, diagnostics, camera, rendering, and
  presentation live here.
- Do not implement topology, legal movement, collision, gravity, rotation,
  scoring, trace semantics, or replay correctness in GDScript.
- Use Python traces, adapter APIs, or documented core APIs as semantic inputs.
- Do not compute semantic truth in GDScript. Route semantic decisions through
  Python traces, native adapter APIs, or documented authoritative core APIs.
- UI constants must follow the repo config/theme policy.
- Godot changes require Godot-facing tests or documented manual verification.
- Do not move Python semantic authority into Godot scripts.
- Do not treat visual plausibility as semantic correctness.
