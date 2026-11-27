"use strict";

// =====================================================================
// Parameters & UI
// =====================================================================
const DEFAULTS = {
  len: 1.6, wid: 0.6, thk: 0.5, swell: 0.95, twist: 1.6,
  opa: 0.55, clar: 0.7, frost: 0.65, gloss: 0.65, edge: 0.85,
  spin: 0.4, axis: "sym", shadow: 0.32, grid: false,
  c1: "#6e32c9", c2: "#b8253c", c3: "#159674", c0: "#efd2c4",
};
const SLIDERS = { len: 2, wid: 2, thk: 2, swell: 2, twist: 2, opa: 2, clar: 2, frost: 2, gloss: 2, edge: 2, spin: 2, shadow: 2 };
const SHAPE_KEYS = new Set(["len", "wid", "thk", "swell", "twist"]);
function resetView() { rotX = 0; rotY = 0; spinAngle = 0; camDist = CAM_DIST0; }
const COLOR_KEYS = ["c0", "c1", "c2", "c3"];
const P = { ...DEFAULTS };
let geoDirty = true;
let frameDirty = true;

const $ = (id) => document.getElementById(id);

function syncUI() {
  for (const k in SLIDERS) {
    $(k).value = P[k];
    $(k + "-v").textContent = (+P[k]).toFixed(SLIDERS[k]);
  }
  for (const k of COLOR_KEYS) $(k).value = P[k];
  $("axis").value = P.axis;
  $("grid").checked = P.grid;
}

function bindUI() {
  for (const k in SLIDERS) {
    $(k).addEventListener("input", () => {
      P[k] = +$(k).value;
      $(k + "-v").textContent = P[k].toFixed(SLIDERS[k]);
      if (SHAPE_KEYS.has(k)) geoDirty = true;
      frameDirty = true;
    });
  }
  for (const k of COLOR_KEYS) $(k).addEventListener("input", () => { P[k] = $(k).value; frameDirty = true; });
  $("axis").addEventListener("change", () => { P.axis = $("axis").value; frameDirty = true; });
  $("grid").addEventListener("change", () => { P.grid = $("grid").checked; frameDirty = true; });
  $("reset").addEventListener("click", () => {
    Object.assign(P, DEFAULTS);
    resetView();
    syncUI();
    geoDirty = frameDirty = true;
  });
  window.addEventListener("keydown", (e) => {
    if ((e.key === "h" || e.key === "H") && !(e.target instanceof HTMLInputElement)) $("ui").classList.toggle("hidden");
  });
}

// =====================================================================
// Geometry: Bryant–Kusner parametrization of Boy's surface
//   w in the closed unit disk, antipodal boundary points identified.
//   X = H |d|^2 / |H|^2  (algebraically identical to the usual g/|g|^2,
//   but finite at the three zeros of d, which all map to the triple point)
// =====================================================================
const S5 = Math.sqrt(5);

function bk(a, b, c, o, k) {
  const a2 = a * a - b * b, b2 = 2 * a * b;               // w^2
  const a3 = a2 * a - b2 * b, b3 = a2 * b + b2 * a;       // w^3
  const a4 = a2 * a2 - b2 * b2, b4 = 2 * a2 * b2;         // w^4
  const a6 = a3 * a3 - b3 * b3, b6 = 2 * a3 * b3;         // w^6
  const dr = a6 + S5 * a3 - 1, di = b6 + S5 * b3;         // d = w^6 + sqrt5 w^3 - 1
  const p1r = 1 - a4, p1i = -b4, p2r = 1 + a4, p2i = b4;
  const n1r = a * p1r - b * p1i, n1i = a * p1i + b * p1r; // w(1 - w^4)
  const n2r = a * p2r - b * p2i, n2i = a * p2i + b * p2r; // w(1 + w^4)
  const n3r = 1 + a6, n3i = b6;                           // 1 + w^6
  const dd = dr * dr + di * di;
  const h1 = -1.5 * (n1i * dr - n1r * di);                // -3/2 Im(n1 conj d)
  const h2 = -1.5 * (n2r * dr + n2i * di);                // -3/2 Re(n2 conj d)
  const h3 = (n3i * dr - n3r * di) - c * dd;              // Im(n3 conj d) - c|d|^2
  const hh = h1 * h1 + h2 * h2 + h3 * h3;
  const s = hh > 1e-300 ? dd / hh : 0;
  o[k] = h1 * s; o[k + 1] = h2 * s; o[k + 2] = h3 * s;
}

// Smooth, orientation-preserving diffeomorphism of R^3 (cylindrical about the
// 3-fold axis). Composing an immersion with a diffeomorphism keeps it an
// immersion, so every slider setting is still a genuine Boy's surface.
//   radial  r' = r (1 + (L-1) u),        u = r^2/(r^2+c^2)    -> lobe length
//   angle   a' = a - k/3 r^3 sin(3(a-a0))/(r^2+c^2)^{3/2} + tw z  -> width, twist
//   axial   z' = z (1 + (T-1) u)                                -> thickness
// Jacobian is triangular with positive diagonal for L>0.12, |k|<1, T>0.
function deform(o, k, D) {
  const x = o[k], y = o[k + 1], z = o[k + 2] - D.z0;
  const r2 = x * x + y * y, q = r2 + D.cc2, u = r2 / q;
  const im3 = (y * (3 * x * x - y * y)) * D.ca - (x * (x * x - 3 * y * y)) * D.sa; // Im(e^{-i a0'} (x+iy)^3)
  const ang = (-D.k / 3) * im3 / (q * Math.sqrt(q)) + D.tw * z;
  const sr = 1 + (D.len - 1) * u, cs = Math.cos(ang) * sr, sn = Math.sin(ang) * sr;
  o[k] = x * cs - y * sn;
  o[k + 1] = x * sn + y * cs;
  o[k + 2] = z * (1 + (D.thk - 1) * u);
}

