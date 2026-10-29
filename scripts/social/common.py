"""Shared helpers for the NookBrief social publishing scripts (run in GitHub Actions)."""
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "social" / "queue"
STATE = ROOT / "social" / "state"
REPO = os.environ.get("GITHUB_REPOSITORY", "walkerwalker9711/nookbrief-images")

IG = "https://graph.instagram.com/v23.0"
TH = "https://graph.threads.net/v1.0"
PIN = "https://api.pinterest.com/v5"
YT = "https://www.googleapis.com"


def cdn(path, sha=None):
    """Public jsDelivr URL for a repo file, pinned to a commit so Meta/Pinterest can fetch it."""
    sha = sha or os.environ.get("GITHUB_SHA", "main")
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{sha}/{path}"


def utm(url, source, medium, campaign):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"


def load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def call(method, url, **kw):
    r = requests.request(method, url, timeout=120, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {r.status_code}: {r.text[:500]}")
    return r.json() if r.content else {}


def wait_until(check, done, failed=(), tries=40, delay=15):
    """Poll check() until its value is in done; raise if it lands in failed or never finishes."""
    for _ in range(tries):
        status = check()
        if status in done:
            return status
        if status in failed:
            raise RuntimeError(f"processing failed: {status}")
        time.sleep(delay)
    raise RuntimeError("processing timed out")


def env(name):
    v = os.environ.get(name, "").strip()
    return v or None


def google_token():
    """Access token for YouTube from the YT_* refresh token secrets, or None when they are not set."""
    cid, secret, refresh = env("YT_CLIENT_ID"), env("YT_CLIENT_SECRET"), env("YT_REFRESH_TOKEN")
    if not (cid and secret and refresh):
        return None
    return call("POST", "https://oauth2.googleapis.com/token", data={
        "client_id": cid, "client_secret": secret, "refresh_token": refresh, "grant_type": "refresh_token"})["access_token"]
