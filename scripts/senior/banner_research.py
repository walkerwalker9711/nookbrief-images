"""Fetch the banners, profile pictures and descriptions of the channels behind this week's top senior/scam Shorts
(trends/latest.json), so channel art is designed from what works now, not from a guess (owner 10-27).

  python banner_research.py      (needs YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN)
Writes senior/research/banners/<n>_<channel>.jpg, <n>_<channel>_avatar.jpg and index.json.
"""
import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from common import YT, google_token  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "senior" / "research" / "banners"
KEYWORDS = ["보이스피싱", "스미싱", "5060", "노후 준비", "국민연금", "건강보험", "치매 예방", "카톡 꿀팁", "스마트폰 사용법"]


def main():
    tok = google_token("YT_REFRESH_TOKEN")
    auth = {"Authorization": f"Bearer {tok}"}
    kr = json.loads((ROOT / "trends" / "latest.json").read_text(encoding="utf-8"))["regions"]["KR"]
    best = {}
    for k in KEYWORDS:
        for v in kr["keywords"].get(k, {}).get("videos", []):
            if v["views_per_hour"] > best.get(v["channel"], (0, ""))[0]:
                best[v["channel"]] = (v["views_per_hour"], v["id"])
    ids = [vid for _, (_, vid) in sorted(best.items(), key=lambda i: -i[1][0])[:30]]
    chan_ids = []
    for i in range(0, len(ids), 50):
        r = requests.get(f"{YT}/youtube/v3/videos", params={"part": "snippet", "id": ",".join(ids[i:i + 50])}, headers=auth, timeout=60)
        chan_ids += [x["snippet"]["channelId"] for x in r.json().get("items", [])]
    r = requests.get(f"{YT}/youtube/v3/channels", headers=auth, timeout=60,
                     params={"part": "snippet,statistics,brandingSettings", "id": ",".join(dict.fromkeys(chan_ids))})
    items = sorted(r.json().get("items", []), key=lambda c: -int(c["statistics"].get("subscriberCount", 0) or 0))
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for n, c in enumerate(items[:24]):
        name = c["snippet"]["title"]
        slug = f"{n:02d}_" + re.sub(r"[^\w가-힣]+", "", name)[:20]
        row = {"name": name, "subs": c["statistics"].get("subscriberCount"), "handle": c["snippet"].get("customUrl"),
               "description": c["brandingSettings"].get("channel", {}).get("description", "")[:600]}
        banner = c["brandingSettings"].get("image", {}).get("bannerExternalUrl")
        if banner:
            b = requests.get(banner + "=w2048-fcrop64=1,00000000ffffffff-k-c0xffffffff-no-nd-rj", timeout=60)
            if b.ok:
                (OUT / f"{slug}.jpg").write_bytes(b.content)
                row["banner"] = f"{slug}.jpg"
        thumb = c["snippet"]["thumbnails"].get("high", {}).get("url")
        if thumb:
            a = requests.get(thumb, timeout=60)
            if a.ok:
                (OUT / f"{slug}_avatar.jpg").write_bytes(a.content)
                row["avatar"] = f"{slug}_avatar.jpg"
        index.append(row)
        print(row["subs"], name, "banner" if banner else "no banner")
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