const NR = 128, NT = 720, ROW = NT + 1, NV = (NR + 1) * ROW;
const dom = new Float64Array(NV * 2);
const uvs = new Float32Array(NV * 2);
for (let i = 0; i <= NR; i++) {
  for (let j = 0; j <= NT; j++) {
    const v = i * ROW + j, r = i / NR, t = (2 * Math.PI * j) / NT;
    dom[2 * v] = r * Math.cos(t);
    dom[2 * v + 1] = r * Math.sin(t);
    uvs[2 * v] = r;
    uvs[2 * v + 1] = j / NT;
  }
}
const indices = (() => {
  const out = new Uint32Array((2 * NR - 1) * NT * 3);
  let n = 0;
  for (let i = 0; i < NR; i++) {
    for (let j = 0; j < NT; j++) {
      const a = i * ROW + j, b = a + ROW;
      out[n++] = a; out[n++] = b; out[n++] = b + 1;
      if (i > 0) { out[n++] = a; out[n++] = b + 1; out[n++] = a + 1; }
    }
  }
  return out;
})();

const COLOR_PHASE = (2 * Math.PI) / 3;   // which lobe gets palette color 1 in the default view
const basePts = new Float64Array(NV * 3);
let posData = new Float32Array(NV * 3);
let nrmData = new Float32Array(NV * 3);
let colData = new Float32Array(NV * 2);
let uvData = uvs, idxData = indices, drawCount = indices.length;
const defPts = new Float64Array(NV * 3);
let buildMs = 0;

function buildGeometry() {
  const t0 = performance.now();
  buildBoy();
  uvData = uvs; idxData = indices;
  drawCount = idxData.length;
  gl.bindBuffer(gl.ARRAY_BUFFER, bufPos); gl.bufferData(gl.ARRAY_BUFFER, posData, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufNrm); gl.bufferData(gl.ARRAY_BUFFER, nrmData, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufCol); gl.bufferData(gl.ARRAY_BUFFER, colData, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufUV); gl.bufferData(gl.ARRAY_BUFFER, uvData, gl.DYNAMIC_DRAW);
  gl.bindVertexArray(meshVao);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, bufIdx); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idxData, gl.DYNAMIC_DRAW);
  gl.bindVertexArray(null);
  buildMs = performance.now() - t0;
}

function buildBoy() {
  const c = P.swell;
  let zmin = Infinity, zmax = -Infinity, rhoMax = 0, tipRho = 0, tipAz = 0;
  for (let v = 0; v < NV; v++) {
    bk(dom[2 * v], dom[2 * v + 1], c, basePts, 3 * v);
    const x = basePts[3 * v], y = basePts[3 * v + 1], z = basePts[3 * v + 2];
    if (z < zmin) zmin = z;
    if (z > zmax) zmax = z;
    const rho = Math.hypot(x, y);
    if (rho > rhoMax) rhoMax = rho;
    const r = uvs[2 * v];
    if (r > 0.55 && r < 0.9 && rho > tipRho) { tipRho = rho; tipAz = Math.atan2(y, x); }
  }
  // the three tips are symmetric: pick the one in a fixed 120° window so lobe colors never jump
  const third = (2 * Math.PI) / 3, win0 = (-10 * Math.PI) / 180;
  tipAz = win0 + ((((tipAz - win0) % third) + third) % third);
  const cc = 0.42 * rhoMax;
  const D = {
    z0: 0.5 * (zmin + zmax), cc2: cc * cc, len: P.len, thk: P.thk,
    k: Math.max(-0.85, Math.min(0.85, (1 - P.wid) * 1.4)),
    ca: Math.cos(3 * tipAz), sa: Math.sin(3 * tipAz),
    tw: P.twist / (zmax - zmin),
  };
  let lo0 = Infinity, lo1 = Infinity, lo2 = Infinity, hi0 = -Infinity, hi1 = -Infinity, hi2 = -Infinity;
  const ct = Math.cos(-tipAz - COLOR_PHASE), st = Math.sin(-tipAz - COLOR_PHASE);
  for (let v = 0; v < NV; v++) {
    defPts[3 * v] = basePts[3 * v]; defPts[3 * v + 1] = basePts[3 * v + 1]; defPts[3 * v + 2] = basePts[3 * v + 2];
    deform(defPts, 3 * v, D);
    const x = defPts[3 * v], y = defPts[3 * v + 1], z = defPts[3 * v + 2];
    if (x < lo0) lo0 = x; if (x > hi0) hi0 = x;
    if (y < lo1) lo1 = y; if (y > hi1) hi1 = y;
    if (z < lo2) lo2 = z; if (z > hi2) hi2 = z;
    // material coordinates: undeformed position, rotated so palette color 1 lands on a fixed lobe
    const bx = basePts[3 * v], by = basePts[3 * v + 1];
    colData[2 * v] = (bx * ct - by * st) / rhoMax;
    colData[2 * v + 1] = (bx * st + by * ct) / rhoMax;
  }
  // Normals from central differences on the polar grid (theta wraps; one-sided at the r = 1 seam).
  // The parametrization is an immersion, so these tangents never vanish away from the pole row.
  const P3 = (i, j, k) => defPts[3 * (i * ROW + j) + k];
  for (let i = 0; i <= NR; i++) {
    const i0 = Math.max(i - 1, 0), i1 = Math.min(i + 1, NR);
    for (let j = 0; j <= NT; j++) {
      const v = i * ROW + j;
      let ux, uy, uz, vx, vy, vz;
      if (i === 0) {  // pole w = 0: cross two diameters of the first ring
        const q = NT / 4;
        ux = P3(1, 0, 0) - P3(1, 2 * q, 0); uy = P3(1, 0, 1) - P3(1, 2 * q, 1); uz = P3(1, 0, 2) - P3(1, 2 * q, 2);
        vx = P3(1, q, 0) - P3(1, 3 * q, 0); vy = P3(1, q, 1) - P3(1, 3 * q, 1); vz = P3(1, q, 2) - P3(1, 3 * q, 2);
      } else {
        const jm = j === 0 ? NT - 1 : j - 1, jp = j === NT ? 1 : j + 1;
        ux = P3(i1, j, 0) - P3(i0, j, 0); uy = P3(i1, j, 1) - P3(i0, j, 1); uz = P3(i1, j, 2) - P3(i0, j, 2);
        vx = P3(i, jp, 0) - P3(i, jm, 0); vy = P3(i, jp, 1) - P3(i, jm, 1); vz = P3(i, jp, 2) - P3(i, jm, 2);
      }
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const nl = Math.hypot(nx, ny, nz) || 1;
      nrmData[3 * v] = nx / nl; nrmData[3 * v + 1] = ny / nl; nrmData[3 * v + 2] = nz / nl;
    }
  }
  const cx = 0.5 * (lo0 + hi0), cy = 0.5 * (lo1 + hi1), cz = 0.5 * (lo2 + hi2);
  let rad = 0;
  for (let v = 0; v < NV; v++) {
    const dx = defPts[3 * v] - cx, dy = defPts[3 * v + 1] - cy, dz = defPts[3 * v + 2] - cz;
    rad = Math.max(rad, dx * dx + dy * dy + dz * dz);
  }
  const s = 1 / Math.sqrt(rad);
  for (let v = 0; v < NV; v++) {
    posData[3 * v] = (defPts[3 * v] - cx) * s;
    posData[3 * v + 1] = (defPts[3 * v + 1] - cy) * s;
    posData[3 * v + 2] = (defPts[3 * v + 2] - cz) * s;
  }
}

