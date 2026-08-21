#!/usr/bin/env python3
"""
intake.py — pull generated images out of a download folder, de-watermark them,
measure them, and stage them as scene layers.

  python3 intake.py examples/thread            # scan the default Downloads dir
  python3 intake.py examples/thread --since 90  # only files from the last 90 min
  python3 intake.py examples/thread --src D:/pics --dry-run

What it does per file:
  1. finds the generator's corner watermark and inpaints it out
  2. measures resolution, aspect, and whether the text bands are dark enough
  3. copies the cleaned image into <project>/raw/ with a sequence name

The watermark rule is measured, not guessed. On this generator the mark sits at
about (0.914w, 0.843h) and its height is very close to h/16 -- confirmed on a
1280x720 video frame (45px) and a 2816x1536 still (96px). Detection thresholds
against the LOCAL median, because on dark rock the mark peaked at luminance 105
while an absolute test looking for >120 found nothing at all.
"""
import argparse
import os
import shutil
import sys

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("needs pillow and numpy")

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass  # only needed for HEIC sources

DEFAULT_SRC = os.path.expanduser("~/Downloads")
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif")

# where this generator places its mark, as a fraction of the frame
WM_CX, WM_CY = 0.914, 0.843
WM_H_FRAC = 1.0 / 16.0


def luminance(a):
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def find_watermark(a):
    """
    Return (x, y, w, h) of the corner mark, or None.

    Searches a generous window around the expected site and keeps the blob only
    if it is roughly square and roughly the expected size -- bright haze near
    the corner otherwise produces a wide, flat false positive.
    """
    h, w = a.shape[:2]
    L = luminance(a)
    exp = WM_H_FRAC * h
    cx, cy = int(WM_CX * w), int(WM_CY * h)
    pad = int(exp * 2.0)
    x0, y0 = max(0, cx - pad), max(0, cy - pad)
    x1, y1 = min(w, cx + pad), min(h, cy + pad)
    reg = L[y0:y1, x0:x1]
    if reg.size == 0:
        return None

    med = float(np.median(reg))
    for delta in (35, 30, 25, 20):
        mask = reg > med + delta
        if mask.sum() < 24:
            continue
        ys, xs = np.nonzero(mask)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        squareness = min(bw, bh) / max(bw, bh)
        # the mark is a compact near-square roughly exp tall
        if squareness > 0.62 and 0.45 * exp <= bh <= 2.1 * exp:
            m = 6
            return (x0 + xs.min() - m, y0 + ys.min() - m, bw + 2 * m, bh + 2 * m)
    return None


def inpaint(a, box, ring=14, feather=12):
    """
    Replace a box with the nearby patch whose surrounding ring best matches,
    blended with a cosine falloff. On texture this beats edge interpolation,
    which smears a visible smudge across any hard line crossing the box.
    """
    X, Y, W, H = box
    H_img, W_img = a.shape[:2]
    X = max(ring, min(X, W_img - W - ring))
    Y = max(ring, min(Y, H_img - H - ring))

    def ring_of(x, y):
        return np.concatenate([
            a[y - ring:y, x - ring:x + W + ring].ravel(),
            a[y + H:y + H + ring, x - ring:x + W + ring].ravel(),
            a[y:y + H, x - ring:x].ravel(),
            a[y:y + H, x + W:x + W + ring].ravel(),
        ])

    target = ring_of(X, Y)
    best, best_err = None, None
    for dy in range(-320, 321, 8):
        for dx in range(-320, 321, 8):
            if abs(dx) < W + 20 and abs(dy) < H + 20:
                continue
            sx, sy = X + dx, Y + dy
            if sx - ring < 0 or sy - ring < 0:
                continue
            if sx + W + ring > W_img or sy + H + ring > H_img:
                continue
            cand = ring_of(sx, sy)
            if cand.shape != target.shape:
                continue
            err = float(np.mean((cand - target) ** 2))
            if best_err is None or err < best_err:
                best_err, best = err, (sx, sy)
    if best is None:
        return a, None

    sx, sy = best
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]).astype(float)
    alpha = np.clip(d / feather, 0, 1)
    alpha = ((1 - np.cos(alpha * np.pi)) / 2)[..., None]

    out = a.copy()
    out[Y:Y + H, X:X + W] = a[sy:sy + H, sx:sx + W] * alpha + a[Y:Y + H, X:X + W] * (1 - alpha)
    return out, best_err


def text_bands(a):
    """Mean luminance of the centred bands where panel copy sits."""
    h, w = a.shape[:2]
    L = luminance(a)
    out = {}
    for label, frac in (("hero", 0.17), ("mid", 0.45), ("low", 0.61)):
        y = int(h * frac)
        y0, y1 = max(0, y - int(h * 0.055)), min(h, y + int(h * 0.055))
        cx, half = w // 2, int(w * 0.22)
        z = L[y0:y1, cx - half:cx + half]
        out[label] = (float(z.mean()), 100.0 * float((z > 150).mean()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="e.g. examples/thread")
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--since", type=float, default=180, help="minutes")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = os.path.join(args.project, "raw")
    if not args.dry_run:
        os.makedirs(raw, exist_ok=True)

    import time

    cutoff = time.time() - args.since * 60
    files = []
    for f in sorted(os.listdir(args.src)):
        p = os.path.join(args.src, f)
        if not os.path.isfile(p) or not f.lower().endswith(EXTS):
            continue
        if os.path.getmtime(p) < cutoff:
            continue
        files.append(p)

    if not files:
        print(f"no images in {args.src} from the last {args.since:.0f} min")
        return

    print(f"{len(files)} candidate(s) in {args.src}\n")
    existing = len([f for f in os.listdir(raw)]) if os.path.isdir(raw) else 0

    for i, p in enumerate(files, start=existing + 1):
        im = Image.open(p)
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        arr = np.asarray(im.convert("RGB"), dtype=np.float64)
        h, w = arr.shape[:2]

        box = find_watermark(arr)
        note = "none found"
        if box:
            arr, err = inpaint(arr, box)
            after = find_watermark(arr)
            note = f"removed {box[2]}x{box[3]} at ({box[0]},{box[1]})"
            note += "  [clean]" if after is None else "  [STILL DETECTED]"

        bands = text_bands(arr)
        base = os.path.splitext(os.path.basename(p))[0][:28]
        out_name = f"{i:02d}-{base}.png"

        print(f"{out_name}")
        print(f"   {w}x{h}  aspect {w/h:.3f}")
        print(f"   watermark: {note}")
        print("   text bands: " + "  ".join(
            f"{k} {m:.0f}/{b:.0f}%" for k, (m, b) in bands.items()))
        flags = [k for k, (m, b) in bands.items() if m > 60 or b > 8]
        if flags:
            print(f"   NOTE: {', '.join(flags)} band(s) may be too bright for cream type")

        if not args.dry_run:
            Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).save(
                os.path.join(raw, out_name))
        print()

    if args.dry_run:
        print("dry run: nothing written")
    else:
        print(f"staged into {raw}")


if __name__ == "__main__":
    main()
