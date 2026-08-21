# Mizoram — intake brief

A real story from a real trip. The rule for this one: **nothing goes on the page
that we cannot source.** You were there, so you are the source. I will not invent
place names, dance names, festival names, dates or figures — if I need one and do
not have it from you or a citable reference, it stays off the page.

## Where to put things

```
examples/mizoram/raw/      the photographs — ORIGINALS, untouched
examples/mizoram/video/    the dance video — original file
```

**Do not resize, crop, compress or re-export anything.** I need full resolution
because layers get scaled up at runtime, and I need the EXIF intact because that
is how I reconstruct the trip.

Filenames do not matter. Dump them in.

## What I do with them

**Read the EXIF.** Capture time, GPS, lens, orientation. That gives me a real
timeline and real locations, which becomes the narrative spine — a story ordered
by what actually happened, not by what I guessed looked good.

**Measure each frame** for what the engine cares about: resolution, aspect, where
the subject sits, and whether there is a dark enough region for cream type. Same
checks I ran on the Petra layers.

**Group into beats** by time and place, then propose a story arc for you to
approve before I build anything.

## What I need from you in words

Pixels cannot tell me these:

1. **Where** — the places, spelled the way you would spell them.
2. **When** — roughly which days, so I can sanity-check EXIF against reality.
3. **The dance** — what it is actually called, what the occasion was, who was
   dancing and why. This is the heart of the piece and the thing I am least
   willing to guess about.
4. **The market** — where, and what was being sold.
5. **What stayed with you.** One or two moments that mattered. That is usually
   the real story; the rest is context.

## Consent

The dance photographs and video show identifiable people. Before anything with
their faces goes on a page that can be shared, I need to know they are happy to be
published. If that is uncertain for some frames, say so and I will build the story
around the ones that are cleared — there is always a way to tell it without
putting someone on the internet who did not agree to it.

## One honest technical limit

Generated layers came with a magenta backdrop, so keying them was exact.
Photographs have no backdrop, so separating a subject from its background needs
real segmentation. That means one of:

- **Full-frame techniques only** — depth push, crossfade, parallax between whole
  frames, grade shifts. Works immediately, no cutouts, and it is most of what the
  Petra piece actually does well.
- **Install a segmentation model** (`rembg`, ~180 MB) — worth it for the dancers
  specifically, where separating a figure from the background would let her move
  against the mountains with real depth. Your call whether we add the dependency.
- **Hand masks** for two or three hero frames only.

The parting mechanic that made the Siq work needs cut layers, so it does not
transfer to raw photographs for free. I would rather say that now than promise it
and walk it back.

## The video

Two pipelines are available and they suit different things:

- `cinema-scroll-pipeline` (this one) — layered stills, scroll-driven
- `scroll-scrub-pipeline` — a video scrubbed frame by frame as you scroll

A dance is cyclical, and the scrub technique wants motion that changes in one
direction so that scrolling back means something. I will check the footage against
that before proposing it, rather than assuming it fits.
