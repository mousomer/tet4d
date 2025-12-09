import sys
import time
import random
import copy

# Dimensions
SIZE_X = 8
SIZE_Y = 8
SIZE_Z = 8
SIZE_H = 20

# A helper for making a 4D array of zeros
def make_4d_grid(x_size, y_size, z_size, h_size):
    return [[[[0 for _ in range(h_size)]
               for _ in range(z_size)]
               for _ in range(y_size)]
               for _ in range(x_size)]

class Tetris4D:
    def __init__(self):
        # The 4D game grid: grid[x][y][z][h]
        self.grid = make_4d_grid(SIZE_X, SIZE_Y, SIZE_Z, SIZE_H)
        self.score = 0

        # Current piece shape offsets (list of (dx, dy, dz, dh))
        self.current_piece = None
        # Current piece position (x0, y0, z0, h0)
        self.current_pos = None

        # We'll define a few 4D shapes as examples
        self.shapes = self.define_4d_shapes()

        # Spawn initial piece
        self.spawn_new_piece()

    def define_4d_shapes(self):
        """
        Return a list of possible 4D Tetris pieces.
        Each piece is a list of (dx, dy, dz, dh) offsets.
        """
        # For demonstration, we define a few small 4D shapes:
        # 1) A single 4D block (just one cell)
        # 2) A "line" extended in x dimension (4 cells)
        # 3) A "line" extended in y dimension (4 cells)
        # 4) A "line" extended in z dimension (4 cells)
        # 5) A "line" extended in h dimension (4 cells)
        # In practice, you'd want more interesting polycubes/polychora.
        return [
            [(0,0,0,0)],  # Single block
            [(0,0,0,0), (1,0,0,0), (2,0,0,0), (3,0,0,0)],  # line in x
            [(0,0,0,0), (0,1,0,0), (0,2,0,0), (0,3,0,0)],  # line in y
            [(0,0,0,0), (0,0,1,0), (0,0,2,0), (0,0,3,0)],  # line in z
            [(0,0,0,0), (0,0,0,1), (0,0,0,2), (0,0,0,3)],  # line in h
        ]

    def spawn_new_piece(self):
        """Pick a random shape and place it near the top (h=19) with random (x, y, z)."""
        self.current_piece = random.choice(self.shapes)
        # Start in the top region (h near 19)
        x0 = random.randint(0, SIZE_X - 1)
        y0 = random.randint(0, SIZE_Y - 1)
        z0 = random.randint(0, SIZE_Z - 1)
        h0 = SIZE_H - 1  # near top
        self.current_pos = [x0, y0, z0, h0]

        # If the newly spawned piece collides immediately, game over or reset
        if self.check_collision(self.current_pos, self.current_piece):
            print("Game Over!")
            sys.exit()

    def check_collision(self, pos, piece):
        """
        Check if a piece at the given position collides with
        occupied cells or goes out of bounds.
        pos: [x0, y0, z0, h0]
        piece: list of (dx, dy, dz, dh)
        """
        x0, y0, z0, h0 = pos
        for (dx, dy, dz, dh) in piece:
            x = x0 + dx
            y = y0 + dy
            z = z0 + dz
            h = h0 + dh
            # Check out of bounds
            if not (0 <= x < SIZE_X and
                    0 <= y < SIZE_Y and
                    0 <= z < SIZE_Z and
                    0 <= h < SIZE_H):
                return True
            # Check occupied
            if self.grid[x][y][z][h] != 0:
                return True
        return False

    def place_piece(self, pos, piece, val):
        """
        Place the piece in the grid with a given val (e.g. piece ID).
        """
        x0, y0, z0, h0 = pos
        for (dx, dy, dz, dh) in piece:
            x = x0 + dx
            y = y0 + dy
            z = z0 + dz
            h = h0 + dh
            self.grid[x][y][z][h] = val

    def lock_piece_and_clear(self):
        """
        When a piece can no longer move down in h, lock it in place
        and check for any full 3D slices (X,Y,Z).
        """
        # Place it with a positive integer ID (or color code).
        # We'll just pick a random color id from 1..7
        val = random.randint(1, 7)
        self.place_piece(self.current_pos, self.current_piece, val)

        # Check for filled 3D slices in h dimension
        cleared_slices = 0
        h = 0
        while h < SIZE_H:
            if self.is_3d_slice_full(h):
                self.clear_3d_slice(h)
                cleared_slices += 1
            else:
                h += 1

        # Increase score based on how many slices were cleared
        if cleared_slices > 0:
            self.score += (cleared_slices ** 2) * 100
            print(f"Cleared {cleared_slices} 3D slices! Current Score: {self.score}")

        # Spawn a new piece
        self.spawn_new_piece()

    def is_3d_slice_full(self, h):
        """
        Check if the entire X,Y,Z space at height h is full (no zeros).
        """
        for x in range(SIZE_X):
            for y in range(SIZE_Y):
                for z in range(SIZE_Z):
                    if self.grid[x][y][z][h] == 0:
                        return False
        return True

    def clear_3d_slice(self, h_cleared):
        """
        Remove the slice at h_cleared by shifting everything above it
        down by 1, and create an empty slice at the top.
        """
        # Shift downward
        for h in range(h_cleared, SIZE_H - 1):
            for x in range(SIZE_X):
                for y in range(SIZE_Y):
                    for z in range(SIZE_Z):
                        self.grid[x][y][z][h] = self.grid[x][y][z][h + 1]

        # Clear the top slice
        top = SIZE_H - 1
        for x in range(SIZE_X):
            for y in range(SIZE_Y):
                for z in range(SIZE_Z):
                    self.grid[x][y][z][top] = 0

    # -----------------------------
    # 4D Rotations
    # -----------------------------
    def rotate_piece(self, plane):
        """
        Rotate current piece by +90 deg in one of the 4D planes:
        plane in {"xy", "xz", "xh", "yz", "yh", "zh"}
        We'll do a simple discrete rotation approach.
        """
        rotated_offsets = []
        for (dx, dy, dz, dh) in self.current_piece:
            if plane == "xy":
                # (x, y) -> (y, -x)
                new_dx, new_dy = dy, -dx
                new_dz, new_dh = dz, dh
            elif plane == "xz":
                # (x, z) -> (z, -x)
                new_dx, new_dz = dz, -dx
                new_dy, new_dh = dy, dh
            elif plane == "xh":
                # (x, h) -> (h, -x)
                new_dx, new_dh = dh, -dx
                new_dy, new_dz = dy, dz
            elif plane == "yz":
                # (y, z) -> (z, -y)
                new_dy, new_dz = dz, -dy
                new_dx, new_dh = dx, dh
            elif plane == "yh":
                # (y, h) -> (h, -y)
                new_dy, new_dh = dh, -dy
                new_dx, new_dz = dx, dz
            elif plane == "zh":
                # (z, h) -> (h, -z)
                new_dz, new_dh = dh, -dz
                new_dx, new_dy = dx, dy
            else:
                # No rotation
                new_dx, new_dy, new_dz, new_dh = dx, dy, dz, dh

            rotated_offsets.append((new_dx, new_dy, new_dz, new_dh))

        # Check collision if we adopt these new offsets
        if not self.check_collision(self.current_pos, rotated_offsets):
            self.current_piece = rotated_offsets

    # -----------------------------
    # Movement / Game Loop
    # -----------------------------
    def move_piece(self, dx, dy, dz, dh):
        """Attempt to move current piece by (dx, dy, dz, dh)."""
        new_pos = [
            self.current_pos[0] + dx,
            self.current_pos[1] + dy,
            self.current_pos[2] + dz,
            self.current_pos[3] + dh
        ]
        if not self.check_collision(new_pos, self.current_piece):
            self.current_pos = new_pos
            return True
        return False

    def step(self):
        """
        One 'tick' of the game:
        - Move piece downward in H dimension by 1 (dh = -1).
        - If collision, lock piece and clear lines, then spawn new piece.
        """
        if not self.move_piece(0, 0, 0, -1):
            # Could not move down -> place & clear
            self.lock_piece_and_clear()

    def run(self):
        """
        Very simple loop to demonstrate progression.
        In a real game, you'd handle user input (moves & rotations)
        and keep track of timing.
        """
        print("Starting 4D Tetris. Press Ctrl+C to stop.")
        frame_count = 0

        while True:
            time.sleep(0.5)

            # Simple demonstration: step the piece down automatically
            self.step()

            # For demonstration, we do a textual render every few frames
            frame_count += 1
            if frame_count % 5 == 0:
                self.render_text()

    def render_text(self):
        """
        Render 8 slices in Z dimension as 8 '3D boards'
        of size X×H each (and ignoring Y just for text clarity).
        A real game might do a more advanced 3D or 2D projection.
        """
        print("----- Current Board State (showing Z=0..7 slices) -----")
        # We'll flatten Y=0..7 by just taking the max or sum,
        # just to demonstrate that there's something in that column:
        # cell_value = max over y
        # (This is just a hacky textual representation.)
        for z in range(SIZE_Z):
            print(f"Z-Slice = {z}")
            for h in reversed(range(SIZE_H)):  # top row at h=19
                row_str = ""
                for x in range(SIZE_X):
                    # find any nonzero in y=0..7
                    val = 0
                    for y in range(SIZE_Y):
                        if self.grid[x][y][z][h] != 0:
                            val = self.grid[x][y][z][h]
                            break
                    row_str += f"{val if val != 0 else '.'} "
                print(row_str)
            print("\n")
        print("------------------------------------------------------")


if __name__ == "__main__":
    game = Tetris4D()
    game.run()
