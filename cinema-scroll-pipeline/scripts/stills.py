#!/usr/bin/env python3
"""
stills.py — render a built scene at exact scroll positions.

  python3 stills.py out/petra 0 1200 2050 2800 3800

Writes out/petra/_still_<N>.html for each position: a copy of the page with the
engine REMOVED and every CSS variable pre-computed and inlined on <html>.

Why not just scroll a headless browser: the engine eases toward its target over
many frames, so a screenshot taken after `window.scrollTo` catches an
indeterminate in-between state. Two such shots came back byte-identical during
development. Solving the variables directly is deterministic and matches what the
engine converges to, so the stills are trustworthy.
"""
import json
import os
import re
import sys


def clamp(v, lo=0.0, hi=1.0):
    return min(hi, max(lo, v))


def smoothstep(e0, e1, v):
    x = clamp((v - e0) / (e1 - e0)) if e1 != e0 else (1.0 if v >= e1 else 0.0)
    return x * x * (3 - 2 * x)


def build_segments(scene, s):
    out = {}
    for name, w in scene.get("segments", {}).items():
        enter = smoothstep(w[0], w[1], s)
        exit_ = smoothstep(w[2], w[3], s)
        out[name] = {"enter": enter, "exit": exit_, "active": enter * (1 - exit_)}
    return out


def resolve(spec, ctx):
    if spec is None:
        return 0.0
    if isinstance(spec, (int, float)):
        return float(spec)
    if isinstance(spec, str):
        if spec == "progress":
            return ctx["progress"]
        if spec == "one":
            return 1.0
        if "." in spec:
            name, key = spec.split(".", 1)
            return ctx["segments"].get(name, {}).get(key, 0.0)
        return ctx["segments"].get(spec, {}).get("active", 0.0)
    v = 0.0
    if spec.get("mouse"):
        v = 0.0                                   # stills are rendered pointer-centred
    elif "sum" in spec:
        v = sum(resolve(c, ctx) for c in spec["sum"])
    elif "product" in spec:
        v = 1.0
        for c in spec["product"]:
            v *= resolve(c, ctx)
    elif "of" in spec:
        v = resolve(spec["of"], ctx)
    if spec.get("oneMinus"):
        v = 1 - v
    if spec.get("clamp"):
        v = clamp(v)
    if spec.get("pow"):
        v = v ** spec["pow"]
    if spec.get("back"):
        c1 = 1.70158 if spec["back"] is True else spec["back"]
        c3 = c1 + 1
        t = v - 1
        v = 1 + c3 * t * t * t + c1 * t * t
    if spec.get("snap"):
        k = 3 if spec["snap"] is True else spec["snap"]
        v = 1 - (1 - clamp(v)) ** k
    return v


def accumulate(vars_, ctx):
    out = {}
    for prop, buckets in vars_.items():
        for unit, spec in buckets.items():
            val = spec["base"] + sum(
                resolve(t["drive"], ctx) * t["amount"] for t in spec["tracks"]
            )
            token = {"%": "pct"}.get(unit, unit)
            out[f"{prop}-{token}" if token else prop] = (val, unit)
    return out


def css_for(scene, s):
    ctx = {
        "progress": clamp(s / (scene.get("progressSpan") or scene.get("scrollHeight") or 1)),
        "segments": build_segments(scene, s),
    }
    parts = ["--mx:0", "--my:0", f"--progress:{ctx['progress']:.4f}"]

    for i, g in enumerate(scene.get("groups", [])):
        for k, (v, u) in accumulate(g["vars"], ctx).items():
            parts.append(f"--g{i}-{k}:{v}{u}")
    for i, l in enumerate(scene.get("layers", [])):
        for k, (v, u) in accumulate(l["vars"], ctx).items():
            parts.append(f"--l{i}-{k}:{v}{u}")
    for i, p in enumerate(scene.get("panels", [])):
        seg = ctx["segments"].get(p.get("segment") or "")
        if seg:
            op = seg["active"] * (1 - seg["exit"])
            y = -seg["exit"] * p["exitSlide"] + (1 - seg["enter"]) * p["enterSlide"]
            parts += [f"--p{i}-opacity:{op}", f"--p{i}-y:calc(-50% + {y}px)"]
        if p.get("vars"):
            for k, (v, u) in accumulate(p["vars"], ctx).items():
                parts.append(f"--p{i}v-{k}:{v}{u}")

    shade = scene.get("shade")
    if shade:
        d = resolve(shade["drive"], ctx)
        parts += [
            f"--shade-top-alpha:{d * shade['top']}",
            f"--shade-mid-alpha:{d * shade['mid']}",
            f"--shade-bottom-alpha:{d * shade['bottom']}",
            f"--shade-z:{2 if d > shade.get('liftAt', 0.02) else 0}",
        ]
    return ";".join(parts)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out_dir, positions = sys.argv[1], [float(x) for x in sys.argv[2:]]
    page = os.path.join(out_dir, "index.html")
    html = open(page, encoding="utf-8").read()
    m = re.search(r"window\.__CINEMA_SCENE__ = (\{.*?\});", html, re.S)
    if not m:
        sys.exit("no compiled scene found in index.html")
    scene = json.loads(m.group(1))

    for s in positions:
        doc = re.sub(r'\s*<script src="engine\.js" defer></script>', "", html)
        doc = doc.replace('<html lang="en">', f'<html lang="en" style="{css_for(scene, s)}">', 1)
        name = f"_still_{int(s)}.html"
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(doc)
        print(f"  {name}")


if __name__ == "__main__":
    main()
