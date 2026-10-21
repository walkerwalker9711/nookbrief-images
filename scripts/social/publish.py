"""Publish approved NookBrief short videos to Pinterest, Instagram Reels, Threads and YouTube Shorts.

Reads social/queue/<topic>.json. A topic is published only when "approved" is true.
Each channel runs once per topic; results go to social/state/<topic>.json, so re-runs skip
what is already live. A channel whose secrets are missing is skipped, not failed.
"""
import os
import sys
import time

import requests

from common import IG, PIN, QUEUE, ROOT, STATE, TH, YT, call, cdn, env, google_token, load, save, utm, wait_until


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


def brand_tag(caption, tag="#NookBrief", limit=5):
    """Every Instagram caption carries #NookBrief; keep the total at five hashtags by dropping the last other one."""
    if tag.lower() in caption.lower():
        return caption
    lines = caption.rstrip().split("\n")
    last = lines[-1].split()
    if last and all(w.startswith("#") for w in last):
        tags = [tag] + last
        others = [t for t in tags if t != tag]
        while len(tags) > limit and others:
            tags.remove(others.pop())
        lines[-1] = " ".join(tags)
    else:
        lines.append(tag)
    return "\n".join(lines)


def instagram(item, st):
    tok = env("IG_TOKEN")
    if not tok:
        return "skipped: IG_TOKEN not set"
    me = call("GET", f"{IG}/me", params={"fields": "user_id", "access_token": tok})["user_id"]
    c = call("POST", f"{IG}/{me}/media", data={
        "media_type": "REELS", "video_url": cdn(item["video"]["ig"]),
        "caption": brand_tag(item["instagram"]["caption"]), "share_to_feed": "true", "access_token": tok})["id"]
    try:
        wait_until(lambda: call("GET", f"{IG}/{c}", params={"fields": "status_code", "access_token": tok})["status_code"],
                   {"FINISHED"}, {"ERROR", "EXPIRED"})
    except RuntimeError as e:  # "status" carries Meta's reason, e.g. a video it could not fetch or decode
        why = call("GET", f"{IG}/{c}", params={"fields": "status", "access_token": tok}).get("status")
        raise RuntimeError(f"{e} ({why})") from None
    media = call("POST", f"{IG}/{me}/media_publish", data={"creation_id": c, "access_token": tok})["id"]
    return {"media_id": media, "published_at": int(time.time())}


def th_publish(tok, me, data):
    c = call("POST", f"{TH}/{me}/threads", data={**data, "access_token": tok})["id"]
    try:
        wait_until(lambda: call("GET", f"{TH}/{c}", params={"fields": "status", "access_token": tok})["status"],
                   {"FINISHED"}, {"ERROR", "EXPIRED"})
    except RuntimeError as e:
        why = call("GET", f"{TH}/{c}", params={"fields": "error_message", "access_token": tok}).get("error_message")
        raise RuntimeError(f"{e} ({why})") from None
    return call("POST", f"{TH}/{me}/threads_publish", data={"creation_id": c, "access_token": tok})["id"]


def threads(item, st):
    tok = env("THREADS_TOKEN")
    if not tok:
        return "skipped: THREADS_TOKEN not set"
    me = call("GET", f"{TH}/me", params={"fields": "id", "access_token": tok})["id"]
    link = utm(item["post_url"], "threads", "video", item["topic"])
    th = item["threads"]
    # Main post carries the video and a conversational hook; the link goes in our own first reply,
    # since posts with outbound links tend to get less reach on Threads.
    post = st.get("threads_post") or th_publish(tok, me, {"media_type": "VIDEO", "video_url": cdn(item["video"]["link"]),
                                                          "text": th["text"].replace("{link}", link)})
    st["threads_post"] = post
    if not th.get("reply"):
        return {"post_id": post}
    reply = th_publish(tok, me, {"media_type": "TEXT", "text": th["reply"].replace("{link}", link), "reply_to_id": post})
    return {"post_id": post, "reply_id": reply}


def threads_more(item, st):
    """One extra reply of ours under an already published Threads post (e.g. a link added later)."""
    tok = env("THREADS_TOKEN")
    if not tok:
        return "skipped: THREADS_TOKEN not set"
    if not st.get("threads_post"):
        return "skipped: Threads post not published yet"
    me = call("GET", f"{TH}/me", params={"fields": "id", "access_token": tok})["id"]
    link = utm(item["post_url"], "threads", "video", item["topic"])
    text = item["threads_more"]["text"].replace("{link}", link)
    return {"reply_id": th_publish(tok, me, {"media_type": "TEXT", "text": text, "reply_to_id": st["threads_post"]})}


def youtube(item, st):
    tok = google_token()
    if not tok:
        return "skipped: YouTube secrets not set"
    y = item["youtube"]
    meta = {
        "snippet": {"title": y["title"][:100], "description": y["description"][:5000],
                    "tags": y.get("tags", []), "categoryId": y.get("category", "26")},  # 26 = Howto & Style
        # Photo-like AI stills count as realistic synthetic media, so YouTube wants the label on.
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    path = item["_video_path"].get("yt") or item["_video_path"]["link"]
    size = os.path.getsize(path)
    r = requests.post(f"{YT}/upload/youtube/v3/videos", params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={"Authorization": f"Bearer {tok}", "X-Upload-Content-Type": "video/mp4",
                               "X-Upload-Content-Length": str(size)}, json=meta, timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"YouTube upload start -> {r.status_code}: {r.text[:300]}")
    with open(path, "rb") as f:
        up = requests.put(r.headers["Location"], data=f, headers={"Content-Type": "video/mp4"}, timeout=600)
    if up.status_code >= 300:
        raise RuntimeError(f"YouTube upload -> {up.status_code}: {up.text[:300]}")
    v = up.json()
    # Uploads from an API project that has not passed YouTube's audit are locked to private.
    return {"video_id": v["id"], "privacy": v.get("status", {}).get("privacyStatus")}


CHANNELS = {"pinterest": pinterest, "instagram": instagram, "threads": threads, "threads_more": threads_more,
            "youtube": youtube}


def main(only=None):
    failed = False
    for qf in sorted(QUEUE.glob("*.json")):
        item = load(qf)
        if not item.get("approved") or (only and item["topic"] != only):
            continue
        sf = STATE / qf.name
        st = load(sf, {})
        item["_video_path"] = {k: str(ROOT / v) for k, v in item["video"].items()}
        for k, v in item["video"].items():  # what Meta/Pinterest will see when they fetch the video (info only)
            try:
                r = requests.head(cdn(v), allow_redirects=True, timeout=30)
                print(qf.stem, "video", k, r.status_code, r.headers.get("content-type"), r.headers.get("content-length"))
            except requests.RequestException as e:
                print(qf.stem, "video", k, "HEAD failed:", e)
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
