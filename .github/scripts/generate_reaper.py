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

    # ── Grim Reaper (Image) ──
    # Dynamically load the image and embed it
    import base64
    img_path = os.path.join(os.path.dirname(__file__), "..", "..", "img", "grim_reaper.png")
    try:
        with open(img_path, "rb") as img_file:
            b64_data = base64.b64encode(img_file.read()).decode("utf-8")
        img_href = f"data:image/png;base64,{b64_data}"
    except Exception as e:
        print(f"[warn] Could not load reaper image: {e}")
        img_href = ""
    
    # We want the image to be centered and nicely sized over the squares
    # Original image is large, let's display it at 40x40 pixels, centered at (0,0)
    reaper_drawing = [
        f'<image href="{img_href}" x="-20" y="-20" width="40" height="40"/>'
    ]

    # Slash flash line (flickers at FRAME_DUR rate, same as movement)
    reaper_drawing.append(
      f'<line x1="-15" y1="-5" x2="15" y2="10" stroke="#00ff00" stroke-width="2.5" '
      f'stroke-linecap="round">'
      f'<animate attributeName="opacity" values="0;1;0" '
      f'keyTimes="0;0.08;0.45" dur="{fmt(FRAME_DUR)}" repeatCount="indefinite"/>'
      f'</line>'
    )

    # Wrap the drawing in a small scale/offset if needed, but x/y -20 centers it
    scaled_reaper = '<g>\n' + "\n".join(reaper_drawing) + '\n</g>'

    # The translation that drives the movement
    anim = (f'<animateTransform attributeName="transform" type="translate" '
            f'calcMode="discrete" '
            f'values="{";".join(pos_v)}" '
            f'keyTimes="{";".join(kts)}" '
            f'dur="{dur}" repeatCount="indefinite"/>')

    # Add the outer group to the main output
    a('<g>\n' + anim + '\n' + scaled_reaper + '\n</g>')

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
