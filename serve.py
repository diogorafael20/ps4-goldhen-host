#!/usr/bin/env python3
"""Serves this folder to a PS4 on your own network.

    python3 serve.py            # port 8000
    python3 serve.py 8080       # another port
    python3 serve.py 8080 192.168.1.50   # pin the address it prints

Then open the printed address in the console's browser. Nothing leaves your
network: the console talks to this machine and to nothing else.

Why a script and not `python3 -m http.server`: the console only caches a page
for offline use when the manifest is served as `text/cache-manifest`. The
stdlib server guesses that from the platform's mime.types, which differs
between machines, and a wrong type fails silently -- the page works online and
dies the moment the network does. This sets it explicitly.

The console's browser is old: no TLS, no modern JS. Plain HTTP on the LAN is
what it expects. Do not expose this to the open internet as-is.
"""

import functools
import os
import socket
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

# Extensions that must not be guessed by the platform's mime.types.
FORCED = {
    ".manifest": "text/cache-manifest",
    ".appcache": "text/cache-manifest",
    ".js": "application/javascript",
    ".html": "text/html; charset=utf-8",
    ".bin": "application/octet-stream",
}


class Handler(SimpleHTTPRequestHandler):
    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in FORCED:
            return FORCED[ext]
        return super().guess_type(path)

    def end_headers(self):
        # The console caches hard; a stale manifest is the usual cause of "I
        # changed it and the PS4 still shows the old page". This stops a normal
        # browser doing the same while you test.
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))


def lan_address():
    """The address another device on this network can reach, if knowable."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No packet is sent: this asks the kernel which interface would carry
        # traffic onward, which is the LAN-facing one.
        probe.connect(("192.0.2.1", 9))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    pinned = sys.argv[2] if len(sys.argv) > 2 else None

    os.chdir(ROOT)
    handler = functools.partial(Handler, directory=ROOT)

    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    except OSError as exc:
        print("Could not listen on port %d: %s" % (port, exc))
        print("Try another port:  python3 serve.py 8080")
        return 1

    address = pinned or lan_address() or "<this machine's IP>"
    url = "http://%s:%d/" % (address, port)

    print()
    print("  PS4 unlock host")
    print("  Open this in the console's browser:")
    print()
    print("      %s" % url)
    print()
    print("  On this machine:  http://127.0.0.1:%d/" % port)
    print("  Serving:          %s" % ROOT)
    print("  Stop with Ctrl+C")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
