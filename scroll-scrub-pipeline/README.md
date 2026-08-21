# scroll-scrub pipeline

Video in, finished single-file scroll-scrub site out. One command.

Scroll down and the footage plays forward. Scroll up and it plays backward.
Done with a frame sequence painted to a canvas — not a `<video>` element,
because scrubbing `video.currentTime` seeks to the nearest keyframe and
stutters badly on iOS.

## Requirements

```bash
ffmpeg              # apt install ffmpeg  /  brew install ffmpeg
python3 -m pip install pillow numpy
```

## Use

```bash
./build.sh input.mp4 site.html
```

That's it. `site.html` is self-contained — open it directly, no server, no
folder alongside it. Every frame is base64-embedded inside the HTML.

With options:

```bash
./build.sh input.mp4 site.html \
  --title "Held" \
  --budget 5 \
  --delogo x=1132:y=576:w=54:h=52
```

| Option | Default | What it does |
|---|---|---|
| `--budget N` | 5 | Target output size in MB |
| `--delogo BOX` | — | Inpaint a watermark: `x=..:y=..:w=..:h=..` |
| `--crop BOX` | — | Crop `w:h:x:y`, e.g. a portrait reframe |
| `--title TEXT` | Scroll | Page title and wordmark |
| `--quality N` | 82 | WebP quality |
| `--fps N` | auto | Force a framerate |
| `--no-grade` | — | Skip colour grading |
| `--keep-frames` | — | Leave the frame directory for inspection |

### Removing a watermark

Auto-detection is unreliable — static scenery looks identical to a static
watermark. So look at it instead:

```bash
python3 scripts/analyse.py input.mp4 --corners
```

That writes `watermark-corners.png`: the four corners of the last frame at 2x,
each labelled with its pixel origin. Find the mark, read its offset inside the
tile, add the tile origin, pass it as `--delogo`. Ten seconds, right every time.

Inpainting beats cropping because it keeps the full frame. Crop only if the
mark moves or is too large to inpaint cleanly.

### Checking footage before you commit to it

```bash
python3 scripts/analyse.py input.mp4
```

```
  source      1280x720  9.0s  24fps
  text zone   mean 34, bright 2.1%  -> already legible
  grade       light (already dark)
  motion      step 4.8 -> minimum 14fps
  cuts        NONE - continuous
```

- **text zone** — mean luminance and bright-pixel share of the left 40%, where
  the copy sits. Under 55 mean and under 5% bright means white text is safe.
- **grade** — chosen automatically from that measurement. Bright daylight
  footage gets a heavy grade, which changes the mood; check the result.
- **motion** — fast motion needs more frames or it steps visibly.
- **cuts** — a cut reads as a broken image load. Regenerate without them.

## What the budget actually trades

Resolution is never reduced. The budget is met by lowering **frame count**,
because resolution is what you see and framerate is what the easing hides.

Base64 inflates everything by 4/3, so a 5 MB page holds about 3.7 MB of frames.
At full HD that's roughly 125 frames at quality 82.

If the build warns that the budget only allows 6fps but the motion wants 18,
raise `--budget`. 5 MB suits a slow transformation; fast camera moves want 8-10.

## Footage that works

> Something in the frame must change monotonically, and the change must mean
> something in both directions.

Two kinds both work:

- **Subject transforms, camera locked** — a flower opening, a sphere
  shattering. The fixed frame leaves a text column free the whole scroll.
- **Camera moves toward an anchor** — a POV approach to a lighthouse, a rise
  past a building. The subject growing is the transformation.

What fails is footage with **no anchor**: a drive down an open road, a flight
over terrain. Nothing arrives, so scrolling back conveys nothing.

Also avoid: cuts, out-and-back moves (the closest point lands at 50% of scroll
and the bottom of the page looks like the top), and bright daylight (nowhere in
frame is dark enough for white text without a grade heavy enough to change what
the footage is).

Generation prompt block that covers it:

```
MOTION: one continuous change in a single direction. No cuts, no reversal.
Subtle natural motion blur.
COMPOSITION: subject right of center at 62%. Left third stays empty and dark.
ARC: reaches about 70% by the final frame — still in progress, not finished.
BACKGROUND: pure black void. No scenery, no horizon.
NEGATIVE: text, watermarks, logos, people, cuts, camera reversing, flicker,
bright background, daylight.
```

Expect roughly a 1-in-3 hit rate. Generate five or six, keep two.

## What's in the page

The template is a working site, not a demo. Replace the copy in
`template/page.html`; the parts worth keeping are structural.

- **Inertia.** `eased += (target - eased) * 0.12` — the frame index chases
  scroll rather than snapping to it, so the sequence has mass and settles after
  a fling. This is the single biggest quality difference. Use `0.12` for heavy
  subjects, `0.25` for mechanical ones.
- **End holds.** 5% of scroll at each end parks on the first and last frame, so
  the transformation lands and holds before the page moves on.
- **Progressive boot.** Starts on 24 frames and pumps the rest in the
  background, rather than blocking on all of them.
- **Nearest-ready fallback.** Scroll ahead of the buffer and it paints the
  closest decoded frame instead of going blank.
- **Mobile memory window.** Under 820px it keeps ±40 frames around the playhead
  and releases the rest. 200+ full-resolution frames is 700 MB of decoded
  bitmap, which reliably crashes iOS Safari.
- **DPR capped at 2**, `100svh` not `100vh`, `env(safe-area-inset-*)` padding,
  and a reduced-motion fallback that unstacks the panels.

## Files

```
build.sh              one command, video -> site
scripts/analyse.py    measurement, grade selection, watermark contact sheet
scripts/embed.py      frames -> single self-contained HTML
template/page.html    the scrubber page
```

## Troubleshooting

**Page sits at the loader.** Almost always a folder-based build opened over
`file://`. Builds from `build.sh` are self-contained and don't have this
problem.

**Visible stepping.** Low framerate on a sharp subject. Raise `--budget`, or
regenerate the source asking for motion blur.

**Reverse feels like nothing.** No anchor in the footage. See above.

**Text hard to read.** Run `analyse.py`. If the text zone is over 55 mean the
grade will fire automatically — check whether the result still looks like the
film you wanted.

**Tab reloads mid-scroll on iOS.** Too much decoded bitmap. Lower `--budget`.
