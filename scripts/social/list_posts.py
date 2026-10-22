"""Read-only: list our latest Instagram and Threads posts (id, time, first words), to check what is live.

Run by the social-list workflow (manual). Prints no tokens."""
from common import IG, TH, call, env


def show(title, rows):
    print(f"== {title}")
    for r in rows:
        text = (r.get("caption") or r.get("text") or "").replace("\n", " ")[:70]
        print(r["id"], r.get("timestamp"), r.get("media_type"), "|", text)


def main():
    tok = env("IG_TOKEN")
    if tok:
        show("instagram", call("GET", f"{IG}/me/media", params={
            "fields": "id,timestamp,media_type,caption", "limit": 15, "access_token": tok}).get("data", []))
    tok = env("THREADS_TOKEN")
    if tok:
        show("threads posts", call("GET", f"{TH}/me/threads", params={
            "fields": "id,timestamp,media_type,text", "limit": 15, "access_token": tok}).get("data", []))
        show("threads replies", call("GET", f"{TH}/me/replies", params={
            "fields": "id,timestamp,media_type,text", "limit": 15, "access_token": tok}).get("data", []))


if __name__ == "__main__":
    main()
