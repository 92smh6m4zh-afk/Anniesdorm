# Publishing the panel to GitHub Pages

## Short answer: no, it does not need to be one file

GitHub Pages serves a folder of static files. Multiple files are the
normal case and the better one here — `mqtt.min.js` is 361 KB, and as a
separate file the browser caches it once instead of re-downloading it
inside every page load. Push the folder as it is.

A single-file build exists if you want one (`python3 build-single.py`
writes `dist/index.html`, 492 KB, no external requests at all), but its
use is emailing the thing, putting it on a USB stick, or opening it with
`file://` — not Pages.

## What the GitHub copy actually is

Worth being clear about, because it is not a second control panel.

The page asks its own origin for `config.json` at load. On the Pi that
file exists and carries the broker credentials, served only over
loopback and, from outside, only through Cloudflare Access. On GitHub
Pages that fetch returns 404, so the page falls back to **demo mode**:
it renders, you can tap through every screen, and the controls change
nothing but the page itself.

That is the correct behaviour for a public URL, not a limitation. A
public page that could actually switch your lights is a public page that
lets anyone else switch them too. Real control goes through the tunnel.

So the Pages copy is good for: showing someone the project, checking a
layout change on your phone before deploying it, and having the source
somewhere other than one SD card. It is not the thing you use to turn
the lamp on.

## Before the first push

`config.json` is generated on the Pi and never belongs in the repo, and
neither does `secrets.h`. The repo root `.gitignore` already covers
both, but check rather than trust:

```bash
cd ~/dorm-control
grep -rn "Supra\|PASTE_\|password" --include="*.h" --include="*.json" --include="*.html" . \
  | grep -v node_modules
```

You want that to return nothing but comments and placeholder text. If a
real password shows up, remove it before committing — a secret pushed to
a public repo has to be treated as burned even after you delete it,
because the commit history keeps it.

## Pushing

Your repo already exists at `hsnkh6n/homecontrol`, so:

```bash
cd ~/dorm-control/web
git init                              # if this folder is not a repo yet
git remote add origin https://github.com/hsnkh6n/homecontrol.git
git add index.html mqtt.min.js manifest.webmanifest icon-*.png
git commit -m "Room panel"
git branch -M main
git push -u origin main
```

If the repo already has content you want to keep, clone it instead and
copy the files in:

```bash
git clone https://github.com/hsnkh6n/homecontrol.git
cp ~/dorm-control/web/{index.html,mqtt.min.js,manifest.webmanifest} homecontrol/
cp ~/dorm-control/web/icon-*.png homecontrol/
cd homecontrol && git add -A && git commit -m "Update panel" && git push
```

Then in the repo: **Settings → Pages → Source: Deploy from a branch →
`main` / `(root)`**. It goes live at
`https://hsnkh6n.github.io/homecontrol/` within a minute or two.

## Keeping the two copies in step

The Pi does not serve from GitHub — `install.sh` copies files into
`/var/www/room/`. After changing `index.html`, update both:

```bash
# the Pi
sudo install -m 0644 index.html /var/www/room/

# GitHub
git add index.html && git commit -m "..." && git push
```

If you would rather have one source of truth, clone the repo onto the Pi
and point nginx's `root` at it, then a `git pull` deploys. That is a
nicer workflow but it puts a git checkout in the web root, so add a
`location ~ /\.git { deny all; }` block to `pi/nginx/room.conf` if you do
— otherwise the whole repo, history included, is readable through the
tunnel by anyone who gets past Access.

## A note on the icons

`icon-*.png` and `manifest.webmanifest` are what make "Add to Home
Screen" produce a proper app icon and a fullscreen launch. Skip them and
iOS falls back to a screenshot of the page, which looks like what it is.
They are small; push them.
