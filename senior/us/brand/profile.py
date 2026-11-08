"""Mayor of Main St. profile picture (11-04): the Mayor's face big on a warm mustard circle (trending US story
channels use one bold mascot face on a flat bright colour)."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ch = Image.open(HERE.parent / "character.png").convert("RGB")
a = np.asarray(ch).astype(float)
# the plain backdrop: low-saturation light grey, reached from the picture edges
sat = a.max(2) - a.min(2)
# the warm top of the backdrop is a little more saturated; below the shoulders keep it strict (light denim)
limit = np.where(np.arange(a.shape[0])[:, None] < 600, 60, 42)
near = (sat < limit) & (a.mean(2) > 95)
m = Image.fromarray((near * 255).astype("uint8")).copy()
for xy in [(x, 0) for x in range(0, ch.width, 32)] + [(0, y) for y in range(0, ch.height, 32)] + [(ch.width - 1, y) for y in range(0, ch.height, 32)] + [(x, y) for x in range(860, ch.width, 24) for y in range(0, 700, 24)]:  # the vignette cuts off the top-right corner
    if m.getpixel(xy) == 255:
        ImageDraw.floodfill(m, xy, 128)
bgmask = np.asarray(m) == 128
alpha = Image.fromarray((~bgmask * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2))
flat = Image.new("RGB", ch.size, (242, 178, 58))
img = Image.composite(ch, flat, alpha)
cx, cy, r = 500, 620, 470  # face centre in character.png (1024x1536), found by eye
img.crop((cx - r, cy - r, cx + r, cy + r)).resize((800, 800), Image.LANCZOS).save(HERE / "profile.png")
print("profile", HERE / "profile.png")
