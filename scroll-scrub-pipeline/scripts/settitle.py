#!/usr/bin/env python3
"""
settitle.py — substitute __TITLE__ in the template.

  TITLE="Smith & Co" settitle.py template/page.html out.html

This exists because sed treats `&` in a replacement as "the matched text" and
`|` as the expression delimiter, so `--title "Smith & Co"` used to render as
"Smith __TITLE__ Co". The title arrives through the environment rather than argv
so no shell quoting can touch it either.

Files are read and written as UTF-8 explicitly: the template contains em dashes
and arrows, and on Windows the default encoding is cp1252.
"""
import os
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__)

src, dest = sys.argv[1], sys.argv[2]
title = os.environ.get("TITLE", "Scroll")

with open(src, encoding="utf-8") as fh:
    html = fh.read()

if "__TITLE__" not in html:
    sys.exit("settitle.py: template has no __TITLE__ placeholder")

with open(dest, "w", encoding="utf-8") as fh:
    fh.write(html.replace("__TITLE__", title))
