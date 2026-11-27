# Adjacent-edge square gluings: sphere and real projective plane

Start with corners A, B, C, D clockwise from the upper left. Orange identifies the top and left edges. Cyan identifies the right and bottom edges. Read every arrow as an edge parameter: corresponding arrow tails, midpoints and heads meet. Each row below gives the two directed copies of each seam.

| Surface | Orange | Cyan | Clockwise boundary word | Final corner classes |
|---|---|---|---|---|
| Sphere | A→B and A→D | B→C and D→C | a b b⁻¹ a⁻¹ | A, B+D, C |
| Real projective plane | A→B and A→D | B→C and C→D | a b b a⁻¹ | A, B+C+D |

## Sphere

The orange seam merges B with D. The two remaining cyan edges then run from this merged point to C. Closing them preserves A, B+D and C as three distinct points. Each original corner supplies 90° of intrinsic angle: A and C each have 90°, and B+D has 180°. The quotient has three vertices, two edges and one face, giving Euler characteristic 2. Both identifications reverse the boundary traversal, so the closed surface is orientable.

The prototype folds along AC and rounds the two triangular patches into a pillow. Its three tips are part of the mesh. Their slopes are stylized, and the labels give intrinsic angles in the original square. [Build animation](REBUILD.md?output=sphere-revised/adjacent-edge-sphere.mp4) · [Numbered stills](sphere-revised/adjacent-edge-sphere-stills.zip) · [Rotatable model](sphere-revised/rotate-sphere.html) · [Interactive gluing](viewers/sphere.html)

## Real projective plane (RP²)

The orange seam again merges B and D. Reversing the second cyan arrow changes the result: each of B and D now meets C. The closed quotient has one 90° corner at A and one 270° corner at B+C+D. Two vertices, two edges and one face give Euler characteristic 1. The cyan identification preserves the boundary traversal, making the surface nonorientable.

In the direct-curl animation each point keeps its distance from A as the orange edges meet. A becomes the apex of the resulting cone. The cyan rim then closes, and the B+C+D apex forms. The final model uses a Boy’s surface immersion modified locally at the two corner classes to produce visible cone tips. In the reset view A points left and B+C+D points right. The camera settles on the three apparent openings between the translucent sheets and holds. Both seams stay visible, with the cone labels off in the final frame and in the viewer’s reset view. At the central triple crossing, three distinct neighborhoods occupy the same displayed position. Only the orange and cyan edge maps identify points of the original square.

In the viewer, Replay starts from the square. Pause or scrub to inspect either seam and drag to rotate at any stage. The second seam closes at 16 seconds. The camera then turns slightly and holds the finished surface with both seams visible and labels off.

[Build direct-curl animation](REBUILD.md?output=direct-curl/boys-surface.mp4) · [Numbered stills](direct-curl/stills.zip) · [Rotatable model](direct-curl/rotate.html) · [Interactive gluing](viewers/rp2-adjacent.html)
