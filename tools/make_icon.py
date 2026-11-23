#!/usr/bin/env python3
"""Draws the site icon.

The icon is the same four-button glyph the pages draw, so the tab and the
screen match. It is generated here rather than committed as an opaque binary:
the source of truth is this file, and re-running it after a colour change is
one command.

    python3 tools/make_icon.py

Writes icon.png at the repository root, which every page links to as its tab
icon.
"""

import math
import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIZE = 128          # final, square
SS = 4              # supersampling per axis
BG = (0x14, 0x1b, 0x24)
BORDER = (0x1f, 0x29, 0x33)
TRIANGLE = (0x5f, 0xd6, 0xc8)
CIRCLE = (0xff, 0x80, 0x80)
CROSS = (0x8f, 0xb6, 0xf0)
SQUARE = (0xf0, 0xa3, 0xd0)

# The glyph is authored on a 32x32 grid and scaled to fit the tile.
PAD = 0.16
STROKE = 2.0


def dist_point_segment(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def inside_rounded_rect(x, y, w, h, r):
    if x < 0 or y < 0 or x > w or y > h:
        return False
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    return math.hypot(x - cx, y - cy) <= r


def glyph_colour(gx, gy):
    """gx, gy in the 32x32 glyph space. Returns the topmost shape's colour."""
    half = STROKE / 2.0

    # triangle, drawn as three edges
    tri = [(16.0, 2.8), (20.4, 10.4), (11.6, 10.4)]
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        if dist_point_segment(gx, gy, a[0], a[1], b[0], b[1]) <= half:
            return TRIANGLE

    # circle
    if abs(math.hypot(gx - 25.2, gy - 16.0) - 4.2) <= half:
        return CIRCLE

    # cross
    if dist_point_segment(gx, gy, 3.9, 12.4, 10.9, 19.6) <= half:
        return CROSS
    if dist_point_segment(gx, gy, 10.9, 12.4, 3.9, 19.6) <= half:
        return CROSS

    # square
    for a, b in (((12.3, 21.6), (19.7, 21.6)), ((19.7, 21.6), (19.7, 29.0)),
                 ((19.7, 29.0), (12.3, 29.0)), ((12.3, 29.0), (12.3, 21.6))):
        if dist_point_segment(gx, gy, a[0], a[1], b[0], b[1]) <= half:
            return SQUARE

    return None


def render():
    pixels = []
    span = 1.0 - 2 * PAD          # glyph occupies this fraction of the tile
    radius = 0.22 * SIZE

    for py in range(SIZE):
        row = []
        for px in range(SIZE):
            r = g = b = a = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    x = px + (sx + 0.5) / SS
                    y = py + (sy + 0.5) / SS

                    if not inside_rounded_rect(x, y, SIZE, SIZE, radius):
                        continue

                    # tile background, with a one-pixel inner border
                    cr, cg, cb = BG
                    edge = (SIZE - x) < 1.4 or x < 1.4 or (SIZE - y) < 1.4 or y < 1.4
                    if edge:
                        cr, cg, cb = BORDER

                    gx = (x / SIZE - PAD) / span * 32.0
                    gy = (y / SIZE - PAD) / span * 32.0
                    hit = glyph_colour(gx, gy)
                    if hit:
                        cr, cg, cb = hit

                    r += cr
                    g += cg
                    b += cb
                    a += 255.0

            n = SS * SS
            if a == 0:
                row.append((0, 0, 0, 0))
            else:
                row.append((int(r / n), int(g / n), int(b / n), int(a / n)))
        pixels.append(row)
    return pixels


def write_png(path, pixels):
    raw = bytearray()
    for row in pixels:
        raw.append(0)                      # filter: none
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", header)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    pixels = render()
    path = os.path.join(ROOT, "icon.png")
    write_png(path, pixels)
    print("icon.png  (%d bytes)" % os.path.getsize(path))


if __name__ == "__main__":
    main()
