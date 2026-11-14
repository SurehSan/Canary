"""Regenerate the app's brand images from design/logo.png.

    python design/make_brand_assets.py

Crops to the bird, removes the cream background (soft alpha edge, colour
un-premultiplied so no cream halo remains on dark backgrounds), and writes
web-sized PNGs plus a favicon into canary/static/brand/.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "design" / "logo.png"
OUT = ROOT / "canary" / "static" / "brand"
INNER, OUTER = 18, 70  # colour distance from background: <= INNER fully transparent, >= OUTER opaque


def remove_background(im):
    im = im.convert("RGBA")
    bg = im.getpixel((5, 5))[:3]
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            dist = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            a = 0.0 if dist <= INNER else 1.0 if dist >= OUTER else (dist - INNER) / (OUTER - INNER)
            if a == 0:
                px[x, y] = (0, 0, 0, 0)
            elif a < 1:  # un-premultiply against the cream background
                px[x, y] = tuple(max(0, min(255, round((c - (1 - a) * k) / a))) for c, k in zip((r, g, b), bg)) + (
                    round(a * 255),)
    return im


def square_crop(im, pad=0.04):
    bbox = im.getchannel("A").getbbox()
    left, top, right, bottom = bbox
    side = max(right - left, bottom - top)
    side = int(side * (1 + 2 * pad))
    cx, cy = (left + right) // 2, (top + bottom) // 2
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im.crop(bbox), (side // 2 - (cx - left), side // 2 - (cy - top)))
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    logo = square_crop(remove_background(Image.open(SRC)))
    for name, size in (("canary-logo-512.png", 512), ("canary-logo-256.png", 256),
                       ("canary-mark-64.png", 64), ("favicon-32.png", 32), ("apple-touch-icon.png", 180)):
        logo.resize((size, size), Image.LANCZOS).save(OUT / name, optimize=True)
    logo.resize((256, 256), Image.LANCZOS).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    for f in sorted(OUT.iterdir()):
        print(f"{f.name}: {f.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