// =====================================================================
// Shaders
// =====================================================================
const VS_MESH = `#version 300 es
precision highp float;
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNrm;
layout(location = 2) in vec2 aCol;
layout(location = 3) in vec2 aUV;
uniform mat4 uModel;
uniform mat4 uVP;
out vec3 vPos;
out vec3 vNrm;
out vec2 vCol;
out vec2 vUV;
invariant gl_Position;
void main() {
  vec4 w = uModel * vec4(aPos, 1.0);
  vPos = w.xyz;
  vNrm = mat3(uModel) * aNrm;
  vCol = aCol;
  vUV = aUV;
  gl_Position = uVP * w;
}`;

const VS_QUAD = `#version 300 es
out vec2 vUv;
void main() {
  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
  vUv = p;
  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`;

// Thin frosted-glass slab model shared by the camera layers and the shadow map.
const MATERIAL = `
uniform vec3 uLobe0, uLobe1, uLobe2, uCenter;
uniform float uSharp;
uniform vec2 uCenterR;
uniform float uDensity, uClarity, uScatter, uRim, uRough;

vec3 materialTint(vec2 c, out float edge) {
  float rho = length(c);
  vec2 n = c / max(rho, 1e-6);
  vec3 cosd = vec3(n.x, dot(n, vec2(-0.5, 0.8660254)), dot(n, vec2(-0.5, -0.8660254)));
  vec3 w = exp(uSharp * (cosd - 1.0));
  vec3 lobe = (w.x * uLobe0 + w.y * uLobe1 + w.z * uLobe2) / (w.x + w.y + w.z);
  edge = smoothstep(uCenterR.x, uCenterR.y, rho);
  return mix(uCenter, lobe, edge);
}
float pathLen(float cosT) { return mix(1.0, 1.0 / (cosT + 0.12), uRim); }
float fresnel(float cosT) {
  float f90 = 0.5 - 0.6 * uRough;
  return 0.04 + max(f90 - 0.04, 0.0) * pow(1.0 - cosT, 5.0);
}
`;

