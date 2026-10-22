"""One successful call per Instagram permission, so Meta's "Use case testing" page counts it.

Meta wants each permission used at least once before the app can be sent to review.
Prints what each call returned and never fails the run.
"""
from common import IG, call, env


def main():
    tok = env("IG_TOKEN")
    if not tok:
        print("IG_TOKEN not set")
        return
    p = {"access_token": tok}
    checks = [
        ("instagram_business_basic", f"{IG}/me", {"fields": "user_id,username,media_count"}),
        ("instagram_business_basic (media)", f"{IG}/me/media", {"fields": "id,comments_count", "limit": 5}),
        ("instagram_business_manage_messages", f"{IG}/me/conversations", {"platform": "instagram"}),
    ]
    media = []
    for perm, url, params in checks:
        try:
            r = call("GET", url, params={**params, **p})
            if perm.endswith("(media)"):
                media = r.get("data", [])
            print(perm, "ok:", str(r)[:200])
        except RuntimeError as e:
            print(perm, "FAILED:", e)
    for m in media[:3]:
        try:
            r = call("GET", f"{IG}/{m['id']}/comments", params={"fields": "id,text,username", **p})
            print("instagram_business_manage_comments ok on", m["id"], "count", m.get("comments_count"), "listed", len(r.get("data", [])))
        except RuntimeError as e:
            print("instagram_business_manage_comments FAILED:", e)


if __name__ == "__main__":
    main()
