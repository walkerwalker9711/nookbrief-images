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
    {"bg": bg, "apply": apply}[sys.argv[1]](sys.argv[2])