const FS_LAYER = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec3 vPos;
in vec3 vNrm;
in vec2 vCol;
in vec2 vUV;
uniform sampler2D uPrevDepth;
uniform int uPeel;
uniform vec3 uCamPos;
uniform float uGrid;
uniform vec3 uKeyDir, uKeyCol, uFillDir, uFillCol, uRimDir, uRimCol, uSky, uGround;
layout(location = 0) out vec4 oRad;
layout(location = 1) out vec4 oTrn;
${MATERIAL}
float sgLobe(vec3 R, vec3 dir, float sharp, float lr) {
  float s = sharp * lr / (sharp + lr);
  return s / sharp * exp(s * (dot(R, dir) - 1.0));
}
vec3 envRad(vec3 R) {
  float lr = 2.0 / max(uRough * uRough, 2e-3);
  vec3 env = mix(uGround, uSky, smoothstep(-0.3, 0.6, R.y));
  env += uKeyCol * 4.0 * sgLobe(R, uKeyDir, 30.0, lr);
  env += uFillCol * 1.4 * sgLobe(R, uFillDir, 14.0, lr);
  env += uRimCol * 1.6 * sgLobe(R, uRimDir, 16.0, lr);
  return env;
}
void main() {
  if (uPeel == 1 && gl_FragCoord.z <= texelFetch(uPrevDepth, ivec2(gl_FragCoord.xy), 0).r) discard;
  vec3 V = normalize(uCamPos - vPos);
  vec3 N = normalize(vNrm);
  float ndv = dot(N, V);
  if (ndv < 0.0) { N = -N; ndv = -ndv; }   // one-sided surface: shade the side we see
  ndv = clamp(ndv, 1e-3, 1.0);

  float edge;
  vec3 tint = materialTint(vCol, edge);
  float dens = uDensity * mix(uClarity, 1.0, edge);
  vec3 sigA = -log(clamp(tint, 0.003, 1.0));
  float path = pathLen(ndv);
  vec3 tau = exp(-sigA * dens * path);
  float scat = 1.0 - exp(-uScatter * dens * path);
  vec3 alb = exp(-sigA * dens * 1.0);

  float nk = dot(N, uKeyDir), nf = dot(N, uFillDir), nr = dot(N, uRimDir);
  vec3 Ef = uKeyCol * max(nk, 0.0) + uFillCol * max(nf, 0.0) + uRimCol * max(nr, 0.0);
  vec3 Eb = uKeyCol * max(-nk, 0.0) + uFillCol * max(-nf, 0.0) + uRimCol * max(-nr, 0.0);
  vec3 amb = mix(uGround, uSky, N.y * 0.5 + 0.5);
  vec3 Ls = alb * scat * (Ef + 0.6 * Eb + amb) * 0.32;

  float F = fresnel(ndv);
  vec3 rad = F * envRad(reflect(-V, N)) + (1.0 - F) * Ls;
  vec3 trn = (1.0 - F) * (1.0 - F) * tau * (1.0 - scat);

  if (uGrid > 0.5) {
    vec2 g = vec2(vUV.x * 18.0, vUV.y * 36.0);
    vec2 d = abs(fract(g + 0.5) - 0.5) / max(fwidth(g), vec2(1e-4));
    vec2 fw = fwidth(g);
    d += 1e3 * step(vec2(1.5), fw);   // suppress the wrap-around seam of the angle coordinates
    float line = 1.0 - clamp(min(d.x, d.y) - 0.5, 0.0, 1.0);
    rad += vec3(0.38) * line;
    trn *= 1.0 - 0.3 * line;
  }
  oRad = vec4(rad, 1.0);
  oTrn = vec4(trn, 1.0);
}`;

const FS_SHADOW = `#version 300 es
precision highp float;
in vec3 vPos;
in vec3 vNrm;
in vec2 vCol;
in vec2 vUV;
out vec4 o;
${MATERIAL}
void main() {
  float c = clamp(abs(normalize(vNrm).y), 1e-3, 1.0);
  float edge;
  vec3 tint = materialTint(vCol, edge);
  float dens = uDensity * mix(uClarity, 1.0, edge);
  float path = pathLen(c);
  vec3 tau = exp(-(-log(clamp(tint, 0.003, 1.0))) * dens * path);
  float scat = 1.0 - exp(-uScatter * dens * path);
  float F = fresnel(c);
  o = vec4((1.0 - F) * (1.0 - F) * tau * (1.0 - 0.6 * scat), 1.0);
}`;

const FS_BG = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec2 vUv;
uniform vec3 uCamPos, uCamR, uCamU, uCamF;
uniform vec2 uTanFov;
uniform float uFloorY, uShadowExt, uShadowStr;
uniform vec3 uBgDark, uBgLight;
uniform sampler2D uShadow;
out vec4 o;
void main() {
  vec2 ndc = vUv * 2.0 - 1.0;
  vec3 dir = normalize(uCamF + ndc.x * uTanFov.x * uCamR + ndc.y * uTanFov.y * uCamU);
  vec3 bg = mix(uBgDark, uBgLight, clamp(0.5 + 0.5 * (vUv.x - vUv.y), 0.0, 1.0));
  vec2 vq = ndc * vec2(0.75, 1.0);
  bg *= 1.0 - 0.06 * dot(vq, vq);
  if (dir.y < -1e-4) {
    vec3 hit = uCamPos + dir * ((uFloorY - uCamPos.y) / dir.y);
    vec2 st = hit.xz / uShadowExt * 0.5 + 0.5;
    if (all(greaterThan(st, vec2(0.0))) && all(lessThan(st, vec2(1.0)))) {
      bg *= mix(vec3(1.0), texture(uShadow, st).rgb, uShadowStr);
    }
  }
  o = vec4(bg, 1.0);
}`;

const FS_COMP = `#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uC, uT, uLR, uLT;
layout(location = 0) out vec4 oC;
layout(location = 1) out vec4 oT;
void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  vec3 T = texelFetch(uT, p, 0).rgb;
  oC = vec4(texelFetch(uC, p, 0).rgb + T * texelFetch(uLR, p, 0).rgb, 1.0);
  oT = vec4(T * texelFetch(uLT, p, 0).rgb, 1.0);
}`;

const FS_DOWN = `#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uC, uT, uBg;
out vec4 o;
void main() {
  ivec2 lim = textureSize(uC, 0) - 1;
  ivec2 p = ivec2(gl_FragCoord.xy) * 2;
  vec3 s = vec3(0.0);
  for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++) {
    ivec2 q = min(p + ivec2(i, j), lim);
    s += texelFetch(uC, q, 0).rgb + texelFetch(uT, q, 0).rgb * texelFetch(uBg, q, 0).rgb;
  }
  o = vec4(0.25 * s, 1.0);
}`;

const FS_BLUR = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec2 vUv;
uniform sampler2D uTex;
uniform vec2 uStep;
out vec4 o;
void main() {
  vec3 s = texture(uTex, vUv).rgb;
  float ws = 1.0;
  for (int i = 1; i <= 10; i++) {
    float x = float(i);
    float w = exp(-x * x / 32.0);   // sigma = 4 taps
    s += w * (texture(uTex, vUv + uStep * x).rgb + texture(uTex, vUv - uStep * x).rgb);
    ws += 2.0 * w;
  }
  o = vec4(s / ws, 1.0);
}`;

const FS_FINAL = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec2 vUv;
uniform sampler2D uFR, uFT, uC, uT, uBg, uBlur;
uniform float uFrostOn, uExposure;
out vec4 o;
// Khronos PBR Neutral tone mapper (reference implementation)
vec3 pbrNeutral(vec3 color) {
  const float startCompression = 0.8 - 0.04;
  const float desaturation = 0.15;
  float x = min(color.r, min(color.g, color.b));
  float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
  color -= offset;
  float peak = max(color.r, max(color.g, color.b));
  if (peak < startCompression) return color;
  const float d = 1.0 - startCompression;
  float newPeak = 1.0 - d * d / (peak + d - startCompression);
  color *= newPeak / peak;
  float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);
  return mix(color, newPeak * vec3(1.0), g);
}
vec3 toSrgb(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}
void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  vec4 fr = texelFetch(uFR, p, 0);
  vec3 bg = texelFetch(uBg, p, 0).rgb;
  vec3 col = bg;
  if (fr.a > 0.5) {
    vec3 behind = uFrostOn > 0.5
      ? texture(uBlur, vUv).rgb
      : texelFetch(uC, p, 0).rgb + texelFetch(uT, p, 0).rgb * bg;
    col = fr.rgb + texelFetch(uFT, p, 0).rgb * behind;
  }
  col = toSrgb(clamp(pbrNeutral(max(col * uExposure, 0.0)), 0.0, 1.0));
  o = vec4(col, fr.a);
}`;

