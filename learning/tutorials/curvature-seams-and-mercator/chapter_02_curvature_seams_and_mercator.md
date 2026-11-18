# Chapter 2 — Curvature, Seam Traversal, and Mercator Maps

**Gluings and Topologies: a computational introduction**
*Mathematical text and executable Python laboratory · 18 November 2026*

> **Central question.** Chapter 1 used edge identifications to construct topological surfaces from a square. Some of those surfaces—especially the sphere—cannot be everywhere flat. Why, then, can we still build them by gluing flat edges? What exactly goes wrong when an Explorer cell crosses a seam? And why is this closely related to the distortions of a Mercator world map?

**Prerequisite:** [Chapter 1 — Gluing Edges and Recognizing Topological Surfaces](../gluing-and-topologies/chapter_01_gluing_and_topologies.md). The chapter's four labelled corners and natural edge directions are retained here. The Python exercises are available separately in [this chapter's laboratory](README.md).

## 2.1 Four distinct mathematical objects

A picture of a surface displayed on a flat board does not uniquely specify its geometry. We must distinguish four layers.

1. **Quotient topology.** An equivalence relation `~` specifies which boundary points are the same point in the constructed space, `Q/~`. The question is whether that quotient is topologically a sphere, torus, projective plane, or another space.
2. **Intrinsic metric.** A metric determines path lengths, angles, geodesics, and curvature **inside** the quotient surface. Two homeomorphic surfaces can have very different metrics.
3. **Coordinate presentation.** A chart labels neighbourhoods by planar coordinates. Charts may overlap and their transition rules may rotate, reflect, stretch, or deform the coordinate grid. A seam in a drawing can be a chart cut rather than a geometric break.
4. **Discrete movement.** A game or simulation defines an update rule for grid cells. That rule need not be a geodesic, a continuous map of the underlying surface, or a rigid motion.

A defect at one layer does not automatically imply a defect at another. In particular, a topologically correct sphere quotient can have a singular piecewise-flat metric and a perfectly well-defined—though non-rigid—cell-update rule.

## 2.2 Why a sphere cannot carry an everywhere-flat metric

Gaussian curvature `K` measures intrinsic curvature: it can be determined by distances within a surface, without examining how the surface sits in an ambient three-dimensional space.

For a smooth compact surface without boundary, the Gauss–Bonnet theorem states

\[
\boxed{\int_M K\,dA=2\pi\chi(M).}
\]

Here `χ(M)` is the Euler characteristic, which depends only on topology. This formula also applies to nonorientable closed surfaces when curvature is integrated as a density, or by passing to the orientable double cover. See the references in §2.12.

For a sphere `S²`, `χ=2`, so

\[
\int_{S^2}K\,dA=4\pi.
\]

If an everywhere-flat metric existed, `K=0` at every point; the integral would be zero, contradicting `4π`. Therefore **no smooth intrinsic metric on the whole sphere can be flat everywhere**.

The same obstruction applies to the real projective plane `RP²`, where `χ=1`. But the torus and Klein bottle have `χ=0` and do admit flat intrinsic metrics.

| Closed surface | `χ` | Total curvature | Flat intrinsic metric? |
|---|---:|---:|---|
| Sphere `S²` | 2 | `4π` | No |
| Projective plane `RP²` | 1 | `2π` | No |
| Torus `T²` | 0 | 0 | Yes |
| Klein bottle | 0 | 0 | Yes |

**Intrinsic versus extrinsic.** A conventional doughnut-shaped torus in Euclidean three-space has varying Gaussian curvature, yet an abstract torus formed by identifying opposite sides of a Euclidean rectangle is intrinsically flat. Its flat metric need not be realizable as a smooth isometric embedding in ordinary three-dimensional space. Similarly, the flat Klein bottle should not be confused with the familiar self-intersecting picture of it.

For a round sphere of radius `R`, `K=1/R²` everywhere and its area is `4πR²`: the total curvature is `(1/R²)(4πR²)=4π`. Positive curvature is uniformly distributed in that particular metric. It need not be distributed uniformly for every metric on a sphere.

## 2.3 The single-square sphere concentrates curvature at three points

Chapter 1 introduced the square

\[
Q=[0,1]^2,\quad
A=(0,0),\ B=(1,0),\ C=(1,1),\ D=(0,1).
\]

Its natural edge parameterizations are

\[
L(t)=(0,t),\quad R(t)=(1,t),\quad
B(t)=(t,0),\quad T(t)=(t,1).
\]

