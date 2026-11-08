"""Study a Short the owner points at (owner 10-28: "can we automate this kind of drama?").

  python video_study.py VIDEO_ID     (needs YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN; OPENAI_API_KEY optional)
Writes senior/research/videos/<id>/: info.json (title, description, channel, stats, length), thumb.jpg, and when
the video can be downloaded, frames.jpg (one frame every 2 seconds) and transcript.txt.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "social"))
from common import YT, google_token  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main(vid):
    out = ROOT / "senior" / "research" / "videos" / vid
    out.mkdir(parents=True, exist_ok=True)
    auth = {"Authorization": f"Bearer {google_token('YT_REFRESH_TOKEN')}"}
    v = requests.get(f"{YT}/youtube/v3/videos", headers=auth, timeout=60,
                     params={"part": "snippet,statistics,contentDetails", "id": vid}).json()["items"][0]
    ch = requests.get(f"{YT}/youtube/v3/channels", headers=auth, timeout=60,
                      params={"part": "snippet,statistics", "id": v["snippet"]["channelId"]}).json()["items"][0]
    info = {"title": v["snippet"]["title"], "description": v["snippet"]["description"], "tags": v["snippet"].get("tags", []),
            "published": v["snippet"]["publishedAt"], "duration": v["contentDetails"]["duration"], "stats": v["statistics"],
            "channel": ch["snippet"]["title"], "channel_description": ch["snippet"]["description"],
            "channel_stats": ch["statistics"]}
    thumbs = v["snippet"]["thumbnails"]
    best = (thumbs.get("maxres") or thumbs.get("high") or thumbs["default"])["url"]
    (out / "thumb.jpg").write_bytes(requests.get(best, timeout=60).content)
    # the picture and sound, if YouTube lets a server download it
    mp4 = out / "video.mp4"
    r = subprocess.run(["yt-dlp", "-f", "mp4/best", "-o", str(mp4), f"https://www.youtube.com/shorts/{vid}"],
                       capture_output=True, text=True)
    info["download"] = "ok" if mp4.exists() else r.stderr[-400:]
    if mp4.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vf", "fps=1/2,scale=216:-1,tile=8x4",
                        "-frames:v", "1", str(out / "frames.jpg")], check=False)
        if os.environ.get("OPENAI_API_KEY"):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vn", "-ac", "1", "-b:a", "48k",
                            str(out / "audio.mp3")], check=False)
            t = requests.post("https://api.openai.com/v1/audio/transcriptions", timeout=300,
                              headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                              files={"file": open(out / "audio.mp3", "rb")},
                              data={"model": "whisper-1", "response_format": "verbose_json"})
            if t.ok:
                (out / "transcript.txt").write_text("\n".join(f"[{s['start']:.1f}] {s['text'].strip()}"
                                                              for s in t.json().get("segments", [])), encoding="utf-8")
            (out / "audio.mp3").unlink(missing_ok=True)
        mp4.unlink()
    (out / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: info[k] for k in ("title", "channel", "duration", "download")}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
