# Layer prompts — Petra / the Siq reveal

Seven layers that map 1:1 onto `examples/mostar/scene.json`, so the built scene
is a URL swap plus a few number tweaks.

| # | layer | role in the engine | Mostar equivalent |
|---|---|---|---|
| 1 | `sky` | full-bleed `fit: cover`, blurs + darkens | sky |
| 2 | `cliffs-far` | in the zooming `back` group, blurs | back-bazaar |
| 3 | `dust-veil` | `screen` blend, drifts up | back-four |
| 4 | `treasury` | the anchor: widens, lifts, launches | bridge |
| 5 | `siq-left` | parts to −46vw | splitframe-left |
| 6 | `siq-right` | parts to +46vw | splitframe-right |
| 7 | `reveal-detail` | fades in behind the parting walls | frame-two |

---

## Read this before generating

**Generate the master frame first (step 1), then derive every layer from it.**
Seven independently generated images will not share light direction, palette or
haze density, and mismatched lighting is the one flaw that cannot be fixed by
tuning the scroll. If your tool supports image-reference / style-reference or
img2img, point every layer generation at the master.

**Backdrop for cut-out layers (2–7):** solid pure magenta `#FF00FF`, no shadow
falling on the backdrop, no gradient. Magenta never occurs in sandstone, so it
keys out cleanly and I can do the cutout locally and deterministically. If your
generator emits real alpha PNGs, use that instead and skip the magenta.

**Size:** the biggest your tool allows, minimum **2560px wide**, ideally 3840.
This is not padding — the CSS scales these layers up at runtime: splitframes
reach `118vw × 1.74`, the anchor `105vw × 1.62`. Undersized layers soften
visibly exactly when they are largest on screen.

**Composition rule:** keep the **centre band dark and low-detail**. The hero
title sits at `clamp(122px, 19vh, 205px)` and the story panels at 29% / 45% /
60% height, all centred, in cream `#fdf1e1`. Busy or bright centres make that
text unreadable and no grade will save it.

**Aspect:** 16:9 for layers 1, 2, 7. Roughly 1:1 or 4:5 tall for 5 and 6 (they
are vertical slabs). Layer 4 is 16:9 but the subject occupies the centre third.

---

## Shared blocks

Append **STYLE** and **NEGATIVE** to every prompt.

**STYLE**
```
Cinematic architectural photography, shot on an ARRI Alexa with a 35mm anamorphic
lens, f/8, dawn light raking from the upper right at a low angle, deep cool
blue-grey shadows, warm amber sandstone highlights, muted teal-and-amber palette,
fine natural film grain, thin layer of atmospheric dust haze, even exposure with
no blown highlights, photoreal.
```

**NEGATIVE**
```
text, letters, numbers, watermark, signature, logo, UI, caption, people, tourists,
crowds, animals, camels, vehicles, modern signage, power lines, scaffolding,
lens flare, bokeh balls, tilt-shift blur, vignette, border, frame, passepartout,
canvas texture, oversaturated colour, HDR halo, duplicated architecture, warped
columns, melted stone, extra doorways, motion blur, drop shadow on background.
```

---

## 1. Master frame (reference only — not a layer)

```
A wide cinematic view from inside the Siq at Petra: a narrow slot canyon of towering
striated sandstone walls opening at the centre onto the carved rock facade of
Al-Khazneh in the far distance, the facade small and centred and catching the first
warm dawn light, canyon walls in deep cool shadow on both sides, dry sandy canyon
floor leading away from camera toward the facade, fine dust suspended in a shaft of
low sunlight from the upper right, dawn sky visible as a thin bright ribbon far
overhead between the canyon rims, empty and silent, no people.
```

Keep this image. Every layer below is a separation of this scene.

---

## 2. `sky` — full bleed, no cutout

```
Only the sky above a slot canyon at dawn, seen looking almost straight up: a smooth
gradient from deep indigo at the top to pale warm apricot near the horizon line, a
few very thin high cirrus streaks catching pink dawn light, soft dust haze, no
clouds with hard edges, no sun disc in frame, no landscape, no rock, sky filling
the entire frame edge to edge.
```
16:9, ≥2560px. **No magenta** — this layer is a full-bleed background.

---

## 3. `cliffs-far` — cut out

