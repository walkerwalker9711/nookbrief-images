"""Mayor of Main St. banner (11-04): Main Street poster picture, the Mayor on the right, serif title on the left.

  python banner.py   -> banner.jpg   (banner_bg.png from channel_art.py poster us)
Fonts (Google Fonts, OFL) are fetched into fonts/ on first run.
"""
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
(HERE / "fonts").mkdir(exist_ok=True)
for name, url in (("DMSerifDisplay-Regular.ttf", "dmserifdisplay/DMSerifDisplay-Regular.ttf"),
                  ("Montserrat.ttf", "montserrat/Montserrat%5Bwght%5D.ttf")):
    if not (HERE / "fonts" / name).exists():
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/" + url, HERE / "fonts" / name)
W, H = 2048, 1152
SX, SY = (W - 1235) // 2, (H - 338) // 2  # the area every device shows
FACE = (1105, 275)
GOLD, CREAM = (238, 190, 98), (252, 246, 234)


def serif(size):
    return ImageFont.truetype(str(HERE / "fonts" / "DMSerifDisplay-Regular.ttf"), size)


def sans(size, weight):
    f = ImageFont.truetype(str(HERE / "fonts" / "Montserrat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def spaced(d, xy, text, f, fill, sp):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + sp
    return x


def banner(out=HERE / "banner.jpg", tagline="The real story behind the headline.", kicker="TRUE STORY DRAMA"):
    # the poster's face sits high; every phone shows only the middle band, so the face goes to the band's centre
    # (FACE: the face in banner_bg.png, found by eye) over a blurred copy for the edges (as the 한국이장님 banner)
    src = Image.open(HERE / "banner_bg.png").convert("RGB")
    src = ImageEnhance.Brightness(src).enhance(1.05)
    s = 1.0
    pic = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    ox, oy = 1400 - round(FACE[0] * s), H // 2 - round(FACE[1] * s)
    img = src.crop((0, 380, 760, 820)).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    img = ImageEnhance.Brightness(img).enhance(0.7)
    m = np.ones((pic.height, pic.width))
    xs, ys = np.arange(pic.width), np.arange(pic.height)
    m *= np.clip(xs / 260, 0, 1)[None, :] * np.clip((pic.width - 1 - xs) / 420, 0, 1)[None, :]
    m *= np.clip(ys / 200, 0, 1)[:, None]
    img.paste(pic, (ox, oy), Image.fromarray((m * 255).astype("uint8")))
    # warm dark wash on the left so the title reads on any device
    xx = np.arange(W)[None, :].repeat(H, 0)
    a = np.clip((1300 - xx) / 900, 0, 1) ** 1.3 * 175
    img = Image.composite(Image.new("RGB", (W, H), (34, 16, 14)), img, Image.fromarray(a.astype("uint8")))

    x = SX + 30
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def text(d, shadow):
        o = 4 if shadow else 0
        c = (0, 0, 0, 170)
        spaced(d, (x + o, 432 + o), kicker, sans(26, b"Bold"), c if shadow else GOLD, 8)
        d.text((x - 2 + o, 462 + o), "Mayor of", font=serif(78), fill=c if shadow else CREAM)
        d.text((x - 6 + o, 528 + o), "Main St.", font=serif(150), fill=c if shadow else CREAM)

    text(ImageDraw.Draw(sh), True)
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    text(d, False)
    d.line((x + 2, 712, x + 64, 712), fill=GOLD, width=3)
    spaced(d, (x + 84, 693), tagline, sans(32, b"Medium"), (240, 232, 220), 1)
    img.convert("RGB").save(out, quality=94)
    print("banner", out)


if __name__ == "__main__":
    banner()
