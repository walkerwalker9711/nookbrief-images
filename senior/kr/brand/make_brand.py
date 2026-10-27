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


def cutout():
    """The full character with the grey studio background removed (flood from the edges)."""
    im = Image.open(CHAR).convert("RGB")
    W, H = im.size
    # neutral grey pixels (the studio backdrop, lighter behind him) that connect to the picture edge
    grey = Image.new("L", (W, H), 0)
    gp, ip = grey.load(), im.load()
    for y in range(H):
        for x in range(W):
            r, g, b = ip[x, y]
            if abs(r - g) < 10 and abs(g - b) < 12 and 120 < r < 236:
                gp[x, y] = 255
    for seed in [(x, 0) for x in range(0, W, 16)] + [(0, y) for y in range(0, H, 16)] + [(W - 1, y) for y in range(0, H, 16)] \
            + [(x, H - 1) for x in range(0, W, 16)]:
        if grey.getpixel(seed) == 255:
            ImageDraw.floodfill(grey, seed, 128)
    mask = grey.point(lambda v: 0 if v == 128 else 255).filter(ImageFilter.MinFilter(3))
    out = im.convert("RGBA")
    out.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
    return out.crop(out.getbbox())


def banner(bg=HERE / "banner_bg.png", out=HERE / "banner.jpg"):
    """2048x1152 YouTube banner. Everything that matters sits in the 1235x338 centre band every device shows."""
    W, H = 2048, 1152
    sx0, sy0, sx1, sy1 = (W - 1235) // 2, (H - 338) // 2, (W + 1235) // 2, (H + 338) // 2
    img = Image.open(bg).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    img = img.crop(((img.width - W) // 2, (img.height - H) // 2, (img.width - W) // 2 + W, (img.height - H) // 2 + H))
    # darken behind the text so it reads on any picture
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for x in range(W):
        t = abs(x - (sx0 + 430)) / 900
        sd.line([(x, sy0 - 120), (x, sy1 + 120)], fill=int(max(0, 170 * (1 - t))))
    shade = shade.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(Image.new("RGB", (W, H), (6, 10, 22)), img, shade)
    d = ImageDraw.Draw(img)
    # the 이장님 on the right of the safe band, from the knees up so the face is big enough on phones
    ch = cutout()
    ch = ch.crop((0, 0, ch.width, int(ch.height * 0.62)))
    ch = ch.resize((int(ch.width * (sy1 - sy0 + 20) / ch.height), sy1 - sy0 + 20), Image.LANCZOS)
    glow = Image.new("RGBA", ch.size, (255, 212, 0, 0))
    glow.putalpha(ch.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55)))
    cx = sx1 - ch.width + 10
    img.paste(glow, (cx, sy1 - ch.height + 20), glow)
    img.paste(ch, (cx, sy1 - ch.height + 20), ch)
    # name, one line of what the channel is, and the format line
    x = sx0 + 20
    d.text((x, sy0 - 12), "한국이장님", font=font(140), fill=WHITE, stroke_width=10, stroke_fill=INK)
    tw = text_w(d, "한국이장님", font(140))
    d.rectangle((x, sy0 + 176, x + tw, sy0 + 185), fill=YEL)
    d.text((x, sy0 + 196), "실제 사건으로 보는 사기 수법", font=font(58), fill=YEL, stroke_width=6, stroke_fill=INK)
    d.text((x, sy0 + 270), "보이스피싱 · 스미싱 · 받을 돈 · 폰 꿀팁", font=font(42), fill=(225, 230, 240), stroke_width=4, stroke_fill=INK)
    img.save(out, quality=93)
    print("banner", out, img.size)


DISPLAY = HERE / "fonts" / "BlackHanSans-Regular.ttf"  # OFL, fonts/OFL.txt


def banner2(bg=HERE / "banner_bg.png", out=HERE / "banner.jpg", face=(0.74, 0.19)):
    """v2 after looking at the channels trending now: one poster picture (host big on the right, dark left), a heavy
    yellow title, one red tag and one line of promise. Text sits in the 1235x338 band every device shows."""
    W, H = 2048, 1152
    sx0, sy0 = (W - 1235) // 2, (H - 338) // 2
    # phones show only the middle band: size and place the picture so his head and shoulders sit inside it, right side
    pic = Image.open(bg).convert("RGB")
    s = 0.80
    pic = pic.resize((round(1536 * s), round(1024 * s)), Image.LANCZOS)
    fx, fy = face
    ox, oy = sx0 + 1235 - 190 - int(pic.width * fx), H // 2 + 10 - int(pic.height * fy)
    # backdrop for the wide desktop/TV view: the same night street, enlarged, blurred and darkened
    back = Image.open(bg).convert("RGB")
    back = back.crop((int(back.width * 0.30), int(back.height * 0.30), int(back.width * 0.62), int(back.height * 0.62)))
    back = back.resize((W, H), Image.LANCZOS)  # the street lights only, no second copy of him
    back = back.filter(ImageFilter.GaussianBlur(26))
    img = Image.blend(Image.new("RGB", (W, H), (5, 8, 18)), back, 0.55)
    fade = Image.new("L", pic.size, 255)
    fd = ImageDraw.Draw(fade)
    for i in range(160):  # soft left, top and right edges
        a = int(255 * i / 160)
        fd.line([(i, 0), (i, pic.height)], fill=a)
        fd.line([(pic.width - 1 - i, 0), (pic.width - 1 - i, pic.height)], fill=a)
    top = Image.new("L", pic.size, 255)
    td = ImageDraw.Draw(top)
    for i in range(140):
        td.line([(0, i), (pic.width, i)], fill=int(255 * i / 140))
    fade = Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(fade), __import__("numpy").array(top)))
    img.paste(pic, (ox, oy), fade)
    # deepen the left so the title owns it
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for x in range(W):
        sd.line([(x, 0), (x, H)], fill=int(max(0, min(200, 230 - x * 0.19))))
    img = Image.composite(Image.new("RGB", (W, H), (4, 7, 16)), img, shade)
    d = ImageDraw.Draw(img)
    x = sx0 + 10
    tag, ft = "실제 사건 파일", font(40)
    tw = text_w(d, tag, ft)
    d.rectangle((x, sy0 + 2, x + tw + 40, sy0 + 58), fill=RED)
    d.text((x + 20, sy0 + 3), tag, font=ft, fill=WHITE)
    title = ImageFont.truetype(str(DISPLAY), 168)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x + 6, sy0 + 62 + 8), "한국이장님", font=title, fill=(0, 0, 0, 200))
    img.paste(shadow.filter(ImageFilter.GaussianBlur(8)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.text((x, sy0 + 62), "한국이장님", font=title, fill=YEL)
    d.text((x + 4, sy0 + 238), "보이스피싱, 당하기 전에 먼저 알려드립니다", font=font(44), fill=WHITE)
    d.text((x + 4, sy0 + 296), "실화 사연  |  받을 돈  |  폰 꿀팁", font=font(32), fill=(176, 186, 204))
    img.save(out, quality=94)
    print("banner", out, img.size)


if __name__ == "__main__":
    if sys.argv[1] == "profile":
        profile()
    elif sys.argv[1] == "banner":
        banner2()
    else:
        thumb(*sys.argv[2:8])
