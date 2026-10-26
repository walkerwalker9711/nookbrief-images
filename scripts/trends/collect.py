"""Collect what is blowing up on YouTube Shorts in Korea and the US, for the senior-channel planning page.

  python collect.py            (needs the YT_* secrets; writes trends/latest.json and trends/history/<date>.json)

Per region: the mostPopular chart filtered to Shorts (<= 3 min), the top Shorts of the last 7 days for each
seed keyword (search.list, order=viewCount), and YouTube search autocomplete for the same keywords.
Plus the top #shorts of the last 3 days, per-category charts and recurring hashtags across all of them.
Quota: about 100 units per search, so ~2,800 of the 10,000 daily units.
"""
import base64
import datetime as dt
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from common import ROOT, YT, call, google_token, save  # noqa: E402

REGIONS = {
    "KR": {"lang": "ko", "overall_q": ["쇼츠", "#shorts"], "keywords": [
        "스미싱", "보이스피싱", "스마트폰 사용법", "카톡 꿀팁", "갤럭시 설정", "아이폰 꿀팁",
        "국민연금", "건강보험", "노후 준비", "5060", "치매 예방", "무릎 운동"]},
    "US": {"lang": "en", "overall_q": ["#shorts", "shorts"], "keywords": [
        "scam text", "phone tips for seniors", "iphone tips", "android tips", "seniors",
        "grandparents", "medicare", "retirement", "social security", "gifts for grandparents"]},
}
MAX_SHORT = 180  # seconds; Shorts can run up to 3 minutes
CATEGORIES = {"24": "엔터테인먼트", "23": "코미디", "22": "인물·블로그", "26": "노하우·스타일", "27": "교육",
              "28": "과학기술", "17": "스포츠", "20": "게임", "10": "음악", "25": "뉴스·정치", "19": "여행", "15": "동물"}


def seconds(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def thumb(url):
    """Small thumbnail inlined as a data URL, so the page needs no outside image host."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
    except requests.RequestException:
        return ""


def details(ids, headers, now):
    out = []
    for i in range(0, len(ids), 50):
        res = call("GET", f"{YT}/youtube/v3/videos", headers=headers, params={
            "part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i + 50])})
        for v in res.get("items", []):
            secs = seconds(v["contentDetails"].get("duration"))
            if not secs or secs > MAX_SHORT:
                continue
            sn, st = v["snippet"], v.get("statistics", {})
            published = dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            hours = max((now - published).total_seconds() / 3600, 1)
            views = int(st.get("viewCount", 0))
            out.append({
                "id": v["id"], "title": sn["title"], "channel": sn["channelTitle"],
                "published": sn["publishedAt"], "seconds": secs, "views": views,
                "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)),
                "views_per_hour": round(views / hours), "tags": sn.get("tags", [])[:8],
                "lang": (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").lower(),
                "thumb": thumb(sn["thumbnails"].get("default", {}).get("url", "")),
            })
    return out


NOISE = {"shorts", "short", "쇼츠", "숏츠", "youtubeshorts", "shortsfeed", "shortsvideo", "viral", "viralvideo",
         "fyp", "foryou", "foryoupage", "trending", "trend", "youtube", "subscribe", "explore", "reels"}


def local(v, region):
    """Keep videos made for this region's language: Hangul titles for KR, English audio or Latin titles for US."""
    if region == "KR":
        return v["lang"].startswith("ko") or bool(re.search(r"[가-힣]", v["title"]))
    if v["lang"]:
        return v["lang"].startswith("en")
    return not re.search(r"[^\x00-\x7F\u2000-\u2BFF\U0001F000-\U0001FFFF]", v["title"])


def hot_words(videos, top=40):
    """Title hashtags that recur across different channels in today's top Shorts, weighted by views."""
    score, chans = {}, {}
    for v in videos:
        for w in {w.lower() for w in re.findall(r"#(\w+)", v["title"])} - NOISE:
            score[w] = score.get(w, 0) + v["views"]
            chans.setdefault(w, set()).add(v["channel"])
    ranked = sorted((w for w in score if len(chans[w]) >= 2), key=lambda w: -score[w])[:top]
    return [{"word": w, "videos": len(chans[w]), "views": score[w]} for w in ranked]


def suggest(q, lang, region):
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", timeout=20, params={
            "client": "firefox", "ds": "yt", "hl": lang, "gl": region, "q": q})
        return r.json()[1][:10]
    except (requests.RequestException, ValueError, IndexError):
        return []


