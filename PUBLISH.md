# PS4 GoldHEN host (offline-capable)

Static exploit host for personal use. Served via GitHub Pages.

## URLs

- Custom: `http://activate.doesitworknow.me/` (or `https://` once DNS/HTTPS is ready)
- Firmware **13.00**: `/1300/index.html`
- Firmware **13.02–13.52**: `/1352/index.html`

## DNS (Cloudflare / registrar)

Point `activate.doesitworknow.me` to GitHub Pages:

| Type | Name | Value |
|------|------|-------|
| CNAME | activate | `<github-user>.github.io` |

For apex `doesitworknow.me` (optional later): A records to GitHub Pages IPs.

## Structure

`index.html` decides which folder serves a firmware, so a new chain is added by
dropping its files in a folder and adding one route. Each folder's
`cache.manifest` must list every file that folder needs, because the console
serves the offline copy once it has one.

## Before publishing

```bash
python3 tools/check.py
python3 tools/selftest.py
```

Both must pass. The first catches a broken host; the second proves the first
still notices when something breaks.
