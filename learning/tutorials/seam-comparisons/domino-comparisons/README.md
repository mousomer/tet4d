# A two-cell piece on three square gluings

Start every clip with A at (0,1) and B at (1,1) on a 5 × 5 Cartesian board. Up increases y. These are board-axis commands in the tutorial convention. A and B stay labelled throughout. A dark link means the cells are cardinal neighbours on the quotient. At a seam the link can appear at two different board edges. Read the bond after each move pauses.

| Sequence | Sphere, adjacent LB+ RT+ | Projective, opposite LR− BT− | Projective, adjacent LB− RT+ |
|---|---|---|---|
| Left Up Right | Broken on Up | Broken on Up | Broken on Up |
| Left Rotate Right | Intact throughout | Intact throughout | Intact throughout |
| Left Right | Broken | Original pose restored | Broken |
| Left Up Left | Broken | Broken | Rejoined on final Left |
| Left Down Left Right Left | Intact throughout | Broken on Down | Broken on final Left |

**Why the turn differs from Up.** Up translates each cell independently. Rotate applies a clockwise quarter-turn about A, the lower-ID material pivot for this domino. Tet4D develops the rest shape in A’s transported frame. Just after Left, that shape points down from A on both adjacent-edge boards and right from A on the opposite-edge board. Turning it clockwise places B to A’s left on the adjacent boards and below A on the opposite-edge board. The final Right keeps the two cells neighbours on all three.

**Why “best” depends on the test.** Opposite-edge reversals make each single-axis command a permutation and its opposite key an inverse on positions. A permutation can still separate neighbours. The adjacent projective example differs from the sphere in only the sign of the left/bottom pairing. It can reunite the domino when the sphere leaves it apart. The word “rejoined” records a real loss and recovery during that sequence.

The last three clips are shortest witnesses from this starting pose with initial Left, cardinal translations only, and every step accepted on every board. The generator enumerates command strings up to length six and checks the final bond pattern. There may be ties. These are examples for the specified presets, rather than global topology rankings.

## Watch the comparisons

From left to right, the clips show boards A, C and B using Lesson 03’s board names.

- [Left → Up → Right](01_left_up_right.gif) · Up breaks the bond on all three boards.
- [Left → Clockwise turn → Right](02_left_rotate_right.gif) · The bond survives on all three boards.
- [Left → Right](03_opposite_only.gif) · Only C finishes bonded.
- [Left → Up → Left](04_adjacent_projective_only.gif) · Only B finishes bonded.
- [Left → Down → Left → Right → Left](05_sphere_only.gif) · Only A finishes bonded.

## Reproduce

Run `python domino.py --out rendered` with Python 3.10+, Pillow and DejaVu Sans. Each endpoint is checked against the included native trace. The smooth interpolation illustrates the motion between discrete poses. The rotation arc is drawn in A’s local chart, clipped at the seam.

The trace records sequence, board index (0 sphere, 1 opposite RP², 2 adjacent RP²), one-based move index, Ax, Ay, Bx, By, and a native neighbour check (1 = bonded). T denotes clockwise rotation. To regenerate the trace from Tet4D commit a5e7db3a65d450075fde512cb7579539ce874f28, set CORE to the path of native/tet4d_core and run:

```sh
g++ -std=c++17 -O0 -I"$CORE/include" verify_native.cpp "$CORE"/src/core/*.cpp -o verify_native
./verify_native LUR LTR LR LUL LDLRL > native_traces.txt
python domino.py --out rendered
```
