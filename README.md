# PS4 exploit host

Static host for a personal PS4, served from GitHub Pages. One page, one
button: it reads the firmware from the console's user agent, picks the folder
that has offsets for it, and starts the chain.

## Using it

On the console: open the URL, press **Desbloquear**, wait. The screen shows a
percentage; it reaches 100 and says *Desbloqueio realizado* only when the
payload is actually running. If it fails, the screen says what to do next —
either retry, or reboot the console.

Options (a small link under the button) let you pick GoldHEN or PS4HEN and
force a firmware, for when detection is not possible.

## Layout

| Path | Firmware | Chain |
|---|---|---|
| `1300/` | 11.00 – 13.00 | Lapse / Poops |
| `1352/` | 13.02 – 13.52 | Slopkit + GoldHEN |
| `1400/` | 14.00 – 14.02 | afterglow |
| `900/` | 9.00 – 9.60 | PSFree |
| `700/` | 7.00 – 8.52 | PSFree |
| `672/` | 6.72 | Lapse |
| `505/` | 5.05 | Lapse |
| `css/` | 6.00 – 11.02 | CSSFontFace |

`index.html` holds the firmware-to-folder table. `ui.js` is the shared
percentage screen; `simple.js` adapts the older vendor pages to it.

## Validation

Every push and pull request runs `.github/workflows/validate.yml`:

```bash
python3 tools/check.py      # structure, links, manifests, chain DOM, syntax
python3 tools/selftest.py   # proves check.py still catches each known failure
```

`check.py` cannot tell whether an exploit still works on a console — nothing
outside a console can. What it catches are the failures a console reports as a
blank screen or a dead button, which is what an edit tends to break:

- a manifest that caches a file that no longer exists
- a link to a renamed page
- a chain page that lost an element its script writes to by name
- a route sending a firmware to a folder whose offset table lacks it
- a payload blob lost or emptied in a merge
- a syntax error, in a file or in an inline script

Run both before pushing. Green means the host is intact, not that a firmware
is exploitable.

## Cache

The console caches aggressively and there are no HTTP headers to set on GitHub
Pages, so each folder carries an HTML5 application cache manifest. Editing a
file without bumping its manifest leaves consoles on the old copy; the
manifest must change for the browser to refetch. `1400/make-manifest.sh`
rebuilds its own from content hashes — run it after editing anything in that
folder.

## Source

Host assets from `ghcr.io/chrisser73/ps4-host-offline-goldhen` (PSPulse).
Exploit chains by their respective authors; see each folder.
