#!/usr/bin/env python3
"""
Take screenshots of the T3DT dashboard using headless Chrome,
then stitch into an animated GIF using Pillow.
"""
import subprocess, time, os
from pathlib import Path
from PIL import Image

ROOT  = Path(__file__).parent.parent          # Tri-Temporal-Digital-Twin/
DOCS  = Path(__file__).parent                 # Tri-Temporal-Digital-Twin/docs/
HTML  = ROOT / "index.html"
URL   = f"file://{HTML.resolve()}"
CHROME = "/usr/bin/google-chrome"
WIDTH, HEIGHT = 1440, 850
TIMEOUT = 40   # seconds per Chrome invocation

def headless_shot(label: str, virtual_ms: int = 2000) -> Path:
    out = DOCS / f"{label}.png"
    cmd = [
        CHROME,
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        f"--window-size={WIDTH},{HEIGHT}",
        f"--screenshot={out}",
        f"--virtual-time-budget={virtual_ms}",
        URL,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {label} – Chrome took too long")
    return out

# ── 1. Static screenshots at different virtual-time budgets ─────────────────
shots = [
    ("screenshot_overview",  500),    # initial load
    ("screenshot_running",  8000),    # after physics ticks
    ("screenshot_orbit",   14000),    # orbits drawn
    ("screenshot_eps",     20000),    # EPS data populated
]

print(f"Target URL: {URL}")
print()
for label, vt in shots:
    print(f"Capturing {label} (virtual-time={vt}ms)...")
    p = headless_shot(label, vt)
    size = p.stat().st_size // 1024 if p.exists() else 0
    print(f"  → {p.name}  ({size} KB)")

# ── 2. Animated GIF from several frames ─────────────────────────────────────
gif_configs = [
    ("_f0",  1000),
    ("_f1",  4000),
    ("_f2",  8000),
    ("_f3", 12000),
    ("_f4", 16000),
    ("_f5", 20000),
]

print("\nCapturing GIF frames...")
gif_paths = []
for lbl, vt in gif_configs:
    p = headless_shot(lbl, vt)
    if p.exists() and p.stat().st_size > 10_000:
        gif_paths.append(p)
        print(f"  frame {lbl} OK ({p.stat().st_size//1024} KB)")
    else:
        print(f"  frame {lbl} FAILED or empty")

if len(gif_paths) >= 2:
    print("\nStitching GIF...")
    GIF_W = 960
    GIF_H = int(HEIGHT * GIF_W / WIDTH)
    frames = []
    for p in gif_paths:
        img = Image.open(p).convert("RGB").resize((GIF_W, GIF_H), Image.LANCZOS)
        frames.append(img)

    gif_out = DOCS / "dashboard_demo.gif"
    frames[0].save(
        gif_out,
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
        optimize=True,
    )
    print(f"  GIF saved → {gif_out}  ({gif_out.stat().st_size//1024} KB)")

    # Clean up temp frames
    for p in gif_paths:
        p.unlink(missing_ok=True)
else:
    print("Not enough frames for GIF.")

print("\nFinal assets:")
for f in sorted(DOCS.iterdir()):
    if not f.name.startswith("_") and f.suffix in (".png", ".gif", ".py"):
        print(f"  {f.name}  ({f.stat().st_size//1024} KB)")
