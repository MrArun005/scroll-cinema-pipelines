#!/usr/bin/env python3
"""
generate.py — build the Mirror scene.

Five acts, each a different mirror operation on the SAME photograph, so the
geometry always opens out of the frame the viewer is already looking at.

The operations are the ones the film's VFX teams describe, not invented:

  radial   a "city block Kaleidoscope" — a 3D block sliced by a series of
           virtual mirrors. Here: eight wedges, every second one reflected, so
           adjacent seams agree (dihedral group D8).
  bands    the same virtual mirrors, but planar and axis-aligned rather than
           radial — the Escher reading of the same idea.
  droste   recursive nesting on an Archimedean spiral: each copy scaled by a
           constant ratio and rotated by a constant angle. A conformal map,
           which is why the repeats look like the same building.
  clones   "clone duplication with offsetting" — the set tiled against itself.
  reveal   the shot where the effect deliberately breaks down and the audience
           sees it was an optical illusion: the composite swings on its own
           axis and turns out to be flat.

Because every layer points at one image file, the browser fetches it once no
matter how many layers there are. Layer count costs almost nothing here.

  python3 examples/mirror/generate.py
"""
import json
import math
import os

SRC = "raw/axis.webp"
SIZE = "118vmax"
ANCHOR = f"left: 50%; top: 50%; width: {SIZE}; height: {SIZE}; object-fit: cover"
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- act windows
SEGMENTS = {
    "intro":  [-1,    0,     120,  640],
    "radial": [560,  1240,  1620, 2020],
    "bands":  [1820, 2420,  2760, 3160],
    "droste": [2960, 3560,  3900, 4300],
    "clones": [4100, 4700,  5040, 5440],
    "reveal": [5240, 5860,  8000, 8200],
    "t1":     [640,  1240,  1560, 1940],
    "t2":     [1900, 2480,  2760, 3120],
    "t3":     [3040, 3620,  3880, 4260],
    "t4":     [4180, 4760,  5020, 5400],
    "t5":     [5240, 5860,  8200, 8400],
}
SCROLL = 6400

layers = []


def add(**kw):
    layers.append(kw)


def fade(act, z_in=1.8, z_out=2.0):
    """Standard in-on-enter, out-on-exit pair for a layer owned by one act."""
    return [
        {"prop": "opacity", "drive": {"of": f"{act}.enter", "snap": z_in}, "amount": 1},
        {"prop": "opacity", "drive": {"of": f"{act}.exit", "snap": z_out}, "amount": -1},
    ]


# ------------------------------------------------------------------ backdrop
add(name="void", src="raw/void.webp", z=0, fit="cover", origin="50% 50%",
    base={"scale": 1.15},
    parallax={"x": "-8px", "y": "-4px"},
    tracks=[{"prop": "scale", "drive": "progress", "amount": 0.22},
            {"prop": "brightness", "drive": "droste.enter", "amount": -0.2}])

# the flat plate: identical geometry to radial cell 0, so the first fracture
# lands on it exactly rather than dissolving into it
add(name="plate", src=SRC, z=2, anchor=ANCHOR, translateX="-50%", translateY="-50%",
    origin="50% 50%",
    base={"scale": 1, "opacity": 1, "rotate": "0deg"},
    parallax={"x": "14px", "y": "7px"},
    tracks=[{"prop": "rotate", "drive": "radial.enter", "amount": "22deg"},
            {"prop": "opacity", "drive": {"of": "radial.enter", "snap": 1.2}, "amount": -1},
            {"prop": "opacity", "drive": {"of": "reveal.enter", "snap": 1.5}, "amount": 1},
            {"prop": "rotateY", "drive": {"of": "reveal.enter", "back": 1.1}, "amount": "-42deg"},
            {"prop": "rotate", "drive": "reveal.enter", "amount": "-22deg"},
            {"prop": "scale", "drive": "reveal.enter", "amount": 0.06},
            {"prop": "brightness", "drive": "reveal.enter", "amount": 0.14},
            {"prop": "contrast", "drive": "reveal.enter", "amount": 0.1}],
    perspective="1500px")

