# TraceReplay Scene Notes

This folder is reserved for `TraceReplay.unity`.

The Unity editor was not available in this environment, so the actual `.unity`
scene asset was not generated here. Runtime bootstrap is handled by
`TraceReplayController`, which creates the camera rig, renderer, light, and HUD
when attached to an empty scene object.
