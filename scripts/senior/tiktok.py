"""한국이장님 TikTok: one-time login, then send approved drafts to the owner's TikTok inbox (owner posts in the app).

  python tiktok.py link              writes senior/tiktok/login_link.txt (needs TIKTOK_CLIENT_KEY)
  python tiktok.py connect CODE      trades the code from callback.html for tokens, saved encrypted in token.enc
  python tiktok.py upload FOLDER     sends FOLDER/video.mp4 to the inbox as a draft, writes tiktok_result.json

The refresh token lives in senior/tiktok/token.enc, encrypted with TIKTOK_CLIENT_SECRET, so the workflow can rotate
it without write access to repository secrets. Inbox uploads cannot set the AI label: the owner turns it on in the app.
"""
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "senior" / "tiktok"
TOKEN = DIR / "token.enc"
API = "https://open.tiktokapis.com/v2"
REDIRECT = "https://walkerwalker9711.github.io/nookbrief-images/callback.html"
SCOPES = "user.info.basic,video.upload"


def env(name):
    v = (os.environ.get(name) or "").strip()  # pasted secrets can carry a stray newline
    if not v:
        sys.exit(f"{name} is not set")
    return v


def crypt(data, decrypt=False):
    args = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-a", "-A", "-pass", "pass:" + env("TIKTOK_CLIENT_SECRET")]
    return subprocess.run(args + (["-d"] if decrypt else []), input=data, capture_output=True, check=True).stdout


def save(tok):
    keep = {k: tok[k] for k in ("refresh_token", "open_id", "scope") if k in tok}
    keep["saved"] = int(time.time())
    TOKEN.write_bytes(crypt(json.dumps(keep).encode()) + b"\n")


def oauth(**data):
    r = requests.post(f"{API}/oauth/token/", timeout=60, data={"client_key": env("TIKTOK_CLIENT_KEY"),
                      "client_secret": env("TIKTOK_CLIENT_SECRET"), **data})
    tok = r.json()
    if "access_token" not in tok:
        sys.exit(f"oauth -> {r.status_code}: {tok.get('error')} {tok.get('error_description')}")
    return tok


def link():
    q = urlencode({"client_key": env("TIKTOK_CLIENT_KEY"), "scope": SCOPES, "response_type": "code",
                   "redirect_uri": REDIRECT, "state": secrets.token_hex(8)})
    (DIR / "login_link.txt").write_text(f"https://www.tiktok.com/v2/auth/authorize/?{q}\n")
    print("login link written")


def connect(code):
    tok = oauth(code=code, grant_type="authorization_code", redirect_uri=REDIRECT)
    save(tok)
    print("connected, scope:", tok.get("scope"))


def access():
    old = json.loads(crypt(TOKEN.read_bytes().strip(), decrypt=True))
    tok = oauth(grant_type="refresh_token", refresh_token=old["refresh_token"])
    save({**old, **tok})  # TikTok may hand back a new refresh token: keep whichever is newest
    return tok["access_token"]


def upload(folder):
    d = ROOT / folder
    done = d / "tiktok_result.json"
    if done.exists() and json.loads(done.read_text()).get("publish_id"):
        print("already sent to the inbox:", done.read_text())
        return
    video = d / "video.mp4"
    size = video.stat().st_size
    auth = {"Authorization": f"Bearer {access()}"}
    r = requests.post(f"{API}/post/publish/inbox/video/init/", headers=auth, timeout=60, json={"source_info": {
        "source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
    body = r.json()
    if body.get("error", {}).get("code") != "ok":
        sys.exit(f"init -> {r.status_code}: {body.get('error')}")
    data = body["data"]
    up = requests.put(data["upload_url"], data=video.read_bytes(), timeout=900, headers={
        "Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"})
    if up.status_code >= 300:
        sys.exit(f"upload -> {up.status_code}: {up.text[:300]}")
    status = {}
    for _ in range(20):  # wait until TikTok has the file in the owner's inbox
        time.sleep(6)
        s = requests.post(f"{API}/post/publish/status/fetch/", headers=auth, timeout=60,
                          json={"publish_id": data["publish_id"]}).json()
        status = s.get("data", {})
        if status.get("status") in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"):
            break
    result = {"publish_id": data["publish_id"], "status": status.get("status"), "fail_reason": status.get("fail_reason")}
    done.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result))
    if result["status"] == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    {"link": link, "connect": connect, "upload": upload}[cmd](*rest)
