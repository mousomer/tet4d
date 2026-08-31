// Environment-layer backdrop for the Tet4D animated background surface.
//
// The pattern is computed in screen space so it never couples to gameplay
// zoom, camera orbit, or board geometry. The material writes no depth and the
// quad sits far behind the play volume, so gameplay always wins the depth test
// regardless of draw order.
shader_type spatial;
render_mode unshaded, shadows_disabled, ambient_light_disabled, fog_disabled, depth_draw_never, cull_disabled;

// Base world-background colour resolved from the semantic palette by the shell.
uniform vec3 base_color : source_color = vec3(0.02, 0.03, 0.04);
// Primary luminous line colour, also palette-resolved.
uniform vec3 line_color : source_color = vec3(0.09, 0.66, 0.73);
// Secondary travelling-pulse colour, also palette-resolved.
uniform vec3 accent_color : source_color = vec3(0.41, 0.85, 0.90);
// 0 keeps the flat base colour; 1 is the strongest shipped treatment.
uniform float animation_intensity : hint_range(0.0, 1.0) = 0.55;
// Monotonic flow phase owned by the shell rather than the engine clock.
uniform float animation_phase = 0.0;
// Viewport aspect ratio, supplied by the shell.
uniform float viewport_aspect = 1.7777778;
// 0 disables every animated contribution and leaves the flat base colour.
uniform float surface_active : hint_range(0.0, 1.0) = 0.0;

const float HORIZON_V = 0.2;
const float DEPTH_SCALE = 0.26;
const float LATTICE_SCALE = 5.0;
const float CENTRE_CALM = 0.72;
const float CENTRE_CALM_SPREAD = 2.2;
// Width of the ramp that removes the dense convergence band near the horizon.
const float HORIZON_CLEAR = 0.16;

// Anti-aliased unit-lattice line. Derivative widening makes dense regions fade
// out on their own, which suppresses shimmer near the horizon.
float lattice_line(float coord) {
	float distance_to_line = abs(fract(coord - 0.5) - 0.5);
	float width = fwidth(coord) * 1.25 + 0.006;
	return 1.0 - smoothstep(0.0, width, distance_to_line);
}

void fragment() {
	vec2 screen = SCREEN_UV;
	float below_horizon = screen.y - HORIZON_V;
	vec2 centred = vec2((screen.x - 0.5) * viewport_aspect, screen.y - 0.5);

	// Keep the middle of the frame markedly quieter than the periphery so the
	// board, its pieces, and the NEXT/HOLD neighbours always read first.
	float calm = 1.0 - CENTRE_CALM * exp(-dot(centred, centred) * CENTRE_CALM_SPREAD);

	// Remove the dense convergence band outright rather than relying on the
	// derivative fade alone: that band is the one region bright enough to
	// compete with board wireframes.
	float ground = smoothstep(0.0, HORIZON_CLEAR, below_horizon);
	float depth = DEPTH_SCALE / max(below_horizon, 0.0001);
	float lane = centred.x * depth * LATTICE_SCALE;
	float run = depth * LATTICE_SCALE + animation_phase;

	float lanes = lattice_line(lane) * 0.6;
	float runs = lattice_line(run) * 0.85;
	float lattice = max(lanes, runs) * ground;

	// One slow luminous band travelling along the receding axis.
	float band_coord = fract(run * 0.1 - animation_phase * 0.03) - 0.5;
	float band = exp(-band_coord * band_coord * 24.0);

	// Thin, restrained luminous horizon seam.
	float horizon = exp(-abs(below_horizon) * 110.0) * 0.18;

	vec3 animated = base_color;
	animated += line_color * lattice * calm;
	animated += accent_color * runs * band * ground * calm * 0.3;
	animated += line_color * horizon * calm;

	ALBEDO = mix(base_color, mix(base_color, animated, animation_intensity), surface_active);
}
