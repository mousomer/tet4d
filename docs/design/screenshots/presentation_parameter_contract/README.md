# Presentation Parameter Contract Screenshots

Agent-driven real-window evidence captured from
`res://scenes/trace_replay.tscn` through production native Live-4D setup and
the bounded `TraceReplayApp.apply_presentation_profile()` entry point.

Environment: Godot 4.7.1 stable official, macOS 26.6.2 on Apple silicon,
`macOS` DisplayServer, Metal Forward+, Apple M1 Pro. The capture used the
current local shell preference store, then explicitly applied the canonical
profile before the default frame. Images are 4112 x 2467 because the current
shell window preference resolved to the active fullscreen display.

| Frame | Evidence |
| --- | --- |
| `default_live_4d.png` | Canonical registry defaults preserve the accepted Instrument Live-4D presentation. |
| `variant_live_4d.png` | The same frozen native game uses Vector Arcade, grid `0.75`, boundary `0.50`, active opacity `0.60`, Ghost multiplier `0.35`, slice spacing `1.45`, and background intensity `0.45` without a restart or camera/basis reset. |
| `settings_large_high_contrast.png` | Generated controls for the expanded presentation envelope remain usable with large UI scale and High Contrast in the scroll-safe Settings surface. |

These are review artifacts, not pixel-diff golden tests and not independent
human sign-off. Automated structural coverage supplies the 2D, 3D, custom-4D,
and W=1 cases; the captured visible comparison intentionally holds one
standard Live-4D game fixed so profile A/B differences are reviewable.
