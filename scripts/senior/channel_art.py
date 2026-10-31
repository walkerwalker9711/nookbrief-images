"""Channel art for the senior channels.

  python channel_art.py bg kr       background picture for the banner (OpenAI, needs OPENAI_API_KEY)
  python channel_art.py apply kr    upload senior/<ch>/brand/banner.jpg and set the channel description
                                    (needs YT_CLIENT_ID, YT_CLIENT_SECRET and the channel's refresh token with youtube.force-ssl)

The banner itself is composed from the background by senior/<ch>/brand/make_brand.py banner.
"""
import base64
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from common import YT, google_token  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TOKENS = {"kr": "KR_YT_REFRESH_TOKEN", "us": "US_YT_REFRESH_TOKEN"}
BG = {"kr": ("Wide cinematic establishing shot of a quiet Korean hillside neighborhood at blue-hour dusk: narrow alley "
             "stairs, low houses with tiled and flat roofs, warm window lights, a small neighborhood community center, "
             "street lamps coming on, power lines, distant city lights and a harbor far below. Korean webtoon drama style "
             "digital illustration, clean fine line art, cinematic lighting, muted deep-navy and warm amber palette, "
             "calm but slightly tense mood. No people. The middle band of the picture is calm and darker so text can sit "
             "on it. Absolutely no text, letters, signs with writing, numbers or logos.")}


# v2 (owner 10-27 "구데기, 요즘 채널 트렌드 확인"): the trending channels use one strong poster picture with the host
# big on one side and a clean dark side for the title (ai방송국, 노후 복지번역기, 김소형채널H), not a busy scenery
POSTER = {"kr": ("Cinematic YouTube channel banner artwork, wide 3:2, in Korean webtoon drama style (semi-realistic, clean fine "
                 "line art, cinematic rim lighting). The young village chief from the reference picture, exactly the same face, "
                 "hair, navy padded vest and light blue shirt, shown from the chest up on the RIGHT side of the picture (his face "
                 "about 72% from the left edge and exactly at the vertical centre), turned three-quarters toward the left, calm "
                 "and serious, holding the white megaphone low at his shoulder. Behind him a Korean residential street at night "
                 "with soft out-of-focus red and blue police lights and a warm street lamp, light haze. The LEFT 55% of the picture "
                 "is a clean dark navy-to-black gradient with only faint bokeh, empty, for a title. Strong contrast, premium "
                 "movie-poster look. Absolutely no text, letters, numbers, signs with writing or logos.")}


def poster(ch):
    import os
    key = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"}
    ref = ROOT / "senior" / ch / "character.png"
    out = ROOT / "senior" / ch / "brand" / "banner_bg.png"
    for model in ("gpt-image-1.5", "gpt-image-1"):
        with open(ref, "rb") as f:
            r = requests.post("https://api.openai.com/v1/images/edits", headers=key, timeout=400,
                              files=[("image[]", (ref.name, f, "image/png"))],
                              data={"model": model, "prompt": POSTER[ch], "size": "1536x1024", "quality": "high"})
        if r.ok:
            out.write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
            print("poster", out, "with", model)
            return
        print(model, "->", r.status_code, r.text[:300])
    sys.exit("no image model worked")


def bg(ch):
    import os
    key = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"}
    out = ROOT / "senior" / ch / "brand" / "banner_bg.png"
    for model in ("gpt-image-1.5", "gpt-image-1"):
        r = requests.post("https://api.openai.com/v1/images/generations", headers=key, timeout=400,
                          json={"model": model, "prompt": BG[ch], "size": "1536x1024", "quality": "high"})
        if r.ok:
            out.write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
            print("background", out, "with", model)
            return
        print(model, "->", r.status_code, r.text[:300])
    sys.exit("no image model worked")


def apply(ch):
    tok = google_token(TOKENS[ch])
    if not tok:
        sys.exit(f"{TOKENS[ch]} is not set")
    auth = {"Authorization": f"Bearer {tok}"}
    brand = ROOT / "senior" / ch / "brand"
    r = requests.post(f"{YT}/upload/youtube/v3/channelBanners/insert", headers={**auth, "Content-Type": "image/jpeg"},
                      data=(brand / "banner.jpg").read_bytes(), timeout=120)
    if r.status_code >= 300:
        sys.exit(f"banner upload -> {r.status_code}: {r.text[:300]}")
    url = r.json()["url"]
    me = requests.get(f"{YT}/youtube/v3/channels", params={"part": "brandingSettings", "mine": "true"}, headers=auth,
                      timeout=60).json()["items"][0]
    settings = me.get("brandingSettings", {})
    settings.setdefault("image", {})["bannerExternalUrl"] = url
    desc = brand / "channel_description.txt"
    if desc.exists():
        settings.setdefault("channel", {})["description"] = desc.read_text(encoding="utf-8").strip()
    u = requests.put(f"{YT}/youtube/v3/channels", params={"part": "brandingSettings"}, headers=auth, timeout=60,
                     json={"id": me["id"], "brandingSettings": settings})
    if u.status_code >= 300:
        sys.exit(f"channel update -> {u.status_code}: {u.text[:300]}")
    print("channel updated:", me["id"], "banner and description set")


if __name__ == "__main__":
    {"bg": bg, "poster": poster, "apply": apply}[sys.argv[1]](sys.argv[2])
