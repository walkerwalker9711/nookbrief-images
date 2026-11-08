"""Views of our own uploaded Shorts by genre, to see which genre the channel's viewers want more of.

  python my_stats.py kr   (needs the YT_* secrets)
Reads senior/drafts/*-<ch>*/upload_result.json, writes senior/research/stats/<date>-<ch>.json and prints a table.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "trends"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from collect import details  # noqa: E402
from common import ROOT, google_token  # noqa: E402

GENRE = {"touching": "감동 실화", "alert": "사기 실화"}


def main(ch):
    now = dt.datetime.now(dt.timezone.utc)
    headers = {"Authorization": f"Bearer {google_token('YT_REFRESH_TOKEN')}"}
    mine = {}
    for f in sorted((ROOT / "senior" / "drafts").glob(f"*-{ch}*/upload_result.json")):
        script = f.parent / "script.json"
        mood = json.loads(script.read_text(encoding="utf-8")).get("mood", "alert") if script.exists() else "alert"
        mine[json.loads(f.read_text(encoding="utf-8"))["video_id"]] = {"folder": f.parent.name, "genre": GENRE.get(mood, mood)}
    rows = [{**mine[v["id"]], **{k: v[k] for k in ("title", "published", "views", "likes", "comments", "views_per_hour")}}
            for v in details(list(mine), headers, now)]
    out = ROOT / "senior" / "research" / "stats" / f"{now:%Y-%m-%d}-{ch}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generated": now.isoformat(timespec="minutes"), "videos": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for r in rows:
        print(r["genre"], r["views"], r["likes"], r["comments"], r["title"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kr")
