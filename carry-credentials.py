#!/usr/bin/env python3
"""
carry-credentials.py — copy the PUBLIC_BROKER block from the page that is
already live into a freshly built one.

    python3 carry-credentials.py LIVE.html NEW.html

Every release of index.html ships with PUBLIC_BROKER blank, because the
credentials are yours and do not belong in the bundle. Blank means the
page silently runs in demo mode: the controls move, the room does not.
That failure looks like a broken deploy and is really a missed edit.

So rather than retyping five fields each time, take them from the copy
already serving on GitHub Pages. NEW.html is edited in place, and it
refuses rather than guesses if anything looks wrong.
"""

import re
import sys

BLOCK = re.compile(
    r"const PUBLIC_BROKER = \{.*?\n\};",
    re.S,
)


def block_of(path):
    text = open(path, encoding="utf-8").read()
    m = BLOCK.search(text)
    if not m:
        sys.exit(f"error: no PUBLIC_BROKER block found in {path}")
    return text, m


def looks_filled(block):
    """A host and a username are the two that decide demo mode."""
    host = re.search(r'host:\s*"([^"]*)"', block)
    user = re.search(r'username:\s*"([^"]*)"', block)
    return bool(host and host.group(1) and user and user.group(1))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip())
    live_path, new_path = sys.argv[1], sys.argv[2]

    _, live_m = block_of(live_path)
    new_text, new_m = block_of(new_path)
    live_block = live_m.group(0)

    if not looks_filled(live_block):
        sys.exit(f"error: {live_path} has no credentials to copy — is that "
                 f"really the page currently serving on GitHub Pages?")

    if looks_filled(new_m.group(0)):
        # Refusing beats overwriting: if the target already has
        # credentials, the safe assumption is that they are the newer ones.
        sys.exit(f"error: {new_path} already has credentials. Nothing done.")

    out = new_text[:new_m.start()] + live_block + new_text[new_m.end():]
    open(new_path, "w", encoding="utf-8").write(out)

    host = re.search(r'host:\s*"([^"]*)"', live_block).group(1)
    user = re.search(r'username:\s*"([^"]*)"', live_block).group(1)
    print(f"copied credentials into {new_path}")
    print(f"  host     {host}")
    print(f"  username {user}")
    print("  password (copied, not shown)")


if __name__ == "__main__":
    main()
