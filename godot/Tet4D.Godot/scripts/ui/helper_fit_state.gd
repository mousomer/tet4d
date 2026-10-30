extends RefCounted

# One fit group's measurements and transitions. No scene nodes or scheduler.
# The view supplies natural height, constraints, intrinsic content identity and
# frame identity; it applies the returned compact/scale/remeasure decision.
const SCALE_FLOOR := 0.6
const SCALE_STEP := 0.02
const SETTLE_FRAMES := 30

var _compact := false
var _relaxed := 0.0
var _scale := 1.0
var _pending := [-1.0, -1]
var _compact_pending := [-1.0, -1]
var _width := 0.0
var _room := 0.0
var _searching := false
var _lo := SCALE_FLOOR
var _hi := 1.0
var _unsettled_since := -1
var _content_key: Array = []
var _remeasure := false
# The last sample and the inputs it was taken under.
var _sample := [-1.0, -1.0, -1.0]


func is_compact() -> bool:
	return _compact


func relaxed_height() -> float:
	return _relaxed


func settled() -> bool:
	return not _searching and float(_pending[0]) < 0.0 and float(_compact_pending[0]) < 0.0 and _unsettled_since < 0


func snapshot() -> Dictionary:
	return {"compact": _compact, "relaxed": _relaxed, "scale": _scale,
		"searching": _searching, "settled": settled(),
		"pending": _pending.duplicate(), "compact_pending": _compact_pending.duplicate()}


func cancel_search() -> void:
	_searching = false
	_pending = [-1.0, -1]
	_compact_pending = [-1.0, -1]
	_width = 0.0
	_room = 0.0
	_lo = SCALE_FLOOR
	_hi = 1.0
	_unsettled_since = -1


func observe(natural: float, room_for: Callable, width: float, ready: bool, frame: int, savings_bound: float, fresh_compaction: bool, content_key: Array) -> Dictionary:
	_remeasure = false
	var previous: Array = _sample
	_sample = [natural, width, savings_bound]
	if _content_key != content_key:
		var changed := not _content_key.is_empty()
		_content_key = content_key.duplicate(true)
		# An edit that leaves a settled group's measurements unchanged (a new
		# piece name in a fixed-width label) leaves its fit unchanged too;
		# restarting would replay the whole search for the same result.
		var same := settled() and absf(natural - float(previous[0])) <= 0.5 \
			and absf(width - float(previous[1])) <= 0.5 and is_equal_approx(savings_bound, float(previous[2]))
		if changed and not same:
			cancel_search()
			_compact = false
			_relaxed = 0.0
			_scale = 1.0
			# This sample was taken at the old scale/spacing. Discard it.
			_remeasure = true
			return _decision()
	if not ready:
		if _unsettled_since < 0:
			_unsettled_since = frame
		if frame - _unsettled_since <= SETTLE_FRAMES:
			_remeasure = true
			return _decision()
	_unsettled_since = -1
	if not _compact:
		_relaxed = natural
		var room: float = room_for.call(natural)
		if room > 1.0 and natural > room:
			if _agreed(false, natural, frame):
				_compact = true
			_remeasure = true
		else:
			_pending = [-1.0, -1]
		_scale = 1.0
	else:
		if _scale >= 1.0:
			_relaxed = minf(_relaxed, natural + savings_bound)
		var room: float = room_for.call(_relaxed)
		if room <= 1.0 or _relaxed <= room or fresh_compaction:
			cancel_search()
			_compact = false
			_scale = 1.0
			_remeasure = true
		else:
			_scale = _scale_step(natural, width, room, frame)
	return _decision()


func _decision() -> Dictionary:
	return {"compact": _compact, "scale": _scale, "remeasure": _remeasure}


func _scale_step(natural: float, width: float, room: float, frame: int) -> float:
	if _scale < 1.0 and (absf(width - _width) > 1.0 or absf(room - _room) > 0.5):
		cancel_search()
		_remeasure = true
		return 1.0
	if not _agreed(true, natural, frame):
		_remeasure = true
		return _scale
	if _scale >= 1.0:
		if natural <= room:
			return 1.0
		_searching = true
		_width = width
		_room = room
		_lo = SCALE_FLOOR
		_hi = 1.0
		_remeasure = true
		return clampf(floorf(room / natural * 100.0) / 100.0, SCALE_FLOOR, 1.0 - SCALE_STEP * 0.5)
	if not _searching:
		return _scale
	if natural * _scale <= room:
		_lo = _scale
	else:
		_hi = _scale
	if _hi - _lo <= SCALE_STEP:
		_searching = false
		return _lo
	_remeasure = true
	return snappedf((_lo + _hi) * 0.5, 0.01)


func _agreed(compacted: bool, value: float, frame: int) -> bool:
	var pending: Array = _compact_pending if compacted else _pending
	if absf(float(pending[0]) - value) > 0.5:
		if compacted:
			_compact_pending = [value, frame]
		else:
			_pending = [value, frame]
		return false
	if frame > int(pending[1]):
		if compacted:
			_compact_pending = [-1.0, -1]
		else:
			_pending = [-1.0, -1]
		return true
	return false
