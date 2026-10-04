#!/usr/bin/env python3
"""Build an animated terminal-style contribution heatmap from REAL GitHub data.

Usage:  GH_TOKEN=... python scripts/generate_heatmap.py <login> [out.svg]
        python scripts/generate_heatmap.py <login> out.svg --empty    (blank placeholder, no network)
No third-party packages needed. Run daily by .github/workflows/update-profile.yml.
"""
import json, os, sys, datetime, urllib.request, html

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{contributionCount contributionLevel date weekday}}}}}}"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-heatmap"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload or not payload.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {payload.get('errors') or 'user not found'}")
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def empty_calendar():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)   # back up to a Sunday
    weeks, d = [], start
    while d <= today:
        days = []
        for wd in range(7):
            if d <= today:
                days.append({"contributionCount": 0, "contributionLevel": "NONE", "date": d.isoformat(), "weekday": wd})
            d += datetime.timedelta(days=1)
        weeks.append({"contributionDays": days})
    return {"totalContributions": 0, "weeks": weeks}

def build_svg(cal, login, placeholder=False):
    """Transparent, theme-aware graph that blends into the page. The grid always fills a fixed
    860px-wide canvas (shown at width=860 in the README), so cells and text stay large.
    Cells pop in left-to-right, then a soft green glow band sweeps slowly across the whole grid."""
    W = 860
    left, right, top = 40, 12, 34
    weeks = cal["weeks"]
    pitch = (W - left - right) / len(weeks)
    cell = round(pitch * 0.80, 2)
    H = round(top + 7 * pitch + 52)
    grid_w, grid_h = len(weeks) * pitch, 7 * pitch
    reveal_end = len(weeks) * 0.02 + 0.5
    sans = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{sans}">',
         '<defs>'
         '<linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">'
         '<stop offset="0" stop-color="#7ee787" stop-opacity="0"/>'
         '<stop offset="0.5" stop-color="#7ee787" stop-opacity="0.65"/>'
         '<stop offset="1" stop-color="#7ee787" stop-opacity="0"/></linearGradient>']
    cells, clip = [], []
    last_month, last_lx = None, -99
    labels = []
    for x, w in enumerate(weeks):
        days = w["contributionDays"]
        if days:
            m = datetime.date.fromisoformat(days[0]["date"]).strftime("%b")
            if m != last_month and x - last_lx >= 3 and x < len(weeks) - 2:
                labels.append(f'<text class="t" x="{left + x*pitch:.1f}" y="{top-11}" font-size="13">{m}</text>')
                last_lx = x
            last_month = m
        for d in days:
            lvl = LEVELS.get(d["contributionLevel"], 0)
            n = d["contributionCount"]
            t = x * 0.02 + d["weekday"] * 0.012
            gx, gy = left + x * pitch, top + d["weekday"] * pitch
            cx, cy = gx + cell / 2, gy + cell / 2
            clip.append(f'<rect x="{gx:.2f}" y="{gy:.2f}" width="{cell}" height="{cell}" rx="2.5"/>')
            cells.append(
                f'<g transform="translate({cx:.2f},{cy:.2f})"><rect class="l{lvl}" x="{-cell/2}" y="{-cell/2}" '
                f'width="{cell}" height="{cell}" rx="2.5" opacity="0">'
                f'<title>{d["date"]}: {n} contribution{"s" if n != 1 else ""}</title>'
                f'<animateTransform attributeName="transform" type="scale" from="0.15" to="1" begin="{t:.3f}s" '
                'dur="0.45s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .9 .3 1.3"/>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{t:.3f}s" dur="0.3s" fill="freeze"/>'
                '</rect></g>')
    band = grid_w * 0.22
    p.append(f'<clipPath id="cells">{"".join(clip)}</clipPath></defs>')
    p.insert(1, '<style>'
         '.l0{fill:#ebedf0}.l1{fill:#9be9a8}.l2{fill:#40c463}.l3{fill:#30a14e}.l4{fill:#216e39}'
         '.t{fill:#656d76}.s{fill:#1f2328}'
         '@media (prefers-color-scheme: dark){'
         '.l0{fill:#161b22}.l1{fill:#0e4429}.l2{fill:#006d32}.l3{fill:#26a641}.l4{fill:#39d353}'
         '.t{fill:#7d8590}.s{fill:#e6edf3}}</style>')
    p += labels
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text class="t" x="{left-9}" y="{top + wd*pitch + cell/2 + 4.5:.1f}" font-size="12" text-anchor="end">{name}</text>')
    p += cells
    # the slow left-to-right sweep: one glow band, clipped to the cells, loops every 11s
    p.append(f'<g clip-path="url(#cells)"><rect x="{left-band:.1f}" y="{top-2}" width="{band:.1f}" height="{grid_h+4:.1f}" '
             'fill="url(#glow)" opacity="0">'
             f'<animate attributeName="x" values="{left-band:.1f};{left+grid_w:.1f};{left+grid_w:.1f}" keyTimes="0;0.72;1" '
             f'dur="11s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/>'
             f'<set attributeName="opacity" to="1" begin="{reveal_end:.2f}s"/></rect></g>')
    fy = top + 7 * pitch + 30
    msg = "waiting for first daily run..." if placeholder else f'{cal["totalContributions"]:,} contributions in the last year'
    p.append(f'<text class="s" x="{left}" y="{fy:.1f}" font-size="17" font-weight="600">{html.escape(msg)}</text>')
    lx = W - right - 5 * (pitch) - 32
    p.append(f'<text class="t" x="{lx:.1f}" y="{fy:.1f}" font-size="12" text-anchor="end">less</text>')
    for i in range(5):
        p.append(f'<rect class="l{i}" x="{lx+8+i*pitch:.1f}" y="{fy-11:.1f}" width="{cell}" height="{cell}" rx="2.5"/>')
    p.append(f'<text class="t" x="{lx+16+5*pitch:.1f}" y="{fy:.1f}" font-size="12">more</text>')
    p.append("</svg>")
    return "\n".join(p)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    login, out = args[0], (args[1] if len(args) > 1 else "contrib-heatmap.svg")
    empty = "--empty" in sys.argv
    cal = empty_calendar() if empty else fetch(login, os.environ["GH_TOKEN"])
    open(out, "w", encoding="utf-8").write(build_svg(cal, login, placeholder=empty))
    print("wrote", out)