Tet4D's normal single-domain `S²` construction identifies **adjacent** edges with positive tangent sign:

\[
\boxed{L(t)\sim B(t),\qquad R(t)\sim T(t).}
\]

This is the repository's `sphere_adjacent_positive` construction, corresponding to `X−↔Y− +` and `X+↔Y+ +`. It is not the old `sphere_2d` negative-adjacent recipe, whose quotient is a Klein bottle. The current product requirements record this in [the Explorer topology RDS](../../../docs/rds/RDS_EXPLORER_TOPOLOGIES.md).

The positive-adjacent endpoint identifications give three quotient vertices:

\[
[A]=\{A\},\qquad [C]=\{C\},\qquad [BD]=\{B,D\}.
\]

There is one quotient face and two quotient edges, so

\[
V=3,\quad E=2,\quad F=1,\qquad \chi=V-E+F=2.
\]

Together with the valid vertex links and orientability established in Chapter 1, this identifies the quotient as `S²`.

### A flat metric, except at cone points

Now retain the Euclidean metric inside the square. Its paired edges have equal length, so they can be joined by local **isometries**. Away from the original square corners, the resulting surface is locally a flat plane. At the quotient vertices, however, the total angle around a point is not necessarily `2π`.

For a quotient vertex `v`, define the *cone angle* and *angular defect* by

\[
\alpha(v)=\sum_{\text{corners identified at }v}\theta_{\text{corner}},
\qquad
\boxed{\delta(v)=2\pi-\alpha(v).}
\]

Every original square corner contributes `π/2`. Thus:

| Quotient vertex | Original corners | Cone angle `α` | Defect `δ` |
|---|---|---|---|
| `[A]` | `A` | `π/2` | `3π/2` |
| `[BD]` | `B,D` | `π` | `π` |
| `[C]` | `C` | `π/2` | `3π/2` |
| **Total** | Four square corners | `2π` | **`4π`** |

The discrete Gauss–Bonnet relation is satisfied exactly:

\[
\boxed{\sum_{v}\delta(v)=4\pi=2\pi\chi(S^2).}
\]

**Where did the sphere's curvature go?** The square quotient is flat everywhere except at those three cone vertices. It has not defeated Gauss–Bonnet; it has concentrated the required total curvature at a finite set of points.

For an arbitrary *complete, valid* square-edge pairing, we always have one face and two quotient edges. If `V` quotient vertices remain, the four right angles contribute `2π` in total. Therefore

\[
\sum_v\delta(v)=2\pi V-2\pi
=2\pi(V-E+F)=2\pi\chi.
\]

This elegant identity checks the curvature sum once the quotient is known to be a surface. It does **not** replace the vertex-link test: a quotient with a branching or disconnected vertex link need not be a manifold at all.

### Other examples

- A flat torus glues opposite edges without reversal. All four corners become one vertex with angle `4(π/2)=2π`; its angular defect is zero.
- A flat Klein bottle, with one opposite-edge pair reversed, likewise has one vertex of total angle `2π`. Its nonorientability is a **global** issue, not a local curvature singularity.
- The standard square projective plane reverses both opposite-edge pairs. It has two vertex classes, each containing two square corners. Each has angle `π` and defect `π`, summing to `2π`.

**Resolution does not remove curvature.** Replacing an `8×8` square grid with `80×80` while keeping the same quotient and inherited flat metric creates more little flat cells but leaves the same three cone defects. Refinement alone does not turn this singular piecewise-flat sphere into a smooth round sphere.

## 2.4 What actually happens at a seam?

A seam joins two edges of the *coordinate representation*. It need not be a physical discontinuity of the surface.

For the sphere's first pairing,

\[
L(t)=(0,t)\sim B(t)=(t,0),
\]

a convenient local unfolding from the neighbourhood of `L` into that of `B` is

\[
\boxed{S_{L\to B}(x,y)=(y,-x).}
\]

For the second,

\[
R(t)=(1,t)\sim T(t)=(t,1),
\]

one local unfolding is

\[
\boxed{S_{R\to T}(x,y)=(y,2-x).}
\]

Both are affine Euclidean isometries. Their linear part is the quarter-turn

\[
J=
\begin{pmatrix}0&1\\-1&0\end{pmatrix},
\qquad J^TJ=I,\quad\det J=1.
\]

Thus the seam can preserve intrinsic lengths and angles. But it changes the *coordinate components* of a direction.

For example,

