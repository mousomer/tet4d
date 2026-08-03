# godot/AGENTS.md

This directory is the Godot product shell and presentation runtime.

Authority is subsystem-specific.

Rules:

- UI, menus, scenes, input routing, animation, diagnostics, camera, rendering,
  accessibility, guidance, Explorer interaction, and presentation live here.
- Godot may establish authority directly for genuinely new product and
  presentation semantics, including camera orientation, 4D view-basis state,
  slice layout, transition animation, challenge presentation, hints, and
  campaign navigation.
- Do not independently implement inherited topology, legal movement,
  collision, gravity, piece rotation, scoring, trace, or replay semantics in
  GDScript.
- Route inherited semantic decisions through documented authoritative core
  APIs, native adapters, or reference fixtures/traces.
- Route new deterministic game or geometry rules through the named native/data
  authority defined by the owning contract; do not hide them in UI glue.
- UI constants must follow the repo config/theme policy.
- Godot changes require Godot-facing tests or documented manual verification.
- Do not move inherited Python/reference authority into Godot scripts without a
  completed transfer.
- Do not create a Python mirror for a new Godot presentation capability solely
  to manufacture parity.
- Do not treat visual plausibility as deterministic semantic correctness.
