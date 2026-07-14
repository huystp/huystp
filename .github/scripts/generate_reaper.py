#!/usr/bin/env python3
"""
SMIL-animated Grim Reaper SVG for GitHub contribution graph.
Pixel-art character drawn with pure SVG rects - no JS, no external images.
Character hunts green contribution cells like a snake.
"""
import json, os, sys, urllib.request, random
from datetime import datetime, timedelta

USERNAME  = os.environ.get("GITHUB_USER", "huystp")
TOKEN     = os.environ.get("GITHUB_TOKEN", "")

CELL      = 11
GAP       = 3
STEP      = CELL + GAP
WEEKS     = 53
DAYS      = 7
PAD_LEFT  = 28
HEADER_H  = 26
FRAME_DUR = 0.14   # seconds per step

BG        = "#0d1117"
COLORS    = ["#161b22","#0e4429","#006d32","#26a641","#39d353"]
SLASHED   = ["#1a0000","#1a1000","#091500","#102000","#082208"]
TXT       = "#8b949e"
BORDER    = "#21262d"

# ── Pixel-art Grim Reaper  (12 cols × 18 rows, 0 = transparent) ──────────────
P = {
    1: "#130820",   # darkest purple shadow
    2: "#3b1468",   # dark purple robe
    3: "#5c2e9c",   # medium purple highlight
    4: "#c8c8d0",   # skull gray-white
    5: "#ff2200",   # red glowing eyes
    6: "#5c3a1e",   # scythe handle brown
    7: "#4477bb",   # scythe blade blue
    8: "#88bbee",   # scythe blade shine
    9: "#0a0a0a",   # near-black
}
SPRITE = [
    [0,0,8,7,7,6,0,0,0,0,0,0],
    [0,8,7,7,6,2,2,2,0,0,0,0],
    [0,0,8,6,2,2,2,2,2,0,0,0],
    [0,0,6,6,2,4,4,4,2,2,0,0],
    [0,0,0,6,2,4,5,4,5,4,2,0],
    [0,0,0,0,2,4,4,9,4,4,2,0],
    [0,0,0,0,2,2,4,4,4,2,2,0],
    [0,0,0,1,2,2,2,2,2,2,3,0],
    [0,0,1,2,2,2,2,2,2,3,3,0],
    [0,1,2,2,2,2,2,2,3,3,0,0],
    [1,2,2,2,2,0,2,2,2,3,0,0],
    [2,2,2,2,0,0,0,2,2,3,0,0],
    [0,2,2,1,0,0,0,0,2,2,0,0],
    [0,0,2,1,0,0,0,0,1,2,0,0],
    [0,0,2,1,0,0,0,0,1,2,0,0],
    [0,0,2,2,1,0,0,1,2,2,0,0],
    [0,1,2,2,2,0,1,2,2,2,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0],
]
PX    = 3                              # pixels per sprite pixel
SP_W  = len(SPRITE[0]) * PX           # 36
SP_H  = len(SPRITE)    * PX           # 54
HW    = SP_W // 2
HH    = SP_H // 2


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
        weeks = (data["data"]["user"]["contributionsCollection"]
                     ["contributionCalendar"]["weeks"])
        grid = []
        for w in weeks:
            col = [d["contributionCount"] for d in w["contributionDays"]]
            while len(col) < DAYS: col.append(0)
            grid.append(col[:DAYS])
        while len(grid) < WEEKS: grid.append([0]*DAYS)
        return grid[:WEEKS]
    except Exception as e:
        print(f"[warn] {e} — using demo data")
        random.seed(77)
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


# ── Pathfinding (hunts green cells like a snake) ──────────────────────────────
def build_path(grid):
    """Greedy nearest-neighbor: hunt every green cell, step by step."""
    green = {(w, d) for w in range(len(grid))
             for d in range(DAYS) if grid[w][d] > 0}

    random.seed(42)
    path  = []
    curr  = (0, 3)   # start near left-middle

    while green:
        # nearest green cell (Manhattan)
        tgt = min(green, key=lambda t: abs(t[0]-curr[0]) + abs(t[1]-curr[1]))
        # walk toward target one step at a time
        while curr != tgt:
            w, d   = curr
            tw, td = tgt
            moves  = []
            if w < tw: moves.append((w+1, d))
            if w > tw: moves.append((w-1, d))
            if d < td: moves.append((w, d+1))
            if d > td: moves.append((w, d-1))
            # small random chance to juke sideways (organic look)
            if random.random() < 0.25:
                moves = [random.choice(moves)]
            curr = random.choice(moves)
            path.append(curr)
        green.discard(tgt)

    return path if path else [(w, 0) for w in range(WEEKS)]


