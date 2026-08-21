#!/usr/bin/env python3
"""
film.py — render a built scene to a video.

  python3 scripts/film.py out/mirror --port 8127 --seconds 8
  python3 scripts/film.py out/petra --port 8125 --seconds 6 --width 1920 --fps 30

The inverse of scroll-scrub-pipeline: that one turns a film into a scroll page,
this turns a scroll page back into a film.

How, and why this way
---------------------
Every frame is a scroll position, and stills.py already solves the engine's
variables exactly for any position, so the frames are deterministic — no waiting
on eased motion to settle.

The naive loop would be one browser launch per frame, which at roughly six
seconds a launch is half an hour for a short clip. Instead this stacks N stills
as iframes down one tall page and takes a single full-page screenshot, then
slices it. Each iframe gets its own document, so each gets its own :root and its
own variables — which is the only reason this works at all.

Batch height is capped because a browser will not composite an arbitrarily tall
surface; 16384px is the usual limit, so the batch size is derived from that
rather than guessed.
"""
import argparse
import os
import shutil
import subprocess
import tempfile
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("needs pillow")

MAX_SURFACE = 15800          # a browser will composite this tall, verified
# but the real limit is documents, not pixels: each iframe instantiates the whole
# scene, so a batch of twenty was ~800 elements and the page never settled
MAX_IFRAMES = 8
CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("chrome", "chromium", "google-chrome"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("no Chromium-based browser found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", help="a built scene directory, e.g. out/mirror")
    ap.add_argument("--port", type=int, required=True, help="port already serving out_dir")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()

    browser = find_browser()
    n_frames = max(2, int(round(args.seconds * args.fps)))
    per_batch = max(1, min(MAX_IFRAMES, MAX_SURFACE // args.height))
    # absolute, and outside the directory being served: a browser profile inside
    # the document root is asking for trouble, and a relative --screenshot path is
    # resolved against the browser's cwd rather than ours
    scratch = os.path.abspath(os.path.join(args.out_dir, "_film"))
    os.makedirs(scratch, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="film-profile-")

    # read the scroll length straight from the compiled scene
    import json
    import re

    html = open(os.path.join(args.out_dir, "index.html"), encoding="utf-8").read()
    scene = json.loads(re.search(r"window\.__CINEMA_SCENE__ = (\{.*?\});", html, re.S).group(1))
    scroll = scene.get("scrollHeight", 3800)

    positions = [round(scroll * i / (n_frames - 1)) for i in range(n_frames)]

    print(f"  {n_frames} frames at {args.fps}fps ({args.seconds}s)")
    print(f"  {args.width}x{args.height}, scroll 0..{scroll}px")
    print(f"  {per_batch} frames per browser launch -> "
          f"{(n_frames + per_batch - 1) // per_batch} launches")

    # 1. solve the variables for every position
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "stills.py"), args.out_dir]
                   + [str(p) for p in positions],
                   check=True, stdout=subprocess.DEVNULL)

    # 2. stack each batch as iframes and grab one tall screenshot
    frame_no = 0
    for start in range(0, n_frames, per_batch):
        batch = positions[start:start + per_batch]
        rows = "\n".join(
            f'<iframe src="_still_{p}.html" width="{args.width}" '
            f'height="{args.height}" scrolling="no"></iframe>'
            for p in batch
        )
        page = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
            "html,body{margin:0;background:#000;font-size:0}"
            f"iframe{{border:0;display:block;width:{args.width}px;height:{args.height}px}}"
            "</style></head><body>" + rows + "</body></html>"
        )
        strip_name = f"_strip_{start}.html"
        with open(os.path.join(args.out_dir, strip_name), "w", encoding="utf-8") as fh:
            fh.write(page)

        shot = os.path.abspath(os.path.join(scratch, f"strip_{start}.png"))
        proc = subprocess.run([
            browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", f"--window-size={args.width},{len(batch)*args.height}",
            "--virtual-time-budget=30000",
            f"--user-data-dir={profile}",
            f"--screenshot={shot}", f"http://127.0.0.1:{args.port}/{strip_name}",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if not os.path.exists(shot):
            err = (proc.stderr or b"").decode(errors="replace").strip()
            msg = f"browser produced no screenshot for batch at {start}"
            if err:
                msg += " | browser said: " + err[-400:]
            sys.exit(msg)
        strip = Image.open(shot).convert("RGB")
        for i in range(len(batch)):
            top = i * args.height
            if top + args.height > strip.height:
                break
            strip.crop((0, top, args.width, top + args.height)).save(
                os.path.join(scratch, f"f_{frame_no:05d}.png"))
            frame_no += 1
        os.remove(shot)
        os.remove(os.path.join(args.out_dir, strip_name))
        print(f"    batch {start:4} -> {frame_no} frames")

    for p in positions:
        f = os.path.join(args.out_dir, f"_still_{p}.html")
        if os.path.exists(f):
            os.remove(f)

    if frame_no < 2:
        sys.exit("not enough frames rendered")

    # 3. encode
    out = args.out or os.path.join(args.out_dir, "film.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-framerate", str(args.fps),
        "-i", os.path.join(scratch, "f_%05d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", out,
    ], check=True)

    size = os.path.getsize(out)
    print(f"\n  {frame_no} frames encoded")
    print(f"  {out}  {size/1048576:.2f} MB")
    shutil.rmtree(profile, ignore_errors=True)
    if not args.keep_frames:
        shutil.rmtree(scratch, ignore_errors=True)
    else:
        print(f"  frames kept in {scratch}")


if __name__ == "__main__":
    main()
