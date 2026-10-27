"""한국이장님 channel art from the drawn character: profile picture (800x800) and a Shorts thumbnail (1080x1920).

  python make_brand.py profile
  python make_brand.py thumb <scene image> "<line 1>" "<line 2>" "<small line>" "<tag>" <out.jpg>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
CHAR = HERE.parent / "character.png"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
NAVY, YEL, RED, WHITE, INK = (20, 33, 61), (255, 212, 0), (227, 36, 43), (255, 255, 255), (17, 20, 24)


def font(size):
    return ImageFont.truetype(FONT, size, index=1)  # index 1 = Korean


def profile(out=HERE / "profile.png", box=(250, 20, 730, 500)):
    """Head and megaphone on navy, yellow ring; reads at 98px in the YouTube sidebar."""
    S = 800
    face = Image.open(CHAR).convert("RGB").crop(box).resize((S, S), Image.LANCZOS)
    bg = Image.new("RGB", (S, S), NAVY)
    # swap the grey studio background for navy: flood from the edges only, so white parts of the
    # megaphone and shirt inside the figure stay
    key = face.copy()
    for seed in [(x, 0) for x in range(0, S, 40)] + [(0, y) for y in range(0, S, 40)] + [(S - 1, y) for y in range(0, S, 40)]:
        r, g, b = key.getpixel(seed)
        if abs(r - g) < 14 and abs(g - b) < 16 and r > 140:
            ImageDraw.floodfill(key, seed, (255, 0, 255), thresh=34)
    mask = Image.eval(Image.merge("RGB", key.split()).convert("RGB").point(lambda v: v), lambda v: v)
    kp = key.load()
    mask = Image.new("L", (S, S), 255)
    mp = mask.load()
    for y in range(S):
        for x in range(S):
            if kp[x, y] == (255, 0, 255):
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    bg.paste(face, (0, 0), mask)
    circle = Image.new("L", (S, S), 0)
    ImageDraw.Draw(circle).ellipse((0, 0, S - 1, S - 1), fill=255)
    out_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out_img.paste(bg, (0, 0), circle)
    ImageDraw.Draw(out_img).ellipse((10, 10, S - 11, S - 11), outline=YEL, width=26)
    out_img.save(out)
    print("profile", out)


def text_w(d, t, f):
    return d.textbbox((0, 0), t, font=f)[2]


def thumb(scene, l1, l2, small, tag, out):
    W, H = 1080, 1920
    img = Image.open(scene).convert("RGB")
    img = img.resize((W, int(img.height * W / img.width)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), INK)
    canvas.paste(img, (0, H - img.height))
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):  # dark at the top for the title, clear in the middle, dark at the bottom for the badge
        t = y / H
        a = 235 if t < 0.12 else int(235 - (t - 0.12) / 0.3 * 200) if t < 0.42 else 35 if t < 0.78 else int(35 + (t - 0.78) / 0.22 * 190)
        sd.line([(0, y), (W, y)], fill=max(0, min(255, a)))
    canvas = Image.composite(Image.new("RGB", (W, H), (8, 10, 14)), canvas, shade)
    d = ImageDraw.Draw(canvas)
    # case tag
    ft = font(44)
    tw = text_w(d, tag, ft)
    d.rectangle((60, 120, 60 + tw + 90, 196), fill=(8, 10, 14))
    d.ellipse((84, 144, 112, 172), fill=RED)
    d.text((132, 128), tag, font=ft, fill=WHITE)
    # title, two lines, stroked
    y = 250
    for line, color, size in ((l1, WHITE, 150), (l2, YEL, 150)):
        f = font(size)
        while text_w(d, line, f) > W - 100:
            size -= 6
            f = font(size)
        d.text(((W - text_w(d, line, f)) / 2, y), line, font=f, fill=color, stroke_width=12, stroke_fill=INK)
        y += size + 30
    y += 20
    fs = font(60)
    sw = text_w(d, small, fs)
    d.rectangle(((W - sw) / 2 - 30, y + 10, (W + sw) / 2 + 30, y + 100), fill=RED)
    d.text(((W - sw) / 2, y + 16), small, font=fs, fill=WHITE)
    # channel badge
    badge = Image.open(HERE / "profile.png").resize((130, 130), Image.LANCZOS)
    name, fn = "한국이장님", font(64)
    nw = text_w(d, name, fn)
    x0 = (W - (130 + 20 + nw)) // 2
    canvas.paste(badge, (x0, H - 260), badge)
    d.text((x0 + 150, H - 240), name, font=fn, fill=WHITE, stroke_width=8, stroke_fill=INK)
    canvas.save(out, quality=92)
    print("thumb", out)


if __name__ == "__main__":
    if sys.argv[1] == "profile":
        profile()
    else:
        thumb(*sys.argv[2:8])