\[
J\begin{pmatrix}-1\\0\end{pmatrix}
=\begin{pmatrix}0\\1\end{pmatrix}.
\]

A vector pointing left on one side points upward in the other coordinate chart. This is what correctly transporting its local geometric direction through that particular seam looks like.

A repeated **fixed board-axis command** does something different: after crossing, the next command again refers to the displayed square's axes. It does not automatically use the transported frame.

The distinction is:

\[
\text{Transport direction through chart:}\quad v'\!=Jv
\]

versus

\[
\text{Reapply a board command:}\quad a'\!=a.
\]

These rules agree for some gluings and directions but not in general.

### Ordinary seams versus singular vertices

Along an ordinary interior point of a paired edge, two half-disc neighbourhoods join to form a Euclidean disc. Nothing singular happens geometrically. The drawn discontinuity is a coordinate cut.

At a cone point, the angle surrounding the point differs from `2π`. The point does not have an ordinary Euclidean metric neighbourhood. In the present sphere example all cone angles are below `2π`, so a locally shortest geodesic cannot pass *through* one of these positive-curvature cone apices in the usual manner.

There are thus two distinct issues: a perfectly regular seam can *look* discontinuous, while a cone vertex is a genuine singularity of the chosen metric.

## 2.5 Parallel transport, holonomy and the absence of global directions

A tangent vector at one point cannot simply be declared equal to a vector at a different point of a curved surface: their tangent planes are different. A geometric rule for comparing directions is needed.

For a Riemannian metric, the standard rule is **Levi-Civita parallel transport**. It preserves the length of a vector and its angle with other transported vectors. However, transporting a vector around a closed path may return it with a different orientation. This phenomenon is called *holonomy*.

On an oriented smooth surface, for a suitable simple closed loop bounding a disc `D`, the net rotation angle is

\[
\boxed{\Delta\theta=\int_D K\,dA\pmod{2\pi}}
\]

up to the sign convention for traversing the loop.

For a round sphere of radius `R`,

\[
\Delta\theta=\frac{\operatorname{Area}(D)}{R^2}\pmod{2\pi}.
\]

For a piecewise-flat cone surface, a loop surrounding one cone point picks up a rotation equal to the enclosed angular defect (modulo `2π`). Around our quotient vertex `[A]`, the magnitude is `3π/2`; around `[BD]`, it is `π`.

Individual seam transitions can therefore be locally isometric while a *sequence* of them has nontrivial global holonomy. This is not evidence of a bad gluing.

### Hairy-ball theorem

A related but distinct obstruction is the hairy-ball theorem: there is no continuous nowhere-zero tangent vector field on the whole `S²`.

Consequently one cannot define one continuous global "rightward" tangent direction everywhere on the sphere, let alone a globally Euclidean pair of coordinate directions. Rotations of the round sphere do exist as global isometries; this theorem does not forbid moving objects on a sphere. It forbids **global flat translation directions** of the kind familiar from the plane.

### The nonorientable counterexample

The Klein bottle shows that nontrivial frame transport is not synonymous with curvature. Its flat metric has zero local Gaussian curvature, but a loop representing an orientation-reversing identification can return a transported frame **reflected**. The obstruction is global nonorientability, not local Gaussian curvature.

For the projective plane, both phenomena can occur: the topology is nonorientable *and* the Euler characteristic prevents an everywhere-flat smooth metric.

## 2.6 Why independently translated grid cells may split or deform

Tet4D's present 2D Explorer adopts a deliberate *free cellwise* movement rule. The [RDS §2.5](../../../docs/rds/RDS_EXPLORER_TOPOLOGIES.md) states that every cell receives the same canonical board-axis action, resolved independently by the native cell-step resolver. Transported frames are recorded but do not remap the next board-axis command. Different constituent cells may deform, change adjacency, or appear separated in the square.

A simplified mathematical description is

\[
p_i'=T_a(p_i),
\]

where `p_i` is a cell's original board position and `T_a` is the single-cell step operation for action `a`.

If some cells cross a seam and others do not, the representation of their updates can involve different local transitions:

\[
p_i'=
\begin{cases}
p_i+a,&\text{if this step stays inside the chart},\\
S_i(\text{continued local step}),&\text{if it crosses a seam}.
\end{cases}
\]

This is a conceptual chart-level illustration, **not** a formula for the actual integer-grid resolver.

The coordinate-space distance `|p_i'-p_j'|` displayed in the flat square need not equal its prior value. That observation alone tells us neither whether the cells are intrinsically separated nor whether a real rigid body deformed.

