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
    return ["".join(ch * 2 for ch in row) for row in grid]   # double width so letters look wide

def build_svg(text, handle):
    lines = make_lines(text)
    CW, CH = 9, 16
    W, H = max(len(l) for l in lines) * CW + 80, len(lines) * CH + 120
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/>'
         '<stop offset="1" stop-color="#0d1117"/></linearGradient>'
         f'<clipPath id="wipe"><rect x="0" y="40" height="{H}" width="0">'
         f'<animate attributeName="width" from="0" to="{W}" begin="0s" dur="1.6s" fill="freeze"/></rect></clipPath></defs>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#30363d"/>',
         f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
         '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
         '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
         f'<text x="{W/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">'
         f'{html.escape(handle)}@github: ~$ ./wordmark.sh --3d</text>',
         '<g clip-path="url(#wipe)">']
    for i, l in enumerate(lines):
        spans = "".join('<tspan fill="#e6edf3">S</tspan>' if c == "S"
                        else '<tspan fill="#22d3ee">+</tspan>' if c == "+" else " " for c in l)
        p.append(f'<text xml:space="preserve" x="40" y="{70 + i*CH}" font-size="14.5">{spans}</text>')
    p.append("</g></svg>")
    return "\n".join(p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="JANEK")
    ap.add_argument("--handle", default="janek")
    ap.add_argument("--out", default="wordmark.svg")
    a = ap.parse_args()
    open(a.out, "w", encoding="utf-8").write(build_svg(a.text, a.handle))
    print("wrote", a.out)
