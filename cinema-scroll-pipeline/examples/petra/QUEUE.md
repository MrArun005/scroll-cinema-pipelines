# Remaining layer queue — send in this order

Done: `master.png` (watermark removed) · `sky.png` · `cliffs.png` · `rays.png`

Append **STYLE** + **NEGATIVE** to every prompt below.

**STYLE**
```
Cinematic architectural photography, shot on an ARRI Alexa with a 35mm anamorphic
lens, f/8, dawn light raking from the upper right at a low angle, deep cool
blue-grey shadows, warm amber sandstone highlights, muted teal-and-amber palette,
fine natural film grain, even exposure with no blown highlights, photoreal.
```

**NEGATIVE**
```
text, letters, numbers, watermark, signature, logo, UI, caption, people, tourists,
animals, vehicles, modern signage, scaffolding, lens flare, bokeh balls, vignette,
border, frame, canvas texture, oversaturated colour, HDR halo, duplicated
architecture, warped columns, melted stone, motion blur, drop shadow on background,
haze over background, fog over background, gradient background, soft edges,
translucent rock edges
```

The last five negatives matter: a previous cliffs generation came back with the
scene's dust haze painted across the magenta, which made it 0.0% keyable.

---

## 1. `siq-left` — portrait 4:5, magenta right third

```
The left-hand wall of a narrow slot canyon at Petra, a towering vertical slab of
striated sandstone filling the frame from top to bottom, deep cool blue-grey shadow
across most of the face with a thin rim of warm dawn light catching the upper right
edge, flowing horizontal water-worn strata, the rock face angled so it recedes away
to the right, the right-hand third of the frame is a solid flat pure magenta #FF00FF
background with absolutely no haze, no dust, no fog, no gradient and no atmosphere
over it, the magenta must be perfectly uniform, hard clean edge between rock and
magenta, no sky, no floor.
```
Rock flush to **left, top, bottom**. Origin `21% 52%`, exits leftward.

## 2. `siq-right` — portrait 4:5, magenta left third

```
The right-hand wall of a narrow slot canyon at Petra, a towering vertical slab of
striated sandstone filling the frame from top to bottom, deep cool blue-grey shadow
with a strong rim of warm dawn light down the upper left edge, flowing horizontal
water-worn strata, the rock face angled so it recedes away to the left, the
left-hand third of the frame is a solid flat pure magenta #FF00FF background with
absolutely no haze, no dust, no fog, no gradient and no atmosphere over it, the
magenta must be perfectly uniform, hard clean edge between rock and magenta, no
sky, no floor.
```
Rock flush to **right, top, bottom**. Origin `79% 52%`, exits rightward. Must match
#1's strata scale and shadow depth — same session, ideally mirror then re-light.

## 3. `reveal-detail` — 16:9, magenta at edges only

```
An extreme close-up of the carved sandstone columns of Al-Khazneh at Petra, two
weathered Corinthian capitals and the fluted column shafts filling the whole frame,
stone grain crisp and sharp, warm dawn light grazing across the carving from the
upper right picking out every chisel mark and erosion pit, deep shadow between the
columns, rose and amber sandstone, solid flat pure magenta #FF00FF only at the
extreme frame edges with no haze or gradient over it.
```
Tighter and more textural than the master — this is the payoff revealed behind the
parting walls, so it must show detail the wide shot could not.

## 4. `treasury` — 16:9, facade in the centre third

```
The full carved rock facade of Al-Khazneh at Petra, shot straight on and centred,
two storeys of Hellenistic columns, pediment and the central urn, carved from rose
and amber sandstone, lit by low warm dawn light raking from the upper right so the
columns cast long shallow shadows, the recessed central doorway in deep shadow,
complete facade with the rock base visible, the facade occupying only the middle
third of the frame with solid flat pure magenta #FF00FF on both sides and above,
perfectly uniform magenta with no haze or gradient over it.
```
Side margin is required — the engine widens this from `67.2vw` to `105vw`, and it
needs room to grow into. Keep the central doorway dark; panels sit against it.

## 5. `dust-veil` — 16:9, **BLACK** backdrop, no cutout needed

```
A single soft shaft of low dawn sunlight cutting diagonally from the upper right
through suspended fine dust, pale warm translucent light with visible floating dust
motes, no visible source, no rock, no ground, no hard edges anywhere, the light
fading smoothly to nothing at all four frame edges, on a solid pure black
background.
```
Black, not magenta — this composites with `mix-blend-mode: screen`, where black is
already transparent. No keying, so it is immune to the soft-edge problem.

---

Priority: **1 and 2 unlock the parting reveal** and make `sky` + `cliffs` visible
from the first frame instead of only in act 3. **3** is the payoff. **4** and **5**
are polish. Portrait aspect on 1 and 2 puts pixels where those layers get scaled
hardest (`118vw x 1.74`).