Four distinct phenomena must be diagnosed separately:

| Observed effect | Mathematical interpretation |
|---|---|
| Cells look far apart across opposite edges | Presentation cut; quotient adjacency may still hold |
| A direction changes axes at a seam | Coordinate transition / tangent-frame transport |
| A path around a vertex returns a rotated direction | Metric holonomy from enclosed curvature |
| A common board-axis command changes piece shape | Property of the discrete movement operator, not necessarily the quotient topology |

One more issue is **injectivity**: two distinct source cells can be proposed for the same destination site. A correct quotient surface does not guarantee that an arbitrarily chosen discrete step is injective on cell centres. Tet4D must still reject such a proposed move if distinct occupied destinations are required for game-state integrity.

This educational distinction does not ask for any alteration of the current free-cellwise Explorer rule.

## 2.7 Mercator projection: preserving angles, sacrificing scale

The problem of representing a sphere in a plane has a long history in cartography. Mercator projection is especially revealing because it makes one deliberate geometrical choice: preserve local angles, not local distances or areas.

Let `R` be the radius of a round sphere, `λ` longitude, and `φ` latitude, with `-π/2<φ<π/2`.

The round sphere's intrinsic line element in latitude–longitude coordinates is

\[
\boxed{ds^2=R^2\bigl(d\phi^2+\cos^2\phi\,d\lambda^2\bigr).}
\]

The longitude coefficient shrinks toward the poles: a fixed longitude difference corresponds to a smaller east–west distance as the parallel of latitude contracts.

Mercator takes horizontal coordinate

\[
x=R\lambda
\]

and chooses a vertical coordinate `y=y(φ)` so the east–west and north–south local scale factors match. The east–west map scaling is

\[
k_E=\frac{R\,d\lambda}{R\cos\phi\,d\lambda}=\sec\phi.
\]

The north–south scaling is `k_N=y'(φ)/R`. Conformality (equal local scale in orthogonal directions) requires

\[
y'(\phi)=R\sec\phi.
\]

Integrating gives the spherical Mercator formula:

\[
\boxed{
x=R\lambda,\qquad
y=R\ln\tan\left(\frac{\pi}{4}+\frac{\phi}{2}\right).
}
\]

The integration constant sets the equator at `y=0`. PROJ's [Mercator documentation](https://proj.org/en/stable/operations/projections/merc.html) describes this vertical coordinate as *isometric latitude*.

Differentiation gives

\[
dx=R\,d\lambda,\qquad dy=R\sec\phi\,d\phi,
\]

hence

\[
\boxed{ds^2=\cos^2\phi\,(dx^2+dy^2).}
\]

The factor multiplies both planar directions equally: Mercator is **conformal**. But that factor is not constant, so the map is not isometric.

The local map-to-ground scale and area scale are

\[
\boxed{k(\phi)=\sec\phi,\qquad k_{\rm area}(\phi)=\sec^2\phi.}
\]

| Latitude | Linear scale | Area scale |
|---:|---:|---:|
| 0° | 1.00× | 1.00× |
| 30° | 1.15× | 1.33× |
| 60° | 2.00× | 4.00× |
| 80° | 5.76× | 33.16× |
| 85° | 11.47× | 131.65× |

These are **local differential** scale factors of the spherical Mercator projection; they are not exact ratios of lengths of arbitrary extended curves.

### Where are the poles?

As `φ→π/2`, `y→+∞`. As `φ→-π/2`, `y→-∞`. Both poles are omitted from the Mercator chart.

This is a **coordinate infinity**, not an infinite distance on the sphere. The meridional distance from the equator to a pole remains `πR/2`:

\[
\int_{0}^{+\infty}\cos\phi(y)\,dy
=
R\int_{0}^{\pi/2}d\phi
=
\frac{\pi R}{2}.
\]

For the complete map with longitude made periodic, the coordinate domain has topology

\[
S^1\times\mathbb R
\cong S^2\setminus\{\text{north pole, south pole}\}.
\]

This is an **open cylinder**, not a complete sphere. Closing the top edge by identifying it with the bottom edge would instead give a torus. To obtain the sphere topologically, each polar end must collapse to its own single point.

A discontinuity at the international date line in an ordinary printed Mercator map is a coordinate cut. Its existence is independent of the genuine scale divergence toward the poles.

## 2.8 The same sphere, represented in two radically different ways

