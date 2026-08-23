# Public page on GitHub Pages, controlling real lights

You chose to put a broker credential in a public page. That is a
reasonable trade for dorm lights, and this file makes it work with the
sharp edges filed down. Read the two limits at the bottom before you
commit — they are not "be careful" boilerplate, they are two specific
things that surprise people.

## 1. Make a credential that exists only for this

HiveMQ Cloud console → your cluster → **Access Management** → **Access
Credentials** → *Create Credential*.

| Field | Value |
|---|---|
| Username | `webpublic` |
| Password | generate one, below |
| Permission | Publish and Subscribe |

```bash
openssl rand -base64 24 | tr -d '/+=' | cut -c1-24
```

**Use this credential nowhere else.** Not on the ESP32s (`esp32`), not
in the Pi's bridge (`pi-bridge`). That separation is the whole point: if
this one ever gets abused, you delete `webpublic` in the console and the
page drops to demo mode by itself, while the boards and the panel carry
on working. Sharing one credential across all three turns a nuisance
into re-flashing two boards.

## 2. Paste it into the page

Near the top of the `<script>` block in `index.html`:

```js
const PUBLIC_BROKER = {
  host:     "e3a13c7fbd494724aa73555c0a8566b9.s1.eu.hivemq.cloud",
  port:     8884,          // WebSocket over TLS — not 8883, that is native MQTT
  path:     "/mqtt",
  username: "webpublic",
  password: "THE_GENERATED_PASSWORD",
};
```

Port 8884 is the one that matters. 8883 is native MQTT and a browser
cannot speak it; a page pointed at 8883 sits on "connecting" forever
with nothing useful in the console.

Leave `host` or `username` empty and the page stays in demo mode, which
is what you want in any copy you are not ready to arm.

## 3. Push

```bash
cd homecontrol
cp ~/dorm-control/web/{index.html,mqtt.min.js,manifest.webmanifest} .
cp ~/dorm-control/web/icon-*.png .
git add -A && git commit -m "Panel with public broker" && git push
```

Settings → Pages → Deploy from a branch → `main` / `(root)`. Live at
`https://hsnkh6n.github.io/homecontrol/` in a minute or two.

GitHub Pages serves over HTTPS, which is required here: an `https://`
page may only open a `wss://` socket, never `ws://`.

## 4. Confirm the Pi still wins on the Pi

The panel must keep using the local broker, not route through the
internet to reach a light two metres away. It already does — the page
tries `config.json` first, and only falls back to `PUBLIC_BROKER` when
that 404s. Check on the panel: gear → **Transport** should read
`WebSocket (LAN)`, not `WebSocket over TLS`.

## Limit one: precisely what the public gets

Anyone who opens the page can switch every light and see the indoor
temperature and humidity. That is the deal you accepted.

What they do **not** get, because I changed the bridge to exclude it:

- `hsn/presence/#` — the CSI motion detector, updating every second
- `hsn/+/info` — the boards' IP addresses, SSID and signal strength

Presence is the one worth pausing on. It is a live feed of whether
someone is moving in your room, and on a public credential that is
occupancy surveillance of a dorm, which is a different order of thing
from someone flicking your lamp. It now stays on the Pi. The panel still
shows it in full, because the panel reads it locally.

If you re-enable `topic # both 0 hsn/ hsn/` in
`pi/mosquitto/room.bridge.conf.template`, you put that feed back on the
public cluster. Don't, unless you have thought about it specifically.

## Limit two: no topic restriction on the free tier

On HiveMQ **Serverless**, permissions are presets — publish, subscribe,
or both. You **cannot** scope a credential to `hsn/#`. Topic filters are
a Starter+ feature.

So `webpublic` can publish anywhere on your cluster, not only to your
light topics. While that cluster carries nothing but this project it
costs you little. If you later put something else on it, this credential
reaches that too, and the fix is a paid tier or a second cluster.

## If it gets abused

Symptoms are lights changing on their own or your HiveMQ session quota
burning down faster than two boards and a phone explain.

1. Console → Access Management → delete `webpublic`. Seconds, and it
   disconnects everyone using it.
2. The public page drops to demo mode. The boards, the bridge and the
   panel are untouched, because they use different credentials.
3. Decide whether to reissue with a new password or move to the tunnel
   (`pi/cloudflare/ACCESS.md`).

Worth knowing in advance: rotating the password does **not** kick
existing connections in every case, and the old password stays in your
git history for anyone who looks. Deleting the credential is the action
that actually stops it.

## The honest summary

For dorm lights this is fine. The failure mode is a stranger being
annoying, not a stranger in your room, and you can end it in ten seconds
from the console.

Two things would change that answer: putting anything other than lights
on this cluster, or re-enabling presence in the bridge. Either one turns
a public credential from a nuisance into a real exposure.