// FXAA (compact Lottes variant, after mattdesl/glsl-fxaa, MIT) + grain/dither
const FS_FXAA = `#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uTex;
uniform vec2 uRes;
uniform float uGrain;
out vec4 o;
float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
void main() {
  vec2 inv = 1.0 / uRes;
  vec2 fc = gl_FragCoord.xy;
  vec3 rgbNW = texture(uTex, (fc + vec2(-1.0, -1.0)) * inv).rgb;
  vec3 rgbNE = texture(uTex, (fc + vec2(1.0, -1.0)) * inv).rgb;
  vec3 rgbSW = texture(uTex, (fc + vec2(-1.0, 1.0)) * inv).rgb;
  vec3 rgbSE = texture(uTex, (fc + vec2(1.0, 1.0)) * inv).rgb;
  vec4 mid = texture(uTex, fc * inv);
  const vec3 luma = vec3(0.299, 0.587, 0.114);
  float lNW = dot(rgbNW, luma), lNE = dot(rgbNE, luma), lSW = dot(rgbSW, luma), lSE = dot(rgbSE, luma);
  float lM = dot(mid.rgb, luma);
  float lMin = min(lM, min(min(lNW, lNE), min(lSW, lSE)));
  float lMax = max(lM, max(max(lNW, lNE), max(lSW, lSE)));
  vec2 dir = vec2(-((lNW + lNE) - (lSW + lSE)), (lNW + lSW) - (lNE + lSE));
  float dirReduce = max((lNW + lNE + lSW + lSE) * (0.25 * 0.125), 1.0 / 128.0);
  float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
  dir = clamp(dir * rcpDirMin, vec2(-8.0), vec2(8.0)) * inv;
  vec3 rgbA = 0.5 * (texture(uTex, fc * inv + dir * (1.0 / 3.0 - 0.5)).rgb +
                     texture(uTex, fc * inv + dir * (2.0 / 3.0 - 0.5)).rgb);
  vec3 rgbB = rgbA * 0.5 + 0.25 * (texture(uTex, fc * inv - dir * 0.5).rgb +
                                   texture(uTex, fc * inv + dir * 0.5).rgb);
  float lB = dot(rgbB, luma);
  vec3 col = (lB < lMin || lB > lMax) ? rgbA : rgbB;
  float n = hash12(fc) + hash12(fc + 17.31) - 1.0;   // triangular dither, also film grain
  col += n * uGrain * (1.0 + 3.5 * mid.a) / 255.0;
  o = vec4(col, 1.0);
}`;

// =====================================================================
// WebGL2 setup
// =====================================================================
const canvas = $("c");
const gl = canvas.getContext("webgl2", {
  antialias: false, alpha: false, depth: false, stencil: false,
  premultipliedAlpha: false, powerPreference: "high-performance",
});

function fail(msg) {
  const e = $("err");
  e.textContent = msg;
  e.style.display = "flex";
  $("ui").style.display = "none";
  throw new Error(msg);
}
if (!gl) fail("This viewer needs WebGL2, which this browser or device does not provide.");

const HAS_FLOAT_RT = !!gl.getExtension("EXT_color_buffer_float");
const HDR = HAS_FLOAT_RT ? gl.RGBA16F : gl.RGBA8;

function makeProgram(vs, fs, label) {
  const prog = gl.createProgram();
  for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      fail(`${label} ${type === gl.VERTEX_SHADER ? "vertex" : "fragment"} shader: ${gl.getShaderInfoLog(sh)}`);
    }
    gl.attachShader(prog, sh);
  }
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) fail(`${label} link: ${gl.getProgramInfoLog(prog)}`);
  const uni = {};
  const n = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) {
    const info = gl.getActiveUniform(prog, i);
    uni[info.name.replace(/\[0\]$/, "")] = { loc: gl.getUniformLocation(prog, info.name), type: info.type };
  }
  return { prog, uni };
}

function use(p, vals) {
  gl.useProgram(p.prog);
  for (const k in vals) {
    const u = p.uni[k];
    if (!u) continue;
    const v = vals[k];
    switch (u.type) {
      case gl.FLOAT: gl.uniform1f(u.loc, v); break;
      case gl.FLOAT_VEC2: gl.uniform2fv(u.loc, v); break;
      case gl.FLOAT_VEC3: gl.uniform3fv(u.loc, v); break;
      case gl.FLOAT_VEC4: gl.uniform4fv(u.loc, v); break;
      case gl.FLOAT_MAT4: gl.uniformMatrix4fv(u.loc, false, v); break;
      default: gl.uniform1i(u.loc, v);
    }
  }
}

function bindTextures(...texs) {
  texs.forEach((t, i) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); });
}

const progLayer = makeProgram(VS_MESH, FS_LAYER, "layer");
const progShadow = makeProgram(VS_MESH, FS_SHADOW, "shadow");
const progBg = makeProgram(VS_QUAD, FS_BG, "background");
const progComp = makeProgram(VS_QUAD, FS_COMP, "composite");
const progDown = makeProgram(VS_QUAD, FS_DOWN, "downsample");
const progBlur = makeProgram(VS_QUAD, FS_BLUR, "blur");
const progFinal = makeProgram(VS_QUAD, FS_FINAL, "final");
const progFxaa = makeProgram(VS_QUAD, FS_FXAA, "fxaa");

