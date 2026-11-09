"""Generate assets/top-langs.svg and assets/activity.svg from the GitHub GraphQL API."""
import json, os, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "jonathan-is-working")
TOKEN = os.environ["GITHUB_TOKEN"]
ACCENT, TEXT, MUTED, GRID = "#A78BFA", "#8B949E", "#6E7681", "#30363D"
FONT = "font-family=\"-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif\""

Q = """query($login:String!){ user(login:$login){
  repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100){
    nodes{ languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } }
  contributionsCollection{ contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }"""

req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": Q, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
data = json.load(urllib.request.urlopen(req))["data"]["user"]

# ---- Top languages ----
langs = {}
for repo in data["repositories"]["nodes"]:
    for e in repo["languages"]["edges"]:
        n = e["node"]["name"]
        langs.setdefault(n, [0, e["node"]["color"] or TEXT])[0] += e["size"]
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
total = sum(v[0] for _, v in top) or 1
W, BAR_X, BAR_W = 360, 25, 310
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="165" viewBox="0 0 {W} 165">',
       f'<text x="25" y="35" fill="{ACCENT}" font-size="18" font-weight="600" {FONT}>Top Languages</text>',
       f'<mask id="m"><rect x="{BAR_X}" y="55" width="{BAR_W}" height="8" rx="4" fill="#fff"/></mask>',
       '<g mask="url(#m)">']
x = BAR_X
for name, (size, color) in top:
    w = size / total * BAR_W
    out.append(f'<rect x="{x:.2f}" y="55" width="{w + 0.5:.2f}" height="8" fill="{color}"/>')
    x += w
out.append("</g>")
for i, (name, (size, color)) in enumerate(top):
    cx, cy = BAR_X + (i % 2) * 160, 92 + (i // 2) * 25
    out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>'
               f'<text x="{cx + 16}" y="{cy}" fill="{TEXT}" font-size="12" {FONT}>{name} {size / total * 100:.1f}%</text>')
out.append("</svg>")
open("assets/top-langs.svg", "w").write("\n".join(out))

# ---- Activity graph (last 31 days) ----
days = [d for w in data["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]][-31:]
W, H, L, R, T, B = 1000, 300, 50, 20, 30, 45
pw, ph = W - L - R, H - T - B
mx = max(max(d["contributionCount"] for d in days), 1)
step = 1 if mx <= 5 else -(-mx // 5)
top_v = -(-mx // step) * step
px = lambda i: L + i * pw / (len(days) - 1)
py = lambda v: T + ph - v / top_v * ph
pts = [(px(i), py(d["contributionCount"])) for i, d in enumerate(days)]
line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
g = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     f'<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".35"/>'
     f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient></defs>']
for v in range(0, top_v + 1, step):
    g.append(f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID}" stroke-dasharray="3 4"/>'
             f'<text x="{L - 10}" y="{py(v) + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="12" {FONT}>{v}</text>')
for i, d in enumerate(days):
    if i % 3 == 0:
        g.append(f'<text x="{px(i):.1f}" y="{H - 18}" text-anchor="middle" fill="{MUTED}" font-size="12" {FONT}>{date.fromisoformat(d["date"]).day}</text>')
g.append(f'<polygon points="{L},{T + ph} {line} {W - R},{T + ph}" fill="url(#a)"/>')
g.append(f'<polyline points="{line}" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-linejoin="round"/>')
g += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{ACCENT}"/>' for x, y in pts]
g.append("</svg>")
open("assets/activity.svg", "w").write("\n".join(g))
print("ok", [n for n, _ in top], sum(d["contributionCount"] for d in days))
