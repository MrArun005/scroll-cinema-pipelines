#!/usr/bin/env python3
"""
analyse.py — inspect a video and emit the ffmpeg settings build.sh should use.

  python3 analyse.py input.mp4              # human-readable report
  python3 analyse.py input.mp4 --emit       # shell vars for build.sh

Decides three things:
  1. Is there a corner watermark, and where  -> DELOGO
  2. How bright is the text zone             -> GRADE strength
  3. Is the motion fast or slow              -> FPS_MIN
"""
import argparse, json, os, subprocess, sys, tempfile

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("pip install pillow numpy --break-system-packages")


def probe(v):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-show_entries", "format=duration", "-of", "json", v],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    n, den = s["r_frame_rate"].split("/")
    return (int(s["width"]), int(s["height"]),
            float(d["format"]["duration"]), int(n) / int(den))


def frames(v, n=8):
    d = tempfile.mkdtemp()
    _, _, dur, _ = probe(v)
    out = []
    for i in range(n):
        t = dur * i / (n - 1) * 0.98
        p = os.path.join(d, f"{i:02d}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t),
                        "-i", v, "-frames:v", "1", p], check=True)
        out.append(np.asarray(Image.open(p).convert("RGB"), dtype=float))
    return out


def lum(a):
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def watermark_sheet(video, out="watermark-corners.png"):
    """
    Auto-detection is unreliable: static scenery looks exactly like a static
    watermark. So show the four corners at 2x and let a human read the box off
    the grid. Takes ten seconds and is right every time.
    """
    arrs = frames(video, 3)
    a = arrs[-1]                      # last frame: marks are usually most visible
    h, w = a.shape[:2]
    ch, cw = int(h * .28), int(w * .28)
    tiles = {
        "top-left":     (0, ch, 0, cw),
        "top-right":    (0, ch, w - cw, w),
        "bottom-left":  (h - ch, h, 0, cw),
        "bottom-right": (h - ch, h, w - cw, w),
    }
    from PIL import ImageDraw
    scale = 2
    sheet = Image.new("RGB", (cw * scale * 2 + 30, ch * scale * 2 + 60), (12, 12, 14))
    d = ImageDraw.Draw(sheet)
    for i, (name, (y0, y1, x0, x1)) in enumerate(tiles.items()):
        tile = Image.fromarray(a[y0:y1, x0:x1].astype("uint8"))
        tile = tile.resize((cw * scale, ch * scale), Image.NEAREST)
        px = 10 + (i % 2) * (cw * scale + 10)
        py = 30 + (i // 2) * (ch * scale + 30)
        sheet.paste(tile, (px, py))
        d.text((px, py - 16), f"{name}   origin x={x0} y={y0}", fill=(200, 200, 210))
    sheet.save(out)
    return out, {k: (v[2], v[0]) for k, v in tiles.items()}


def text_zone(arrs):
    vals = []
    for a in arrs:
        L = lum(a)
        z = L[:, :int(L.shape[1] * .40)]
        vals.append((z.mean(), 100 * (z > 150).mean()))
    return max(v[0] for v in vals), max(v[1] for v in vals)


def motion(v):
    d = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v,
                    "-vf", "fps=8,scale=320:-2", f"{d}/%03d.png"], check=True)
    import glob
    fs = sorted(glob.glob(f"{d}/*.png"))
    prev, diffs = None, []
    for f in fs:
        a = np.asarray(Image.open(f).convert("L"), dtype=float)
        if prev is not None:
            diffs.append(np.abs(a - prev).mean())
        prev = a
    d_ = np.array(diffs)
    cuts = [i for i, x in enumerate(d_) if x > d_.mean() * 3]
    return d_.mean(), d_.max(), cuts


def build_report(w, h, dur, fps, zmean, zbright, gname, mmean, fps_min, cuts):
    """The human report as a string, so one pass can both emit and report."""
    legible = "-> needs grading" if zmean > 55 else "-> already legible"
    cut_line = ("NONE - continuous" if not cuts
                else f"{len(cuts)} DETECTED - will look broken when scrubbed")
    out = [
        "",
        f"  source      {w}x{h}  {dur:.1f}s  {fps:.0f}fps",
        f"  text zone   mean {zmean:.0f}, bright {zbright:.1f}%  {legible}",
        f"  grade       {gname}",
        f"  motion      step {mmean:.1f} -> minimum {fps_min}fps",
        f"  cuts        {cut_line}",
        "",
    ]
    if cuts:
        out += ["  WARNING: cuts break scrubbing. A cut reads as a failed image load,",
                "           not as an edit. Re-generate the source without cuts.", ""]
    return chr(10).join(out) + chr(10)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--report", help="also write the human report here, so one "
                                     "pass can serve build.sh and the reader")
    ap.add_argument("--corners", action="store_true",
                    help="write watermark-corners.png for reading off a delogo box")
    a = ap.parse_args()

    w, h, dur, fps = probe(a.video)
    if a.corners:
        out, origins = watermark_sheet(a.video)
        print(f"\nwrote {out}")
        print("Find the mark, read its pixel offset inside its tile, add the tile origin:")
        for k, (ox, oy) in origins.items():
            print(f"   {k:14} origin x={ox} y={oy}")
        print("\nThen: ./build.sh in.mp4 out.html --delogo x=..:y=..:w=..:h=..\n")
        return
    arrs = frames(a.video)
    zmean, zbright = text_zone(arrs)
    mmean, mmax, cuts = motion(a.video)

    # --- decisions ---
    if zmean > 85:
        grade, gname = ("eq=contrast=1.10:saturation=0.90:brightness=-0.14,"
                        "curves=all='0/0 0.5/0.36 1/0.84',vignette=PI/3.8"), "heavy (bright source)"
    elif zmean > 50:
        grade, gname = ("eq=contrast=1.09:saturation=0.95:brightness=-0.08,"
                        "curves=all='0/0 0.5/0.42 1/0.90',vignette=PI/4"), "medium"
    else:
        grade, gname = ("eq=contrast=1.10:saturation=1.16:gamma=0.97,"
                        "curves=b='0/0 0.35/0.29 1/1',vignette=PI/5"), "light (already dark)"

    fps_min = 18 if mmean > 8 else (14 if mmean > 4 else 11)

    report = build_report(w, h, dur, fps, zmean, zbright, gname, mmean, fps_min, cuts)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(report)

    if a.emit:
        print(f"SRC_W={w}")
        print(f"SRC_H={h}")
        print(f"DUR={dur:.3f}")
        print(f"SRC_FPS={fps:.3f}")
        print(f"GRADE={grade!r}")
        print(f"FPS_MIN={fps_min}")
        print(f"ZMEAN={zmean:.1f}")
        print(f"CUTS={len(cuts)}")
        return

    print(report, end="")


if __name__ == "__main__":
    main()