// Mesh buffers / VAO
const bufPos = gl.createBuffer(), bufNrm = gl.createBuffer(), bufCol = gl.createBuffer(), bufUV = gl.createBuffer();
const meshVao = gl.createVertexArray();
gl.bindVertexArray(meshVao);
[[bufPos, 3], [bufNrm, 3], [bufCol, 2], [bufUV, 2]].forEach(([b, n], i) => {
  gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.enableVertexAttribArray(i);
  gl.vertexAttribPointer(i, n, gl.FLOAT, false, 0, 0);
});
gl.bindBuffer(gl.ARRAY_BUFFER, bufUV);
gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
const bufIdx = gl.createBuffer();
gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, bufIdx);
gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
gl.bindVertexArray(null);
const quadVao = gl.createVertexArray();

function drawMesh() {
  gl.bindVertexArray(meshVao);
  gl.drawElements(gl.TRIANGLES, drawCount, gl.UNSIGNED_INT, 0);
}
function drawQuad() {
  gl.bindVertexArray(quadVao);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
}

// Render targets
const SHADOW_RES = 256;
const INNER_LAYERS = 8;   // depth-peeled layers behind the front surface
let RT = null;
let W = 1, H = 1;

function makeTex(w, h, fmt, filter) {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texStorage2D(gl.TEXTURE_2D, 1, fmt, w, h);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}
function makeFbo(colors, depth) {
  const fb = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  colors.forEach((t, i) => gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0 + i, gl.TEXTURE_2D, t, 0));
  if (depth) gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, depth, 0);
  gl.drawBuffers(colors.map((_, i) => gl.COLOR_ATTACHMENT0 + i));
  const st = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
  if (st !== gl.FRAMEBUFFER_COMPLETE) fail("Framebuffer incomplete (0x" + st.toString(16) + ")");
  return fb;
}

function allocTargets(w, h) {
  if (RT) {
    RT.textures.forEach((t) => gl.deleteTexture(t));
    RT.fbos.forEach((f) => gl.deleteFramebuffer(f));
  }
  const textures = [], fbos = [];
  const T = (ww, hh, fmt, filt) => { const t = makeTex(ww, hh, fmt, filt); textures.push(t); return t; };
  const F = (c, d) => { const f = makeFbo(c, d); fbos.push(f); return f; };
  const N = gl.NEAREST, L = gl.LINEAR;
  const hw = Math.max(1, w >> 1), hh = Math.max(1, h >> 1);
  const r = {
    bg: T(w, h, HDR, N),
    frontR: T(w, h, HDR, N), frontT: T(w, h, HDR, N),
    layR: T(w, h, HDR, N), layT: T(w, h, HDR, N),
    dA: T(w, h, gl.DEPTH_COMPONENT32F, N), dB: T(w, h, gl.DEPTH_COMPONENT32F, N),
    accC: [T(w, h, HDR, N), T(w, h, HDR, N)], accT: [T(w, h, HDR, N), T(w, h, HDR, N)],
    half: [T(hw, hh, HDR, L), T(hw, hh, HDR, L)],
    ldr: T(w, h, gl.RGBA8, L),
    shadow: [T(SHADOW_RES, SHADOW_RES, gl.RGBA8, L), T(SHADOW_RES, SHADOW_RES, gl.RGBA8, L)],
    hw, hh,
  };
  r.fbBg = F([r.bg]);
  r.fbFront = F([r.frontR, r.frontT], r.dA);
  r.fbLayA = F([r.layR, r.layT], r.dA);
  r.fbLayB = F([r.layR, r.layT], r.dB);
  r.fbAcc = [F([r.accC[0], r.accT[0]]), F([r.accC[1], r.accT[1]])];
  r.fbHalf = [F([r.half[0]]), F([r.half[1]])];
  r.fbLdr = F([r.ldr]);
  r.fbShadow = [F([r.shadow[0]]), F([r.shadow[1]])];
  r.textures = textures;
  r.fbos = fbos;
  RT = r;
}

// =====================================================================
// Math helpers (column-major 4x4)
// =====================================================================
const M4 = {
  mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
      o[c * 4 + r] = s;
    }
    return o;
  },
  rotX(t) { const c = Math.cos(t), s = Math.sin(t); return new Float32Array([1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]); },
  rotY(t) { const c = Math.cos(t), s = Math.sin(t); return new Float32Array([c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]); },
  rotZ(t) { const c = Math.cos(t), s = Math.sin(t); return new Float32Array([c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]); },
  persp(fovy, asp, n, f) {
    const t = 1 / Math.tan(fovy / 2);
    return new Float32Array([t / asp, 0, 0, 0, 0, t, 0, 0, 0, 0, (f + n) / (n - f), -1, 0, 0, (2 * f * n) / (n - f), 0]);
  },
};
const v3 = {
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
};

