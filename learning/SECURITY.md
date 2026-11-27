# Security review of the learning material

Reviewed 2026-11-27 on `learning-surfaces`, the work branch of `learning` (everything under `learning/`). No exploitable
issue was found; one dependency pin was raised.

## What was checked

- **Secrets and personal data.** No keys, tokens, passwords, private keys, e-mail addresses or personal
  file paths in the files or in the branch's history (diffs against master, binaries excluded).
- **Browser pages.** Every `innerHTML` write in the gluing viewers builds markup from the page's own
  constants, numbers and colour-input values (`#rrggbb`). URL parameters (`glue`, `motion`, `cones`,
  `play`) are parsed as numbers or compared with fixed strings and never reach HTML. Lesson 3 compares
  `location.hash` with a fixed string. No `eval`, `new Function`, `document.write`, string timers,
  `postMessage` listeners or network requests; no scripts or styles load from other sites. Local storage
  holds only panel open/closed flags. The embed script accepts only a 3–4 digit `data-height` and loads its
  own page.
- **Python.** No `shell=True`, `os.system`, `eval`/`exec`, pickle or YAML loading, and no downloads.
  `square-gluings/rebuild/build.py` runs fixed argument lists, writes only to a new or empty output folder,
  and compiles `raster.c` into a private temporary folder; the surface scripts load that library with
  `ctypes`. The local test servers (`smoke_embed.py`) bind to 127.0.0.1.
- **C.** `raster.c` clamps its pixel loops to the image for any input, including NaN and infinite
  coordinates, and receives arrays built by the scripts beside it. Since the review it also validates its
  arguments and triangle indices, checks every allocation and guards the growth of its buffer against
  overflow, and returns a status (0 ok, 1 invalid arguments, 2 out of memory) that the five surface scripts
  turn into an error. It renders the same frames bit for bit, and runs clean under AddressSanitizer and
  UndefinedBehaviorSanitizer on valid, invalid, NaN and oversized inputs.
- **Archives.** The six `stills.zip` files hold only PNG stills: no absolute paths, `..` entries or
  symlinks, and their CRCs check.
- **Dependencies.** `rebuild/requirements.txt` pinned Pillow 12.3.0, which has 42 published
  vulnerabilities fixed in 13.0.0. The pin is now Pillow 13.0.0; it renders the rebuild's frames
  pixel-identical to 12.3.0 (14 frames across all six surface scripts). NumPy 2.5.3 and imageio-ffmpeg 0.6.0
  have no known vulnerabilities.
- **Wheels in history.** The three macOS wheels that were in the tutorial (removed; still in the branch's
  history) are byte-identical to the files PyPI publishes.

## Repeat the checks

```sh
python3 -m pip install pip-audit
python3 -m pip_audit -r learning/tutorials/gluing-and-topologies/square-gluings/rebuild/requirements.txt --no-deps
git grep -nIE "innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|postMessage" -- learning ':!learning/released'
git grep -nIE "shell=True|os\.system|pickle|allow_pickle|yaml\.load|urlopen|extractall" -- learning ':!learning/released'
```