```
A distant massif of eroded sandstone cliffs and rounded rock domes receding into
dawn haze, seen from below, only the upper silhouette and its sunlit crowns visible,
horizontal strata bands in amber and rose, the lower third dissolving into pale dust
haze, flat frontal composition with no foreground, isolated on a solid pure magenta
background above the rock line.
```
16:9, ≥2560px, magenta backdrop. The rock must reach the **left and right frame
edges** — this layer sits full-bleed inside the zooming group and a margin would
show as a seam.

---

## 4. `dust-veil` — cut out, will be `screen` blended

```
A single soft shaft of low dawn sunlight cutting diagonally from the upper right
through suspended fine dust, rendered as pale warm translucent light with visible
floating dust motes, no visible source, no rock, no ground, no hard edges anywhere,
the light fading smoothly to nothing at all four frame edges, isolated on a solid
pure black background.
```
16:9, ≥2560px. **Pure black backdrop, not magenta** — this layer is composited
with `mix-blend-mode: screen`, where black is already transparent, so it needs no
cutout at all.

---

## 5. `treasury` — the anchor, cut out

```
The full carved rock facade of Al-Khazneh at Petra, shot straight on and centred,
two storeys of Hellenistic columns, pediment and the central urn, carved from rose
and amber sandstone, lit by low warm dawn light raking from the upper right so the
columns cast long shallow shadows across the facade, the recessed doorway at the
centre in deep shadow, complete facade with the rock base visible, isolated on a
solid pure magenta background.
```
16:9, ≥3000px, magenta backdrop. The facade should occupy the **centre third**
with clear magenta on both sides — the engine widens this layer from `67.2vw` to
`105vw`, so side margin is what lets it grow without clipping. The dark central
doorway is deliberate: it is what the story panels sit against.

---

## 6. `siq-left` — cut out

```
The left-hand wall of a narrow slot canyon at Petra, a towering vertical slab of
striated sandstone filling the frame from top to bottom, deep cool blue-grey shadow
across most of the face with a thin rim of warm dawn light catching the upper right
edge, flowing horizontal water-worn strata, the rock face angled so it recedes away
to the right, the right-hand quarter of the frame open to solid pure magenta, no
sky, no floor.
```
Tall — 4:5 or 1:1, ≥2560px on the long edge, magenta backdrop.

The rock must be **flush to the left, top and bottom frame edges** with magenta
only on the right. This layer's `transform-origin` is `21% 52%` and it translates
to `−46vw`, so its left edge leaves the viewport first: any transparent margin on
the left shows as a gap opening at the screen edge.

---

## 7. `siq-right` — cut out

```
The right-hand wall of a narrow slot canyon at Petra, a towering vertical slab of
striated sandstone filling the frame from top to bottom, deep cool blue-grey shadow
with a strong rim of warm dawn light down the upper left edge, flowing horizontal
water-worn strata, the rock face angled so it recedes away to the left, the
left-hand quarter of the frame open to solid pure magenta, no sky, no floor.
```
Tall, mirror of layer 6, ≥2560px, magenta backdrop. Rock flush to the **right,
top and bottom** edges. `transform-origin: 79% 52%`.

These two must read as **one canyon split down the middle** — same strata scale,
same shadow depth, light consistently from the upper right (so the left wall is
lit on its right edge and the right wall on its left edge). Generate them as a
pair, in one session, ideally by generating one wall and mirroring it before
re-lighting.

---

## 8. `reveal-detail` — cut out

```
An extreme close-up of the carved sandstone columns of Al-Khazneh, two weathered
Corinthian capitals and the fluted column shafts filling the whole frame, shallow
depth of field with the stone grain crisp, warm dawn light grazing across the
carving from the upper right and picking out every chisel mark and erosion pit,
deep shadow between the columns, rose and amber sandstone, isolated on a solid pure
magenta background at the frame edges only.
```
16:9, ≥2560px, magenta backdrop. This is revealed *behind* the parting walls, so
it should be **tighter and more textural** than layer 5 — the payoff for
scrolling is detail you could not see before.

---

## Hand-off

Drop the files in `examples/petra/raw/` and tell me. I will:

1. key the magenta (and trim the black on the veil) with a tuned edge feather
2. check every layer reaches the frame edges it needs to, and report any that do not
3. verify the centre-band luminance against the cream text and report the number
4. write `examples/petra/scene.json` and build it
5. render stills at each segment boundary so you can see the choreography

If a layer comes back with soft or fringed edges I will say so rather than ship a
halo — semi-transparent dust and frayed rock edges are the known weak spot of
chroma keying, and layer 4 avoids it by being additive instead.
