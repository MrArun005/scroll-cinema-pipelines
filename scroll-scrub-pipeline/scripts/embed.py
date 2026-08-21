#!/usr/bin/env python3
"""
embed.py — fold a frame sequence into a single self-contained HTML file.

  python3 embed.py page.html frames/ out.html

The page must contain the placeholder `__FRAMES__` where the base64 array
goes, and read `TOTAL` from that array's length:

    const B64 = __FRAMES__;
    const TOTAL = B64.length;
    img.src = "data:image/webp;base64," + B64[i];

Why: no server, no file paths, no network. One tap opens it on a phone.
Base64 adds ~33%, so keep the source frames under ~700 KB total.
"""
import base64, glob, os, sys

if len(sys.argv) != 4:
    sys.exit(__doc__)

page, frame_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]

frames = sorted(glob.glob(os.path.join(frame_dir, "*.webp"))) or \
         sorted(glob.glob(os.path.join(frame_dir, "*.jpg")))
if not frames:
    sys.exit(f"no frames found in {frame_dir}")

raw = sum(os.path.getsize(f) for f in frames)
arr = "[" + ",".join(
    '"' + base64.b64encode(open(f, "rb").read()).decode() + '"'
    for f in frames) + "]"

html = open(page).read()
if "__FRAMES__" not in html:
    sys.exit("page has no __FRAMES__ placeholder")

open(out, "w").write(html.replace("__FRAMES__", arr))

size = os.path.getsize(out)
print(f"frames : {len(frames)}")
print(f"raw    : {raw//1024} KB")
print(f"output : {out}  ({size//1024} KB)")
if size > 1_500_000:
    print("\nWARNING: over 1.5 MB. Drop fps or width — this is slow to open on mobile data.")