def main():
    token = google_token()
    if not token:
        sys.exit("YT_* secrets are not set")
    headers = {"Authorization": f"Bearer {token}"}
    now = dt.datetime.now(dt.timezone.utc)
    week_ago = (now - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"generated": now.isoformat(timespec="minutes"), "regions": {}}
    for region, cfg in REGIONS.items():
        chart = call("GET", f"{YT}/youtube/v3/videos", headers=headers, params={
            "part": "id", "chart": "mostPopular", "regionCode": region, "maxResults": 50})
        popular = [v for v in details([v["id"] for v in chart.get("items", [])], headers, now) if local(v, region)]
        ids = []
        for q in cfg["overall_q"]:
            found = call("GET", f"{YT}/youtube/v3/search", headers=headers, params={
                "part": "id", "q": q, "type": "video", "videoDuration": "short", "order": "viewCount",
                "publishedAfter": (now - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "regionCode": region, "relevanceLanguage": cfg["lang"], "maxResults": 50})
            ids += [i["id"]["videoId"] for i in found.get("items", []) if i["id"]["videoId"] not in ids]
        overall = sorted((v for v in details(ids, headers, now) if local(v, region)), key=lambda v: -v["views"])
        categories = {}
        for cid, name in CATEGORIES.items():
            try:
                res = call("GET", f"{YT}/youtube/v3/videos", headers=headers, params={
                    "part": "id", "chart": "mostPopular", "regionCode": region, "videoCategoryId": cid, "maxResults": 50})
            except RuntimeError:  # not every category has a chart in every region
                continue
            vids = [v for v in details([v["id"] for v in res.get("items", [])], headers, now) if local(v, region)]
            if vids:
                categories[name] = sorted(vids, key=lambda v: -v["views_per_hour"])[:8]
        keywords = {}
        for kw in cfg["keywords"]:
            found = call("GET", f"{YT}/youtube/v3/search", headers=headers, params={
                "part": "id", "q": kw, "type": "video", "videoDuration": "short", "order": "viewCount",
                "publishedAfter": week_ago, "regionCode": region, "relevanceLanguage": cfg["lang"],
                "maxResults": 8})
            vids = details([i["id"]["videoId"] for i in found.get("items", [])], headers, now)
            keywords[kw] = {"videos": sorted(vids, key=lambda v: -v["views"]),
                            "suggest": suggest(kw, cfg["lang"], region)}
        pool = {v["id"]: v for v in overall + popular + [v for c in categories.values() for v in c]}
        data["regions"][region] = {"popular": sorted(popular, key=lambda v: -v["views_per_hour"]),
                                   "overall": overall, "categories": categories,
                                   "hot_words": hot_words(list(pool.values())), "keywords": keywords}
    save(ROOT / "trends" / "latest.json", data)
    slim = {"generated": data["generated"], "regions": {
        r: {"popular": [{k: v[k] for k in ("id", "title", "views", "views_per_hour")} for v in d["popular"]],
            "overall": [{k: v[k] for k in ("id", "title", "views")} for v in d["overall"]],
            "hot_words": d["hot_words"],
            "keywords": {k: [{x: v[x] for x in ("id", "title", "views")} for v in kd["videos"]]
                         for k, kd in d["keywords"].items()}}
        for r, d in data["regions"].items()}}
    save(ROOT / "trends" / "history" / f"{now:%Y-%m-%d}.json", slim)
    print({r: len(d["popular"]) for r, d in data["regions"].items()})


if __name__ == "__main__":
    main()