# ── Sprite SVG builder ────────────────────────────────────────────────────────
def sprite_svg():
    parts = []
    for ri, row in enumerate(SPRITE):
        for ci, code in enumerate(row):
            if code == 0: continue
            x = ci * PX - HW
            y = ri * PX - HH
            parts.append(f'<rect x="{x}" y="{y}" width="{PX}" height="{PX}" fill="{P[code]}"/>')
    return "\n".join(parts)


# ── Main SVG generation ───────────────────────────────────────────────────────
def generate(grid):
    W = PAD_LEFT + WEEKS*STEP + 4
    H = HEADER_H + DAYS*STEP  + 4

    path = build_path(grid)
    n    = len(path)
    dur  = fmt(n * FRAME_DUR)

    kts   = [f"{i/n:.4f}" for i in range(n)] + ["1.0000"]
    pos_v = [f"{center(w,d)[0]},{center(w,d)[1]}" for (w,d) in path]
    pos_v.append(pos_v[0])

    out = []
    a   = out.append

    # Background
    a(f'<rect width="{W}" height="{H}" fill="{BG}" rx="6"/>')

    # Month labels
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

    # Day-of-week labels
    for i, name in enumerate(["","Mon","","Wed","","Fri",""]):
        if name:
            y = HEADER_H + i*STEP + CELL - 1
            a(f'<text x="{PAD_LEFT-4}" y="{y}" fill="{TXT}" '
              f'font-size="8" font-family="monospace" text-anchor="end">'
              f'{name}</text>')

    # Contribution cells with slash animation
    visited = {}
    for i, cell in enumerate(path):
        if cell not in visited:
            visited[cell] = i

    for w, col in enumerate(grid):
        for d, cnt in enumerate(col):
            x  = PAD_LEFT + w*STEP
            y  = HEADER_H + d*STEP
            c0 = COLORS[lv(cnt)]
            c1 = SLASHED[lv(cnt)]
            if (w, d) in visited:
                fi = visited[(w, d)] / n
                a(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                  f'rx="2" fill="{c0}" stroke="{BORDER}" stroke-width="0.5">'
                  f'<animate attributeName="fill" calcMode="discrete" '
                  f'values="{c0};{c1};{c0}" keyTimes="0;{fi:.4f};1.0000" '
                  f'dur="{dur}" repeatCount="indefinite"/>'
                  f'</rect>')
            else:
                a(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                  f'rx="2" fill="{c0}" stroke="{BORDER}" stroke-width="0.5"/>')

    # Grim Reaper — pixel art drawn as SVG rects
    # Slash flash line (green, flickers on each step)
    flash = (f'<line x1="-{HW+4}" y1="{HH//2}" x2="{HW+4}" y2="-{HH//2}" '
             f'stroke="#00ff77" stroke-width="2.5" stroke-linecap="round">'
             f'<animate attributeName="opacity" values="0;1;0" '
             f'keyTimes="0;0.07;0.4" dur="{fmt(FRAME_DUR)}" repeatCount="indefinite"/>'
             f'</line>')

    # Eye glow pulse (on top of sprite)
    glow = ('<circle cx="0" cy="-10" r="3" fill="#ff2200" opacity="0">'
            '<animate attributeName="opacity" values="0;0.6;0" '
            'dur="0.8s" repeatCount="indefinite"/>'
            '</circle>')

    reaper_g = (
        '<g>\n'
        f'<animateTransform attributeName="transform" type="translate" '
        f'calcMode="discrete" values="{";".join(pos_v)}" '
        f'keyTimes="{";".join(kts)}" dur="{dur}" repeatCount="indefinite"/>\n'
        + sprite_svg() + '\n'
        + flash + '\n'
        + glow + '\n'
        '</g>'
    )
    a(reaper_g)

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
    print(f"[info] Building SVG with pixel-art reaper …")
    svg = generate(grid)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    size_kb = len(svg) // 1024
    print(f"[ok]  Saved → {out_path}  ({size_kb} KB)")
