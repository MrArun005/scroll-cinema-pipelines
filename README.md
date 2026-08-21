# scroll-cinema-pipelines

Two pipelines and one reference site for building cinematic scroll-driven web
pages — the kind where scrolling drives a camera rather than moving a document.

Both pipelines take media in and produce a working page out. They solve the same
problem two different ways, and which one you want depends entirely on what your
source material is.

| | [`cinema-scroll-pipeline`](cinema-scroll-pipeline/) | [`scroll-scrub-pipeline`](scroll-scrub-pipeline/) |
|---|---|---|
| Input | layered transparent images + a scene file | a video |
| Output | `index.html` + `styles.css` + `engine.js` | one self-contained `.html` |
| Technique | real DOM layers, CSS variables driven per frame | WebP frame sequence painted to a canvas |
| Text | selectable, real elements | overlaid on the canvas |
| Scales | resolution-independent transforms | fixed to the exported frames |
| Best for | depth, parting reveals, parallax between planes | a continuous camera move or transformation |

---

## cinema-scroll-pipeline

Layer images in, cinematic scroll site out. One command, one JSON file.

```bash
cd cinema-scroll-pipeline
./build.sh examples/petra/scene.json out/petra --open
```

Everything about **how it moves** lives in `scene.json`. Everything about **what
the numbers mean** lives in `template/engine.js`, which is generic and never
edited per project. A compiler generates the CSS that wires one to the other, so a
new site is a JSON file rather than four hundred lines of hand-tuned transforms.

Three ideas make it work:

- **Progress is measured in absolute pixels**, not percentages, so a segment at
  `[560, 1200, 1650, 2050]` reads like an edit decision list and does not silently
  rescale when the page height changes.
- **One primitive: the segment.** `[a, b, c, d]` fades in over `a→b`, holds, fades
  out over `c→d`, and yields three signals — `enter`, `exit`, `active`.
- **One rAF loop publishes CSS custom properties.** The engine never touches an
  element's style; it computes numbers and the browser composites. That is why 40+
  animated properties stay smooth.

See [its README](cinema-scroll-pipeline/README.md) for the full scene reference.

### Examples

**`examples/petra/`** — the complete build. Seven layers, one group, five panels,
four segments, 43 tracks over 3800px of scroll: canyon walls part to reveal a
carved facade, which dissolves into a close-up of its own columns, which blurs out
into open desert. Source layers are in `examples/petra/raw/` so it builds from a
clean checkout.

**`examples/mostar/`** — the acid test. It reproduces `mostar-city/` (below) from a
scene file, and its numbers were checked against the hand-written original at every
key scroll position.

**`examples/mizoram/`** — a brief and empty intake folders for a documentary piece
built from real photographs. Not started.

### Tools

- `scripts/compile.py` — validates a scene, normalises every value, generates CSS
- `scripts/stills.py` — renders a built scene at exact scroll positions by solving
  the CSS variables directly. Driving a headless browser by scroll does not work:
  the engine eases toward its target over many frames, so a screenshot catches an
  indeterminate in-between state. Two such shots once came back byte-identical.

---

## scroll-scrub-pipeline

Video in, finished single-file scroll-scrub site out.

```bash
cd scroll-scrub-pipeline
./build.sh input.mp4 site.html --title "Held" --budget 5
```

Scroll down and the footage plays forward; scroll up and it plays backward. Done
with a frame sequence painted to a canvas rather than a `<video>` element, because
scrubbing `video.currentTime` seeks to the nearest keyframe and stutters badly on
iOS. Output is fully self-contained — every frame is base64-embedded, so one tap
opens it on a phone with no server and no folder alongside it.

The budget is met by lowering **frame count**, never resolution, on the reasoning
that resolution is what you see and framerate is what the easing hides.

`scripts/analyse.py` measures footage before you commit to it — text-zone
luminance, motion magnitude, cut detection — and `--corners` writes a contact
sheet for reading a watermark box off by eye, because auto-detection cannot tell a
static watermark from static scenery.

### Known issues, unfixed

Documented rather than silently carried:

- **macOS builds fail.** `build.sh` uses GNU `du -bc`; BSD `du` has no `-b`. The
  script already forks `stat -c%s || stat -f%z` for exactly this reason, so the
  awareness is there but not applied.
- **`embed.py` will crash on Windows** the first time the template contains a
  character whose UTF-8 includes a byte cp1252 cannot decode — a curly closing
  quote is enough. It opens without `encoding=`, and currently round-trips only by
  luck.
- **Frame ordering breaks above 999 frames.** `f_%03d` means frame 1000 sorts
  before frame 999 lexicographically, so the sequence would scramble with no error.
- **`&` in a `--title`** is a sed replacement metacharacter and corrupts the title.
- **`analyse.py` runs twice per build**, duplicating the slowest step for identical
  numbers.

---

## mostar-city

A hand-written cinematic scroll page, built to a specification rather than
generated. It exists as the reference the compiler was measured against, and as a
worked example of the technique before it was abstracted.

Note: it loads its scene photographs and its display font from third-party remote
URLs. Those are not vendored here, so the page depends on hosts that may not stay
up. Its CSS also carries a few values the generic pipeline does not — notably a
literal `14rem` hero — which is why the compiled version reads slightly smaller.

---

## Requirements

```bash
ffmpeg                                  # scroll-scrub-pipeline only
python3 -m pip install pillow numpy     # both
python3 -m pip install pillow-heif      # only for HEIC source photographs
```

`cinema-scroll-pipeline` needs Python and nothing else — no ffmpeg, no build step,
no npm.

### Windows notes

`build.sh` in both projects invokes `python3`. A `uv`-managed interpreter is
PEP-668 externally managed and will refuse `pip install`, so the deps belong in a
virtual environment — and a `uv venv` on Windows contains only `python.exe`, no
`python3.exe`. Either copy `python.exe` to `python3.exe` inside the venv, or set
`PYTHON=python` for `cinema-scroll-pipeline`, whose `build.sh` honours it.

## Choosing footage or layers

The technique needs change that means something in both directions.

For **scroll-scrub**: something in frame must change monotonically. A subject
transforming with a locked camera, or a camera closing on an anchor. What fails is
footage with no anchor — a drive down an open road — because nothing arrives, so
scrolling back conveys nothing.

For **cinema-scroll**: depth that means something. A foreground the camera can
part or pass, a mid-ground subject that holds the eye, a background that can blur
away. If two layers always move together they are one layer. Four to eight layers,
each with clean transparent edges.

## Licence

No licence chosen yet. The Petra example layers are AI-generated; the Mostar page
references third-party remote assets it does not own.
