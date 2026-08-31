extends RefCounted

class_name PhysicalKeyFallback

# Layout-independent resolution for the canonical live action contract.
#
# `LiveInputContract.ACTION_SPECS` is the single binding authority and is
# registered into the runtime InputMap by logical keycode. On a US-layout
# desktop keyboard the logical keycode and the physical keycode agree, so that
# registration resolves every action. External keyboards attached to Android
# tablets and iPads, and non-US desktop layouts, can report a logical keycode
# that differs from the physical key position the binding was designed around.
#
# Rather than giving handheld platforms their own action IDs, this helper adds
# one narrow fallback: when a key event's *typed* keycode is bound to nothing
# at all, the event is retried using its physical keycode. Because the fallback
# only ever runs for characters the contract does not claim, it cannot make a
# single key press dispatch two actions, and it is inert whenever logical and
# physical keycodes agree. Windows behaviour is therefore unchanged.

# Keycodes registered outside `LiveInputContract`, by
# `TraceReplayApp._ensure_input_map()`. Listed here so "is this character
# claimed?" has one answer rather than two.
const SHELL_KEYCODES := [
	KEY_LEFT,
	KEY_RIGHT,
	KEY_UP,
	KEY_DOWN,
	KEY_SPACE,
	KEY_R,
	KEY_1,
	KEY_2,
	KEY_3,
	KEY_F,
	KEY_H,
	KEY_Q,
	KEY_ESCAPE,
	KEY_TAB,
]


# Every keycode the shell claims by printed character. A physical fallback is
# only attempted for events whose typed keycode is absent from this set.
static func bound_keycodes(action_specs: Dictionary) -> Dictionary:
	var bound: Dictionary = {}
	for keycode in SHELL_KEYCODES:
		bound[int(keycode)] = true
	for action_name in action_specs:
		var spec: Dictionary = action_specs.get(action_name, {})
		for keycode in spec.get("keys", []):
			bound[int(keycode)] = true
	return bound


# Returns a synthetic logical event standing in for the physical key position,
# or null when the fallback does not apply.
static func synthesize(event: InputEvent, bound: Dictionary) -> InputEventKey:
	if not (event is InputEventKey):
		return null
	var key_event := event as InputEventKey
	var physical := int(key_event.physical_keycode)
	if physical == 0 or physical == int(key_event.keycode):
		return null
	# The typed character already means something; the contract's printed-key
	# reading wins and no positional reinterpretation happens.
	if bound.has(int(key_event.keycode)):
		return null
	if not bound.has(physical):
		return null
	var synthetic := InputEventKey.new()
	synthetic.keycode = physical
	synthetic.physical_keycode = physical
	synthetic.pressed = key_event.pressed
	synthetic.echo = key_event.echo
	synthetic.alt_pressed = key_event.alt_pressed
	synthetic.shift_pressed = key_event.shift_pressed
	synthetic.ctrl_pressed = key_event.ctrl_pressed
	synthetic.meta_pressed = key_event.meta_pressed
	return synthetic
