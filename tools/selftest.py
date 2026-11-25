#!/usr/bin/env python3
"""Proves the validator still catches a broken page.

A checker that always passes is worse than none, because it is trusted. Each
case below copies the repository to a temporary directory, breaks one thing
that has broken on a console before, runs the checker there, and requires it
to fail -- with the right message.

    python3 tools/selftest.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

failures = []


def run_check(workdir):
    """Runs the copy's own checker, not this repository's: each case breaks a
    file inside its temporary copy and must see that copy fail."""
    script = os.path.join(workdir, "tools", "check.py")
    result = subprocess.run(
        [sys.executable, script], cwd=workdir, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def edit(path, old, new, count=1):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if old not in text:
        raise AssertionError("fixture text not found in %s: %r" % (path, old[:60]))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(old, new, count))


def case(name, mutate, expect, must_mention):
    tmp = tempfile.mkdtemp(prefix="hostcheck-")
    try:
        work = os.path.join(tmp, "repo")
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "node_modules"))
        mutate(work)
        code, output = run_check(work)

        if code == 0:
            failures.append("%s: expected a failure, checker passed" % name)
            return
        if expect not in output:
            failures.append("%s: expected %r in the report, got:\n%s"
                            % (name, expect, output.strip()[:400]))
            return
        if must_mention and must_mention not in output:
            failures.append("%s: report does not mention %r:\n%s"
                            % (name, must_mention, output.strip()[:400]))
            return
        print("ok: " + name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# A file the manifest caches is deleted but the manifest still lists it: the
# console caches a 404 and then serves a broken run page forever.
def drop_cached_file(work):
    os.remove(os.path.join(work, "1352", "goldhen.bin"))


# The alternate 9.xx cache uses its own manifest and must be checked too.
def add_missing_cached_file(work):
    edit(os.path.join(work, "900", "cache5.manifest"),
         "psfree5.js\n", "psfree5.js\nmissing.js\n")


# A chain's DOM contract is broken by renaming the element it writes to.
def rename_chain_element(work):
    page = os.path.join(work, "1352", "jb.html")
    edit(page, 'id="out"', 'id="output"')


# The start page sends a firmware to a folder whose table has no entry for it.
def bad_route(work):
    page = os.path.join(work, "index.html")
    edit(page, 'max: 14.02', 'max: 15.02')


# A link to a page that was renamed.
def dead_link(work):
    edit(os.path.join(work, "index.html"), 'dir: "1352"', 'dir: "1353"')


# A payload blob lost in a merge.
def empty_payload(work):
    open(os.path.join(work, "1400", "hen.bin"), "w").close()


# An inline script that no longer parses -- a blank screen with no message.
def bad_inline_script(work):
    page = os.path.join(work, "1300", "index.html")
    edit(page, "var UI = window.HostUI;", "var UI = window.HostUI(;")


def main():
    case("manifest lists a deleted file", drop_cached_file,
         "does not exist", "1352/cache.manifest")
    case("alternate manifest lists a missing file", add_missing_cached_file,
         "does not exist", "900/cache5.manifest")
    case("chain element renamed", rename_chain_element,
         "which the chain writes to", "id='out'")
    case("route past the offset table", bad_route,
         "has no offsets for", "15.02")
    case("link to a renamed page", dead_link,
         "does not exist", "1353")
    case("payload blob empty", empty_payload,
         "is empty", "hen.bin")
    case("inline script syntax error", bad_inline_script,
         "does not parse", "1300/index.html")

    if failures:
        print("\n%d self-test failure(s):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("\nok: the checker catches every failure it is meant to")
    return 0


if __name__ == "__main__":
    sys.exit(main())
