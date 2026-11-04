"""Mayor of Main St. Shorts cover (same layout as 한국이장님, Montserrat).

  python thumb.py <scene> "<line 1>" "<line 2>" "<red badge>" "<tag>" <out.jpg>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
YEL, RED, WHITE, INK = (255, 212, 0), (227, 36, 43), (255, 255, 255), (17, 20, 24)


def font(size):
    f = ImageFont.truetype(str(HERE / "fonts" / "Montserrat.ttf"), size)
    f.set_variation_by_name(b"ExtraBold")
    return f


def text_w(d, t, f):
    return d.textlength(t, font=f)


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
    badge = Image.open(HERE / "profile.png").convert("RGB").resize((130, 130), Image.LANCZOS)
    m = Image.new("L", (130, 130), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 129, 129), fill=255)
    name, fn = "Mayor of Main St.", font(60)
    nw = text_w(d, name, fn)
    x0 = (W - (130 + 20 + nw)) // 2
    canvas.paste(badge, (int(x0), H - 260), m)
    d.text((int(x0) + 150, H - 236), name, font=fn, fill=WHITE, stroke_width=8, stroke_fill=INK)
    canvas.save(out, quality=92)
    print("thumb", out)



if __name__ == "__main__":
    thumb(*sys.argv[1:7])
