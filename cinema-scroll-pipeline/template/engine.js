/*
 * engine.js — the brain. Generic, never edited per project.
 *
 * Reads a compiled scene (window.__CINEMA_SCENE__) and publishes numbers to CSS
 * custom properties on :root, once per animation frame. It never writes to an
 * element's style directly: the browser composites, JS only publishes.
 *
 * Progress is measured in ABSOLUTE PIXELS of scroll through the sticky stage,
 * not percentages, so the numbers in scene.json read like a timeline.
 */
(() => {
  "use strict";

  const SCENE = window.__CINEMA_SCENE__;
  if (!SCENE) return;

  const root = document.documentElement;
  const section = document.querySelector(".cinema-scroll");
  if (!section) return;

  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");

  const SCROLL_EASE = SCENE.smoothing == null ? 0.14 : SCENE.smoothing;
  const MOUSE_EASE = SCENE.mouseSmoothing == null ? 0.12 : SCENE.mouseSmoothing;
  const SNAP = 0.08;

  let targetScroll = 0;
  let smoothScroll = 0;
  let targetMouseX = 0;
  let targetMouseY = 0;
  let mouseX = 0;
  let mouseY = 0;
  let initialized = false;
  let rafPending = false;
  // Borrowed from how ThreeUI's canvas components behave: do no work while the
  // thing you are animating is not on screen. Without this, a pointermove over
  // a footer recomputes every variable in the scene.
  let onScreen = true;

  /* ---------- primitives ---------- */

  const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
  const lerp = (a, b, t) => a + (b - a) * t;

  const smoothstep = (e0, e1, v) => {
    const x = clamp((v - e0) / (e1 - e0));
    return x * x * (3 - 2 * x);
  };

  // The one choreography primitive: a scene with a fade-in window, a hold,
  // and a fade-out window, all keyed to absolute scroll pixels.
  const segmentInOut = (s, a, b, c, d) => {
    const enter = smoothstep(a, b, s);
    const exit = smoothstep(c, d, s);
    return { enter, exit, active: enter * (1 - exit) };
  };

  const getScrollDistance = () =>
    clamp(-section.getBoundingClientRect().top, 0, section.offsetHeight - window.innerHeight);

  /* ---------- driver resolution ----------
   * A driver is any 0..1 signal a track can be multiplied by:
   *   "progress"              scroll through the whole rig
   *   "frame2.enter"          a segment's enter / exit / active
   *   {"mouse": "x"}          pointer offset from centre, -0.5..0.5
   *   {"sum": [...]}          combined, with optional clamp / pow / oneMinus
   */
  function resolveDriver(spec, ctx) {
    if (spec == null) return 0;
    if (typeof spec === "number") return spec;

    if (typeof spec === "string") {
      if (spec === "progress") return ctx.progress;
      if (spec === "one") return 1;
      const dot = spec.indexOf(".");
      if (dot > 0) {
        const seg = ctx.segments[spec.slice(0, dot)];
        if (seg) {
          const key = spec.slice(dot + 1);
          if (key in seg) return seg[key];
        }
        return 0;
      }
      const seg = ctx.segments[spec];
      return seg ? seg.active : 0;
    }

    if (typeof spec === "object") {
      let v = 0;
      if (spec.mouse === "x") v = ctx.mx;
      else if (spec.mouse === "y") v = ctx.my;
      else if (Array.isArray(spec.sum)) v = spec.sum.reduce((a, x) => a + resolveDriver(x, ctx), 0);
      else if (Array.isArray(spec.product))
        v = spec.product.reduce((a, x) => a * resolveDriver(x, ctx), 1);
      else if (spec.of !== undefined) v = resolveDriver(spec.of, ctx);

      if (spec.oneMinus) v = 1 - v;
      if (spec.clamp) v = clamp(v);
      if (spec.pow) v = Math.pow(v, spec.pow);
      // back: overshoots past 1 then settles, so a move lands with weight
      if (spec.back) {
        const c1 = spec.back === true ? 1.70158 : spec.back;
        const c3 = c1 + 1;
        const t = v - 1;
        v = 1 + c3 * t * t * t + c1 * t * t;
      }
      // snap: front-loads the motion, fast out then a long settle
      if (spec.snap) {
        const k = spec.snap === true ? 3 : spec.snap;
        v = 1 - Math.pow(1 - clamp(v), k);
      }
      return v;
    }

    return 0;
  }

  /* ---------- track accumulation ----------
   * Every property starts at its base and each track ADDS
   * driver * amount. That additive model is what lets one layer answer to
   * scroll progress, a segment, and the pointer at the same time.
   */
  // must match UNIT_TOKEN in compile.py
  const UNIT_TOKEN = { "%": "pct" };

  function accumulate(vars, ctx) {
    const out = {};
    for (const prop in vars) {
      const buckets = vars[prop];
      for (const unit in buckets) {
        const spec = buckets[unit];
        let value = spec.base;
        const tracks = spec.tracks;
        if (tracks) {
          for (let i = 0; i < tracks.length; i += 1) {
            value += resolveDriver(tracks[i].drive, ctx) * tracks[i].amount;
          }
        }
        const token = UNIT_TOKEN[unit] || unit;
        out[token ? `${prop}-${token}` : prop] = { value, unit, prop };
      }
    }
    return out;
  }

  // Writing a custom property invalidates style for everything that reads it,
  // so a few hundred identical writes per frame is real main-thread cost during
  // a hold. Only publish what actually moved.
  const lastWritten = new Map();

  function setVar(name, value) {
    if (lastWritten.get(name) === value) return;
    lastWritten.set(name, value);
    root.style.setProperty(name, value);
  }

  function publish(prefix, resolved) {
    for (const name in resolved) {
      const r = resolved[name];
      setVar(`--${prefix}-${name}`, r.unit ? `${r.value}${r.unit}` : r.value);
    }
    // take fully transparent layers out of compositing altogether
    if ("opacity" in resolved) {
      setVar(`--${prefix}-vis`, resolved.opacity.value > 0.01 ? "visible" : "hidden");
    }
  }

  // scale lives in the unitless bucket, so look it up by prop name
  function scaleOf(resolved) {
    return resolved.scale ? resolved.scale.value : 1;
  }

  /* ---------- per-frame ---------- */

  function update() {
    rafPending = false;
    // variables keep their last values, which is the correct resting state
    if (!onScreen) return;

    targetScroll = getScrollDistance();
    if (!initialized || reduceMotion.matches) {
      smoothScroll = targetScroll;
      initialized = true;
    } else {
      smoothScroll = lerp(smoothScroll, targetScroll, SCROLL_EASE);
    }
    if (Math.abs(smoothScroll - targetScroll) < SNAP) smoothScroll = targetScroll;

    mouseX = lerp(mouseX, targetMouseX, MOUSE_EASE);
    mouseY = lerp(mouseY, targetMouseY, MOUSE_EASE);

    const mx = reduceMotion.matches ? 0 : mouseX;
    const my = reduceMotion.matches ? 0 : mouseY;

    const segments = {};
    const defs = SCENE.segments || {};
    for (const name in defs) {
      const w = defs[name];
      segments[name] = segmentInOut(smoothScroll, w[0], w[1], w[2], w[3]);
    }

    const span = SCENE.progressSpan || SCENE.scrollHeight || 1;
    const progress = clamp(smoothScroll / span);
    const ctx = { progress, segments, scroll: smoothScroll, mx, my };

    setVar("--mx", mx.toFixed(4));
    setVar("--my", my.toFixed(4));
    setVar("--progress", progress.toFixed(4));

    // Groups first: a group is a parent transform, so a stack of layers can
    // zoom or drift as one unit while each child still has its own motion.
    const groups = SCENE.groups || [];
    const groupScale = [];
    for (let i = 0; i < groups.length; i += 1) {
      const resolved = accumulate(groups[i].vars, ctx);
      publish(`g${i}`, resolved);
      groupScale[i] = scaleOf(resolved);
    }

    const layers = SCENE.layers || [];
    for (let i = 0; i < layers.length; i += 1) {
      publish(`l${i}`, accumulate(layers[i].vars, ctx));
    }

    const panels = SCENE.panels || [];
    for (let i = 0; i < panels.length; i += 1) {
      const panel = panels[i];
      const seg = ctx.segments[panel.segment];
      if (seg) {
        const opacity = seg.active * (1 - seg.exit);
        const y = -seg.exit * panel.exitSlide + (1 - seg.enter) * panel.enterSlide;
        setVar(`--p${i}-opacity`, opacity);
        setVar(`--p${i}-y`, `calc(-50% + ${y}px)`);
      }
      if (panel.vars) publish(`p${i}v`, accumulate(panel.vars, ctx));
    }

    const shade = SCENE.shade;
    if (shade) {
      const drive = resolveDriver(shade.drive, ctx);
      setVar("--shade-top-alpha", drive * shade.top);
      setVar("--shade-mid-alpha", drive * shade.mid);
      setVar("--shade-bottom-alpha", drive * shade.bottom);
      setVar("--shade-z", drive > (shade.liftAt == null ? 0.02 : shade.liftAt) ? "2" : "0");
    }

    // Keep any element screen-true inside a parent that is still scaling.
    const counter = SCENE.counterScale;
    if (counter) {
      const s =
        counter.group != null
          ? groupScale[counter.group] || 1
          : (() => {
              return scaleOf(accumulate(SCENE.layers[counter.layer].vars, ctx));
            })();
      setVar("--counter-scale", 1 / s);
      if (counter.screenTop != null) {
        const screenTop =
          Math.min(counter.max, Math.max(counter.min, window.innerHeight * counter.vh)) -
          counter.screenTop;
        const parentTop = window.innerHeight - (window.innerHeight - screenTop) / s;
        setVar("--counter-screen-top", `${screenTop}px`);
        setVar("--counter-parent-top", `${parentTop}px`);
      }
    }

    if (
      Math.abs(smoothScroll - targetScroll) > SNAP ||
      Math.abs(mouseX - targetMouseX) > 0.001 ||
      Math.abs(mouseY - targetMouseY) > 0.001
    ) {
      requestTick();
    }
  }

  function requestTick() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(update);
  }

  /* ---------- listeners ---------- */

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(
      (entries) => {
        const wasOff = !onScreen;
        onScreen = entries[0].isIntersecting;
        if (onScreen && wasOff) requestTick();   // resync on the way back in
      },
      { rootMargin: "15% 0px" }
    ).observe(section);
  }

  window.addEventListener("scroll", requestTick, { passive: true });
  window.addEventListener("resize", requestTick);
  window.addEventListener(
    "pointermove",
    (event) => {
      if (!onScreen) return;
      targetMouseX = event.clientX / window.innerWidth - 0.5;
      targetMouseY = event.clientY / window.innerHeight - 0.5;
      requestTick();
    },
    { passive: true }
  );

  // Expose the primitives so a project can add bespoke UI on the same clock.
  window.cinema = { clamp, lerp, smoothstep, segmentInOut, requestTick, resolveDriver };

  requestTick();
})();
