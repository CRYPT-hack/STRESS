#!/usr/bin/env python3
"""Build the reaper sprites for the desktop pet.

Reads the source clipart (checkerboard-flattened webp), knocks out the
background by flood-filling from the borders, feathers the edge, crops,
scales and writes:

    assets/reaper.png        facing right
    assets/reaper_flip.png   facing left

Run once whenever the source art changes:
    python3 make_sprites.py [source_image]
"""

import os
import sys
from collections import deque

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
DEFAULT_SOURCE = os.path.join(ASSETS, "source.webp")
TARGET_HEIGHT = 260  # hi-res sprite; the pet scales it down at runtime
PAD = 6


def has_real_alpha(im):
    return im.getchannel("A").getextrema()[0] < 250


def backgroundish(px, x, y):
    """Checkerboard tiles are neutral gray/white; the reaper's blacks,
    reds and bone whites don't qualify (skull white is pure 255 but is
    enclosed by the outline, so the border flood never reaches it)."""
    r, g, b = px[x, y][:3]
    if max(r, g, b) - min(r, g, b) > 10:
        return False
    v = (r + g + b) / 3
    return v >= 186


def _flood_from_borders(bgmask, w, h):
    """Connected background starting at the borders (bgmask: 1=bg-ish)."""
    visited = bytearray(w * h)
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgmask[y * w + x] and not visited[y * w + x]:
                visited[y * w + x] = 1
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bgmask[y * w + x] and not visited[y * w + x]:
                visited[y * w + x] = 1
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and bgmask[ny * w + nx] \
                    and not visited[ny * w + nx]:
                visited[ny * w + nx] = 1
                queue.append((nx, ny))
    return visited


def knock_out_background(im):
    """Flood-fill from the borders, with a morphological closing first so
    thin anti-aliased gaps can't leak the flood into hollow parts of the
    figure (robe interior) — wide real gaps stay transparent."""
    w, h = im.size
    px = im.load()
    bgmask = bytearray(w * h)
    for y in range(h):
        base = y * w
        for x in range(w):
            bgmask[base + x] = 1 if backgroundish(px, x, y) else 0
    bg_img = Image.frombytes("L", (w, h), bytes(255 if v else 0 for v in bgmask))
    k = 9  # seals leaks narrower than ~4px; fringe gaps are far wider
    closed = bg_img.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    closed_mask = bytearray(1 if v > 127 else 0 for v in closed.tobytes())
    visited = _flood_from_borders(closed_mask, w, h)
    alpha = Image.new("L", (w, h), 255)
    alpha.putdata([0 if visited[i] else 255 for i in range(w * h)])
    removed = sum(visited) / (w * h)
    if removed > 0.75:
        raise SystemExit("background knockout removed "
                         f"{removed:.0%} of the image -- wrong source?")
    return alpha


def build(src):
    im = Image.open(src).convert("RGBA")
    print(f"source: {src} {im.size}")
    if has_real_alpha(im):
        print("source already has alpha; skipping knockout")
    else:
        alpha = knock_out_background(im)
        im.putalpha(alpha)
        pct = sum(1 for v in alpha.tobytes() if v == 0) / (im.width * im.height)
        print(f"knocked out {pct:.0%} background via border flood-fill")
    im.putalpha(im.getchannel("A").filter(ImageFilter.MinFilter(3))
                .filter(ImageFilter.GaussianBlur(1.1)))
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop((max(0, bbox[0] - PAD), max(0, bbox[1] - PAD),
                      min(im.width, bbox[2] + PAD), min(im.height, bbox[3] + PAD)))
    scale = TARGET_HEIGHT / im.height
    im = im.resize((round(im.width * scale), TARGET_HEIGHT), Image.LANCZOS)

    os.makedirs(ASSETS, exist_ok=True)
    im.save(os.path.join(ASSETS, "reaper.png"))
    im.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(ASSETS, "reaper_flip.png"))
    hist = im.getchannel("A").histogram()
    coverage = sum(hist[41:]) / (im.width * im.height)
    print(f"sprites: {im.width}x{im.height}, opaque coverage {coverage:.0%} "
          f"-> assets/reaper.png + reaper_flip.png")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE)
