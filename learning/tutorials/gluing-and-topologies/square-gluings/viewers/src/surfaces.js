// Six square gluings, ported line for line from the tutorial's renderers in ../rebuild/
// (tet4d_sphere_revised.py, directboy.py, orp.py, torus_direct.py, klein_direct.py, opklein.py).
//
// Every module evaluates its surface at a point (X, Y) of the square [-1, 1]^2, corner A = (-1, 1) at the
// top left, B top right, C bottom right, D bottom left (y up), at a stage of its two-stage construction
// (fold closes the orange seam a, puff the cyan seam b), with cone tips scaled by `cone` (1 = with cone
// points, 0 = smooth). Sides are listed clockwise: top A->B, right B->C, bottom C->D, left D->A; `dir` is
// +1 where the seam's arrow runs clockwise and -1 where it runs against.
"use strict";
const SURFACES = {};
(() => {
  const PI = Math.PI, S2 = Math.SQRT2, S5 = Math.sqrt(5);
  const ease = (x) => { const t = Math.min(1, Math.max(0, x)); return t * t * (3 - 2 * t); };
  const sinc = (k, y) => (Math.abs(k * y) < 1e-9 ? 1 : Math.sin(k * y) / (k * y));   // sin(k y)/(k y)
  const sq = (a) => a * a;
  const STD = (t) => ({ fold: ease((t - 1.55) / 2.7), puff: ease((t - 5.15) / 2.75), gap: 0 });
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

  // ---- Boy's surface as the tutorial builds it (directboy.py): Bryant-Kusner, family member c = 0.5,
  // on the sphere through stereographic projection; evaluated in the stable form H |d|^2 / |H|^2.
  function immersion(q) {
    const s = 1 + q[2] + 1e-15, wr = q[0] / s, wi = q[1] / s;
    const mul = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
    const w = [wr, wi], w2 = mul(w, w), w3 = mul(w2, w), w4 = mul(w2, w2), w6 = mul(w3, w3);
    const d = [w6[0] + S5 * w3[0] - 1, w6[1] + S5 * w3[1]], dc = [d[0], -d[1]], dd = d[0] * d[0] + d[1] * d[1];
    const n1 = mul(w, [1 - w4[0], -w4[1]]), n2 = mul(w, [1 + w4[0], w4[1]]), n3 = [1 + w6[0], w6[1]];
    const h = [-1.5 * mul(n1, dc)[1], -1.5 * mul(n2, dc)[0], mul(n3, dc)[1] - 0.5 * dd];
    const s2 = dd / Math.max(dot(h, h), 1e-300);
    return [h[0] * s2, h[1] * s2, h[2] * s2];
  }
  function param(r, theta) {   // directboy.param: disk point -> rotated unit sphere point
    theta += 0.64;
    const k = 1 / (1 + r * r);
    const q = [2 * r * Math.cos(theta) * k, 2 * r * Math.sin(theta) * k, (1 - r * r) * k];
    const ax = [Math.cos(0.64), Math.sin(0.64), 0], ang = 0.64, c = Math.cos(ang), s = Math.sin(ang);
    const axq = cross(ax, q), qa = dot(q, ax);
    return [0, 1, 2].map((i) => q[i] * c + axq[i] * s + qa * ax[i] * (1 - c));
  }
  const CENTERS = [param(0, 0), param(1, 0)];
  // cone-tip frames: tip position and outward normal of the immersion at each center (computed once)
  const TIPS = CENTERS.map((center) => {
    const pos = immersion(center);
    const tangent = norm(cross(center, [0, 0, 1])), tangent2 = cross(center, tangent);
    const p1 = immersion(norm(center.map((v, i) => v + 1e-5 * tangent[i])));
    const p2 = immersion(norm(center.map((v, i) => v + 1e-5 * tangent2[i])));
    let n = norm(cross(p1.map((v, i) => v - pos[i]), p2.map((v, i) => v - pos[i])));
    if (dot(n, pos.map((v, i) => v - [0, 0, -0.55][i])) < 0) n = n.map((v) => -v);
    return { center, pos, n };
  });

  // ---------------------------------------------------------------- sphere (adjacent edges)
  const sphereCtr = { c: [0, 0, 0], r: 1 };
  function spherePatch(X, Y, fold, puff, gap) {
    const xd = (X - Y) / 2, yd = (X + Y) / 2 - 0.5;   // the tutorial's diamond, folded along A-C
    const side = X + Y >= 0 ? 1 : -1;
    const b = Math.max(0, side * (yd + 0.5)), c = Math.max(0, (1 - b + xd) / 2), a = Math.max(0, (1 - b - xd) / 2);
    const u = Math.sqrt(a), v = Math.sqrt(b), w = Math.sqrt(c), bend = puff;
    let x = c - a + bend * 0.42 * b * (c - a);
    let y = b - 0.5 + bend * 0.18 * b * (a + c);
    let z = side * 2.48 * puff * u * v * w;
    if (side < 0) {
      const angle = PI * (1 - fold);
      y = (y + 0.5) * Math.cos(angle) - 0.5;
      z -= (b + bend * 0.18 * b * (a + c)) * Math.sin(angle);
      z -= gap * 4 * b * c;
    }
    return [x, y, z];
  }
  SURFACES.sphere = {
    title: "Adjacent-edge sphere", short: "Sphere", word: "a b b⁻¹ a⁻¹",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["b", -1], left: ["a", -1] },
    hasCones: true, orientable: true,
    note: "Three cone tips: A (90°), B+D (180°), C (90°). Without cone points the pillow becomes a round sphere.",
    span: [1.6, 6.9],
    params: (t) => ({
      fold: ease((t - 1.65) / 2.7), puff: ease((t - 1.6) / 3.2),
      gap: 0.62 * ease((t - 1.8) / 1.7) * (1 - ease((t - 5.25) / 1.65)),
    }),
    init() {   // centre and mean radius of the finished pillow, for the smooth (cone-free) version
      let c = [0, 0, 0], n = 0;
      const pts = [];
      for (let i = 0; i <= 40; i++) for (let j = 0; j <= 40; j++) {
        const p = spherePatch(-1 + i / 20, -1 + j / 20, 1, 1, 0); pts.push(p); c = c.map((v, k) => v + p[k]); n++;
      }
      c = c.map((v) => v / n);
      sphereCtr.c = c;
      sphereCtr.r = pts.reduce((s, p) => s + Math.hypot(p[0] - c[0], p[1] - c[1], p[2] - c[2]), 0) / n;
    },
    point(X, Y, s, cone) {
      const p = spherePatch(X, Y, s.fold, s.puff, s.gap);
      const k = (1 - cone) * s.puff;   // without cone points: inflate towards the round sphere
      if (k <= 0) return p;
      const c = sphereCtr.c, d = [p[0] - c[0], p[1] - c[1], p[2] - c[2]], l = Math.hypot(d[0], d[1], d[2]) || 1;
      return [0, 1, 2].map((i) => p[i] + k * (c[i] + (sphereCtr.r * d[i]) / l - p[i]));
    },
    home: { tilt: 0.35, turn: -0.3, roll: -Math.PI / 4 }, view: { rotX: 0.45, rotY: 0.7 },
  };

  // ---------------------------------------------------------------- RP^2, adjacent edges (direct curl)
  function boyDirect(X, Y, cone) {   // directboy.boy, at the square point
    const x = (X + 1) / 2, y = (1 - Y) / 2;
    const side = x >= y ? 1 : -1;
    const r = Math.max(x, y), s = r > 0 ? (side === 1 ? y / r : x / r) : 0;
    const theta = side === 1 ? PI * s : PI * (2 - s);
    const q = param(r, theta);
    const p = immersion(q);
    for (const t of TIPS) {
      if (Math.abs(dot(q, t.center)) <= 0.84) continue;   // local support on the same quotient sheet
      const dist = Math.hypot(p[0] - t.pos[0], p[1] - t.pos[1], p[2] - t.pos[2]);
      const h = sq(Math.max(0, 1 - dist / 0.54)) * 0.85 * cone;
      for (let i = 0; i < 3; i++) p[i] += h * t.n[i];
    }
    return p;
  }
  SURFACES["rp2-adjacent"] = {
    title: "Adjacent-edge projective plane", short: "RP² (adjacent edges)", word: "a b b a⁻¹",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["b", 1], left: ["a", -1] },
    hasCones: true, orientable: false,
    note: "Two cone tips: A (90°) and B+C+D (270°). Without cone points the finished surface is the smooth Boy's surface.",
    span: [1.55, 7.9], params: STD,
    final: boyDirect,   // the expensive part, cached by the engine per cone setting
    point(X, Y, s, cone, F) {
      const x = (X + 1) / 2, y = (1 - Y) / 2;
      const length = Math.hypot(x, y), theta = PI / 4 - Math.atan2(y, x);
      // a circular cone develops to a sector; increasing the azimuth preserves its arc lengths
      const beta = PI / 2 - s.fold * Math.acos(0.25), sine = Math.sin(beta), phi = theta / sine;
      const along = length * sine * Math.cos(phi), across = length * sine * Math.sin(phi), z = length * Math.cos(beta);
      const px = (along + across) / S2, py = (-along + across) / S2, angle = 1.37 * s.fold;
      const apex = [-0.5 - 0.15 * s.fold, 0.5 - 0.38 * s.fold, 0];
      const coneP = [apex[0] + Math.cos(angle) * px + Math.sin(angle) * z, apex[1] + py, apex[2] - Math.sin(angle) * px + Math.cos(angle) * z];
      if (s.puff <= 0) return coneP;
      const target = F || boyDirect(X, Y, cone);
      return [0, 1, 2].map((i) => (1 - s.puff) * coneP[i] + s.puff * 0.86 * target[i]);
    },
    home: { tilt: 0.2, turn: 0.4 },
  };

  // ---------------------------------------------------------------- RP^2, opposite edges
  const E1 = CENTERS[0], E2 = CENTERS[1], E3 = cross(E1, E2);
  function boyOpposite(X, Y, cone) {   // orp.final
    const x = X / 2, y = Y / 2;
    const r = 2 * Math.max(Math.abs(x), Math.abs(y)), th = (3 * PI) / 4 - Math.atan2(y, x), lat = (PI * r) / 2;
    const q = [0, 1, 2].map((i) => Math.sin(lat) * Math.cos(th) * E1[i] + Math.sin(lat) * Math.sin(th) * E2[i] + Math.cos(lat) * E3[i]);
    const p = immersion(q[2] < 0 ? q.map((v) => -v) : q);
    for (const t of TIPS) {
      const d = Math.hypot(p[0] - t.pos[0], p[1] - t.pos[1], p[2] - t.pos[2]);
      let gate = Math.min(1, Math.max(0, (Math.abs(dot(q, t.center)) - 0.72) / 0.2));
      gate = gate * gate * (3 - 2 * gate);   // smoothly limited to this preimage on the immersed sheet
      const height = 0.79 * sq(Math.max(0, 1 - d / ((2 * 0.79) / Math.sqrt(3)))) * cone;
      for (let i = 0; i < 3; i++) p[i] += t.n[i] * gate * height;
    }
    return p.map((v) => v * 0.86);
  }
  SURFACES["rp2-opposite"] = {
    title: "Opposite-edge projective plane", short: "RP² (opposite edges)", word: "a b a b",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["a", 1], left: ["b", 1] },
    hasCones: true, orientable: false,
    note: "Two cone tips: A+C and B+D, each 180°. Without cone points the finished surface is the smooth Boy's surface.",
    span: [1.55, 7.9], params: STD,
    final: boyOpposite,
    point(X, Y, s, cone, F) {
      const x = X / 2, y = Y / 2, fold = s.fold, puff = s.puff;
      let mob;
      if (fold === 0) mob = [x, y, 0];
      else {
        const k = 2 * PI * fold, angle = k * y, twist = angle / 2, radius = (1 - fold) / k + 0.65 * fold;
        const across = x * Math.cos(twist);
        mob = [across * Math.cos(angle) + radius * (-2 * sq(Math.sin(angle / 2)) + fold * fold), (radius + across) * Math.sin(angle), x * Math.sin(twist)];
      }
      if (puff <= 0) return mob;
      const f = F || boyOpposite(X, Y, cone);
      return [0, 1, 2].map((i) => (1 - puff) * mob[i] + puff * f[i]);
    },
    home: { tilt: 0.2, turn: 0.4 },
  };

  // ---------------------------------------------------------------- torus (opposite edges)
  function rollThenBend(x, y, fold, puff, extra) {   // torus_direct.patch / opklein.patch
    const k = 2 * PI * fold, circum = 1 + 0.8 * fold;
    let height = circum * y * sinc(k, y);
    let offset = fold === 0 ? 0 : (circum / k) * (-2 * sq(Math.sin((k * y) / 2)) + fold * fold);
    if (puff === 0) return [(1 + 0.65 * fold) * x, height, offset];
    const k2 = 2 * PI * puff, radius = (1.65 * (1 - puff)) / k2 + 0.93 * puff, angle = k2 * x;
    if (extra) [offset, height] = extra(x, y, puff, offset, height);
    return [(radius - offset) * Math.sin(angle), height, radius * (2 * sq(Math.sin(angle / 2)) - puff * puff) + offset * Math.cos(angle)];
  }
  SURFACES.torus = {
    title: "Opposite-edge torus", short: "Torus", word: "a b a⁻¹ b⁻¹",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["a", -1], left: ["b", -1] },
    hasCones: false, orientable: true,
    note: "The four 90° corners meet in one smooth 360° point, so there is no cone point.",
    span: [1.55, 7.9], params: STD,
    point: (X, Y, s) => rollThenBend(X / 2, Y / 2, s.fold, s.puff, null),
    home: { tilt: 0.55, turn: 0.2 },
  };

  // ---------------------------------------------------------------- Klein bottle, adjacent edges
  SURFACES["klein-adjacent"] = {
    title: "Adjacent-edge Klein bottle", short: "Klein bottle (adjacent edges)", word: "a b b a",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["b", 1], left: ["a", 1] },
    hasCones: false, orientable: false,
    note: "The four 90° corners meet in one smooth 360° point, so there is no cone point.",
    span: [1.55, 7.9], params: STD,
    point(X, Y, s) {
      const x = (X + 1) / 2, y = (1 - Y) / 2, l = x - y, m = x + y - 0.5, v = PI * m, fold = s.fold, puff = s.puff;
      if (fold === 0) return [(l + m - 0.5) / 2, (l - m + 0.5) / 2, 0];
      const k = 2 * PI * fold, u = k * l, radius = (1 - fold) / (S2 * k) + 0.93 * fold;
      const transverse = (1 - puff) * m * (0.7071 - 0.29 * fold) + puff * 0.41 * Math.sin(v);
      const height = puff * 0.29 * Math.sin(2 * v);
      const radial = transverse * Math.cos(u / 2) - height * Math.sin(u / 2);
      const z = transverse * Math.sin(u / 2) + height * Math.cos(u / 2);
      const d = (radius + radial) * Math.sin(u);
      const e = radius * (-2 * sq(Math.sin(u / 2)) + fold * fold) + radial * Math.cos(u) - ((1 - fold) * 0.5) / S2;
      return [(d + e) / S2, (d - e) / S2, z];
    },
    home: { tilt: 0.75, turn: 0.4 },
  };

  // ---------------------------------------------------------------- Klein bottle, opposite edges
  SURFACES["klein-opposite"] = {
    title: "Opposite-edge Klein bottle", short: "Klein bottle (opposite edges)", word: "a b a⁻¹ b",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["a", -1], left: ["b", 1] },
    hasCones: false, orientable: false,
    note: "The four 90° corners meet in one smooth 360° point, so there is no cone point.",
    span: [1.55, 7.9], params: STD,
    point: (X, Y, s) => rollThenBend(X / 2, Y / 2, s.fold, s.puff, (x, y, puff, offset, height) => {
      const twist = PI * x, v = 2 * PI * y + 0.85 * Math.cos(PI * x + 0.54);
      const one = 0.42 * Math.sin(v), two = 0.3 * Math.sin(2 * v);
      return [(1 - puff) * offset + puff * (one * Math.cos(twist) - two * Math.sin(twist)),
              (1 - puff) * height + puff * (one * Math.sin(twist) + two * Math.cos(twist))];
    }),
    home: { tilt: 0.55, turn: 0.2 },
  };

  // ---------------------------------------------------------------- Klein bottle, the glass bottle
  // The classic bottle immersion as a tube: point = C(σ) + r(σ) (cos φ N + sin φ ẑ) with the core C in the
  // xy-plane, N its in-plane normal, φ = π/2 - πY around the tube and σ along it. The finished core and
  // radius are periodic uniform cubic B-splines with a cusp at σ = 0: the control polygon is symmetric there
  // (P11 = P1), so C'(0) = 0 and the core arrives going down and leaves going up. N flips with it, which is
  // exactly the Klein identification (X = -1, Y) ~ (X = 1, -Y); the radius keeps growing through the join,
  // so the surface is smooth there. Stages: roll the square into a cylinder (orange a, as on the torus page);
  // stand it up as bulb and neck; then the neck's open end travels along the core - up, over, down outside,
  // through the wall, down inside - and flares to meet the bulb's bottom rim from within (cyan b).
  const BOTTLE = [   // control polygon: x, y, radius
    [0, -0.2, 0.45], [0, 0.55, 1.15], [0, 1.4, 1.0], [0, 2.05, 0.32], [0, 2.75, 0.25], [-0.35, 3.55, 0.24],
    [-1.35, 3.65, 0.24], [-2.0, 2.85, 0.24], [-1.85, 1.75, 0.24], [-1.05, 1.2, 0.24], [-0.25, 0.95, 0.24], [0, 0.55, 0.27],
  ];
  const BN = BOTTLE.length, BQ = Array.from({ length: BN + 3 }, (_, k) => BOTTLE[(k - 1 + BN) % BN]);   // Q_-1 .. Q_n+1
  function track(sig) {   // core point, unit direction and radius at σ in [0, 1]
    const j = Math.min(Math.floor(sig * BN), BN - 1), t = sig * BN - j, u = 1 - t;
    const b = [u * u * u / 6, (3 * t * t * t - 6 * t * t + 4) / 6, (-3 * t * t * t + 3 * t * t + 3 * t + 1) / 6, t * t * t / 6];
    const d = [-u * u / 2, (3 * t * t - 4 * t) / 2, (-3 * t * t + 2 * t + 1) / 2, t * t / 2];
    const e = [u, 3 * t - 2, 1 - 3 * t, t];
    const o = [0, 0, 0, 0, 0, 0, 0];   // x, y, r, x', y', x'', y''
    for (let i = 0; i < 4; i++) {
      const q = BQ[j + i];
      o[0] += b[i] * q[0]; o[1] += b[i] * q[1]; o[2] += b[i] * q[2];
      o[3] += d[i] * q[0]; o[4] += d[i] * q[1]; o[5] += e[i] * q[0]; o[6] += e[i] * q[1];
    }
    let dx = o[3], dy = o[4];
    if (Math.hypot(dx, dy) < 1e-12) { const g = sig < 0.5 ? 1 : -1; dx = g * o[5]; dy = g * o[6]; }   // the cusp
    const l = Math.hypot(dx, dy);
    return { x: o[0], y: o[1], r: o[2], dx: dx / l, dy: dy / l };
  }
  const tube = (x, y, r, dx, dy, phi) => [x - r * Math.cos(phi) * dy, y + r * Math.cos(phi) * dx, r * Math.sin(phi)];
  const SIG_A = 3 / BN, U_B = 0.5, RHO0 = 1.8 / (2 * PI);   // standing tube = track [0, SIG_A]; cylinder radius
  const BASE = track(0), TOP = track(SIG_A);
  SURFACES["klein-bottle"] = {
    title: "Klein bottle, the glass bottle", short: "Klein bottle (glass bottle)", word: "a b a⁻¹ b",
    sides: { top: ["a", 1], right: ["b", 1], bottom: ["a", -1], left: ["b", 1] },
    hasCones: false, orientable: false,
    note: "No cone point: the four 90° corners meet in one smooth 360° point. The neck passes through the wall and meets the base from inside.",
    span: [1.55, 10.4],
    params: (t) => ({
      fold: ease((t - 1.55) / 2.7), stand: ease((t - 4.6) / 1.6), lam: SIG_A + (1 - SIG_A) * ease((t - 6.2) / 4.2),
      puff: Math.min(1, Math.max(0, (t - 4.6) / 5.8)), gap: 0,
    }),
    point(X, Y, s) {
      const u = (X + 1) / 2, phi = PI / 2 - PI * Y;
      if (s.stand <= 0) return rollThenBend(X / 2, Y / 2, s.fold, 0, null);   // stage 1: the cylinder along x
      if (s.lam <= SIG_A) {   // stand the cylinder up about its end and shape it into bulb and neck
        const b = s.stand, T = track(u * SIG_A), th = (b * PI) / 2;
        const len = (1 - b) * 1.65 + b * (TOP.y - BASE.y), frac = (1 - b) * u + (b * (T.y - BASE.y)) / (TOP.y - BASE.y);
        const sx = (1 - b) * -0.825 + b * BASE.x, sy = b * BASE.y, r = (1 - b) * RHO0 + b * T.r;
        return tube(sx + len * frac * Math.cos(th), sy + len * frac * Math.sin(th), r, Math.cos(th), Math.sin(th), phi);
      }
      // the neck's end travels along the core; the bulb (first half of the square) stays put
      const w = Math.max(0, (u - U_B) / (1 - U_B)) ** 2, T = track(u * SIG_A + (s.lam - SIG_A) * w);
      return tube(T.x, T.y, T.r, T.dx, T.dy, phi);
    },
    home: { tilt: 0.12, turn: 0.45 },
    defaults: { opa: 0.2, frost: 0.08, clar: 0.9 },
  };

  for (const [id, m] of Object.entries(SURFACES)) { m.id = id; if (m.init) m.init(); }
})();
if (typeof module !== "undefined") module.exports = SURFACES;
