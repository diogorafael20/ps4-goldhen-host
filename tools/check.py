#!/usr/bin/env python3
"""Validation for the exploit host.

Run from the repository root:

    python3 tools/check.py

Exits non-zero on the first category of problem, and prints every failure it
found rather than only the first -- a host that half-loads is worse than one
that refuses to start.

What it can and cannot do: this checks structure, not exploitation. It cannot
tell whether an exploit still works on a console; it catches the failures that
a console reports as a blank screen or a dead button, which are the ones that
creep in when a page is edited.
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []
notes = []


def fail(msg):
    problems.append(msg)


def rel(path):
    return os.path.relpath(path, ROOT)


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def html_files():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "assets")]
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(base, f))
    return sorted(out)


# ---------------------------------------------------------------- manifests

MANIFEST_NAMES = ("cache.manifest", "cache.appcache", "PSPulse.manifest",
                  "PSPulse.cache", "navigation.manifest")


def parse_manifest(path):
    """Returns the CACHE entries of an HTML5 application cache manifest.

    A query string is part of the cached URL (which is how these hosts keep
    `jb.html?log=1` separate from `jb.html`), so it is stripped only for the
    existence check.
    """
    entries = []
    section = None
    for raw in read(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":") and line[:-1].upper() in ("CACHE", "NETWORK", "FALLBACK", "SETTINGS"):
            section = line[:-1].upper()
            continue
        if section != "CACHE":
            continue
        # "file #hash" -- the hash is our own convention, not part of the URL
        entries.append(line.split(" #")[0].strip())
    return entries


def check_manifests():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github")]
        for f in files:
            if f not in MANIFEST_NAMES:
                continue
            path = os.path.join(base, f)
            for entry in parse_manifest(path):
                target = os.path.normpath(os.path.join(base, entry.split("?")[0]))
                if not os.path.exists(target):
                    fail("%s lists %r, which does not exist" % (rel(path), entry))


# ------------------------------------------------------------ internal links

LINK_RE = re.compile(r'(?:href|src)="([^"#?][^"]*)"')


def check_links():
    for path in html_files():
        text = read(path)
        for raw in LINK_RE.findall(text):
            if raw.startswith(("http:", "https:", "//", "data:", "javascript:", "mailto:")):
                continue
            target = raw.split("?")[0].split("#")[0]
            if not target:
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(full) and not os.path.exists(full + ".html"):
                fail("%s links to %r, which does not exist" % (rel(path), raw))


# --------------------------------------------------------- chain DOM contract

# Each chain reads and writes these elements by name. Renaming one in the page
# is exactly the mistake that produces a screen that never finishes.
CHAIN_CONTRACT = {
    "1300/run_poops.html": {"script": "chain_poops", "ids": ["out", "state"]},
    "1300/run_lapse.html": {"script": "chain_lapse", "ids": ["out", "state"]},
    "1352/jb.html": {"script": "jb", "ids": ["out", "state", "msg"]},
    "1400/jb.html": {"script": "jb", "ids": ["out", "state", "msg", "ramBox"]},
}


def check_contract():
    for page, spec in CHAIN_CONTRACT.items():
        path = os.path.join(ROOT, page)
        if not os.path.exists(path):
            fail("%s is missing" % page)
            continue
        text = read(path)
        if spec["script"] not in text:
            fail("%s no longer loads ./%s.js" % (page, spec["script"]))
        for element_id in spec["ids"]:
            if 'id="%s"' % element_id not in text:
                fail("%s has no element with id=%r, which the chain writes to"
                     % (page, element_id))
        if "../ui.js" not in text:
            fail("%s does not load ../ui.js (the progress screen)" % page)


# ------------------------------------------------------------- firmware map

# The start page decides which folder serves a firmware. Each folder carries
# its own offset table, and a firmware is only usable if that table has an
# entry for it -- so the endpoints of every route must exist there. A table
# may hold extra entries the start page never routes to; those are legacy and
# harmless.
FOLDER_TABLES = {
    "1300": "1300/ps4_offsets.js",
    "1352": "1352/ps4_offsets.js",
    "1400": "1400/ps4_offsets.js",
}


def offset_keys(path):
    text = read(path)
    keys = set(re.findall(r'"(1[0-9]\.[0-9]{2}|[0-9]\.[0-9]{2})"\s*:\s*\{', text))
    keys |= set(re.findall(r'PS4\["(1[0-9]\.[0-9]{2}|[0-9]\.[0-9]{2})"\]', text))
    return keys


def check_firmware_map():
    index = os.path.join(ROOT, "index.html")
    if not os.path.exists(index):
        fail("index.html is missing")
        return
    text = read(index)

    routes = re.findall(
        r"\{\s*min:\s*([0-9.]+),\s*max:\s*([0-9.]+),.*?dir:\s*\"([^\"]+)\"", text)
    if not routes:
        fail("index.html has no ROUTES table")
        return

    for folder, table in FOLDER_TABLES.items():
        if not os.path.exists(os.path.join(ROOT, table)):
            fail("%s is missing" % table)

    for lo, hi, direction in routes:
        first = direction.split("/")[0]
        if not os.path.exists(os.path.join(ROOT, first)):
            fail("index.html routes %s-%s to %r, which does not exist"
                 % (lo, hi, first))
            continue

        table = FOLDER_TABLES.get(first)
        if not table or not os.path.exists(os.path.join(ROOT, table)):
            continue

        keys = offset_keys(os.path.join(ROOT, table))
        for endpoint in (lo, hi):
            # Only the endpoints need a table entry: everything between them is
            # covered by the same kernel build, which is what ranges encode.
            if endpoint not in keys:
                fail("%s routes %s-%s to %s/, but %s has no offsets for %s"
                     % ("index.html", lo, hi, first, table, endpoint))


# ------------------------------------------------------------------- scripts

def check_syntax():
    node = None
    for candidate in ("node", "nodejs"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            node = candidate
            break
        except (OSError, subprocess.CalledProcessError):
            continue
    if not node:
        notes.append("node not found: JavaScript syntax was not checked")
        return

    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "node_modules")]
        for f in files:
            if not f.endswith(".js"):
                continue
            path = os.path.join(base, f)
            result = subprocess.run([node, "--check", path], capture_output=True, text=True)
            if result.returncode != 0:
                detail = (result.stderr or "").strip().splitlines()
                fail("%s does not parse: %s" % (rel(path), detail[0] if detail else ""))

    # Inline scripts too: a syntax error there leaves a blank page with no
    # message at all, which is the hardest kind to diagnose from a sofa.
    inline = re.compile(r'<script(?![^>]*\bsrc=)(?![^>]*type="module")[^>]*>(.*?)</script>',
                        re.S)
    import tempfile
    for path in html_files():
        for number, code in enumerate(inline.findall(read(path))):
            if not code.strip():
                continue
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tmp:
                tmp.write(code)
                name = tmp.name
            result = subprocess.run([node, "--check", name], capture_output=True, text=True)
            os.unlink(name)
            if result.returncode != 0:
                detail = (result.stderr or "").strip().splitlines()
                fail("%s inline script #%d does not parse: %s"
                     % (rel(path), number + 1, detail[0] if detail else ""))


# ------------------------------------------------------------------- reports

def check_reports():
    """The chain folders must have the payload blobs their pages fetch."""
    required = {
        "1300": ["payload.bin", "core.js", "mem.js", "chain_poops.js", "chain_lapse.js"],
        "1352": ["goldhen.bin", "jb.js", "core.js"],
        "1400": ["hen.bin", "goldhen.bin", "jb.js", "afterglow.js"],
    }
    for folder, files in required.items():
        for f in files:
            path = os.path.join(ROOT, folder, f)
            if not os.path.exists(path):
                fail("%s/%s is missing" % (folder, f))
            elif os.path.getsize(path) == 0:
                fail("%s/%s is empty" % (folder, f))


def check_permissions():
    """Every published file must be readable by the server's user.

    The commit mode is what a clone gets, and a file committed as 600 is
    unreadable to nginx (a different user) -- it answers 403, so a page that
    exists looks missing. This has happened, which is why it is checked.
    """
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github")]
        for f in files:
            path = os.path.join(base, f)
            mode = os.stat(path).st_mode
            if not (mode & 0o004):
                fail("%s is not readable by other users (mode %o), so a server "
                     "running as a different user returns 403"
                     % (rel(path), mode & 0o777))


def main():
    check_permissions()
    check_manifests()
    check_links()
    check_contract()
    check_firmware_map()
    check_reports()
    check_syntax()

    for note in notes:
        print("note: " + note)

    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - " + p)
        print("\nThis host would fail on a console. Nothing was published.")
        return 1

    print("ok: manifests, links, chain contract, firmware map, payloads and syntax")
    return 0


if __name__ == "__main__":
    sys.exit(main())
