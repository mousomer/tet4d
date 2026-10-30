extends Node

# Sole owner of ordinary cockpit layout scheduling. Callbacks read current
# measurements; queued work never stores scene measurements or decisions.
var _apply: Callable
var _measure: Callable
var _scheduled: Callable
var _generation := 0
var _applying := false
var _metrics_pending := false
var _fit_pending := false


func configure(apply_layout: Callable, measure_layout: Callable) -> void:
	_apply = apply_layout
	_measure = measure_layout


func applying() -> bool:
	return _applying


func idle() -> bool:
	return not _applying and not _metrics_pending and not _fit_pending


func generation() -> int:
	return _generation


# External context updates stay synchronous. Discard queued work belonging to
# the old context; this pass requests any measurements its new context needs.
func apply_now() -> void:
	if _applying:
		request_fit()
		return
	invalidate()
	_run_apply()


# Ownership changes (for example detached Designer panels) can invalidate old
# work without applying ordinary cockpit placement in the new owner.
# Cancels queued presentation work; does not compute gameplay validity.
# tet4d-semantic-boundary: allow display-only
func invalidate() -> void:
	_generation += 1
	_cancel_pending()


func request_metrics() -> void:
	if not is_inside_tree():
		return
	_metrics_pending = true
	_schedule()


func request_fit() -> void:
	if not is_inside_tree():
		return
	_fit_pending = true
	_schedule()


func _schedule() -> void:
	if _scheduled.is_valid():
		return
	_scheduled = _flush.bind(_generation)
	get_tree().process_frame.connect(_scheduled, CONNECT_ONE_SHOT)


func _flush(revision: int) -> void:
	if revision != _generation:
		return
	_scheduled = Callable()
	var fit := _fit_pending
	var metrics := _metrics_pending
	_fit_pending = false
	_metrics_pending = false
	if fit:
		_run_apply()
	elif metrics and _measure.is_valid():
		_measure.call()


func _run_apply() -> void:
	_applying = true
	if _apply.is_valid():
		_apply.call()
	_applying = false


func _cancel_pending() -> void:
	if _scheduled.is_valid() and is_inside_tree() and get_tree().process_frame.is_connected(_scheduled):
		get_tree().process_frame.disconnect(_scheduled)
	_scheduled = Callable()
	_metrics_pending = false
	_fit_pending = false


func _exit_tree() -> void:
	_generation += 1
	_cancel_pending()
