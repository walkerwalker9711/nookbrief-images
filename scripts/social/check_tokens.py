"""Weekly check that the Instagram, Threads and YouTube tokens still work.

Exits non-zero when a token is rejected, so the run fails and GitHub emails the owner.
(Tokens last 60 days; a new token has to be pasted into the repo secrets before then.)
"""
import sys

from common import IG, TH, YT, call, env, google_token


def main():
    bad = False
    for name, url, fields in (("IG_TOKEN", f"{IG}/me", "user_id,username"), ("THREADS_TOKEN", f"{TH}/me", "id,username")):
        tok = env(name)
        if not tok:
            print(name, "not set")
            continue
        try:
            print(name, "ok:", call("GET", url, params={"fields": fields, "access_token": tok}).get("username"))
        except RuntimeError as e:
            print(name, "REJECTED:", e)
            bad = True
    try:
        tok = google_token()
        if not tok:
            print("YT_REFRESH_TOKEN not set")
        else:
            ch = call("GET", f"{YT}/youtube/v3/channels", params={"part": "snippet", "mine": "true"},
                      headers={"Authorization": f"Bearer {tok}"}).get("items", [])
            print("YT_REFRESH_TOKEN ok:", ch[0]["snippet"]["title"] if ch else "no channel on this account yet")
    except RuntimeError as e:
        print("YT_REFRESH_TOKEN REJECTED:", e)
        bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
