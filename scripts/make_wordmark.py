#!/usr/bin/env python3
"""Generate an extruded 3D ASCII wordmark SVG (letters A-Z). No dependencies.

Usage:  python scripts/make_wordmark.py --text JANEK [--handle janek] [--out wordmark.svg]
Keep the text short (5-6 letters): the extruded letters get wide quickly.
"""
import argparse, html

FONT = {
 "A": [".###.","#...#","#...#","#####","#...#","#...#","#...#"],
 "B": ["####.","#...#","#...#","####.","#...#","#...#","####."],
 "C": [".####","#....","#....","#....","#....","#....",".####"],
 "D": ["####.","#...#","#...#","#...#","#...#","#...#","####."],
 "E": ["#####","#....","#....","####.","#....","#....","#####"],
 "F": ["#####","#....","#....","####.","#....","#....","#...."],
 "G": [".####","#....","#....","#.###","#...#","#...#",".###."],
 "H": ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
 "I": ["#####","..#..","..#..","..#..","..#..","..#..","#####"],
 "J": ["..###","...#.","...#.","...#.","...#.","#..#.",".##.."],
 "K": ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
 "L": ["#....","#....","#....","#....","#....","#....","#####"],
 "M": ["#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"],
 "N": ["#...#","##..#","#.#.#","#..##","#...#","#...#","#...#"],
 "O": [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
 "P": ["####.","#...#","#...#","####.","#....","#....","#...."],
 "Q": [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
 "R": ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
 "S": [".####","#....","#....",".###.","....#","....#","####."],
 "T": ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
 "U": ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
 "V": ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
 "W": ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
 "X": ["#...#","#...#",".#.#.","..#..",".#.#.","#...#","#...#"],
 "Y": ["#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."],
 "Z": ["#####","....#","...#.","..#..",".#...","#....","#####"],
}
PITCH, DEPTH = 7, 2

def make_lines(text):
    text = "".join(c for c in text.upper() if c in FONT)
    w = len(text) * PITCH - (PITCH - 5) + DEPTH
    grid = [[" "] * w for _ in range(7 + DEPTH)]
    for i, ch in enumerate(text):
        for r in range(7):
            for c in range(5):
                if FONT[ch][r][c] == "#":
                    for d in range(DEPTH, 0, -1):
                        if grid[r + d][i * PITCH + c + d] == " ":
                            grid[r + d][i * PITCH + c + d] = "+"
    for i, ch in enumerate(text):
        for r in range(7):
            for c in range(5):
                if FONT[ch][r][c] == "#":
                    grid[r][i * PITCH + c] = "S"
    rows = ["".join(ch * 2 for ch in row) for row in grid]   # double width so letters look wide
    return [r for row in rows for r in (row, row)]            # and double height

def build_svg(text, handle, aspect=0.7755, rock=True):
    """aspect = height/width of the panel. 0.7755 makes it the same height as portrait.svg
    when the README shows the portrait at width 370 and this at width 490."""
    lines = make_lines(text)
    CW, CH = 9, 16
    W = max(len(l) for l in lines) * CW + 80
    H = round(W * aspect)
    block_h = len(lines) * CH
    # centre the bright letter faces (the dim extrusion trails off to the lower-right,
    # so centring on it would make the word look shifted left and up)
    ink = [i for l in lines for i, c in enumerate(l) if c == "S"]
    x0 = (W - (max(ink) - min(ink) + 1) * CW) / 2 - min(ink) * CW
    face_rows = [r for r, l in enumerate(lines) if "S" in l]
    face_mid = (min(face_rows) + max(face_rows) + 1) / 2 * CH
    top = 30 + (H - 30) / 2 - face_mid            # centre the faces in the area under the title bar
    cx, cy = W / 2, 30 + (H - 30) / 2
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/>'
         '<stop offset="1" stop-color="#0d1117"/></linearGradient>'
         f'<clipPath id="wipe"><rect x="0" y="31" height="{H}" width="0">'
         f'<animate attributeName="width" from="0" to="{W}" begin="0s" dur="1.6s" fill="freeze"/></rect></clipPath></defs>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#30363d"/>',
         f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
         '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
         '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
         f'<text x="{W/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">'
         f'{html.escape(handle)}@github: ~$ ./wordmark.sh --3d</text>',
         '<g clip-path="url(#wipe)">',
         f'<g transform="translate({cx:.1f},{cy:.1f})"><g>']
    if rock:   # rock back and forth on the vertical axis: squeeze + lean, in sync
        p.append('<animateTransform attributeName="transform" type="scale" additive="replace" '
                 'values="0.86 1;1 1;0.86 1;1 1;0.86 1" keyTimes="0;0.25;0.5;0.75;1" dur="6s" begin="1.6s" repeatCount="indefinite" calcMode="spline" '
                 'keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/>')
        p.append('<animateTransform attributeName="transform" type="skewY" additive="sum" '
                 'values="-4;0;4;0;-4" keyTimes="0;0.25;0.5;0.75;1" dur="6s" begin="1.6s" repeatCount="indefinite" calcMode="spline" '
                 'keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/>')
    p.append(f'<g transform="translate({-cx:.1f},{-cy:.1f})">')
    for i, l in enumerate(lines):
        spans = "".join('<tspan fill="#e6edf3">S</tspan>' if c == "S"
                        else '<tspan fill="#39d353">+</tspan>' if c == "+" else " " for c in l)
        p.append(f'<text xml:space="preserve" x="{x0:.1f}" y="{top + 12 + i*CH:.1f}" font-size="14.5">{spans}</text>')
    p.append("</g></g></g></g></svg>")
    return "\n".join(p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="JANEK")
    ap.add_argument("--handle", default="janek")
    ap.add_argument("--out", default="wordmark.svg")
    ap.add_argument("--no-rock", action="store_true", help="disable the rocking animation")
    a = ap.parse_args()
    open(a.out, "w", encoding="utf-8").write(build_svg(a.text, a.handle, rock=not a.no_rock))
    print("wrote", a.out)
