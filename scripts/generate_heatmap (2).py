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
    """Transparent contribution graph on a fixed 888x158 canvas (show it at width=860 in the README).
    Cells are 13px on a 16px grid. They pop in as a slow left-to-right cascade; days with
    contributions flash bright for a moment and then settle. Dark colours by default, light
    colours when the viewer's theme is light."""
    CELL, PITCH, LEFT, TOP = 13, 16, 34, 24
    COL_DELAY, ROW_DELAY = 0.065, 0.0358
    weeks = cal["weeks"]
    W, H = 888, 158
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
         '<style>'
         '.l0{fill:#161b22}.l1{fill:#0e4429}.l2{fill:#006d32}.l3{fill:#26a641}.l4{fill:#39d353}'
         'text.lbl{fill:#7d8590;font-size:13px;font-weight:600}'
         'text.total{fill:#e6edf3;font-size:15px;font-weight:700}'
         '.c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s ease-out both}'
         '.g{animation:pop .55s ease-out both,flash .7s ease-out both}'
         '@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}'
         '@keyframes flash{0%{filter:brightness(2.4)}45%{filter:brightness(2.4)}100%{filter:brightness(1)}}'
         '@media (prefers-color-scheme: light){'
         '.l0{fill:#ebedf0}.l1{fill:#9be9a8}.l2{fill:#40c463}.l3{fill:#30a14e}.l4{fill:#216e39}'
         'text.lbl{fill:#656d76}text.total{fill:#1f2328}}'
         '@media (prefers-reduced-motion: reduce){.c{opacity:1!important;animation:none!important}}'
         '</style>']
    last_month, last_x = None, -99
    for x, w in enumerate(weeks):
        days = w["contributionDays"]
        if days:
            m = datetime.date.fromisoformat(days[0]["date"]).strftime("%b")
            if m != last_month and x - last_x >= 3 and x < len(weeks) - 2:
                p.append(f'<text class="lbl" x="{LEFT + x*PITCH}" y="16">{m}</text>')
                last_x = x
            last_month = m
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text class="lbl" x="2" y="{TOP + wd*PITCH + 11}">{name}</text>')
    for x, w in enumerate(weeks):
        for d in w["contributionDays"]:
            lvl = LEVELS.get(d["contributionLevel"], 0)
            delay = x * COL_DELAY + d["weekday"] * ROW_DELAY
            cls = "c g" if lvl > 0 else "c e"
            p.append(f'<rect class="{cls} l{lvl}" x="{LEFT + x*PITCH}" y="{TOP + d["weekday"]*PITCH}" '
                     f'width="{CELL}" height="{CELL}" rx="2.5" style="animation-delay:{delay:.3f}s"/>')
    msg = "waiting for first daily run..." if placeholder else f'{cal["totalContributions"]:,} contributions in the last year'
    p.append(f'<text class="total" x="{LEFT}" y="152">{html.escape(msg)}</text>')
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