# ------------------------------------------------- act 1: radial kaleidoscope
N = 8
SEG = 360.0 / N
half = 50 * math.tan(math.radians(SEG / 2))
WEDGE = f"polygon(50% 50%, {50 - half:.2f}% 0%, {50 + half:.2f}% 0%)"
a = math.radians(SEG / 2)
EDGE_L = f"{math.sin(-a):.4f}, {-math.cos(-a):.4f}, 0"
EDGE_R = f"{math.sin(a):.4f}, {-math.cos(a):.4f}, 0"

for i in range(N):
    odd = i % 2 == 1
    add(name=f"radial{i}", src=SRC, z=3, anchor=ANCHOR,
        translateX="-50%", translateY="-50%", origin="50% 50%",
        clipRaw=WEDGE, perspective="1700px",
        hingeAxis=EDGE_R if odd else EDGE_L,
        base={"rotate": f"{i * SEG}deg", "scaleX": -1 if odd else 1,
              "opacity": 0, "hinge": "0deg", "blur": "9px"},
        parallax={"x": f"{-14 if odd else 14}px", "y": "7px"},
        tracks=fade("radial") + [
            {"prop": "blur", "drive": "radial.enter", "amount": "-9px"},
            {"prop": "rotate", "drive": "radial.enter", "amount": "22deg"},
            # each cell pivots on the edge it shares, so that edge never moves
            {"prop": "hinge", "drive": {"of": "radial.exit", "back": 1.15},
             "amount": f"{-46 if odd else 46}deg"},
            {"prop": "contrast", "drive": "radial.enter", "amount": 0.16},
        ])

# --------------------------------------------- act 2: planar mirror bands
B = 6
for i in range(B):
    top = i * 100.0 / B
    bot = 100.0 - (i + 1) * 100.0 / B
    odd = i % 2 == 1
    add(name=f"band{i}", src=SRC, z=4, anchor=ANCHOR,
        translateX="-50%", translateY="-50%", origin="50% 50%",
        clipRaw=f"inset({top:.3f}% 0 {bot:.3f}% 0)",
        base={"scaleY": -1 if odd else 1, "opacity": 0, "blur": "8px",
              "y": f"{(12 if odd else -12)}px"},
        parallax={"x": f"{18 if odd else -18}px", "y": "6px"},
        tracks=fade("bands") + [
            {"prop": "blur", "drive": "bands.enter", "amount": "-8px"},
            # the bands slide against one another as they settle
            {"prop": "y", "drive": {"of": "bands.enter", "back": 1.2},
             "amount": f"{(-12 if odd else 12)}px"},
            {"prop": "x", "drive": "bands.exit", "amount": f"{(70 if odd else -70)}px"},
            {"prop": "contrast", "drive": "bands.enter", "amount": 0.12},
        ])

# ------------------------------------------------- act 3: Droste recursion
K = 6
RATIO = 0.615          # scale between successive copies
TWIST = 13.0           # degrees per step: the Archimedean spiral
for k in range(K):
    s = RATIO ** k
    add(name=f"droste{k}", src=SRC, z=5 + k, anchor=ANCHOR,
        translateX="-50%", translateY="-50%", origin="50% 50%",
        clipRaw="circle(46% at 50% 50%)" if k else None,
        base={"scale": s * 1.5, "rotate": f"{k * TWIST}deg", "opacity": 0,
              "blur": f"{5 + k}px"},
        parallax={"x": f"{10 - k * 2}px", "y": f"{5 - k}px"},
        tracks=fade("droste") + [
            {"prop": "scale", "drive": {"of": "droste.enter", "back": 1.08},
             "amount": -s * 0.5},
            {"prop": "blur", "drive": "droste.enter", "amount": f"{-(5 + k)}px"},
            # the spiral keeps turning, which is what sells it as endless
            {"prop": "rotate", "drive": "progress", "amount": f"{-6 - k * 3}deg"},
            {"prop": "hue", "drive": "droste.enter", "amount": f"{k * 4}deg"},
        ])

