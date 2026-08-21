# cinema-scroll pipeline

Layer images in, cinematic scroll site out. One command, one JSON file.

A tall section with a sticky stage. Scroll it and layered transparent PNGs
drift, part, blur and zoom against each other on a scroll timeline. Not a video,
not a frame sequence — real elements the browser composites, so text stays
selectable and nothing pixelates.

## Use

```bash
./build.sh examples/mostar/scene.json out/mostar
./build.sh scene.json out/site --open        # build, serve, open
```

Output is `index.html` + `styles.css` + `engine.js`, plus `layers/` if your
sources are local files. Remote URLs are referenced as-is, never bundled.

## The idea

Everything about **how it moves** lives in `scene.json`. Everything about **what
the numbers mean** lives in `template/engine.js`, which you never edit per
project. The compiler in between generates the CSS that wires one to the other.

Three things make it work:

**Progress is measured in absolute pixels**, not percentages. `scrollHeight:
3700` gives you a 3700px timeline, and a segment at `[560, 900, 1300, 1620]`
reads like an edit decision list. Change the page height and your timings don't
silently rescale.

**One primitive: the segment.** `[a, b, c, d]` is a scene that fades in over
`a→b`, holds, and fades out over `c→d`. It yields three signals:

| signal | meaning |
|---|---|
| `enter` | 0→1 across `a→b`, then stays 1 |
| `exit` | 0→1 across `c→d` |
| `active` | `enter * (1 - exit)` — on screen right now |

**One rAF loop publishes CSS variables.** The engine never touches an element's
style. It computes numbers, writes them to `:root`, and the browser composites.
That is why 40+ animated properties stay smooth.

## scene.json

```jsonc
{
  "scrollHeight": 3700,        // px of scroll through the sticky stage
  "progressSpan": 2700,        // px over which "progress" goes 0 -> 1
  "smoothing": 0.14,           // scroll inertia (lower = heavier)
  "segments": { "frame2": [560, 900, 1300, 1620] },
  "groups": [ ... ],           // parent transforms
  "layers": [ ... ],           // images
  "panels": [ ... ],           // text
  "shade": { ... }             // tint gradient
}
```

### Tracks

A track adds `driver × amount` to a property. Every property starts at its base
and accumulates, which is what lets one layer answer to scroll, a segment, and
the pointer at once:

```jsonc
{
  "base": { "width": "67.2vw", "bottom": "5vh", "scale": 1.02 },
  "parallax": { "x": "18px", "y": "8px" },
  "tracks": [
    { "prop": "width", "drive": "frame2.enter", "to": "105vw" },
    { "prop": "y",     "drive": "frame2.exit",  "amount": "-760px" },
    { "prop": "scale", "drive": "progress",     "amount": 0.23 }
  ]
}
```

Properties: `x y scale rotate rotateX rotateY opacity blur brightness contrast
saturate hue clip width height top bottom left right`.

Set `perspective` on a layer (e.g. `"1500px"`) and `rotateX`/`rotateY` become real
3D — a pair of layers can swing open like doors instead of tilting like stickers.

**Percentages are relative to the layer's own size**, which is how you move a
layer clear of the frame at any viewport: `-100%` of its own width always clears,
where a `vw` figure that works on a desktop will not on a phone.

**Units mix per axis.** A layer can drift `-46vw` with the scroll *and* `22px`
with the pointer; each unit becomes its own variable and the generated `calc()`
sums them.

### Transitions

`clip` drives a `clip-path` from 0 to 1. Pick the shape with `clipMode`:

| mode | effect |
|---|---|
| `wipe-left` / `-right` / `-up` / `-down` | directional wipe |
| `iris` | circular reveal from the centre |
| `bars` | letterbox opening vertically |
| `curtain` | opens from the centre outward |

Combine one with a `blur` track running to zero and the layer arrives *into*
focus rather than simply appearing.

### Drivers

| driver | value |
|---|---|
| `"progress"` | 0→1 over `progressSpan` |
| `"frame2.enter"` / `.exit` / `.active` | that segment's signal |
| `{"mouse": "x"}` | pointer offset from centre, −0.5→0.5 |
| `{"sum": [...], "clamp": true}` | combined signals |
| `{"product": [...]}` | multiplied |
| `{"of": "frame2.enter", "pow": 1.5}` | re-eased, slower off the mark |
| `{"of": "...", "snap": 2.2}` | front-loaded: fast out, long settle |
| `{"of": "...", "back": 1.15}` | overshoots past the target, then lands |
| `{"of": "...", "oneMinus": true}` | inverted |

### Portrait

A layer sized in `vw` with `height: auto` collapses vertically on a phone — a
`112vw` landscape image is only about 29% of the screen height at 390x844. Give
such a layer a `portrait` override and it is sized by height there instead:

```jsonc
{ "portrait": "height: 116vh; width: auto; max-width: none" }
```

Emitted as `@media (max-aspect-ratio: 4/5)`. Layers using `fit: "cover"` never
need it.

### Groups

A group is a parent transform, so a stack zooms as one unit while each child
keeps its own motion. Layers join with `"group": "back"`.

```jsonc
"groups": [{
  "name": "back",
  "anchor": "top: 0; bottom: 0; left: -3vw; right: -3vw",
  "origin": "50% 100%",
  "base": { "scale": 0.76 },
  "tracks": [{ "prop": "scale", "drive": "progress", "amount": 0.2 }]
}]
```

### Panels

Two flavours. **With `segment`**, you get the standard story panel: vertically
centred, fades in on enter, slides `+enterSlide → −exitSlide`, fades out on exit.
**Without**, the panel is driven entirely by its own tracks — which is how a hero
that only fades on the way *out* is expressed without faking a segment.

### Counter-scale

`counterScale` keeps an element screen-true inside a parent that is still
scaling, by publishing `--counter-scale: 1 / parentScale`. Use it for UI that
must not zoom with the scenery.

## The example

`examples/mostar/scene.json` is the acid test: it reproduces a hand-built page
from 1 group, 7 layers, 4 panels, 3 segments and 43 tracks. Its numbers were
checked against the original at every key scroll position — bridge, splitframes,
group scale, shade alphas and panel curves all match exactly.

## Files

```
build.sh                one command, scene -> site
scripts/compile.py      validates, normalises, generates the CSS
template/engine.js      the brain — generic, never edited per project
template/base.css       the rig, panels, optional header
template/page.html      the shell
examples/mostar/        a full scene
```

## Choosing layers

The technique needs **depth that means something**. What works:

- a foreground element the camera can part or pass (an arch, a doorway, trees)
- a mid-ground subject that holds the eye
- a far background that can blur and desaturate without losing the scene

What fails is a flat photograph sliced arbitrarily. If two layers always move
together, they are one layer.

Aim for 4–8 layers. Each needs clean transparent edges; a hard cut-out line
reads as a mistake the moment it moves against its background.

## Not covered

**Bespoke UI** — the Mostar original had an infinite card slider. Interactive
components are not expressible as tracks; build them as normal DOM and drive
them off `window.cinema` (the engine exposes `clamp`, `lerp`, `smoothstep`,
`segmentInOut` and `requestTick` so your component shares its clock).

**Auto-layering** — turning one photograph into depth planes (depth estimation,
segmentation, inpainting) is the intended next stage. It feeds `layers/` and
changes nothing about the compiler.

## Weight

Layers are full-bleed images and they add up — the Mostar example pulls ~41 MB
across 7 remote PNGs. Nothing is bundled, so first load is the real cost. Export
layers no larger than they render, and prefer WebP or AVIF over PNG unless you
need the alpha precision.
