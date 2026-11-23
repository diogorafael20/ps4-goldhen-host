# does it work now?

A personal exploit host for one PlayStation 4, served from GitHub Pages.
One screen, one button. It reads the firmware from the console's own user
agent, picks the folder that carries offsets for it, and runs the chain.

```
        open the URL  ->  press Desbloquear  ->  100%  ->  done
```

No file manager, no payload menu, no log to read. If a run fails the screen
says which of the two things to do next: retry, or power-cycle the console.

> **Read this first.** This repository exists for educational purposes and for
> testing on hardware I own. See [NOTICE.md](NOTICE.md). Running an exploit
> changes the security state of your console, can corrupt its storage, and can
> get a PSN account banned. Use it on a console you are willing to lose.

## What it does

| Firmware | Folder | Chain |
|---|---|---|
| 14.00 – 14.02 | `1400/` | afterglow |
| 13.02 – 13.52 | `1352/` | Slopkit |
| 11.00 – 13.00 | `1300/` | Lapse / Poops |
| 9.00 – 9.60 | `900/` | PSFree |
| 7.00 – 8.52 | `700/` | PSFree |
| 6.72 | `672/` | Lapse |
| 5.05 | `505/` | Lapse |
| 6.00 – 11.02 | `css/` | CSSFontFace |

`index.html` holds the firmware-to-folder table. `ui.js` is the shared
progress screen. `simple.js` adapts the older vendor pages to it.

The chains are not modified — this repository is the front door and the
packaging, not the research. Credit for each belongs to its authors, named in
each folder.

## The screen

A percentage, a bar, and one sentence. The number is driven by checkpoints
the chain already emits, so it never claims more than the chain has done: it
holds at 99 until the payload is running, then goes to 100 and says
*Desbloqueio realizado*.

Options sit behind a small link: GoldHEN or PS4HEN, and a manual firmware
choice for when detection is not possible.

## Validation

Every push and pull request runs `.github/workflows/validate.yml`:

```bash
python3 tools/check.py      # structure, links, manifests, chain DOM, syntax
python3 tools/selftest.py   # proves check.py still catches each known failure
```

What that can and cannot tell you: it cannot tell whether an exploit still
works on a console — nothing outside a console can. It catches what an edit
tends to break, which a console reports as a blank screen or a dead button:

- a manifest caching a file that no longer exists
- a link to a renamed page
- a chain page missing an element its script writes to by name
- a route sending a firmware to a folder whose offset table lacks it
- a payload blob lost or emptied in a merge
- a syntax error, in a file or in an inline script

`tools/selftest.py` breaks the repository six ways in a temporary copy and
requires the checker to fail each time. A checker that always passes is worse
than none, because it gets trusted.

Green means the host is intact, not that a firmware is exploitable.

## Cache

The console caches aggressively and GitHub Pages sets no headers, so each
folder carries an HTML5 application cache manifest. Editing a file without
bumping its manifest leaves consoles on the old copy — the manifest itself
must change for the browser to refetch. `1400/make-manifest.sh` rebuilds its
own from content hashes.

## Credits and licence

The exploit chains, patches and payloads in the firmware folders are not mine
and are not relicensed here; each file keeps the copyright and licence notice
it arrived with, and several are AGPL. If you redistribute this repository, keep
those notices intact — the licence requires it, and stripping them would be
both a licence breach and a false claim of authorship.

This repository's own work is the front door: the firmware detection, the
percentage screen, the packaging and the validation in `tools/`.

PlayStation, PS4 and PSN are trademarks of Sony Interactive Entertainment. This
project is independent and not affiliated with or endorsed by Sony.
