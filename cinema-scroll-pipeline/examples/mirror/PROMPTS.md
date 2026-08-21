# Mirror — the physics, and what the images have to be

## What the effect actually is

Strip the fiction away and the Mirror Dimension is three real pieces of optics
and geometry stacked on each other.

**1. A dihedral reflection group.** A kaleidoscope with N mirrors generates the
symmetry group D(N): N rotations and N reflections. The reason a real
kaleidoscope looks *solid* rather than like a collage is that adjacent cells are
**reflections of each other, not copies**. Where two cells meet, the image runs
into its own mirror image, so every line crosses the seam at the same angle it
arrived. The seam disappears. Rotate instead of reflect and every seam becomes a
visible cut.

**2. Catoptrics — the count is fixed by the angle.** Two mirrors at angle θ
produce 360/θ − 1 images. At 45° that is seven reflections plus the original:
eight cells. The angle is not a style choice, it is the cell count.

**3. Conformal mapping for the recursion.** The endless-repetition look — Escher's
*Print Gallery*, the Droste effect — is a logarithmic spiral conformal map. It
preserves angles while scaling, which is why the repeats look like the same
building rather than a distorted one.

So the whole thing is **rigorous, not chaotic**. That is the aesthetic point: the
city folds but nothing tears. Every constraint below follows from that.

## What the source image must therefore be

These are consequences, not preferences.

**A vanishing point dead centre.** The wedges pivot about the frame centre. If the
image already recedes to a point there, the eight cells converge into one coherent
tunnel. If the vanishing point is off-centre it is reflected to eight different
places and the figure has no focus. *This is the single most important property.*

**Flat, frontal, directionless light.** Mirroring flips the light direction. A
source lit strongly from the left produces a neighbour lit from the right, the two
disagree across the seam, and the eye reads it as a collage. Ambient, frontal or
symmetric light is the only kind that survives reflection. This is the constraint
I got wrong in the first prototype.

**Straight lines radiating from the centre.** Fold seams have to land on real
architectural lines. Where a wedge boundary crosses a girder or a cornice, the
reflection continues it and the seam vanishes. Organic curves — foliage, cloth,
crowds — cannot continue across a mirror, so they expose the cut.

**Repeating modular elements.** Windows, columns, arches, tiles, balustrades. A
module meeting its own reflection reads as more of the same structure. Unique
objects read as duplicated mistakes.

**Content to all four edges, and no sky.** The cells are radial, so the frame
corners land on the outer rim. Empty sky becomes a dead ring around everything.

**Dark, desaturated, with bright linear accents.** The accents give the fold
seams something to catch, and the darkness is what lets cream type sit on top.

**No faces, no text, no single off-centre subject.** Anything identifiable appears
eight times at once, which is comic rather than uncanny.

The ideal subject is therefore an **architectural interior photographed straight
down its own axis** — or better, straight up. A vertical shot up a light well is
already centrally symmetric, every line already converges to the middle, the
modules already repeat, and there is no horizon to break.

---

## Shared blocks

**STYLE**
```
Architectural photography, shot on a 16mm rectilinear ultra-wide lens, f/8, flat
even ambient light with no directional shadow, cool desaturated palette of
graphite, slate and pale concrete, restrained warm accents, fine natural film
grain, deep shadows that retain detail, absolutely symmetrical composition,
photoreal, no stylisation.
```

**NEGATIVE**
```
text, letters, numbers, signage, watermark, logo, UI, caption, people, faces,
crowds, animals, vehicles, sky, clouds, horizon, sun, strong directional light,
hard cast shadows, lens flare, bokeh, tilt-shift blur, vignette, border, frame,
fisheye distortion, curved lines, warped architecture, asymmetry, off-centre
composition, single focal object, oversaturated colour, HDR halo
```

Note `asymmetry` and `off-centre composition` in the negatives, and `sky` — those
are load-bearing here, not boilerplate.

Square or near-square output if the tool allows it: the wedges are cut from a
square element, so a 1:1 source wastes nothing. Otherwise 16:9 is fine.

---

## 1. `axis` — the fold source, and the most important one

```
Looking straight up the interior light well of a vast concrete and steel
building, perfect one-point symmetry with the vanishing point exactly at the
centre of the frame, dozens of identical floors receding upward and inward,
repeating rectangular window bays and steel walkway railings on every level,
straight structural lines radiating from the centre of the frame to all four
corners, flat even ambient light with no sun and no directional shadow, graphite
and pale concrete, a few small warm interior lights as accents, the structure
filling the entire frame edge to edge with no sky visible at the centre.
```
The centre must be **structure, not sky**. If the shaft opens to daylight the
kaleidoscope gets a blown-out hole in the middle where its focus should be.

## 2. `street` — the ordinary world, before the fold

```
A narrow city street between tall buildings photographed dead straight down its
centre line, perfect one-point perspective with the vanishing point exactly in
the middle of the frame, identical facades and window rows repeating away on both
sides in strict symmetry, fire escapes and cornice lines running straight toward
the centre, wet asphalt reflecting evenly, flat overcast ambient light with no
directional shadow, cool graphite and slate palette, no people, no vehicles, the
buildings closing the top of the frame so almost no sky is visible.
```
Same geometry as `axis` but horizontal, so the fold can begin from something that
reads as an ordinary place.

## 3. `seams` — prismatic fold edges, on black

```
Thin sharp iridescent light streaks of refracted spectrum, like the edge of a
prism or a thin film of oil, arranged as fine straight rays crossing a pure black
field, subtle cyan magenta and gold separation along each streak, no source
visible, no objects, no surfaces, no glow blooms, the streaks fading to nothing at
all four edges, on a solid pure black background.
```
Pure black, composited with `mix-blend-mode: screen` — black is already
transparent there, so no keying, and no edge artefacts. This is what will catch
along the wedge boundaries and sell the fold as refraction rather than a cut.

## 4. `void` — depth behind the gaps

```
A deep dark abstract field of faint volumetric haze, almost black, with a very
slight cool gradient from the centre outward and a barely visible suggestion of
immense distance, no stars, no objects, no structures, no discernible surface,
extremely low contrast, smooth and free of banding, filling the entire frame.
```
This fixes a real defect in the first prototype: when the wedges hinge out of
plane they separate, and the gaps between them showed the page background, which
read as broken. A void behind turns those gaps into depth.

---

## What still needs fixing on my side

The wedges currently hinge about the **shared centre**, so rotating them out of
plane pulls them apart into a radial fan. Real folding needs each wedge to pivot
about **its own radial edge** — a per-wedge `transform-origin` on the boundary
rather than `50% 50%`. That is a code change, not an image problem, and it is next
regardless of what you send.