The Mercator construction and the single-square quotient can describe homeomorphic surfaces, but they put their geometrical difficulty in different places.

| Property | Mercator on a round sphere | Tet4D one-square `S²` quotient |
|---|---|---|
| Underlying topology when completed | Sphere | Sphere |
| Metric | Round spherical metric | Euclidean metric in the square, completed as a cone metric |
| Curvature | Smooth, `K=1/R²` | Zero off three cone vertices |
| Total curvature | `4π` | `4π` |
| Main coordinate issue | Scale grows without bound near omitted poles | Glued-edge cuts and sharply concentrated cone curvature |
| Locally angle-preserving? | Yes, between chart and round sphere | Yes at regular seams through isometric unfolding |
| What cannot be removed? | Nonzero total intrinsic curvature | Nonzero total intrinsic curvature |

Mercator **distributes** curvature across its smoothly curved sphere while representing distances with a varying planar scale. The square quotient retains flat geometry at most points but **concentrates** curvature at three vertices. Both respect the same topological obstruction.

The essential point is not that one is a better map. They describe **different metrics** on the same topological type, with different coordinate limitations.

### Why multiple charts matter

A sphere has no single globally regular coordinate chart covering every point. A mathematical atlas uses overlapping charts and transition maps, so the neighbourhood of a pole or a seam can be described in coordinates that remain regular there.

Switching from Mercator to a stereographic chart near a pole avoids the specific Mercator infinity in that new chart. It does not make the sphere intrinsically flat, nor does it create globally uniform Euclidean directions.

Likewise, a multi-chart Explorer could make a seam crossing visually continuous in one chart and discontinuous in another without changing the topology at all. This is a statement about representation, not a proposal to change the present runtime.

### Interactive Earth demonstration

The [offline draggable Earth on the Tet4D S² square](interactive-earth/index.html) illustrates how geography can rotate continuously under the fixed pairings `L(t) ≡ B(t)` and `R(t) ≡ T(t)`. The [demo source and dataset attribution](interactive-earth/README.md) explain the two-triangle projection, raster coastline source and local browser controls. It is an educational mapping, not an implementation of Explorer cell movement.

## 2.9 A mathematical diagnostic framework for Explorer

A robust analysis labels each property by the layer to which it belongs. It must not silently reject a mathematically valid sphere because a flat-board piece appears to deform.

| Diagnostic | Mathematical test | What it decides |
|---|---|---|
| Quotient correctness | Reciprocal edge maps, endpoint classes | Which points are identified |
| Manifold correctness | Vertex-link circles or intervals | Whether local neighbourhoods are surface-like |
| Topological class | `χ`, boundary count, orientability | Which compact surface results |
| Metric consistency | Isometry of seam parameter maps | Whether the chosen flat metric extends across regular seams |
| Singular curvature | Cone angle defects | Where intrinsic piecewise-flat curvature lives |
| Curvature accounting | `Σδ=2πχ` | Consistency with Gauss–Bonnet |
| Direction transport | Seam Jacobians and loop products | Orientation change and holonomy |
| Discrete movement | Per-cell resolver and destination injection | Whether a proposed grid action is well-defined |
| Visual presentation | Chart cuts, projection and overlays | Whether apparent gaps imply intrinsic gaps |

For the repository's current named examples, the invariant target values are

\[
\begin{array}{c|cc}
\text{Surface} & \chi & \sum\delta\\ \hline
S^2 & 2 & 4\pi\\
\mathbb{RP}^2 & 1 & 2\pi\\
T^2 & 0 & 0\\
\text{Klein bottle} & 0 & 0
\end{array}
\]

These geometric computations supplement, rather than replace, the existing independent quotient classification and vertex-link tests.

### Research implication

If a user cannot predict the visual location of a cell after crossing a seam, it is important to distinguish three explanations:

1. The user has not learned the **topological pairing**.
2. The user understands the pairing but has not learned the **coordinate-frame change**.
3. The user understands both but expects the **discrete piece movement** to preserve a geometric property the game does not impose.

Those are different kinds of spatial reasoning. Conflating them would make it difficult to study what Tet4D users actually learn.

## 2.10 The Python laboratory

The source files for this chapter are [curvature_mercator_lab.py](curvature_mercator_lab.py) and [test_curvature_mercator_lab.py](test_curvature_mercator_lab.py). They require only Python's standard library and do **not** import the Tet4D engine.

The first calculation starts with exactly the edge endpoint maps defined in Chapter 1. Its function `vertex_classes` uses union-find to identify square corners. It then computes

