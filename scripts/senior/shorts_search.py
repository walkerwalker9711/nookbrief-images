"""Top Shorts for given keywords (last 30 days, by views), to check what a genre looks like before writing a script.

  python shorts_search.py <keyword> [<keyword> ...]   (needs the YT_* secrets; keywords with spaces use _)
Writes senior/research/shorts/<date>.json: per keyword, the 15 most viewed Korean Shorts with length and views.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "trends"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from collect import details, local, search  # noqa: E402
from common import ROOT, google_token  # noqa: E402


def main(words):
    now = dt.datetime.now(dt.timezone.utc)
    headers = {"Authorization": f"Bearer {google_token('YT_REFRESH_TOKEN')}"}
    since = (now - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {"generated": now.isoformat(timespec="minutes"), "keywords": {}}
    for w in words:
        q = w.replace("_", " ")
        ids = search(headers, q=q, publishedAfter=since, regionCode="KR", relevanceLanguage="ko", maxResults=25)
        vids = [v for v in details(ids, headers, now) if local(v, "KR")]
        for v in vids:
            v.pop("thumb", None)
        out["keywords"][q] = sorted(vids, key=lambda v: -v["views"])[:15]
        print(q, len(vids))
    path = ROOT / "senior" / "research" / "shorts" / f"{now:%Y-%m-%d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