function hexToLinear(hex) {
  return [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
}

// =====================================================================
// Scene constants
// =====================================================================
const FOVY = (30 * Math.PI) / 180;
const CAM_ELEV = (11 * Math.PI) / 180;
const CAM_DIST0 = 5.3;
const TARGET = [0, -0.2, 0];
const FLOOR_Y = -1.28;
const SHADOW_EXT = 2.6;
const BASE_TILT = (24 * Math.PI) / 180;   // tilt of the symmetry axis toward the camera
const AXIS_FLIP = Math.PI;                // show the pole side (folds open toward viewer)
const LIGHTS = {
  uKeyDir: v3.norm([-0.55, 0.7, 0.45]), uKeyCol: [2.6, 2.55, 2.45],
  uFillDir: v3.norm([0.8, 0.15, 0.55]), uFillCol: [0.65, 0.68, 0.72],
  uRimDir: v3.norm([0.25, 0.55, -0.8]), uRimCol: [1.4, 1.4, 1.4],
  uSky: [0.55, 0.56, 0.58], uGround: [0.22, 0.22, 0.23],
};
const BG_DARK = [0.7, 0.7, 0.705], BG_LIGHT = [0.8, 0.8, 0.8];

let rotX = 0, rotY = 0, spinAngle = 0, camDist = CAM_DIST0;
let renderScale = 1, slowMs = 0, lastRenderT = 0, prevTickRendered = false;   // drops internal resolution if frames stay slow
let dragging = false, px = 0, py = 0;

function materialUniforms() {
  return {
    uLobe0: hexToLinear(P.c1), uLobe1: hexToLinear(P.c2), uLobe2: hexToLinear(P.c3), uCenter: hexToLinear(P.c0),
    uSharp: 3.5, uCenterR: [0.02, 0.42],
    uDensity: 0.08 + 1.6 * P.opa * P.opa,
    uClarity: 1 - 0.9 * P.clar,
    uScatter: 0.05 + 0.6 * P.frost,
    uRim: P.edge,
    uRough: 0.5 - 0.42 * P.gloss,
  };
}

function objectMatrix() {
  const base = M4.mul(M4.rotX(-BASE_TILT), M4.rotX(AXIS_FLIP));
  const drag = M4.mul(M4.rotX(rotX), M4.rotY(rotY));
  if (P.axis === "sym") return M4.mul(drag, M4.mul(base, M4.rotZ(spinAngle)));
  return M4.mul(M4.rotY(spinAngle), M4.mul(drag, base));
}

function camera() {
  const eye = [0, TARGET[1] + camDist * Math.sin(CAM_ELEV), camDist * Math.cos(CAM_ELEV)];
  const f = v3.norm(v3.sub(TARGET, eye));
  const r = v3.norm(v3.cross(f, [0, 1, 0]));
  const u = v3.cross(r, f);
  const view = new Float32Array([
    r[0], u[0], -f[0], 0, r[1], u[1], -f[1], 0, r[2], u[2], -f[2], 0,
    -v3.dot(r, eye), -v3.dot(u, eye), v3.dot(f, eye), 1,
  ]);
  const aspect = W / H;
  const proj = M4.persp(FOVY, aspect, Math.max(0.05, camDist - 1.6), camDist + 1.6);
  const th = Math.tan(FOVY / 2);
  return { eye, r, u, f, vp: M4.mul(proj, view), tanFov: [th * aspect, th] };
}

// =====================================================================
// Frame
// =====================================================================
const SHADOW_VP = new Float32Array([1 / SHADOW_EXT, 0, 0, 0, 0, 0, 0, 0, 0, 1 / SHADOW_EXT, 0, 0, 0, 0, 0, 1]);

function blur(src, dstFbo, w, h, dx, dy, sigmaPx) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, dstFbo);
  gl.viewport(0, 0, w, h);
  const step = sigmaPx / 4;
  use(progBlur, { uTex: 0, uStep: [(dx * step) / w, (dy * step) / h] });
  bindTextures(src);
  drawQuad();
}

let frameCount = 0, lastFrameMs = 0;