# --------------------------------------------- act 4: clone grid, offset
G = 3
for gy in range(G):
    for gx in range(G):
        idx = gy * G + gx
        ox = (gx - 1) * 33.5
        oy = (gy - 1) * 33.5
        flip = (gx + gy) % 2 == 1
        add(name=f"clone{idx}", src=SRC, z=12, anchor=ANCHOR,
            translateX="-50%", translateY="-50%", origin="50% 50%",
            clipRaw=f"inset({33.34*gy:.2f}% {33.34*(G-1-gx):.2f}% "
                    f"{33.34*(G-1-gy):.2f}% {33.34*gx:.2f}%)",
            perspective="1500px",
            base={"scale": 1, "opacity": 0, "blur": "7px",
                  "scaleX": -1 if flip else 1,
                  "x": f"{ox*1.6:.1f}px", "y": f"{oy*1.6:.1f}px"},
            parallax={"x": f"{(gx-1)*16}px", "y": f"{(gy-1)*10}px"},
            tracks=fade("clones") + [
                {"prop": "blur", "drive": "clones.enter", "amount": "-7px"},
                # each tile drifts back toward the grid it belongs to
                {"prop": "x", "drive": {"of": "clones.enter", "back": 1.15},
                 "amount": f"{-ox*1.6:.1f}px"},
                {"prop": "y", "drive": {"of": "clones.enter", "back": 1.15},
                 "amount": f"{-oy*1.6:.1f}px"},
                {"prop": "rotate", "drive": "clones.exit",
                 "amount": f"{(8 if flip else -8)}deg"},
                {"prop": "opacity", "drive": {"of": "reveal.enter", "snap": 1.4},
                 "amount": 0.30},
                {"prop": "rotateY", "drive": {"of": "reveal.enter", "back": 1.1},
                 "amount": "-42deg"},
            ])

# ------------------------------------------------------------ seam passes
add(name="seams-tex", src="raw/seams-tex.webp", z=20, fit="cover", blend="screen",
    origin="50% 50%",
    base={"scale": 1.14, "opacity": 0, "rotate": "0deg"},
    parallax={"x": "-26px", "y": "-13px"},
    tracks=[{"prop": "opacity", "drive": "radial.enter", "amount": 0.28},
            {"prop": "opacity", "drive": "droste.enter", "amount": 0.12},
            {"prop": "opacity", "drive": {"of": "reveal.enter", "snap": 2}, "amount": -0.4},
            {"prop": "rotate", "drive": "progress", "amount": "-14deg"},
            {"prop": "scale", "drive": "progress", "amount": 0.26}])

add(name="seams", src="raw/seams.webp", z=21, fit="cover", blend="screen",
    origin="50% 50%",
    base={"scale": 1.1, "opacity": 0, "rotate": "0deg"},
    parallax={"x": "-30px", "y": "-15px"},
    tracks=[{"prop": "opacity", "drive": "radial.enter", "amount": 0.5},
            {"prop": "opacity", "drive": "bands.enter", "amount": -0.2},
            {"prop": "opacity", "drive": "droste.enter", "amount": 0.25},
            {"prop": "opacity", "drive": {"of": "reveal.enter", "snap": 2}, "amount": -0.55},
            {"prop": "rotate", "drive": "radial.enter", "amount": "22deg"},
            {"prop": "scale", "drive": "progress", "amount": 0.28}])

