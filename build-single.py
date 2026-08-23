#!/usr/bin/env python3
"""
build-single.py — fold web/ into one self-contained index.html.

    python3 build-single.py            # writes dist/index.html

You do NOT need this for GitHub Pages: Pages serves a folder of files
perfectly well, and keeping mqtt.min.js separate is actually better
there, because the browser caches 361 KB of library once instead of
re-downloading it inside every page load.

It is useful when you want ONE file you can email, drop on a USB stick,
open with file://, or paste into some other host that only takes a
single document.

What it inlines:
  · mqtt.min.js            -> a <script> tag
  · icon-*.png             -> data: URIs
  · manifest.webmanifest   -> a data: URI, with its icons inlined too

The result has no external requests at all, so it still runs with no
network beyond the broker itself.
"""

import base64
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT_DIR = HERE / "dist"


def b64_data_uri(path: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    src = HERE / "index.html"
    lib = HERE / "mqtt.min.js"
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 1
    if not lib.exists():
        print(f"error: {lib} not found — copy it in from the repo", file=sys.stderr)
        return 1

    html = src.read_text(encoding="utf-8")

    # ── icons -> data URIs ───────────────────────────────────────
    icons = {}
    for png in sorted(HERE.glob("icon-*.png")):
        icons[png.name] = b64_data_uri(png, "image/png")
        html = html.replace(f'href="{png.name}"', f'href="{icons[png.name]}"')

    # ── manifest -> data URI, with its own icon paths swapped ────
    man_path = HERE / "manifest.webmanifest"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        for entry in man.get("icons", []):
            entry["src"] = icons.get(entry.get("src", ""), entry.get("src", ""))
        # A relative start_url is meaningless once this is a lone file.
        man.pop("start_url", None)
        man.pop("scope", None)
        blob = base64.b64encode(
            json.dumps(man, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        html = html.replace(
            'href="manifest.webmanifest"',
            f'href="data:application/manifest+json;base64,{blob}"',
        )

    # ── the library -> inline <script> ───────────────────────────
    js = lib.read_text(encoding="utf-8")
    # A literal </script> anywhere inside would close the tag early. The
    # bundle does not contain one today, but a future version might, and
    # the failure would look like a mystery syntax error.
    js = js.replace("</script", "<\\/script")

    needle = '<script src="mqtt.min.js"></script>'
    if needle not in html:
        print("error: could not find the mqtt.min.js script tag", file=sys.stderr)
        return 1
    html = html.replace(
        needle,
        "<script>/* mqtt.js, inlined by build-single.py */\n" + js + "\n</script>",
    )

    # The runtime fallback that re-fetches the library is now dead weight
    # and, worse, would fire on a transient error and request a file that
    # does not exist beside a single-file build.
    html = html.replace('s.src = "mqtt.min.js";', 's.src = "";')

    if re.search(r'src="(?!data:)[^"]+"|href="(?!data:|#)[^"]+"', html):
        leftovers = re.findall(r'(?:src|href)="(?!data:|#)([^"]+)"', html)
        print(f"warning: still references external files: {sorted(set(leftovers))}",
              file=sys.stderr)

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size / 1024:.0f} KB, one file, no external requests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
