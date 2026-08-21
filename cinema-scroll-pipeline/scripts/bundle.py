#!/usr/bin/env python3
"""
bundle.py — fold a built scene into one self-contained HTML file.

  python3 scripts/bundle.py out/mirror mirror.html

A folder build needs a web server, which means it cannot be emailed, put on a
USB stick, or opened by tapping it on a phone. One file can. This inlines the
stylesheet, the engine and every layer image as a data URI, so the result opens
straight from the filesystem.

Base64 costs 4/3 on the encoded bytes, and these scenes are small enough that
the trade is worth it: a 900 KB folder becomes roughly a 1.2 MB file.

Fonts are deliberately NOT inlined. The display face is fetched from someone
else's CDN and embedding a licensed font into a file you then hand around is
redistribution. The @font-face rule is kept as-is, so the page needs one network
request for it and falls back to a system serif offline.
"""
import argparse
import base64
import mimetypes
import os
import re
import sys

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", help="a built scene directory, e.g. out/mirror")
    ap.add_argument("dest", help="the single HTML file to write")
    args = ap.parse_args()

    index = os.path.join(args.out_dir, "index.html")
    if not os.path.isfile(index):
        sys.exit(f"no index.html in {args.out_dir}")

    html = open(index, encoding="utf-8").read()
    before = html

    # --- stylesheet ---
    css_path = os.path.join(args.out_dir, "styles.css")
    if os.path.isfile(css_path):
        css = open(css_path, encoding="utf-8").read()
        html = re.sub(
            r'\s*<link rel="stylesheet" href="styles\.css"\s*/?>',
            "\n    <style>\n" + css + "\n    </style>",
            html,
            count=1,
        )

    # --- engine ---
    js_path = os.path.join(args.out_dir, "engine.js")
    if os.path.isfile(js_path):
        js = open(js_path, encoding="utf-8").read()
        html = re.sub(
            r'\s*<script src="engine\.js" defer></script>',
            "\n    <script>\n" + js + "\n    </script>",
            html,
            count=1,
        )

    # --- layer images: inline each ONE time, however many layers use it ---
    # Naively substituting the data URI at every src= embeds the same bytes once
    # per layer. Mirror has 33 layers sharing one image, which turned an 0.84 MB
    # folder into a 21 MB file. The images go in a table instead, and a three
    # line script assigns them; the page already requires JS for the engine.
    srcs = sorted(set(re.findall(r'src="(layers/[^"]+)"', html)))
    table = {}
    total_raw = 0
    for i, rel in enumerate(srcs):
        p_abs = os.path.join(args.out_dir, rel)
        if not os.path.isfile(p_abs):
            sys.exit(f"missing layer file: {p_abs}")
        key = f"i{i}"
        table[key] = data_uri(p_abs)
        total_raw += os.path.getsize(p_abs)
        n = html.count(f'src="{rel}"')
        # a 1x1 transparent gif keeps the element valid until the table lands
        html = html.replace(
            f'src="{rel}"',
            'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAAB'
            f'AAEAAAIBRAA7" data-img="{key}"')
        print(f"  {rel:34} {os.path.getsize(p_abs)/1024:7.0f} KB  used by {n} layer(s)")

    if table:
        joiner = "\n"
        payload = joiner.join(f'  {k}: "{v}",' for k, v in table.items())
        parts = [
            "\n    <script>\n",
            "      var __IMG = {\n",
            payload,
            "\n      };\n",
            "      for (var el of document.querySelectorAll(\'[data-img]\')) \n",
            "        el.src = __IMG[el.dataset.img];\n",
            "    </script>",
        ]
        script = "".join(parts)
        # after the markup and before the engine, so the elements exist and
        # the engine reads their natural sizes
        html = html.replace("    <script>", script + "\n    <script>", 1)

    leftover = re.findall(r'(?:src|href)="(?!data:|https?:|#)([^"]+)"', html)
    if leftover:
        print(f"\n  WARNING: still references local files: {sorted(set(leftover))}")

    remote = sorted(set(re.findall(r'url\("(https?://[^"]+)"\)', html)))
    with open(args.dest, "w", encoding="utf-8") as fh:
        fh.write(html)

    size = os.path.getsize(args.dest)
    print(f"\n  {inlined} image(s) inlined, {total_raw/1048576:.2f} MB raw")
    print(f"  {args.dest}  {size/1048576:.2f} MB  "
          f"(folder was {before and sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(args.out_dir) for f in fs)/1048576:.2f} MB)")
    if remote:
        print("  still fetched from the network:")
        for r in remote:
            print(f"    {r}")
        print("  (a font: falls back to a system serif offline)")


if __name__ == "__main__":
    main()
