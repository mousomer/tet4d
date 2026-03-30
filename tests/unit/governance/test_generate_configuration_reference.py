from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

import tools.governance.generate_configuration_reference as config_doc


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scratch_root() -> Path:
    root = Path('.tmp_test_generate_configuration_reference') / uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    return root


def test_render_configuration_reference_covers_config_tree(
    monkeypatch,
) -> None:
    scratch_root = _scratch_root()
    config_root = scratch_root / "config"
    docs_root = scratch_root / "docs"
    _write_text(
        config_root / "project" / "constants.json",
        '{"tutorial": {"action_delay_ms": {"movement": 140}}}\n',
    )
    _write_text(
        config_root / "project" / "format_allowlist.txt",
        "docs/*.md\nsrc/**/*.py\n",
    )
    _write_text(
        config_root / "ui" / "theme.json",
        '{"panel": {"bg": [18, 22, 38]}}\n',
    )
    _write_text(
        config_root / "schema" / "menu_settings.schema.json",
        '{"type": "object"}\n',
    )
    monkeypatch.setattr(config_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(config_doc, "CONFIG_ROOT", config_root)
    monkeypatch.setattr(config_doc, "CONFIG_SCHEMA_DIR", config_root / "schema")
    monkeypatch.setattr(
        config_doc,
        "CONFIG_DOC_PATH",
        docs_root / "CONFIGURATION_REFERENCE.md",
    )

    rendered = config_doc.render_configuration_reference()

    assert "config/project/constants.json" in rendered
    assert "tutorial.action_delay_ms.movement" in rendered
    assert "`140` (`int`)" in rendered
    assert "config/project/format_allowlist.txt" in rendered
    assert "docs/*.md" in rendered
    assert "config/ui/theme.json" in rendered
    assert "panel.bg" in rendered
    assert "config/schema/menu_settings.schema.json" not in rendered


def test_render_user_settings_reference_is_bucketed_and_label_resolved(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        config_doc,
        "_user_settings_defaults_payload",
        lambda: {
            "version": 1,
            "active_profile": "tiny",
            "last_mode": "4d",
            "display": {
                "fullscreen": False,
                "overlay_transparency": 0.25,
                "windowed_size": [1200, 760],
            },
            "audio": {
                "master_volume": 0.8,
                "sfx_volume": 0.7,
                "mute": False,
            },
            "analytics": {"score_logging_enabled": False},
            "settings": {
                "2d": {
                    "width": 10,
                    "piece_set_index": 0,
                    "random_mode_index": 0,
                    "topology_advanced": 1,
                    "topology_profile_index": 0,
                    "kick_level_index": 1,
                    "bot_budget_ms": 10,
                },
                "3d": {},
                "4d": {},
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_menu_settings_schema_payload",
        lambda: {
            "type": "object",
            "properties": {
                "active_profile": {"type": "string"},
                "display": {
                    "type": "object",
                    "properties": {
                        "fullscreen": {"type": "boolean"},
                        "overlay_transparency": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 0.9,
                        },
                        "windowed_size": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
                "audio": {
                    "type": "object",
                    "properties": {
                        "master_volume": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "sfx_volume": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "mute": {"type": "boolean"},
                    },
                },
                "analytics": {
                    "type": "object",
                    "properties": {"score_logging_enabled": {"type": "boolean"}},
                },
                "settings": {
                    "type": "object",
                    "properties": {
                        "2d": {
                            "type": "object",
                            "properties": {
                                "width": {"type": "integer", "minimum": 4},
                                "piece_set_index": {"type": "integer", "minimum": 0},
                                "random_mode_index": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "topology_advanced": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "topology_profile_index": {
                                    "type": "integer",
                                    "minimum": 0,
                                },
                                "kick_level_index": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 3,
                                },
                                "bot_budget_ms": {
                                    "type": "integer",
                                    "minimum": 1,
                                },
                            },
                        },
                        "3d": {"type": "object", "properties": {}},
                        "4d": {"type": "object", "properties": {}},
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_keybindings_defaults_payload",
        lambda: {
            "profiles": {
                "small": {
                    "system": {"quit": [27]},
                    "game": {"d2": {"move_x_neg": [1]}},
                    "camera": {"d3": {"yaw_neg": [2]}},
                },
                "tiny": {
                    "system": {"quit": [27], "menu": [8]},
                    "game": {"d2": {"move_x_neg": [1], "move_x_pos": [2]}},
                    "camera": {"d4": {"view_xw_neg": [3]}},
                },
            }
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_option_labels_payload",
        lambda: {
            "game_random_mode": ("Fixed seed", "True random"),
            "game_kick_level": ("Off", "Light", "Standard", "Forgiving"),
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_category_docs_payload",
        lambda: {
            "profiles": {
                "label": "Profiles",
                "description": "Keybinding profile selection, creation, and persistence.",
            },
            "display": {
                "label": "Display",
                "description": "Window and overlay presentation settings.",
            },
            "audio": {
                "label": "Audio",
                "description": "Volume and mute defaults.",
            },
            "analytics": {
                "label": "Analytics",
                "description": "Score logging and related telemetry toggles.",
            },
            "gameplay": {
                "label": "Gameplay",
                "description": "Shared run rules and advanced gameplay tuning.",
            },
            "gameplay_setup": {
                "label": "Gameplay Setup",
                "description": "Board size, piece set, and setup defaults.",
            },
            "bot": {
                "label": "Bot Options",
                "description": "Bot mode, planner, and budget defaults.",
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_keybinding_category_docs_payload",
        lambda: {
            "scope_order": ("general", "2d", "3d", "4d", "all"),
            "groups": {
                "system": {
                    "label": "General / System",
                    "description": "Global actions available in all modes.",
                },
                "game": {
                    "label": "Gameplay",
                    "description": "Piece translation, drop, and rotation actions.",
                },
                "camera": {
                    "label": "Camera / View",
                    "description": "Board orbit, zoom, and projection controls.",
                },
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_topology_mode_labels",
        lambda: ("Bounded", "Wrap all", "Invert all"),
    )
    monkeypatch.setattr(
        config_doc,
        "_piece_set_labels_by_dimension",
        lambda: {
            2: ("Classic", "Random cells", "Debug rectangles"),
            3: ("Native 3D",),
            4: ("Native 4D",),
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_topology_profile_labels_by_dimension",
        lambda: {
            2: ("Default bounded", "Wrap sample"),
            3: ("3D default",),
            4: ("4D default",),
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_bot_mode_labels",
        lambda: ("OFF", "ASSIST", "AUTO"),
    )
    monkeypatch.setattr(
        config_doc,
        "_bot_profile_labels",
        lambda: ("FAST", "BALANCED", "DEEP"),
    )
    monkeypatch.setattr(
        config_doc,
        "_bot_algorithm_labels",
        lambda: ("AUTO", "HEURISTIC", "GREEDY_LAYER"),
    )

    rendered = config_doc.render_user_settings_reference()

    assert "# User Settings Reference" in rendered
    assert "## Global settings" in rendered
    assert "### Profiles" in rendered
    assert "### Display" in rendered
    assert "## 2D settings" in rendered
    assert "### Gameplay Setup" in rendered
    assert "### Gameplay" in rendered
    assert "### Bot Options" in rendered
    assert "#### General / System" in rendered
    assert "#### Camera / View" in rendered
    assert (
        '`settings.2d.piece_set_index`: `0`; integer; min: 0; '
        'default option: Classic'
    ) in rendered
    assert "choices: 0=Classic, 1=Random cells, 2=Debug rectangles" in rendered
    assert "default option: Default bounded" in rendered
    assert "default option: On; choices: 0=Off, 1=On" in rendered
    assert "choices: 0=Off, 1=Light, 2=Standard, 3=Forgiving" in rendered
    assert "### `tiny`" in rendered
    assert "General: 2 actions" in rendered
    assert "2D: 2 actions" in rendered
    assert "4D: 1 actions" in rendered


def test_render_user_settings_reference_fails_on_unbucketed_setting(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        config_doc,
        "_user_settings_defaults_payload",
        lambda: {
            "version": 1,
            "active_profile": "tiny",
            "last_mode": "2d",
            "display": {},
            "audio": {},
            "analytics": {},
            "settings": {
                "2d": {"unexpected_toggle": 1},
                "3d": {},
                "4d": {},
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_menu_settings_schema_payload",
        lambda: {"type": "object"},
    )
    monkeypatch.setattr(
        config_doc,
        "_keybindings_defaults_payload",
        lambda: {"profiles": {}},
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_option_labels_payload",
        lambda: {},
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_category_docs_payload",
        lambda: {
            "profiles": {"label": "Profiles", "description": ""},
            "display": {"label": "Display", "description": ""},
            "audio": {"label": "Audio", "description": ""},
            "analytics": {"label": "Analytics", "description": ""},
            "gameplay": {"label": "Gameplay", "description": ""},
            "gameplay_setup": {"label": "Gameplay Setup", "description": ""},
            "bot": {"label": "Bot Options", "description": ""},
        },
    )
    monkeypatch.setattr(config_doc, "_topology_mode_labels", lambda: ())
    monkeypatch.setattr(
        config_doc,
        "_piece_set_labels_by_dimension",
        lambda: {2: (), 3: (), 4: ()},
    )
    monkeypatch.setattr(
        config_doc,
        "_topology_profile_labels_by_dimension",
        lambda: {2: (), 3: (), 4: ()},
    )
    monkeypatch.setattr(config_doc, "_bot_mode_labels", lambda: ())
    monkeypatch.setattr(config_doc, "_bot_profile_labels", lambda: ())
    monkeypatch.setattr(config_doc, "_bot_algorithm_labels", lambda: ())

    with pytest.raises(
        RuntimeError,
        match="unbucketed 2d mode setting path: unexpected_toggle",
    ):
        config_doc.render_user_settings_reference()


def test_render_user_settings_reference_fails_on_unknown_keybinding_group(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        config_doc,
        "_user_settings_defaults_payload",
        lambda: {
            "version": 1,
            "active_profile": "tiny",
            "last_mode": "2d",
            "display": {},
            "audio": {},
            "analytics": {},
            "settings": {
                "2d": {},
                "3d": {},
                "4d": {},
            },
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_menu_settings_schema_payload",
        lambda: {"type": "object"},
    )
    monkeypatch.setattr(
        config_doc,
        "_keybindings_defaults_payload",
        lambda: {
            "profiles": {
                "tiny": {
                    "mystery": {"custom": [1]},
                }
            }
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_option_labels_payload",
        lambda: {},
    )
    monkeypatch.setattr(
        config_doc,
        "_settings_category_docs_payload",
        lambda: {
            "profiles": {"label": "Profiles", "description": ""},
            "display": {"label": "Display", "description": ""},
            "audio": {"label": "Audio", "description": ""},
            "analytics": {"label": "Analytics", "description": ""},
            "gameplay": {"label": "Gameplay", "description": ""},
            "gameplay_setup": {"label": "Gameplay Setup", "description": ""},
            "bot": {"label": "Bot Options", "description": ""},
        },
    )
    monkeypatch.setattr(
        config_doc,
        "_keybinding_category_docs_payload",
        lambda: {
            "scope_order": ("general", "2d", "3d", "4d", "all"),
            "groups": {
                "system": {"label": "General / System", "description": ""},
                "game": {"label": "Gameplay", "description": ""},
                "camera": {"label": "Camera / View", "description": ""},
            },
        },
    )
    monkeypatch.setattr(config_doc, "_topology_mode_labels", lambda: ())
    monkeypatch.setattr(
        config_doc,
        "_piece_set_labels_by_dimension",
        lambda: {2: (), 3: (), 4: ()},
    )
    monkeypatch.setattr(
        config_doc,
        "_topology_profile_labels_by_dimension",
        lambda: {2: (), 3: (), 4: ()},
    )
    monkeypatch.setattr(config_doc, "_bot_mode_labels", lambda: ())
    monkeypatch.setattr(config_doc, "_bot_profile_labels", lambda: ())
    monkeypatch.setattr(config_doc, "_bot_algorithm_labels", lambda: ())

    with pytest.raises(
        RuntimeError,
        match="unknown keybinding group in profile tiny: mystery",
    ):
        config_doc.render_user_settings_reference()


def test_check_generated_docs_detects_stale_output(
    monkeypatch,
) -> None:
    scratch_root = _scratch_root()
    docs_root = scratch_root / "docs"
    config_path = docs_root / "CONFIGURATION_REFERENCE.md"
    user_path = docs_root / "USER_SETTINGS_REFERENCE.md"
    monkeypatch.setattr(config_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(config_doc, "CONFIG_DOC_PATH", config_path)
    monkeypatch.setattr(config_doc, "USER_SETTINGS_DOC_PATH", user_path)
    monkeypatch.setattr(
        config_doc,
        "render_configuration_reference",
        lambda: "config-doc\n",
    )
    monkeypatch.setattr(
        config_doc,
        "render_user_settings_reference",
        lambda: "user-doc\n",
    )

    _write_text(config_path, "config-doc\n")
    _write_text(user_path, "stale\n")
    assert config_doc.check_generated_docs() == 1

    _write_text(user_path, "user-doc\n")
    assert config_doc.check_generated_docs() == 0
