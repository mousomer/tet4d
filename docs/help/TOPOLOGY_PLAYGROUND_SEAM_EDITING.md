# Topology Playground Seam Editing

This guide matches the current `Topology Playground` implementation in
`Editor` mode.

## Scope

Use this guide when you want to create, adjust, or remove seams in the modern
`Topology Playground` shell.

Current workspace model:

- `Editor`
- `Sandbox`
- `Play`

Seam editing happens in `Editor`.

## Before You Start

1. Open `Topology Playground`.
2. Switch to `Editor`.
3. Set `Tool` to `Edit`.

If `Tool` is set to `Probe`, boundary clicks only inspect and select. They do
not build or change a seam draft.

## What A Seam Contains

Each seam stores:

- a source boundary
- a target boundary
- a tangent-axis permutation
- one sign value per tangent axis

The live edit flow is always:

1. choose boundaries
2. adjust the transform
3. press `Apply`

Nothing is committed until `Apply` runs.

## Create A New Seam

1. In `Editor`, keep `Tool = Edit`.
2. Click the source boundary in the scene.
3. Click the target boundary in the scene.
4. In the transform editor:
   - choose the permutation button you want
   - toggle `Tangent 1`, `Tangent 2`, and higher tangent rows as needed
5. Press `Apply`.

Expected result:

- the seam is added to the current topology draft
- the new seam stays selected in the editor
- the scene highlight and helper panel update to the new active seam

## Edit An Existing Seam

You can load an existing seam into the editor in either of these ways:

1. Click the seam itself in the scene.
2. Click one of that seam's boundaries while `Tool = Edit`.

When the seam is loaded:

- the active seam becomes selected
- the transform editor switches to that seam's slot
- source and target come from the selected seam

Then:

1. change the permutation if needed
2. toggle tangent signs as needed
3. press `Apply`

## Remove A Seam

1. Select the seam first by clicking the seam or one of its boundaries in
   `Edit`.
2. Confirm the helper panel shows the seam as selected.
3. Press `Remove`.

If no seam is active, `Remove` fails with `No active glue selected`.

## How To Check What You Are Editing

Use the helper/status lines on the right side of the shell.

The current implementation exposes:

- `Selected boundary`
- `Hover boundary`
- `Selected seam`
- `Hover seam`
- `Workspace`
- `Tool focus`

If you are unsure what `Apply` or `Remove` will affect, check `Selected seam`
first.

## Common Mistakes

### Clicking boundaries while still in `Probe`

That only changes inspection/selection state. Switch `Tool` to `Edit` before
changing seams.

### Forgetting the second boundary

One boundary click sets the source only. The seam draft is not ready until the
target boundary is also chosen.

### Changing the transform without pressing `Apply`

The transform editor updates the draft only. The topology profile is not
changed until `Apply`.

### Pressing `Remove` without an active seam

`Remove` works only on the currently selected seam slot.

## Practical Workflow

For reliable seam edits, use this loop:

1. `Editor`
2. `Tool = Edit`
3. click seam or source boundary
4. click target boundary if you are creating a new seam
5. adjust permutation
6. adjust tangent sign flips
7. press `Apply`
8. verify the result in the scene and helper panel

## Related Surfaces

- `Trace` and `Probe Neighbors` are Editor-side inspection aids.
- `Topology Preset` changes the broader topology setup before seam refinement.
- `Sandbox` is for piece experimentation, not seam authoring.
- `Play` launches gameplay from the current topology state.
