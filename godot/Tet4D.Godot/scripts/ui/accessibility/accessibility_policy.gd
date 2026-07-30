extends RefCounted

class_name AccessibilityPolicy

const STANDARD_TRANSITION_DURATION_SCALE := 1.0
const REDUCED_TRANSITION_DURATION_SCALE := 0.0
const STANDARD_CAMERA_INTERPOLATION_SCALE := 1.0
const REDUCED_CAMERA_INTERPOLATION_SCALE := 0.0

var _high_contrast := false
var _reduced_motion := false
var _show_help_hints := true


func configure(high_contrast: bool, reduced_motion: bool, show_help_hints: bool) -> bool:
	var changed := (
		_high_contrast != high_contrast
		or _reduced_motion != reduced_motion
		or _show_help_hints != show_help_hints
	)
	_high_contrast = high_contrast
	_reduced_motion = reduced_motion
	_show_help_hints = show_help_hints
	return changed


func is_high_contrast_enabled() -> bool:
	return _high_contrast


func is_reduced_motion_enabled() -> bool:
	return _reduced_motion


func should_show_help_hints() -> bool:
	return _show_help_hints


func transition_duration_scale() -> float:
	return REDUCED_TRANSITION_DURATION_SCALE if _reduced_motion else STANDARD_TRANSITION_DURATION_SCALE


func camera_interpolation_scale() -> float:
	return REDUCED_CAMERA_INTERPOLATION_SCALE if _reduced_motion else STANDARD_CAMERA_INTERPOLATION_SCALE


func decorative_animation_enabled() -> bool:
	return not _reduced_motion


func pulse_enabled() -> bool:
	return not _reduced_motion


func flash_enabled() -> bool:
	return not _reduced_motion


func deterministic_snapshot() -> Dictionary:
	return {
		"high_contrast": _high_contrast,
		"reduced_motion": _reduced_motion,
		"show_help_hints": _show_help_hints,
		"transition_duration_scale": transition_duration_scale(),
		"camera_interpolation_scale": camera_interpolation_scale(),
		"decorative_animation_enabled": decorative_animation_enabled(),
		"pulse_enabled": pulse_enabled(),
		"flash_enabled": flash_enabled(),
		"focus_visibility_required": true,
		"non_colour_cues_required": true,
	}