function renderFrame() {
  const t0 = performance.now();
  if (geoDirty) { buildGeometry(); geoDirty = false; }
  const model = objectMatrix();
  const cam = camera();
  const mat = materialUniforms();
  gl.disable(gl.CULL_FACE);
  gl.disable(gl.BLEND);
  gl.disable(gl.DEPTH_TEST);

  // 1) Colored soft shadow: multiplicative transmittance seen from straight above
  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbShadow[0]);
  gl.viewport(0, 0, SHADOW_RES, SHADOW_RES);
  gl.clearColor(1, 1, 1, 1);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ZERO, gl.SRC_COLOR);
  use(progShadow, { ...mat, uModel: model, uVP: SHADOW_VP });
  drawMesh();
  gl.disable(gl.BLEND);
  const shSigma = SHADOW_RES * 0.04;
  for (let i = 0; i < 2; i++) {
    blur(RT.shadow[0], RT.fbShadow[1], SHADOW_RES, SHADOW_RES, 1, 0, shSigma);
    blur(RT.shadow[1], RT.fbShadow[0], SHADOW_RES, SHADOW_RES, 0, 1, shSigma);
  }

  // 2) Backdrop + floor shadow
  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbBg);
  gl.viewport(0, 0, W, H);
  use(progBg, {
    uCamPos: cam.eye, uCamR: cam.r, uCamU: cam.u, uCamF: cam.f, uTanFov: cam.tanFov,
    // looked up 20% smaller: a large overhead softbox leaves an umbra smaller than the object
    uFloorY: FLOOR_Y, uShadowExt: SHADOW_EXT * 0.8, uShadowStr: P.shadow,
    uBgDark: BG_DARK, uBgLight: BG_LIGHT, uShadow: 0,
  });
  bindTextures(RT.shadow[0]);
  drawQuad();

  // 3) Depth peeling: front layer, then INNER_LAYERS composited front-to-back
  const meshU = { ...mat, ...LIGHTS, uModel: model, uVP: cam.vp, uCamPos: cam.eye, uGrid: P.grid ? 1 : 0, uPrevDepth: 0 };
  gl.enable(gl.DEPTH_TEST);
  gl.depthFunc(gl.LESS);
  gl.depthMask(true);
  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbFront);
  gl.clearBufferfv(gl.COLOR, 0, [0, 0, 0, 0]);
  gl.clearBufferfv(gl.COLOR, 1, [1, 1, 1, 1]);
  gl.clearBufferfv(gl.DEPTH, 0, [1]);
  use(progLayer, { ...meshU, uPeel: 0 });
  bindTextures(RT.dB);
  drawMesh();

  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbAcc[0]);
  gl.clearBufferfv(gl.COLOR, 0, [0, 0, 0, 1]);
  gl.clearBufferfv(gl.COLOR, 1, [1, 1, 1, 1]);
  let acc = 0;
  for (let k = 1; k <= INNER_LAYERS; k++) {
    const odd = k & 1;
    gl.enable(gl.DEPTH_TEST);
    gl.bindFramebuffer(gl.FRAMEBUFFER, odd ? RT.fbLayB : RT.fbLayA);
    gl.clearBufferfv(gl.COLOR, 0, [0, 0, 0, 0]);
    gl.clearBufferfv(gl.COLOR, 1, [1, 1, 1, 1]);
    gl.clearBufferfv(gl.DEPTH, 0, [1]);
    use(progLayer, { uPeel: 1 });
    bindTextures(odd ? RT.dA : RT.dB);
    drawMesh();
    gl.disable(gl.DEPTH_TEST);
    gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbAcc[1 - acc]);
    use(progComp, { uC: 0, uT: 1, uLR: 2, uLT: 3 });
    bindTextures(RT.accC[acc], RT.accT[acc], RT.layR, RT.layT);
    drawQuad();
    acc = 1 - acc;
  }
  gl.disable(gl.DEPTH_TEST);

  // 4) Frosted transmission: blur everything seen through the front surface
  const frostOn = P.frost > 0.005;
  if (frostOn) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbHalf[0]);
    gl.viewport(0, 0, RT.hw, RT.hh);
    use(progDown, { uC: 0, uT: 1, uBg: 2 });
    bindTextures(RT.accC[acc], RT.accT[acc], RT.bg);
    drawQuad();
    const sigma = Math.max(0.3, P.frost * 0.0055 * RT.hh);
    blur(RT.half[0], RT.fbHalf[1], RT.hw, RT.hh, 1, 0, sigma);
    blur(RT.half[1], RT.fbHalf[0], RT.hw, RT.hh, 0, 1, sigma);
  }

  // 5) Front layer over blurred interior, tone map
  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fbLdr);
  gl.viewport(0, 0, W, H);
  use(progFinal, { uFR: 0, uFT: 1, uC: 2, uT: 3, uBg: 4, uBlur: 5, uFrostOn: frostOn ? 1 : 0, uExposure: 1.0 });
  bindTextures(RT.frontR, RT.frontT, RT.accC[acc], RT.accT[acc], RT.bg, RT.half[0]);
  drawQuad();

  // 6) FXAA + grain to screen
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.viewport(0, 0, W, H);
  use(progFxaa, { uTex: 0, uRes: [W, H], uGrain: 1.2 });
  bindTextures(RT.ldr);
  drawQuad();

  frameCount++;
  lastFrameMs = performance.now() - t0;
}

// =====================================================================
// Interaction & loop
// =====================================================================
function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  let w = Math.round(innerWidth * dpr * renderScale), h = Math.round(innerHeight * dpr * renderScale);
  const maxPix = 2.6e6;                       // cap internal resolution (many full-res passes)
  if (w * h > maxPix) {
    const s = Math.sqrt(maxPix / (w * h));
    w = Math.round(w * s);
    h = Math.round(h * s);
  }
  w = Math.max(2, w); h = Math.max(2, h);
  if (w !== W || h !== H || !RT) {
    W = canvas.width = w;
    H = canvas.height = h;
    allocTargets(W, H);
  }
  frameDirty = true;
}

canvas.addEventListener("pointerdown", (e) => {
  dragging = true; px = e.clientX; py = e.clientY;
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  if (!dragging) return;
  rotY += (e.clientX - px) * 0.008;
  rotX += (e.clientY - py) * 0.008;
  px = e.clientX; py = e.clientY;
  frameDirty = true;
});
const endDrag = () => { dragging = false; };
canvas.addEventListener("pointerup", endDrag);
canvas.addEventListener("pointercancel", endDrag);
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  camDist = Math.max(3.0, Math.min(12, camDist * Math.exp(e.deltaY * 0.001)));
  frameDirty = true;
}, { passive: false });
window.addEventListener("resize", resize);

let lastT = performance.now();
function loop(now) {
  requestAnimationFrame(loop);
  const dt = Math.min(0.1, (now - lastT) / 1000);
  lastT = now;
  if (!dragging && P.spin > 0) { spinAngle += dt * P.spin * 0.5; frameDirty = true; }
  const willRender = frameDirty || geoDirty;
  if (willRender) {
    if (prevTickRendered && !geoDirty) {                // back-to-back frames: the gap is real frame time
      const gap = now - lastRenderT;
      if (gap > 40) slowMs += gap; else slowMs = Math.max(0, slowMs - 4 * gap);
      if (slowMs > 2500 && renderScale > 0.55) { renderScale *= 0.85; slowMs = 0; resize(); }
    }
    lastRenderT = now;
    frameDirty = false;
    renderFrame();
  }
  prevTickRendered = willRender;
}

resetView();
syncUI();
bindUI();
resize();
requestAnimationFrame(loop);

// Small hook for automated checks (harmless in normal use)
window.__boy = {
  P, gl, get stats() { return { frameCount, lastFrameMs, buildMs, W, H, renderScale, floatRT: HAS_FLOAT_RT }; },
  set(obj) { Object.assign(P, obj); syncUI(); if (Object.keys(obj).some((k) => SHAPE_KEYS.has(k))) geoDirty = true; frameDirty = true; },
  pose(o) { if ("rotX" in o) rotX = o.rotX; if ("rotY" in o) rotY = o.rotY; if ("spin" in o) spinAngle = o.spin; frameDirty = true; },
  renderNow() { frameDirty = false; renderFrame(); gl.finish(); },
  internals: () => ({ meshVao, count: drawCount, model: objectMatrix(), cam: camera(), RT }),
};
