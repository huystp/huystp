#!/usr/bin/env python3
"""
SMIL-animated Grim Reaper SVG for GitHub contribution graph.
Pure SVG/SMIL - no JavaScript - works in GitHub README img tags.
"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta

USERNAME  = os.environ.get("GITHUB_USER", "huystp")
TOKEN     = os.environ.get("GITHUB_TOKEN", "")

CELL      = 11
GAP       = 3
STEP      = CELL + GAP        # 14 px
WEEKS     = 53
DAYS      = 7
PAD_LEFT  = 28
HEADER_H  = 26
FRAME_DUR = 0.12              # seconds per cell

BG        = "#0d1117"
COLORS    = ["#161b22","#0e4429","#006d32","#26a641","#39d353"]
SLASHED   = ["#200000","#1a1000","#091a00","#122000","#0a2a08"]
TXT       = "#8b949e"
BORDER    = "#21262d"


# ── GitHub API ────────────────────────────────────────────────────────────────

def fetch_contributions():
    q = """query($l:String!){user(login:$l){contributionsCollection{
           contributionCalendar{weeks{contributionDays{contributionCount}}}}}}"""
    body = json.dumps({"query": q, "variables": {"l": USERNAME}}).encode()
    req  = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "reaper-svg"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        weeks = data["data"]["user"]["contributionsCollection"] \
                    ["contributionCalendar"]["weeks"]
        grid = []
        for w in weeks:
            col = [d["contributionCount"] for d in w["contributionDays"]]
            while len(col) < DAYS: col.append(0)
            grid.append(col[:DAYS])
        while len(grid) < WEEKS: grid.append([0]*DAYS)
        return grid[:WEEKS]
    except Exception as e:
        print(f"[warn] {e} — using demo data")
        import random; random.seed(42)
        return [[random.choices([0,1,2,5,10],[40,20,20,12,8])[0]
                 for _ in range(DAYS)] for _ in range(WEEKS)]


def lv(n):
    if n==0: return 0
    if n<=2: return 1
    if n<=5: return 2
    if n<=9: return 3
    return 4

def center(w, d):
    return PAD_LEFT + w*STEP + CELL//2, HEADER_H + d*STEP + CELL//2

def fmt(s): return f"{s:.4f}s"


# ── SVG generation ────────────────────────────────────────────────────────────

def generate(grid):
    W = PAD_LEFT + WEEKS*STEP + 4
    H = HEADER_H + DAYS*STEP  + 4

    # Traversal order: column-by-column, top-to-bottom
    path = [(w, d) for w in range(len(grid)) for d in range(DAYS)]
    n    = len(path)
    dur  = fmt(n * FRAME_DUR)
    total_s = n * FRAME_DUR

    # keyTimes for reaper position  (n+1 points, last wraps to start)
    kts   = [f"{i/n:.4f}" for i in range(n)] + ["1.0000"]
    pos_v = [f"{center(w,d)[0]},{center(w,d)[1]}" for (w,d) in path]
    pos_v.append(pos_v[0])

    out = []
    a = out.append   # shorthand

    # ── Background ──────────────────────────────────────────────────────────
    a(f'<rect width="{W}" height="{H}" fill="{BG}" rx="6"/>')

    # ── Month labels ─────────────────────────────────────────────────────────
    today = datetime.utcnow().date()
    start = today - timedelta(weeks=WEEKS)
    prev  = None
    for w in range(WEEKS):
        dt = start + timedelta(weeks=w)
        if dt.month != prev:
            a(f'<text x="{PAD_LEFT+w*STEP}" y="{HEADER_H-5}" '
              f'fill="{TXT}" font-size="9" font-family="monospace">'
              f'{dt.strftime("%b")}</text>')
            prev = dt.month

    # ── Day-of-week labels ───────────────────────────────────────────────────
    for i, name in enumerate(["","Mon","","Wed","","Fri",""]):
        if name:
            y = HEADER_H + i*STEP + CELL - 1
            a(f'<text x="{PAD_LEFT-4}" y="{y}" fill="{TXT}" '
              f'font-size="8" font-family="monospace" text-anchor="end">'
              f'{name}</text>')

    # ── Cells with SMIL colour animation ────────────────────────────────────
    pos_idx = {cell: i for i, cell in enumerate(path)}
    for w, col in enumerate(grid):
        for d, cnt in enumerate(col):
            x = PAD_LEFT + w*STEP
            y = HEADER_H + d*STEP
            c0 = COLORS[lv(cnt)]
            c1 = SLASHED[lv(cnt)]
            fi = pos_idx[(w, d)] / n          # fraction when slashed
            # 3-stop discrete: original → slashed → original (next loop)
            kts_c = f"0;{fi:.4f};1.0000"
            vals_c = f"{c0};{c1};{c0}"
            a(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
              f'rx="2" fill="{c0}" stroke="{BORDER}" stroke-width="0.5">'
              f'<animate attributeName="fill" calcMode="discrete" '
              f'values="{vals_c}" keyTimes="{kts_c}" '
              f'dur="{dur}" repeatCount="indefinite"/>'
              f'</rect>')

    # ── Grim Reaper (drawn centred at 0,0; translated by animateTransform) ──
    # Robe
    a('<polygon points="-4,8 4,8 3,-1 -3,-1" fill="#1a1a2e" stroke="#444" stroke-width="0.5"/>')
    # Hood
    a('<polygon points="0,-12 -6,-1 6,-1" fill="#111" stroke="#444" stroke-width="0.5"/>')
    # Scythe handle
    a('<line x1="3" y1="-9" x2="7" y2="8" stroke="#999" stroke-width="1.2" stroke-linecap="round"/>')
    # Scythe blade (static curve)
    a('<path d="M3,-9 Q-6,-17 -4,-4" stroke="#cc2222" stroke-width="2.0" fill="none" stroke-linecap="round"/>')
    # Eye glow with pulse
    a('<circle cx="0" cy="-5" r="1.4" fill="#ff3300">'
      '<animate attributeName="opacity" values="0.6;1;0.6" dur="0.8s" repeatCount="indefinite"/>'
      '</circle>')
    # Slash flash line (flickers at FRAME_DUR rate, same as movement)
    a(f'<line x1="-9" y1="-3" x2="9" y2="5" stroke="#ff3300" stroke-width="1.4" '
      f'stroke-linecap="round">'
      f'<animate attributeName="opacity" values="0;1;0" '
      f'keyTimes="0;0.08;0.45" dur="{fmt(FRAME_DUR)}" repeatCount="indefinite"/>'
      f'</line>')

    # The translation that drives all of the above
    a(f'<animateTransform attributeName="transform" type="translate" '
      f'calcMode="discrete" '
      f'values="{";".join(pos_v)}" '
      f'keyTimes="{";".join(kts)}" '
      f'dur="{dur}" repeatCount="indefinite"/>')

    # Wrap everything reaper-related in a single <g>
    reaper_start = out.index(
        '<polygon points="-4,8 4,8 3,-1 -3,-1" fill="#1a1a2e" stroke="#444" stroke-width="0.5"/>')
    reaper_parts  = out[reaper_start:]
    out           = out[:reaper_start]
    out.append('<g>' + "".join(reaper_parts) + '</g>')

    body = "\n  ".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'  {body}\n</svg>\n')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 \
               else "dist/github-contribution-grid-reaper.svg"
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    print(f"[info] Fetching contributions for {USERNAME} …")
    grid = fetch_contributions()
    print(f"[info] Building SVG ({WEEKS} weeks × {DAYS} days) …")
    svg = generate(grid)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[ok]  Saved → {out_path}")
