# Rebuilding the six square gluings

Run these commands from this **square-gluings** folder. The complete build renders 3,144 PNG frames, selects 96 numbered key stills, encodes six H.264 movies at 24 fps and generates six standalone HTML viewers from the final meshes. Each construction gets its own full-frame and key-still ZIP. The output includes the collection index and construction notes.

## Apple silicon Mac

The pinned dependencies (NumPy, Pillow, and imageio-ffmpeg with an FFmpeg executable) install from PyPI. On macOS, install Apple Command Line Tools for the C compiler and SDK.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r rebuild/requirements.txt
.venv/bin/python rebuild/build.py --output /tmp/tet4d-square-gluings
```

Open **/tmp/tet4d-square-gluings/index.html** after the command finishes. Use a new or empty output directory for each run. Reserve approximately 2 GB of free space in the output location. The movies are silent. A different FFmpeg build, font or numerical library can change encoded bytes or raster pixels.

## Encoder for byte-level comparisons

On the tested Apple silicon Mac, the bundled encoder reproduced all decoded video frames. For byte-identical MP4 containers as well, the original Homebrew FFmpeg 9.0.2 build with libx264 reproduced all six reference SHA-256 hashes. The two RP² recipes now render revised endings. To rebuild the current recipes with the same encoder, use a fresh output directory:

```sh
IMAGEIO_FFMPEG_EXE="$(command -v ffmpeg)" .venv/bin/python rebuild/build.py --output /tmp/tet4d-original-encoder
```

## Building one construction

```sh
.venv/bin/python rebuild/build.py --only opposite-rp2 --output /tmp/tet4d-rp2-test --jobs 4
```

The available names are **sphere-revised** (adjacent sphere), **direct-curl** (adjacent RP²), **adjacent-klein**, **opposite-torus**, **opposite-klein** and **opposite-rp2**. A single-construction run writes its media and viewer under the named subfolder. The complete index is produced by the all-six build.

## Other environments and fonts

On Linux, provide a C compiler with shared-library support. Set `CC` to its executable if needed. The build compiles the included rasterizer into a temporary directory. For an external H.264-enabled FFmpeg, set `IMAGEIO_FFMPEG_EXE` to its executable path.

On macOS the renderer uses the system Arial Unicode font when available. Elsewhere it requests DejaVu Sans. Set `GLUING_FONT` to the path of an installed TrueType font supporting the arrow, diamond and degree glyphs to override this. System fonts, Python, the OS SDK and the C compiler are host prerequisites.

## Source layout

- **rebuild/build.py** selects the recipe, renders the frames in batches, picks the numbered stills, encodes the movie and packages the image sequences.
- **rebuild/viewer.py** evaluates the final geometry, builds the mesh, labels, seams and crossing data, and inserts them into the matching HTML/JavaScript source under **rebuild/templates/**.
- **rebuild/tet4d_sphere_revised.py**, **directboy.py**, **klein_direct.py**, **torus_direct.py**, **opklein.py** and **orp.py** contain the parameterizations and animation renderers. The opposite-edge RP² renderer shares the Boy’s surface parameterization in **directboy.py**.
- **rebuild/raster.c** composites translucent triangle fragments in depth order. The sphere uses a Pillow renderer.
- **rebuild/requirements.txt** pins the three Python dependencies.
