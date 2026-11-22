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

## Source

Files from the local Docker image `ghcr.io/chrisser73/ps4-host-offline-goldhen` (PSPulse / GoldHEN host assets).
