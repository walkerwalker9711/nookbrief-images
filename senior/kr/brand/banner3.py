"""한국이장님 banner v3 (10-29): serif drama-poster title, three lines only, no pills or chips.

  python banner3.py   -> banner.jpg
"""
import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
HERE = Path(__file__).resolve().parent
S = HERE  # fonts/ next to this file (Google Fonts, OFL); fetched on first run
BG = HERE / "banner_bg.png"
for _n, _u in (("NotoSerifKR.ttf", "notoserifkr/NotoSerifKR%5Bwght%5D.ttf"), ("NotoSansKR.ttf", "notosanskr/NotoSansKR%5Bwght%5D.ttf")):
    if not (HERE / "fonts" / _n).exists():
        __import__("urllib.request").request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/" + _u, HERE / "fonts" / _n)
W, H = 2048, 1152
sx0, sy0 = (W - 1235) // 2, (H - 338) // 2

def vf(name, size, w):
    f = ImageFont.truetype(str(S / "fonts" / name), size); f.set_variation_by_name(w); return f

def spaced(d, xy, t, f, fill, sp):
    x, y = xy
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + sp
    return x

def base(warm):
    pic = Image.open(BG).convert("RGB")
    pic = ImageEnhance.Brightness(pic).enhance(1.12)
    s = 0.86
    pic = pic.resize((round(1536 * s), round(1024 * s)), Image.LANCZOS)
    ox, oy = sx0 + 1235 - 170 - int(pic.width * 0.74), H // 2 + 20 - int(pic.height * 0.19)
    back = Image.open(BG).convert("RGB").crop((460, 300, 950, 640)).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(30))
    img = Image.blend(Image.new("RGB", (W, H), (14, 16, 26)), back, 0.75)
    m = np.ones((pic.height, pic.width), float)
    xs = np.arange(pic.width); ys = np.arange(pic.height)
    m *= np.clip(xs / 300, 0, 1)[None, :] * np.clip((pic.width - 1 - xs) / 200, 0, 1)[None, :]
    m *= np.clip(ys / 160, 0, 1)[:, None]
    img.paste(pic, (ox, oy), Image.fromarray((m * 255).astype("uint8")))
    # soft left gradient for the title, lighter than before: the picture breathes
    xx = np.arange(W)[None, :].repeat(H, 0)
    a = np.clip((1250 - xx) / 900, 0, 1) ** 1.4 * 170
    img = Image.composite(Image.new("RGB", (W, H), (10, 12, 20)), img, Image.fromarray(a.astype("uint8")))
    if warm:
        yy, xg = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xg - 520) / 1.6) ** 2 + ((yy - 640) / 1.0) ** 2) / 700
        g = (np.clip(1 - r, 0, 1) ** 2 * 60).astype("uint8")
        img = Image.composite(Image.new("RGB", (W, H), (255, 170, 90)), img, Image.fromarray(g))
    return img

def shadowed(img, draw_fn, blur=10, alpha=170):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(sh), (0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(blur)))
    draw_fn(ImageDraw.Draw(img), None); return img

def v1(out, line="", kicker="REAL STORY  DRAMA"):  # drama poster: serif title, gold kicker, thin subtitle, no pills
    img = base(True)
    x = sx0 + 20
    gold, cream = (232, 196, 120), (250, 244, 232)
    kf, tf, sf = vf("NotoSansKR.ttf", 26, b"SemiBold"), vf("NotoSerifKR.ttf", 128, b"Black"), vf("NotoSansKR.ttf", 36, b"Regular")
    def draw(d, sh):
        o = 4 if sh else 0
        spaced(d, (x + o, 430 + o), kicker, kf, sh or gold, 7)
        d.text((x - 4 + o, 452 + o), "한국이장님", font=tf, fill=sh or cream)
    img = shadowed(img, draw)
    d = ImageDraw.Draw(img)
    d.line((x + 2, 676, x + 70, 676), fill=gold, width=3)
    gf = vf("NotoSansKR.ttf", 30, b"Medium")
    spaced(d, (x + 90, 654), line, vf("NotoSansKR.ttf", 32, b"Medium"), (236, 232, 222), 3)
    img.convert("RGB").save(out, quality=94)

def v2(out):  # bold modern sans, white title + one yellow word, clean
    img = base(False)
    x = sx0 + 20
    tf = vf("NotoSansKR.ttf", 156, b"Black"); sf = vf("NotoSansKR.ttf", 38, b"Medium"); kf = vf("NotoSansKR.ttf", 28, b"Bold")
    def draw(d, sh):
        o = 4 if sh else 0
        d.text((x + o, 452 + o), "한국", font=tf, fill=sh or (255, 255, 255))
        w = d.textlength("한국", font=tf)
        d.text((x + w + 6 + o, 452 + o), "이장님", font=tf, fill=sh or (255, 214, 0))
        d.text((x + 6 + o, 664 + o), "사기 실화 · 감동 실화 웹툰 드라마", font=sf, fill=sh or (235, 235, 240))
    img = shadowed(img, draw)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x + 4, 420, x + 4 + 8, 452), 3, fill=(255, 214, 0))
    spaced(d, (x + 26, 418), "진짜 있었던 이야기만 합니다", kf, (255, 214, 0), 1)
    img.convert("RGB").save(out, quality=94)



if __name__ == "__main__":
    v1(HERE / "banner.jpg", "사건·뉴스 한 줄 뒤의 진짜 이야기", "REAL STORY  DRAMA")
