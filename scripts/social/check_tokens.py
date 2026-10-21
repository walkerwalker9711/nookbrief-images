"""Weekly check that the Instagram and Threads tokens still work.

Exits non-zero when a token is rejected, so the run fails and GitHub emails the owner.
(Tokens last 60 days; a new token has to be pasted into the repo secrets before then.)
"""
import sys

from common import IG, TH, call, env


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
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