# --------------------------------------------------------------- the scene
PANELS = [
    ("hero", "Mirror Dimension", None, {"bottom": "clamp(48px, 14vh, 200px)"},
     "min(1040px, calc(100vw - 40px))",
     "      <h1>MIRROR</h1>\n      <p>One photograph of one light well. Every shape after "
     "this is the same picture, reflected against itself.</p>"),
    ("p1", "Radial mirrors", "t1", {"top": "22%"}, None,
     "      <h2>Eight cells, not eight copies.</h2>\n      <p>A block sliced by virtual "
     "mirrors. Every second cell is reversed, so each line meets the seam at the angle it "
     "arrived and the join disappears.</p>"),
    ("p2", "Planar mirrors", "t2", {"top": "77%"}, None,
     "      <h2>Straighten the mirrors.</h2>\n      <p>The same operation, axis aligned "
     "instead of radial. Six bands, alternating reflections, sliding against each other.</p>"),
    ("p3", "Recursion", "t3", {"top": "21%"}, None,
     "      <h2>Then put it inside itself.</h2>\n      <p>Each copy scaled by the same ratio "
     "and turned by the same angle. The map preserves angles, which is why every repeat still "
     "reads as the same building.</p>"),
    ("p4", "Clones", "t4", {"top": "78%"}, None,
     "      <h2>Nine of it, offset.</h2>\n      <p>Duplicated and slid out of register, then "
     "allowed to fall back into a grid it was never built for.</p>"),
    ("p5", "The illusion", "t5", {"top": "26%"}, None,
     "      <h2>And it was flat all along.</h2>\n      <p>Turn the whole thing on its own axis "
     "and the depth goes with it. One picture. Nothing was ever added.</p>\n"
     "      <button class=\"note-button\"><span aria-hidden=\"true\">↑</span>"
     "<span>Fold it back</span></button>"),
]

panels = []
for name, aria, seg, pos, width, html in PANELS:
    p = {"name": name, "aria": aria, "z": 30, "html": html}
    p.update(pos)
    if width:
        p["width"] = width
    if seg:
        p["segment"] = seg
    else:
        p.update({
            "base": {"opacity": 1, "scale": 1},
            "tracks": [
                {"prop": "y", "drive": "intro.exit", "amount": "-110px"},
                {"prop": "opacity", "drive": "intro.exit", "amount": -1},
            ],
        })
    panels.append(p)

scene = {
    "title": "Mirror Dimension",
    "description": "One photograph, reflected against itself five ways.",
    "aria": "A scroll story in which one image is folded by five mirror operations",
    "scrollHeight": SCROLL,
    "progressSpan": SCROLL,
    "smoothing": 0.1,
    "mouseSmoothing": 0.09,
    "tint": "8, 12, 22",
    "stage": {"background": "#04060a"},
    "font": {
        "family": "Ogg Medium",
        "url": "https://dcym8fthxf5uu.cloudfront.net/fonts/247a073c-29f5-4a89-aa3a-741020f346fc/OggText-Medium.woff2",
        "weight": 500,
    },
    "segments": SEGMENTS,
    "layers": [{k: v for k, v in l.items() if v is not None} for l in layers],
    "shade": {"drive": 1, "top": 0.36, "mid": 0.08, "bottom": 0.4, "liftAt": -1},
    "extraCss": "\n.shade { z-index: 25 !important; }\n",
    "chrome": (
        "      <header class=\"site-header\" aria-label=\"Primary navigation\">\n"
        "        <a class=\"site-logo\" href=\"#cinema\">Mirror</a>\n"
        "        <nav class=\"site-nav\" aria-label=\"Main menu\">\n"
        "          <a href=\"#cinema\">Radial</a>\n"
        "          <a href=\"#cinema\">Planar</a>\n"
        "          <a href=\"#cinema\">Recursive</a>\n"
        "          <a href=\"#cinema\">Reveal</a>\n"
        "        </nav>\n      </header>"
    ),
    "panels": panels,
}

out = os.path.join(HERE, "scene.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(scene, fh, indent=2, ensure_ascii=False)

acts = ["radial", "bands", "droste", "clones", "reveal"]
print(f"  {len(scene['layers'])} layers, {len(panels)} panels, {len(SEGMENTS)} segments")
print(f"  acts: {', '.join(acts)}")
print(f"  distinct image files: {len({l['src'] for l in scene['layers']})}")
print(f"  scroll {SCROLL}px")
print(f"  wrote {out}")
