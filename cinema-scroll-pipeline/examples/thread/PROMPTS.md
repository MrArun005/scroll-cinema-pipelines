# Thread — a match-cut dive

## The idea

One continuous fall from a mountain range down to a single woven thread. Five
photographs. You scroll, the frame scales *into* a small detail, and at the
moment it fills the screen the next photograph takes over — matched on shape and
tone — and the fall continues.

Scroll back and it pulls out: thread, cloth, loom, lane, village, mountain. That
reverse actually means something, which is the test the technique has to pass.

## Why this project, specifically

**No cut-outs. No magenta. No keying.** Every move is scale, clip, focus and
grade on full frames. Two of our generations died on chroma backdrops — one had
atmospheric haze painted across the magenta and keyed at 0.0%. This structure
removes that failure mode completely.

**It is also a rehearsal for the Mizoram piece.** Mountains, a market lane,
hands working, cloth. Build the dive now with generated stand-ins, get the
timings right, and when the real photographs arrive it is a file swap rather
than a rebuild.

## The one prompt rule that matters

Each frame must contain the **next** frame's subject, **small and centred**,
occupying roughly **10–14% of the frame width**.

That is the dive's target. The scale-in has to land on something, and if the next
subject is off-centre or already large there is nothing to fall into. Every
prompt below states where its target sits — do not drop that clause.

## Shared blocks

Append to every prompt.

**STYLE**
```
Cinematic photography, shot on an ARRI Alexa with a 40mm lens, f/5.6, cool
overcast dawn light falling from the upper left, muted palette of slate blue,
wet green and warm ochre, fine natural film grain, deep shadows that keep detail,
even exposure with no blown highlights, photoreal, no stylisation.
```

**NEGATIVE**
```
text, letters, numbers, watermark, signature, logo, UI, caption, borders, frame,
vignette, tilt-shift blur, lens flare, bokeh balls, HDR halo, oversaturated
colour, duplicated architecture, warped geometry, melted detail, plastic skin,
extra fingers, faces in close-up, motion blur, fisheye distortion
```

Light comes from the **upper left in every frame**. Five frames generated
separately will not match otherwise, and mismatched light is the one flaw the
choreography cannot hide.

Resolution: as large as it will give you. The last Gemini stills came out
2816x1536, which is ideal — these layers get scaled hard on the dive.

---

## 1. `range` — the widest frame

```
A vast range of steep green mountain ridges at dawn under low cloud, receding
layer behind layer into cool grey haze, the nearest ridge dark and detailed with
terraced cultivation cut into its flank, no sky above the horizon line visible,
and in the exact centre of the frame a tiny cluster of village rooftops perched
on a distant spur, occupying only about twelve percent of the frame width, small
enough that you would miss it if you were not looking.
```
16:9. The village cluster is the dive target — **dead centre, tiny**.

## 2. `village` — the rooftops

```
A hillside village of corrugated tin and timber rooftops packed tightly along a
steep ridge, seen from slightly above, rust reds and faded blues against wet
green vegetation, narrow steps and washing lines between the houses, cool
overcast morning light, and in the exact centre of the frame the dark mouth of a
single narrow covered lane running between two buildings, occupying about twelve
percent of the frame width, deep in shadow.
```
16:9. The lane mouth is the target — **centred, dark, small**. That darkness
matters: it is what the next frame opens out of.

## 3. `lane` — the market

```
Inside a narrow covered market lane, timber posts and hanging tarpaulins
overhead, stacked baskets and folded fabric along both sides, wet stone underfoot
catching a little light, cool daylight filtering down from a gap above, the lane
receding away from camera, and in the exact centre of the frame a small open
doorway with a wooden weaving loom just visible inside it, occupying about
thirteen percent of the frame width.
```
16:9. Keep the left and right thirds busy but **dim** — the panel copy sits over
them.

## 4. `loom` — the work

```
A traditional wooden backstrap weaving loom in a doorway, warp threads stretched
taut and evenly lit, a partly woven length of striped cloth in deep red, black
and ochre gathered at the near end, a shuttle and a bamboo beater resting across
the threads, worn timber and packed earth floor, cool light from the left, no
person in frame, and in the exact centre a small patch of the finished weave
sharply in focus, occupying about fourteen percent of the frame width.
```
16:9. **No hands or faces** — those need consent, and this is a stand-in. The
real piece uses your photographs.

## 5. `weave` — the last frame

```
An extreme macro photograph of handwoven cloth filling the entire frame,
individual cotton threads clearly separated, a deep red and black striped pattern
crossing at right angles, slubs and irregularities in the yarn, tiny loose fibres
catching the light, shallow depth of field so the weave softens toward the frame
edges, cool directional light from the upper left raking across the surface to
throw each thread into relief.
```
16:9. This is the floor of the dive. It should be **texture, not object** — the
thing you could never have seen from the mountain.

## 6. `dust` — atmosphere, optional but cheap

```
Fine airborne dust and lint drifting in a soft shaft of cool daylight, pale
motes at varying focal depths, no source visible, no objects, no surfaces, the
light falling away to nothing at all four edges, on a solid pure black
background.
```
16:9, **pure black**. Composited with `mix-blend-mode: screen`, where black is
already transparent — so it needs no keying and is immune to edge problems. One
layer of this drifting across the whole dive ties the five frames together.

---

## How it will be built

Five segments, one per dive, each doing the same three things at different scales:

| | motion |
|---|---|
| outgoing frame | `scale` up hard on a `snap` curve, `blur` rising, `opacity` to 0 |
| incoming frame | `clip` iris or `curtain` open from the centre, `blur` 9px to 0, `scale` settling on `back` |
| whole stack | slow `hue` drift cool to warm as you descend, `contrast` lifting |

The `dust` layer runs the full length on `screen`, drifting and rotating slowly,
so the dive feels like one continuous fall rather than five stacked crossfades.

## Hand-off

Drop them in `~/Downloads` and I will run:

```bash
python3 scripts/intake.py examples/thread --since 120
```

That finds them, strips the corner watermark this generator adds — measured at
(0.914w, 0.843h), height h/16, verified on two different resolutions — checks
whether the text bands are dark enough for cream type, and stages them into
`examples/thread/raw/`. Then I build the dive.
