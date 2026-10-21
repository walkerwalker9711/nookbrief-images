"""Send the guide link by DM to people who comment the keyword on a NookBrief Reel.

Uses Instagram Private Replies: one DM per comment, within 7 days of the comment.
Already-answered comment ids are kept in social/state/dm_sent.json for 90 days (as the privacy policy says).
"""
import calendar
import re
import sys
import time

from common import IG, QUEUE, STATE, call, env, load, save, utm

WINDOW = 7 * 24 * 3600 - 3600  # stay inside Meta's 7-day limit
WATCH = 30 * 24 * 3600  # how long after publishing a Reel we keep checking its comments
KEEP = 90 * 24 * 3600  # privacy policy: answered comment ids are deleted after 90 days


def main():
    tok = env("IG_TOKEN")
    if not tok:
        print("skipped: IG_TOKEN not set")
        return 0
    me = call("GET", f"{IG}/me", params={"fields": "user_id", "access_token": tok})["user_id"]
    sent_file = STATE / "dm_sent.json"
    sent = load(sent_file, {})
    now = time.time()
    count = 0
    for qf in QUEUE.glob("*.json"):
        item = load(qf)
        media = (load(STATE / qf.name, {}).get("instagram") or {})
        if not isinstance(media, dict) or now - media.get("published_at", 0) > WATCH:
            continue
        ig = item["instagram"]
        words = [w.lower() for w in ig.get("keywords", ["GUIDE", "LINK"])]
        pattern = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.I)
        link = utm(item["post_url"], "instagram", "dm", item["topic"])
        text = ig["dm"].replace("{link}", link)
        comments = call("GET", f"{IG}/{media['media_id']}/comments",
                        params={"fields": "id,text,timestamp", "limit": 50, "access_token": tok}).get("data", [])
        for c in comments:
            if c["id"] in sent or not pattern.search(c.get("text", "")):
                continue
            ts = calendar.timegm(time.strptime(c["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
            if now - ts > WINDOW:
                continue
            try:
                call("POST", f"{IG}/{me}/messages", json={"recipient": {"comment_id": c["id"]},
                     "message": {"text": text}}, params={"access_token": tok})
                if ig.get("public_reply"):
                    call("POST", f"{IG}/{c['id']}/replies", data={"message": ig["public_reply"], "access_token": tok})
                sent[c["id"]] = {"topic": item["topic"], "at": int(now)}
                count += 1
            except RuntimeError as e:
                print("dm failed", c["id"], e)
    sent = {k: v for k, v in sent.items() if now - v.get("at", now) < KEEP}
    save(sent_file, sent)
    print("DMs sent:", count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
