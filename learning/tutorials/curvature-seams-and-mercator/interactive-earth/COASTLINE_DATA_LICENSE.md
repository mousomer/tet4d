# Third-party coastline data: GSHHG

The derived land/water mask in `gshhg_landmask.generated.js` comes from **GSHHG** (Global Self-consistent, Hierarchical, High-resolution Geography Database), authored by **Paul Wessel** and **Walter H. F. Smith**, distributed with Matplotlib Basemap's `basemap-data` package (low-resolution layer).

The GSHHG dataset and the derived mask remain under **LGPL-3.0-or-later**; they are third-party data and are **not relicensed under the repository's PolyForm Noncommercial licence**. See [the source dataset and licence notice](https://www.soest.hawaii.edu/wessel/gshhg/), [basemap-data terms](https://pypi.org/project/basemap-data/), and [LGPL-3.0 text](https://www.gnu.org/licenses/lgpl-3.0.html) (with [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html), incorporated by reference).

The generated mask is a 720×360 rasterization of that dataset; use `generate_landmask.py` to rebuild it from a local Basemap installation (the demo itself needs no Basemap installation).

Geographic colour and polar colouring are illustrative; no measured terrain or elevation data is claimed.
