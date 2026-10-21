"""Publish approved NookBrief short videos to Pinterest, Instagram Reels and Threads.

Reads social/queue/<topic>.json. A topic is published only when "approved" is true.
Each channel runs once per topic; results go to social/state/<topic>.json, so re-runs skip
what is already live. A channel whose secrets are missing is skipped, not failed.
"""
import sys
import time

import requests

from common import IG, PIN, QUEUE, ROOT, STATE, TH, call, cdn, env, load, save, utm, wait_until


def pinterest(item, st):
    app_id, secret, refresh = env("PINTEREST_APP_ID"), env("PINTEREST_APP_SECRET"), env("PINTEREST_REFRESH_TOKEN")
    if app_id and secret and refresh:
        tok = call("POST", f"{PIN}/oauth/token", auth=(app_id, secret),
                   data={"grant_type": "refresh_token", "refresh_token": refresh})["access_token"]
    else:
        tok = env("PINTEREST_ACCESS_TOKEN")  # token generated on the app page
    if not tok:
        return "skipped: Pinterest secrets not set"
    h = {"Authorization": f"Bearer {tok}"}
    p = item["pinterest"]
    boards = call("GET", f"{PIN}/boards", headers=h, params={"page_size": 100})["items"]
    board = next((b["id"] for b in boards if b["name"] == p["board"]), None)
    if not board:
        raise RuntimeError(f"Pinterest board not found: {p['board']}")
    media = call("POST", f"{PIN}/media", headers=h, json={"media_type": "video"})
    with open(item["_video_path"]["link"], "rb") as f:
        r = requests.post(media["upload_url"], data=media["upload_parameters"], files={"file": f}, timeout=300)
    if r.status_code >= 300:
        raise RuntimeError(f"Pinterest upload -> {r.status_code}: {r.text[:300]}")
    wait_until(lambda: call("GET", f"{PIN}/media/{media['media_id']}", headers=h)["status"],
               {"succeeded"}, {"failed"})
    pin = call("POST", f"{PIN}/pins", headers=h, json={
        "board_id": board,
        "title": p["title"][:100],
        "description": p["description"][:500],
        "link": utm(item["post_url"], "pinterest", "video", item["topic"]),
        "media_source": {"source_type": "video_id", "media_id": media["media_id"],
                         "cover_image_url": cdn(item["video"]["link"].replace(".mp4", "-cover.jpg"))},
    })
    return {"pin_id": pin["id"]}


def instagram(item, st):
    tok = env("IG_TOKEN")
    if not tok:
        return "skipped: IG_TOKEN not set"
    me = call("GET", f"{IG}/me", params={"fields": "user_id", "access_token": tok})["user_id"]
    c = call("POST", f"{IG}/{me}/media", data={
        "media_type": "REELS", "video_url": cdn(item["video"]["ig"]),
        "caption": item["instagram"]["caption"], "share_to_feed": "true", "access_token": tok})["id"]
    wait_until(lambda: call("GET", f"{IG}/{c}", params={"fields": "status_code", "access_token": tok})["status_code"],
               {"FINISHED"}, {"ERROR", "EXPIRED"})
    media = call("POST", f"{IG}/{me}/media_publish", data={"creation_id": c, "access_token": tok})["id"]
    return {"media_id": media, "published_at": int(time.time())}


def threads(item, st):
    tok = env("THREADS_TOKEN")
    if not tok:
        return "skipped: THREADS_TOKEN not set"
    me = call("GET", f"{TH}/me", params={"fields": "id", "access_token": tok})["id"]
    text = item["threads"]["text"].replace("{link}", utm(item["post_url"], "threads", "video", item["topic"]))
    c = call("POST", f"{TH}/{me}/threads", data={
        "media_type": "VIDEO", "video_url": cdn(item["video"]["link"]), "text": text, "access_token": tok})["id"]
    wait_until(lambda: call("GET", f"{TH}/{c}", params={"fields": "status", "access_token": tok})["status"],
               {"FINISHED"}, {"ERROR", "EXPIRED"})
    post = call("POST", f"{TH}/{me}/threads_publish", data={"creation_id": c, "access_token": tok})["id"]
    return {"post_id": post}


CHANNELS = {"pinterest": pinterest, "instagram": instagram, "threads": threads}


def main(only=None):
    failed = False
    for qf in sorted(QUEUE.glob("*.json")):
        item = load(qf)
        if not item.get("approved") or (only and item["topic"] != only):
            continue
        sf = STATE / qf.name
        st = load(sf, {})
        item["_video_path"] = {k: str(ROOT / v) for k, v in item["video"].items()}
        for name, fn in CHANNELS.items():
            if name not in item or isinstance(st.get(name), dict):
                continue
            try:
                st[name] = fn(item, st)
            except Exception as e:  # keep going with the other channels
                st[name + "_error"] = str(e)
                failed = True
            else:
                st.pop(name + "_error", None)
            print(qf.stem, name, st.get(name), st.get(name + "_error", ""))
            save(sf, st)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
