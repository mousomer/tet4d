# Drag Earth across the Tet4D S² board

Get the repository checkout and open `learning/tutorials/curvature-seams-and-mercator/interactive-earth/index.html` in a browser. Keep the adjacent JavaScript, CSS and generated land mask together. The [HTML link](index.html) on GitHub shows the source.

The square uses the exact adjacent positive gluings from [Chapter 1](../../gluing-and-topologies/chapter_01_gluing_and_topologies.md) and analysed in [Chapter 2](../chapter_02_curvature_seams_and_mercator.md):

`L(t) ≡ B(t)`, `R(t) ≡ T(t)`.

The square is divided into two triangles, initially mapping to the northern and southern hemispheres. Dragging applies a quaternion rotation to the geographical sphere underneath the *fixed* board. The underlying Earth mapping is not equal-area, conformal or distance-preserving.

**Controls:** pointer/touch drag, **Reset globe**, **Hide/Show graticule**.

## Code and data

| File | Purpose |
|---|---|
| [index.html](index.html) | Offline interactive app, controls and layout |
| [styles.css](styles.css) | Responsive presentation |
| [earth_s2.js](earth_s2.js) | Square-to-sphere geometry, quaternion drag, raster rendering, interaction |
| [gshhg_landmask.generated.js](gshhg_landmask.generated.js) | Losslessly encoded, locally available GSHHG land mask |
| [generate_landmask.py](generate_landmask.py) | Optional reproducible mask builder using Basemap and Pillow |
| [earth_on_tet4d_s2.py](earth_on_tet4d_s2.py) | Original Python static map and numerical verification source (requires NumPy, Pillow, Matplotlib, Basemap) |
| [COASTLINE_DATA_LICENSE.md](COASTLINE_DATA_LICENSE.md) | Dataset licence and attribution |
| [smoke_browser.py](smoke_browser.py) | Optional Playwright seam/drag/controls smoke test |

For local serving (optional): `python -m http.server 8000` from this directory, then open `http://localhost:8000/`. No network or third-party packages are needed to *run* the HTML demo.

To regenerate the coastlines:

```sh
python -m pip install basemap pillow
python generate_landmask.py
```

The external coastline dataset is **LGPL-3.0-or-later**; see its dedicated attribution. The demo is only a projection of the topological quotient, not the game's native cell-step transport.

Optional browser verification (requires Playwright and Chromium): `python smoke_browser.py`.
