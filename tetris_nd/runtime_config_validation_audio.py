from __future__ import annotations

from typing import Any

from .runtime_config_validation_shared import require_int, require_number, require_object


def validate_audio_sfx_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="audio.version", min_value=1)

    events_obj = require_object(payload.get("events"), path="audio.events")
    if not events_obj:
        raise RuntimeError("audio.events must not be empty")

    events: dict[str, dict[str, float | int]] = {}
    for event_name, raw_spec in events_obj.items():
        if not isinstance(event_name, str) or not event_name.strip():
            raise RuntimeError("audio.events keys must be non-empty strings")
        spec = require_object(raw_spec, path=f"audio.events.{event_name}")
        events[event_name] = {
            "frequency_hz": require_number(
                spec.get("frequency_hz"),
                path=f"audio.events.{event_name}.frequency_hz",
                min_value=1.0,
            ),
            "duration_ms": require_int(
                spec.get("duration_ms"),
                path=f"audio.events.{event_name}.duration_ms",
                min_value=1,
            ),
            "amplitude": require_number(
                spec.get("amplitude"),
                path=f"audio.events.{event_name}.amplitude",
                min_value=0.0,
                max_value=1.0,
            ),
        }
    return {
        "version": payload["version"],
        "events": events,
    }