\[
\delta([v])=2\pi-\frac{\pi}{2}\,|\,[v]\,|.
\]

The following abbreviated calls illustrate the laboratory:

~~~python
from math import pi, radians
from curvature_mercator_lab import (
    SURFACES,
    vertex_classes,
    cone_defects,
    quotient_summary,
    sphere_seam_vector,
    mercator_y,
    mercator_scale,
)

print(vertex_classes(SURFACES["sphere"]))
# (('A',), ('B', 'D'), ('C',))

chi, total_defect = quotient_summary(SURFACES["sphere"])
assert chi == 2
assert abs(total_defect - 4 * pi) < 1e-12

print(sphere_seam_vector(-1, 0))  # (0, 1)
print(mercator_scale(radians(60)))  # approximately 2
print(mercator_y(radians(80)))  # finite, but rapidly increasing
~~~

The seam illustration implements the two affine unfoldings from §2.4; its vector function returns the associated Jacobian action. This is **not** a substitute for Tet4D's native cell-step resolver.

The Mercator portion evaluates the exact spherical coordinate formula and the local linear and area scale factors.

Run the examples and ten regression tests from the repository root:

~~~sh
PY="$(./scripts/resolve_python_env.sh)"
"$PY" learning/tutorials/curvature-seams-and-mercator/curvature_mercator_lab.py
"$PY" -m unittest discover \
  -s learning/tutorials/curvature-seams-and-mercator \
  -p 'test_curvature_mercator_lab.py' -v
~~~

The laboratory verifies vertex classes, all four curvature totals, the flat torus/Klein metrics, seam endpoint correspondence and norm preservation, Mercator symmetry and scaling, pole exclusion and malformed input rejection. Its four named pairings are known surface examples; for **general** user-authored gluing specifications the program would still need an independent vertex-link/manifold validator before interpreting angular defects as surface curvature.

## 2.11 Exercises

1. **Cones and vertices.** Compute the angle defects for the standard square `RP²` gluing and explain why its total must be `2π`. Then compute the same quantity for the torus.
2. **Inverse crossing.** Invert the coordinate map `(x',y')=(y,-x)`. Check explicitly that its Jacobian preserves squared vector norms and has determinant `+1`.
3. **Holonomy.** A loop encloses exactly the `[BD]` cone point of our square sphere. Predict the rotation accumulated by parallel transport, modulo `2π`.
4. **Mercator scale.** Derive `dy/dφ=R sec φ` from the formula for `y`, and verify why the local map area scale is the square of its length scale.
5. **A finite journey to infinity.** Evaluate the meridional ground distance represented by `y∈[0,+∞)`, using `ds=cos φ\,dy`.
6. **Classification of a visual failure.** Give one example each of an apparent chart discontinuity, a genuine cone singularity, and a non-injective discrete cell move. Explain which one is a topology error, if any.
7. **Study design.** Propose a learning task that isolates the understanding of *edge adjacency* from the understanding of *transported direction*.

## 2.12 References and boundaries of this chapter

- [Tet4D Explorer topology requirements](../../../docs/rds/RDS_EXPLORER_TOPOLOGIES.md), especially §2.5, for the chosen positive-adjacent sphere and authoritative free-cellwise movement rule.
- [Tet4D topology certification contract](../../../docs/architecture/explorer_topology_catalog_certification_contract.md) for the exact one-square quotient evidence procedure and mathematical versus runtime status.
- [MathWorld — Gauss–Bonnet Formula](https://mathworld.wolfram.com/Gauss-BonnetFormula.html), for the smooth curvature theorem.
- [Oregon State University — Gauss–Bonnet](https://sites.science.oregonstate.edu/physics/coursewikis/GDF/book/content/gaussbonnet.html), for the relation between angle defects and Euler characteristic.
- [PROJ — Mercator projection](https://proj.org/en/stable/operations/projections/merc.html), for isometric latitude and projection definitions.
- [Snyder, *Map Projections: A Working Manual*, Mercator section](https://neacsu.net/geodesy/snyder/3-cylindrical/sect_7/), for spherical map-scale formulas.

The chapter is an **educational mathematical exposition**, not a new topology certification or movement specification. It does not redefine the native solver's action semantics, promote any experimental surface, or imply that visual discontinuity requires repair. The core lesson is that **topological identification, intrinsic curvature, coordinate representation and discrete movement are separate structures**: a correct quotient does not make them interchangeable.
