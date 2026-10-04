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
    """Transparent, theme-aware graph that blends into the GitHub page (no window frame).
    Every cell pops in along a left-to-right wave, then a soft shimmer keeps sweeping across
    the active days."""
    cell, gap, left, top = 12, 3, 24, 30
    weeks = cal["weeks"]
    step = cell + gap
    W = left * 2 + len(weeks) * step
    H = top + 7 * step + 46
    reveal_end = len(weeks) * 0.022 + 0.45
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
         '<style>'
         '.l0{fill:#ebedf0}.l1{fill:#9be9a8}.l2{fill:#40c463}.l3{fill:#30a14e}.l4{fill:#216e39}'
         '.t{fill:#656d76}'
         '@media (prefers-color-scheme: dark){'
         '.l0{fill:#161b22}.l1{fill:#0e4429}.l2{fill:#006d32}.l3{fill:#26a641}.l4{fill:#39d353}.t{fill:#7d8590}}'
         '</style>']
    last_month = None
    for x, w in enumerate(weeks):
        days = w["contributionDays"]
        if days:
            m = datetime.date.fromisoformat(days[0]["date"]).strftime("%b")
            if m != last_month and x < len(weeks) - 1:
                p.append(f'<text class="t" x="{left + x*step}" y="{top-10}" font-size="10">{m}</text>')
                last_month = m
        for d in days:
            lvl = LEVELS.get(d["contributionLevel"], 0)
            n = d["contributionCount"]
            t = x * 0.022 + d["weekday"] * 0.012
            cx, cy = left + x * step + cell / 2, top + d["weekday"] * step + cell / 2
            anim = (f'<animateTransform attributeName="transform" type="scale" from="0.15" to="1" begin="{t:.3f}s" '
                    'dur="0.4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .9 .3 1.3"/>'
                    f'<animate attributeName="opacity" from="0" to="1" begin="{t:.3f}s" dur="0.3s" fill="freeze"/>')
            if lvl > 0:   # shimmer wave: dips in brightness, sweeping left to right
                anim += (f'<animate attributeName="opacity" values="1;0.4;1;1" keyTimes="0;0.1;0.28;1" dur="6s" '
                         f'begin="{reveal_end + x*0.05:.2f}s" repeatCount="indefinite"/>')
            p.append(f'<g transform="translate({cx},{cy})"><rect class="l{lvl}" x="{-cell/2}" y="{-cell/2}" '
                     f'width="{cell}" height="{cell}" rx="2" opacity="0">'
                     f'<title>{d["date"]}: {n} contribution{"s" if n != 1 else ""}</title>{anim}</rect></g>')
    fy = top + 7 * step + 18
    msg = ("waiting for first daily run..." if placeholder
           else f'{cal["totalContributions"]} contributions in the last year')
    p.append(f'<text class="t" x="{left}" y="{fy}" font-size="12">{html.escape(msg)}</text>')
    lx = W - left - 5 * step - 28
    p.append(f'<text class="t" x="{lx}" y="{fy}" font-size="10" text-anchor="end">less</text>')
    for i in range(5):
        p.append(f'<rect class="l{i}" x="{lx+8+i*step}" y="{fy-10}" width="{cell}" height="{cell}" rx="2"/>')
    p.append(f'<text class="t" x="{lx+16+5*step}" y="{fy}" font-size="10">more</text>')
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
