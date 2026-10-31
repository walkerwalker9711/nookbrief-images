"""Upload an approved senior Shorts draft to its channel (owner approves each one in the thread).

  python upload.py senior/drafts/2026-10-26-kr      (needs YT_CLIENT_ID, YT_CLIENT_SECRET, KR_/US_YT_REFRESH_TOKEN)

Reads upload.json in the draft folder, uploads video.mp4 public with the AI label on, sets thumb.jpg when the
channel is allowed custom thumbnails, and writes upload_result.json next to it. An uploaded draft is never sent twice:
running it again only updates the title, description and tags (and retries the thumbnail).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from common import YT, google_token  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TOKENS = {"kr": "KR_YT_REFRESH_TOKEN", "us": "US_YT_REFRESH_TOKEN"}


def with_cover(video, thumb):
    """Shorts shelves show a frame of the video, not the custom thumbnail (owner 10-28), and the app's thumbnail
    picker only offers frames. So the thumbnail goes in as the first 0.1 s; the owner picks the first frame."""
    if not thumb.exists() or not shutil.which("ffmpeg"):
        return video
    out = video.with_name("video_cover.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", "0.1", "-framerate", "30", "-i", str(thumb), "-i", str(video),
           "-f", "lavfi", "-t", "0.1", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
           "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[c];"
           "[1:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[m];[1:a]aresample=48000[ma];"
           "[c][2:a][m][ma]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow",
           "-crf", "24", "-maxrate", "3500k", "-bufsize", "7000k", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    if subprocess.run(cmd).returncode != 0:
        print("cover frame not added; uploading the video as it is")
        return video
    return out


def main(folder):
    d = ROOT / folder
    meta = json.loads((d / "upload.json").read_text(encoding="utf-8"))
    done = d / "upload_result.json"
    tok = google_token(TOKENS[meta["channel"]])
    if not tok:
        sys.exit(f"{TOKENS[meta['channel']]} is not set")
    snippet = {"title": meta["title"][:100], "description": meta["description"][:5000], "tags": meta.get("tags", []),
               "categoryId": meta.get("category", "25"), "defaultLanguage": "ko" if meta["channel"] == "kr" else "en"}
    prev = json.loads(done.read_text(encoding="utf-8")) if done.exists() else {}
    if prev.get("video_id"):  # already up: never upload twice, only bring title, description and tags up to date
        r = requests.put(f"{YT}/youtube/v3/videos", params={"part": "snippet"}, timeout=60,
                         headers={"Authorization": f"Bearer {tok}"}, json={"id": prev["video_id"], "snippet": snippet})
        if r.status_code >= 300:
            sys.exit(f"update -> {r.status_code}: {r.text[:300]}")
        prev["title"] = r.json()["snippet"]["title"]
        thumb = d / meta.get("thumbnail", "thumb.jpg")
        if thumb.exists() and prev.get("thumbnail") != "set":
            t = requests.post(f"{YT}/upload/youtube/v3/thumbnails/set", params={"videoId": prev["video_id"]},
                              headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"},
                              data=thumb.read_bytes(), timeout=120)
            prev["thumbnail"] = "set" if t.status_code < 300 else f"failed {t.status_code}: {t.text[:200]}"
        done.write_text(json.dumps(prev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("updated", json.dumps(prev, ensure_ascii=False))
        return
    body = {
        "snippet": snippet,
        "status": {"privacyStatus": meta.get("privacy", "public"), "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": bool(meta.get("made_with_ai", True))},
    }
    video = with_cover(d / meta.get("video", "video.mp4"), d / meta.get("thumbnail", "thumb.jpg"))
    r = requests.post(f"{YT}/upload/youtube/v3/videos", params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={"Authorization": f"Bearer {tok}", "X-Upload-Content-Type": "video/mp4",
                               "X-Upload-Content-Length": str(video.stat().st_size)}, json=body, timeout=60)
    if r.status_code >= 300:
        sys.exit(f"upload start -> {r.status_code}: {r.text[:300]}")
    with open(video, "rb") as f:
        up = requests.put(r.headers["Location"], data=f, headers={"Content-Type": "video/mp4"}, timeout=900)
    if up.status_code >= 300:
        sys.exit(f"upload -> {up.status_code}: {up.text[:300]}")
    v = up.json()
    out = {"video_id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}", "privacy": v.get("status", {}).get("privacyStatus")}
    thumb = d / meta.get("thumbnail", "thumb.jpg")
    if thumb.exists():  # custom thumbnails need a phone-verified channel; a refusal is noted, the upload stands
        t = requests.post(f"{YT}/upload/youtube/v3/thumbnails/set", params={"videoId": v["id"]},
                          headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"},
                          data=thumb.read_bytes(), timeout=120)
        out["thumbnail"] = "set" if t.status_code < 300 else f"failed {t.status_code}: {t.text[:200]}"
    done.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    for folder in sys.argv[1:]:
        main(folder)
