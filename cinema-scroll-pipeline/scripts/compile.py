#!/usr/bin/env python3
"""
compile.py — scene.json -> a standalone cinematic scroll site.

  python3 compile.py scene.json out/

Emits out/index.html, out/styles.css, out/engine.js. Local layer images are
copied into out/layers/; remote URLs are referenced as-is.

The compiler does three things and nothing else:
  1. validates the scene and fails loudly on a bad reference
  2. normalises every value into {base, unit, tracks} so the engine stays dumb
  3. generates the per-layer CSS that wires elements to the engine's variables

Everything about HOW it moves lives in scene.json. Everything about WHAT the
numbers mean lives in template/engine.js.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "template")

# prop -> (css role, default base, default unit)
PROPS = {
    "x": ("transform", 0.0, "px"),
    "y": ("transform", 0.0, "px"),
    "scale": ("transform", 1.0, ""),
    "scaleX": ("transform", 1.0, ""),
    "scaleY": ("transform", 1.0, ""),
    "rotate": ("transform", 0.0, "deg"),
    "rotateX": ("transform", 0.0, "deg"),
    "rotateY": ("transform", 0.0, "deg"),
    "hinge": ("transform", 0.0, "deg"),
    "clip": ("clip", 1.0, ""),
    "opacity": ("plain", 1.0, ""),
    "blur": ("filter", 0.0, "px"),
    "brightness": ("filter", 1.0, ""),
    "contrast": ("filter", 1.0, ""),
    "saturate": ("filter", 1.0, ""),
    "hue": ("filter", 0.0, "deg"),
    "width": ("box", None, "vw"),
    "height": ("box", None, "vh"),
    "top": ("box", None, "vh"),
    "bottom": ("box", None, "vh"),
    "left": ("box", None, "vw"),
    "right": ("box", None, "vw"),
}

NUM = re.compile(r"^\s*(-?\d*\.?\d+)\s*([a-z%]*)\s*$")


def die(msg):
    sys.exit(f"compile.py: {msg}")


def parse_value(raw, prop):
    """'67.2vw' -> (67.2, 'vw');  1.02 -> (1.02, default unit)."""
    default_unit = PROPS[prop][2]
    if isinstance(raw, (int, float)):
        return float(raw), default_unit
    if not isinstance(raw, str):
        die(f"cannot read value {raw!r} for {prop}")
    m = NUM.match(raw)
    if not m:
        die(f"cannot parse {raw!r} for {prop} (expected a number with optional unit)")
    return float(m.group(1)), (m.group(2) or default_unit)


def build_vars(spec, segments, label):
    """
    Turn a layer/panel block into {prop: {unit: {base, tracks[]}}}.

    A property is keyed by unit as well as name, because one axis legitimately
    mixes units -- a layer can drift -46vw with the scroll AND 22px with the
    pointer. Each (prop, unit) pair becomes its own CSS variable and the
    generated calc() sums them.
    """
    base_block = spec.get("base", {})
    out = {}

    def ensure(prop, unit):
        if prop not in PROPS:
            die(f"{label}: unknown property {prop!r} (known: {', '.join(sorted(PROPS))})")
        buckets = out.setdefault(prop, {})
        if unit not in buckets:
            default = PROPS[prop][1]
            # only the layer's declared-unit bucket carries the base value;
            # extra unit buckets start at 0 so they are pure offsets
            seed = 0.0 if (default is None or buckets) else default
            buckets[unit] = {"base": seed, "tracks": []}
        return buckets[unit]

    for prop, raw in base_block.items():
        value, unit = parse_value(raw, prop)
        ensure(prop, unit)["base"] = value

    # parallax sugar: {"x": "18px", "y": "8px"} -> two mouse-driven tracks
    for axis, raw in (spec.get("parallax") or {}).items():
        if axis not in ("x", "y"):
            die(f"{label}: parallax axis must be x or y, got {axis!r}")
        amount, unit = parse_value(raw, axis)
        ensure(axis, unit)["tracks"].append({"drive": {"mouse": axis}, "amount": amount})

    for i, track in enumerate(spec.get("tracks") or []):
        where = f"{label} track #{i}"
        prop = track.get("prop") or die(f"{where}: missing 'prop'")
        drive = track.get("drive")
        if drive is None:
            die(f"{where}: missing 'drive'")
        validate_driver(drive, segments, where)

        if "to" in track:
            to_v, unit = parse_value(track["to"], prop)
            if "from" in track:
                from_v, from_u = parse_value(track["from"], prop)
                if from_u != unit:
                    die(f"{where}: 'from' unit {from_u!r} != 'to' unit {unit!r}")
                ensure(prop, unit)["base"] = from_v
            amount = to_v - ensure(prop, unit)["base"]
        elif "amount" in track:
            amount, unit = parse_value(track["amount"], prop)
        else:
            die(f"{where}: needs either 'to' or 'amount'")

        ensure(prop, unit)["tracks"].append({"drive": drive, "amount": amount})

    return out


UNIT_TOKEN = {"%": "pct"}


def unit_token(u):
    """A unit as it appears in a CSS custom-property name."""
    return UNIT_TOKEN.get(u, u)


def var_names(prefix, prop, buckets):
    """CSS variable name per (prop, unit) bucket."""
    return [f"{prefix}-{prop}{('-' + unit_token(u)) if u else ''}" for u in buckets]


def sum_expr(prefix, prop, vars_, fallback, extra=None):
    """Sum every unit bucket of a property into one calc() expression."""
    if prop not in vars_:
        return extra or fallback
    parts = ([extra] if extra else []) + [
        f"var({n})" for n in var_names(prefix, prop, vars_[prop])
    ]
    return parts[0] if len(parts) == 1 else f"calc({' + '.join(parts)})"


def validate_driver(spec, segments, where):
    if isinstance(spec, (int, float)):
        return
    if isinstance(spec, str):
        if spec in ("progress", "one"):
            return
        name = spec.split(".")[0]
        if name not in segments:
            die(f"{where}: unknown segment {name!r} (defined: {', '.join(segments) or 'none'})")
        if "." in spec:
            key = spec.split(".", 1)[1]
            if key not in ("enter", "exit", "active"):
                die(f"{where}: driver key must be enter/exit/active, got {key!r}")
        return
    if isinstance(spec, dict):
        if "mouse" in spec:
            if spec["mouse"] not in ("x", "y"):
                die(f"{where}: mouse driver must be x or y")
            return
        for key in ("sum", "product"):
            if key in spec:
                for child in spec[key]:
                    validate_driver(child, segments, where)
                return
        if "of" in spec:
            validate_driver(spec["of"], segments, where)
            return
        if any(k in spec for k in ("back", "snap", "pow", "clamp", "oneMinus")):
            return
        die(f"{where}: driver object needs mouse/sum/product/of")
    die(f"{where}: bad driver {spec!r}")


CLIP_MODES = {
    # each reveals as var goes 0 -> 1
    "wipe-left":  "inset(0 calc(100% - var({v}) * 100%) 0 0)",
    "wipe-right": "inset(0 0 0 calc(100% - var({v}) * 100%))",
    "wipe-up":    "inset(calc(100% - var({v}) * 100%) 0 0 0)",
    "wipe-down":  "inset(0 0 calc(100% - var({v}) * 100%) 0)",
    "iris":       "circle(calc(var({v}) * 78%) at 50% 50%)",
    "bars":       "inset(calc((1 - var({v})) * 50%) 0 calc((1 - var({v})) * 50%) 0)",
    "curtain":    "inset(0 calc((1 - var({v})) * 50%) 0 calc((1 - var({v})) * 50%))",
}


def clip_rule(prefix, mode, where):
    if mode not in CLIP_MODES:
        die(f"{where}: unknown clip mode {mode!r} (known: {', '.join(sorted(CLIP_MODES))})")
    return CLIP_MODES[mode].format(v=f"{prefix}-clip")


def css_for_layer(index, layer):
    """Wire one layer's element to the engine's variables."""
    p = f"--l{index}"
    v = layer["vars"]
    lines = [f".layer-{index} {{", f"  z-index: {layer.get('z', index)};"]

    fit = layer.get("fit")
    if fit == "cover":
        lines += ["  inset: 0;", "  width: 100%;", "  height: 100%;", "  object-fit: cover;"]
    elif fit == "contain":
        lines += ["  object-fit: contain;"]

    for prop in ("width", "height", "top", "bottom", "left", "right"):
        if prop in v:
            lines.append(f"  {prop}: {sum_expr(p, prop, v, '')};")

    anchor = layer.get("anchor")
    if anchor:
        lines.append(f"  {anchor};")

    x_expr = sum_expr(p, "x", v, layer.get("translateX", "0px"), layer.get("translateX"))
    y_expr = sum_expr(p, "y", v, layer.get("translateY", "0px"), layer.get("translateY"))
    scale_expr = sum_expr(p, "scale", v, "1")
    rot_expr = sum_expr(p, "rotate", v, "0deg")
    parts = [f"translate3d({x_expr}, {y_expr}, 0)"]
    # perspective must come first in the function list to apply to this element
    if layer.get("perspective"):
        parts.insert(0, f"perspective({layer['perspective']})")
    if "hinge" in v:
        axis = layer.get("hingeAxis", "0, 1, 0")
        parts.append(f"rotate3d({axis}, {sum_expr(p, 'hinge', v, '0deg')})")
    if "rotateX" in v:
        parts.append(f"rotateX({sum_expr(p, 'rotateX', v, '0deg')})")
    if "rotateY" in v:
        parts.append(f"rotateY({sum_expr(p, 'rotateY', v, '0deg')})")
    parts.append(f"rotate({rot_expr})")
    parts.append(f"scale({scale_expr})")
    if "scaleX" in v:
        parts.append(f"scaleX({sum_expr(p, 'scaleX', v, '1')})")
    if "scaleY" in v:
        parts.append(f"scaleY({sum_expr(p, 'scaleY', v, '1')})")
    lines.append("  transform: " + " ".join(parts) + ";")
    if layer.get("clipRaw"):
        lines.append(f"  clip-path: {layer['clipRaw']};")
    elif "clip" in v:
        lines.append(f"  clip-path: {clip_rule(p, layer.get('clipMode', 'wipe-left'), f'layer {index}')};")
    if layer.get("perspective") or "rotateX" in v or "rotateY" in v:
        lines.append("  transform-style: preserve-3d;")
        lines.append("  backface-visibility: hidden;")

    if layer.get("origin"):
        lines.append(f"  transform-origin: {layer['origin']};")

    filters = []
    for fn in ("blur", "brightness", "contrast", "saturate", "hue"):
        if fn in v:
            css_fn = "hue-rotate" if fn == "hue" else fn
            filters.append(f"{css_fn}({sum_expr(p, fn, v, '')})")
    if filters:
        lines.append(f"  filter: {' '.join(filters)};")

    if "opacity" in v:
        lines.append(f"  opacity: {sum_expr(p, 'opacity', v, '1')};")
    elif layer.get("staticOpacity") is not None:
        lines.append(f"  opacity: {layer['staticOpacity']};")

    if layer.get("blend"):
        lines.append(f"  mix-blend-mode: {layer['blend']};")

    lines.append("}")

    # A layer sized in vw with height:auto collapses vertically on a portrait
    # viewport -- a 112vw landscape image is barely a third of the screen
    # height on a phone. `portrait` lets it be sized by height there instead.
    if layer.get('portrait'):
        lines.append('')
        lines.append('@media (max-aspect-ratio: 4/5) {')
        lines.append(f"  .layer-{index} {{ {layer['portrait']}; }}")
        lines.append('}')

    return "\n".join(lines)


def css_for_group(index, group):
    """A group is a parent transform: its children zoom and drift as one unit."""
    p = f"--g{index}"
    v = group["vars"]
    lines = [f".group-{index} {{", "  position: absolute;", f"  z-index: {group.get('z', 1)};"]

    lines.append(f"  {group.get('anchor', 'inset: 0')};")

    for prop in ("width", "height", "top", "bottom", "left", "right"):
        if prop in v:
            lines.append(f"  {prop}: {sum_expr(p, prop, v, '')};")

    x_expr = sum_expr(p, "x", v, "0px")
    y_expr = sum_expr(p, "y", v, "0px")
    scale_expr = sum_expr(p, "scale", v, "1")
    rot_expr = sum_expr(p, "rotate", v, "0deg")
    lines.append(
        f"  transform: translate3d({x_expr}, {y_expr}, 0) "
        f"rotate({rot_expr}) scale({scale_expr});"
    )
    lines.append(f"  transform-origin: {group.get('origin', '50% 100%')};")

    if "opacity" in v:
        lines.append(f"  opacity: {sum_expr(p, 'opacity', v, '1')};")
    lines.append("  will-change: transform, opacity;")
    lines.append("}")
    return "\n".join(lines)


def css_for_panel(index, panel):
    """
    Two flavours:
      - with "segment": the standard story panel (vertically centred, fades in
        on enter, slides +enterSlide -> -exitSlide, fades out on exit)
      - without: a free panel driven entirely by its own tracks, so a hero that
        only fades on the way out is expressible without faking a segment
    """
    width = panel.get("width", "min(760px, calc(100vw - 42px))")
    lines = [
        f".panel-{index} {{",
        f"  z-index: {panel.get('z', 10)};",
        "  left: 50%;",
    ]
    if panel.get("bottom"):
        lines.append(f"  bottom: {panel['bottom']};")
    else:
        lines.append(f"  top: {panel.get('top', '45%')};")
    lines += [
        f"  width: {width};",
        f"  text-align: {panel.get('align', 'center')};",
        f"  pointer-events: {panel.get('pointerEvents', 'none')};",
    ]

    if panel.get("segment"):
        lines.append(f"  opacity: var(--p{index}-opacity, 0);")
        lines.append(f"  transform: translate3d(-50%, var(--p{index}-y, calc(-50% + 58px)), 0);")
    else:
        p = f"--p{index}v"
        v = panel.get("vars", {})
        x_expr = sum_expr(p, "x", v, "-50%", "-50%")
        y_expr = sum_expr(p, "y", v, "0px")
        scale_expr = sum_expr(p, "scale", v, "1")
        rot_expr = sum_expr(p, "rotate", v, "0deg")
        lines.append(f"  opacity: {sum_expr(p, 'opacity', v, '1')};")
        lines.append(
            f"  transform: translate3d({x_expr}, {y_expr}, 0) "
            f"rotate({rot_expr}) scale({scale_expr});"
        )

    lines.append("  will-change: transform, opacity;")
    lines.append("}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    scene_path, out_dir = sys.argv[1], sys.argv[2]

    with open(scene_path, encoding="utf-8") as fh:
        scene = json.load(fh)

    scene_dir = os.path.dirname(os.path.abspath(scene_path))
    segments = scene.get("segments", {})
    for name, window in segments.items():
        if not (isinstance(window, list) and len(window) == 4):
            die(f"segment {name!r} must be [a, b, c, d]")
        if not all(window[i] <= window[i + 1] for i in range(3)):
            die(f"segment {name!r} must be non-decreasing, got {window}")

    os.makedirs(out_dir, exist_ok=True)
    layer_dir = os.path.join(out_dir, "layers")

    layers = scene.get("layers") or []
    if not layers:
        die("scene has no layers")

    # ---- groups (parent transforms) ----
    groups = scene.get("groups") or []
    group_index = {}
    compiled_groups = []
    group_css = []
    for i, group in enumerate(groups):
        name = group.get("name") or die(f"group #{i}: missing 'name'")
        if name in group_index:
            die(f"duplicate group name {name!r}")
        group_index[name] = i
        compiled_groups.append({"vars": build_vars(group, segments, f"group {name!r}")})
        group_css.append(css_for_group(i, {**group, "vars": compiled_groups[i]["vars"]}))

    compiled_layers = []
    layer_html = []
    layer_css = []
    grouped_html = {name: [] for name in group_index}

    for i, layer in enumerate(layers):
        label = f"layer {layer.get('name', i)!r}"
        src = layer.get("src") or die(f"{label}: missing 'src'")

        if src.startswith(("http://", "https://", "data:")):
            href = src
        else:
            local = os.path.join(scene_dir, src)
            if not os.path.isfile(local):
                die(f"{label}: no such file {local}")
            os.makedirs(layer_dir, exist_ok=True)
            shutil.copy2(local, os.path.join(layer_dir, os.path.basename(src)))
            href = f"layers/{os.path.basename(src)}"

        compiled = dict(layer)
        compiled["vars"] = build_vars(layer, segments, label)
        compiled_layers.append({"vars": compiled["vars"]})

        layer_css.append(css_for_layer(i, compiled))
        name = layer.get("name", f"layer{i}")
        tag = f'<img class="scene-img layer-{i}" data-layer="{name}" src="{href}" alt="" />'

        group = layer.get("group")
        if group is not None:
            if group not in group_index:
                die(f"{label}: unknown group {group!r} (defined: {', '.join(group_index) or 'none'})")
            grouped_html[group].append(f"          {tag}")
            # a group renders where its FIRST member sits, keeping source order
            marker = ("group", group)
            if marker not in layer_html:
                layer_html.append(marker)
        else:
            layer_html.append(("layer", f"      {tag}"))

    # resolve the ordered world markers into real HTML
    world_html = []
    for kind, value in layer_html:
        if kind == "layer":
            world_html.append(value)
        else:
            gi = group_index[value]
            world_html.append(f'      <div class="group-{gi}" data-group="{value}">')
            world_html.extend(grouped_html[value])
            world_html.append("      </div>")

    panels = scene.get("panels") or []
    compiled_panels = []
    panel_html = []
    panel_css = []
    for i, panel in enumerate(panels):
        label = f"panel {panel.get('name', i)!r}"
        seg = panel.get("segment")
        if seg and seg not in segments:
            die(f"{label}: unknown segment {seg!r}")
        entry = {
            "segment": seg,
            "enterSlide": panel.get("enterSlide", 58),
            "exitSlide": panel.get("exitSlide", 86),
        }
        if panel.get("tracks") or panel.get("base"):
            entry["vars"] = build_vars(panel, segments, label)
        compiled_panels.append(entry)
        panel_css.append(css_for_panel(i, {**panel, "vars": entry.get("vars", {})}))
        aria = panel.get("aria", panel.get("name", f"Panel {i + 1}"))
        panel_html.append(
            f'    <section class="story-panel panel-{i}" aria-label="{aria}">\n'
            f'{panel.get("html", "")}\n'
            f"    </section>"
        )

    shade = scene.get("shade")
    compiled_shade = None
    if shade:
        validate_driver(shade.get("drive"), segments, "shade.drive")
        compiled_shade = {
            "drive": shade["drive"],
            "top": shade.get("top", 0.465),
            "mid": shade.get("mid", 0.42),
            "bottom": shade.get("bottom", 0.51),
            "liftAt": shade.get("liftAt", 0.02),
        }

    runtime = {
        "scrollHeight": scene.get("scrollHeight", 3700),
        "progressSpan": scene.get("progressSpan", scene.get("scrollHeight", 3700)),
        "smoothing": scene.get("smoothing", 0.14),
        "mouseSmoothing": scene.get("mouseSmoothing", 0.12),
        "segments": segments,
        "groups": compiled_groups,
        "layers": compiled_layers,
        "panels": compiled_panels,
    }
    if compiled_shade:
        runtime["shade"] = compiled_shade
    if scene.get("counterScale"):
        runtime["counterScale"] = scene["counterScale"]

    # ---- assemble ----
    with open(os.path.join(TEMPLATE, "base.css"), encoding="utf-8") as fh:
        base_css = fh.read()
    with open(os.path.join(TEMPLATE, "page.html"), encoding="utf-8") as fh:
        page = fh.read()
    with open(os.path.join(TEMPLATE, "engine.js"), encoding="utf-8") as fh:
        engine = fh.read()

    font = scene.get("font") or {}
    font_css = ""
    if font.get("url"):
        font_css = (
            "@font-face {\n"
            f'  font-family: "{font.get("family", "Display")}";\n'
            f'  src: url("{font["url"]}") format("woff2");\n'
            f'  font-weight: {font.get("weight", 500)};\n'
            "  font-style: normal;\n"
            "  font-display: swap;\n"
            "}\n\n"
        )

    css = (
        font_css
        + base_css.replace("__SCROLL_HEIGHT__", str(runtime["scrollHeight"]))
        .replace("__STAGE_BG__", scene.get("stage", {}).get("background", "#0b1110"))
        .replace("__DISPLAY_FONT__", font.get("family", "Georgia"))
        .replace("__TINT__", scene.get("tint", "74, 181, 224"))
        + "\n\n/* ---- generated groups ---- */\n\n"
        + "\n\n".join(group_css)
        + "\n\n/* ---- generated layers ---- */\n\n"
        + "\n\n".join(layer_css)
        + "\n\n/* ---- generated panels ---- */\n\n"
        + "\n\n".join(panel_css)
        + "\n"
        + scene.get("extraCss", "")
    )

    html = (
        page.replace("__TITLE__", scene.get("title", "Cinematic scroll"))
        .replace("__DESCRIPTION__", scene.get("description", ""))
        .replace("__ARIA__", scene.get("aria", scene.get("title", "Cinematic scroll story")))
        .replace("__CHROME__", scene.get("chrome", ""))
        .replace("__LAYERS__", "\n".join(world_html))
        .replace("__SHADE__", '      <div class="shade"></div>' if shade else "")
        .replace("__PANELS__", "\n".join(panel_html))
        .replace("__SCENE_JSON__", json.dumps(runtime, separators=(",", ":")))
    )

    # Prune layers left behind by earlier builds. Without this, switching a
    # scene from PNG to WebP leaves the old files in place and the output
    # directory keeps reporting the weight of assets the page no longer loads.
    if os.path.isdir(layer_dir):
        keep = {os.path.basename(l["src"]) for l in layers if not l["src"].startswith(("http", "data:"))}
        for stale in sorted(set(os.listdir(layer_dir)) - keep):
            os.remove(os.path.join(layer_dir, stale))
            print(f"  pruned      layers/{stale}")

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    with open(os.path.join(out_dir, "styles.css"), "w", encoding="utf-8") as fh:
        fh.write(css)
    with open(os.path.join(out_dir, "engine.js"), "w", encoding="utf-8") as fh:
        fh.write(engine)

    total_tracks = sum(
        len(bucket["tracks"])
        for group in compiled_groups + compiled_layers
        for prop in group["vars"].values()
        for bucket in prop.values()
    )
    print(f"  groups      {len(compiled_groups)}")
    print(f"  layers      {len(compiled_layers)}")
    print(f"  panels      {len(compiled_panels)}")
    print(f"  segments    {len(segments)}  ({', '.join(segments) or 'none'})")
    print(f"  tracks      {total_tracks}")
    print(f"  scroll      {runtime['scrollHeight']}px")
    print(f"  out         {out_dir}")


if __name__ == "__main__":
    main()
