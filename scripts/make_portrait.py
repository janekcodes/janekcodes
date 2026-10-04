#!/usr/bin/env python3
"""Turn a photo into an animated terminal-style ASCII portrait SVG.

Usage:  python scripts/make_portrait.py [--photo source-photo.png] [--handle janek]
                                        [--name Janek] [--crop L,T,R,B] [--out portrait.svg]
Needs:  pip install pillow numpy
Tip:    use a front-facing photo with a plain background. --crop picks the square-ish
        region that gets converted (default: whole photo).
"""
import argparse, html
import numpy as np
from PIL import Image, ImageFilter

COLS, ROWS = 100, 53           # 100*8px by 53*15px  ->  roughly square
RAMP = " `:-=+*cs#%@"

def ascii_rows(photo, crop=None):
    im = Image.open(photo).convert("RGB")
    if crop:
        im = im.crop(crop)
    im = im.resize((COLS * 4, ROWS * 4), Image.LANCZOS)
    a = np.asarray(im).astype(float) / 255
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    sat = (a.max(2) - a.min(2)) / (a.max(2) + 1e-6)
    # rough subject mask: dark or colourful pixels are "subject", flat light ones are background
    fg = ((lum < 0.36) | (sat > 0.27)).astype("uint8") * 255
    m = Image.fromarray(fg)
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(5))
    mask = np.asarray(m.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    sharp = Image.fromarray((lum * 255).astype("uint8")).filter(
        ImageFilter.UnsharpMask(radius=4, percent=160, threshold=1))
    lum2 = np.asarray(sharp).astype(float) / 255
    inside = mask > 0.5
    lo, hi = np.percentile(lum2[inside], 3), np.percentile(lum2[inside], 97)
    ln = np.clip((lum2 - lo) / (hi - lo), 0, 1)
    d = mask * (0.30 + 0.70 * ln ** 0.9)
    dg = np.asarray(Image.fromarray((d * 255).astype("uint8")).resize((COLS, ROWS), Image.BOX)).astype(float) / 255
    dg[dg < 0.14] = 0
    idx = (dg * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]

def build_svg(rows, handle, name):
    W, H = 840, 37 + len(rows) * 15 + 38
    step = 0.11
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/>'
         '<stop offset="1" stop-color="#0d1117"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#30363d"/>',
         f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
         '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
         '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
         f'<text x="{W/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">{html.escape(handle)}@github: ~$ ./portrait.sh</text>']
    for i, row in enumerate(rows):
        y, t = 37 + i * 15, i * step
        p.append(f'<clipPath id="r{i}"><rect x="20" y="{y}" height="15" width="0">'
                 f'<animate attributeName="width" from="0" to="800" begin="{t:.3f}s" dur="{step}s" fill="freeze"/></rect></clipPath>')
        p.append(f'<g clip-path="url(#r{i})"><text xml:space="preserve" x="20" y="{y+11.1:.1f}" fill="#c9d1d9" '
                 f'font-size="12.9" textLength="800" lengthAdjust="spacing">{html.escape(row)}</text></g>')
        p.append(f'<rect y="{y+1}" width="8" height="13" fill="#c9d1d9" opacity="0">'
                 f'<animate attributeName="x" from="20" to="820" begin="{t:.3f}s" dur="{step}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0.85" begin="{t:.3f}s"/>'
                 f'<set attributeName="opacity" to="0" begin="{t+step:.3f}s"/></rect>')
    fy = 37 + len(rows) * 15
    p.append(f'<line x1="0" y1="{fy}" x2="{W}" y2="{fy}" stroke="#30363d"/>')
    prompt = f"{handle}@github:~$ whoami "
    p.append(f'<text x="20" y="{fy+19}" xml:space="preserve" fill="#7d8590" font-size="13">{html.escape(prompt)}'
             f'<tspan fill="#c9d1d9">{html.escape(name)}</tspan></text>')
    cx = 20 + (len(prompt) + len(name) + 1) * 7.8
    p.append(f'<rect x="{cx:.0f}" y="{fy+7}" width="8" height="14" fill="#c9d1d9"><animate attributeName="opacity" '
             'values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>')
    p.append("</svg>")
    return "\n".join(p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default="source-photo.png")
    ap.add_argument("--handle", default="janek")
    ap.add_argument("--name", default="Janek")
    ap.add_argument("--crop", default="58,18,248,208", help="L,T,R,B in pixels, or 'none'")
    ap.add_argument("--out", default="portrait.svg")
    a = ap.parse_args()
    crop = None if a.crop == "none" else tuple(int(v) for v in a.crop.split(","))
    open(a.out, "w", encoding="utf-8").write(build_svg(ascii_rows(a.photo, crop), a.handle, a.name))
    print("wrote", a.out)
