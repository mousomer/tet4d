"""Regenerate the demo's RLE coastline asset from locally installed Basemap data.
Data source: GSHHG, LGPL-3.0-or-later. Requires basemap and pillow.
Run: python generate_landmask.py
"""
import base64
import json
from pathlib import Path
from mpl_toolkits.basemap import Basemap
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 720, 360

def generate_bits():
    globe = Basemap(projection="cyl", llcrnrlon=-180, urcrnrlon=180,
                    llcrnrlat=-90, urcrnrlat=90, resolution="l")
    raster = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(raster)
    for (lons, lats), kind in zip(globe.coastpolygons, globe.coastpolygontypes):
        vertices = [((lon+180)/360*(WIDTH-1), (90-lat)/180*(HEIGHT-1))
                    for lon,lat in zip(lons,lats)]
        if len(vertices)>2: draw.polygon(vertices, fill=255 if int(kind)%2 else 0)
    return [1 if px>127 else 0 for px in raster.getdata()]

def encode(bits):
    runs=[]; current=bits[0]; length=0
    for bit in bits:
        if bit!=current:
            while length>255:
                runs.extend([255,0]);length-=255
            runs.append(length);current=bit;length=1
        else: length+=1
    while length>255:
        runs.extend([255,0]);length-=255
    runs.append(length)
    return base64.b64encode(bytes([bits[0]]+runs)).decode("ascii")

def main():
    payload=encode(generate_bits())
    output=Path(__file__).with_name("gshhg_landmask.generated.js")
    header = (
        "/* Generated GSHHG low-resolution mask; data LGPL-3.0-or-later.\n"
        " * Provenance: https://www.soest.hawaii.edu/wessel/gshhg/\n"
        " * Rebuild with python generate_landmask.py; see COASTLINE_DATA_LICENSE.md.\n"
        " */\n"
    )
    text = header + "window.EARTH_S2_GSHHG_MASK_B64 = " + json.dumps(payload) + ";\n"
    output.write_text(text,encoding="utf-8")
    print(f"Wrote {output}; {len(payload)} encoded characters")

if __name__=="__main__": main()
