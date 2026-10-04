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
    cell, gap, left, top = 12, 3, 40, 52
    weeks = cal["weeks"]
    W = left * 2 + len(weeks) * (cell + gap)
    H = top + 7 * (cell + gap) + 62
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
         f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117"/>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#30363d"/>',
         f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
         '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
         '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
         f'<text x="{W/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">'
         f'{html.escape(login)}@github: ~$ ./contributions.sh</text>']
    last_month = None
    for x, w in enumerate(weeks):
        days = w["contributionDays"]
        if days:
            m = datetime.date.fromisoformat(days[0]["date"]).strftime("%b")
            if m != last_month and x < len(weeks) - 1:
                p.append(f'<text x="{left + x*(cell+gap)}" y="{top-8}" fill="#7d8590" font-size="10">{m}</text>')
                last_month = m
        for d in days:
            lvl = LEVELS.get(d["contributionLevel"], 0)
            t = (x * 0.025) + d["weekday"] * 0.01
            cx, cy = left + x * (cell + gap), top + d["weekday"] * (cell + gap)
            p.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" rx="2" fill="{COLORS[lvl]}" opacity="0">'
                     f'<title>{d["date"]}: {d["contributionCount"]} contribution{"s" if d["contributionCount"] != 1 else ""}</title>'
                     f'<animate attributeName="opacity" from="0" to="1" begin="{t:.3f}s" dur="0.25s" fill="freeze"/></rect>')
    fy = top + 7 * (cell + gap) + 12
    p.append(f'<line x1="0" y1="{fy}" x2="{W}" y2="{fy}" stroke="#30363d"/>')
    msg = ("waiting for first daily run..." if placeholder
           else f'{cal["totalContributions"]} contributions in the last year')
    p.append(f'<text x="{left}" y="{fy+27}" fill="#7d8590" font-size="13">$ <tspan fill="#c9d1d9">{html.escape(msg)}</tspan></text>')
    lx = W - left - 5 * (cell + gap) - 70
    p.append(f'<text x="{lx}" y="{fy+27}" fill="#7d8590" font-size="11" text-anchor="end">less</text>')
    for i, c in enumerate(COLORS):
        p.append(f'<rect x="{lx+8+i*(cell+gap)}" y="{fy+16}" width="{cell}" height="{cell}" rx="2" fill="{c}"/>')
    p.append(f'<text x="{lx+16+5*(cell+gap)}" y="{fy+27}" fill="#7d8590" font-size="11">more</text>')
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
