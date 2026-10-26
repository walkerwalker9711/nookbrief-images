"""Voice samples for 한국이장님 and Pops Knows from Google Cloud Text-to-Speech (free tier).

  python tts_sample.py      (needs GOOGLE_TTS_KEY; writes senior/samples/<voice>.mp3)

Each candidate voice reads the first line of week 1, episode 1 so the owner can pick one by ear.
A voice this key or region can't use is skipped, not fatal.
"""
import base64
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
LINES = {
    "ko-KR": "아, 아. 과태료 미납 문자 받으신 분, 누르지 마세요. 그거 사기입니다. 진짜 벌금이 있는지는 이파인에 직접 들어가 보세요.",
    "en-US": "Four bucks and a deadline? Nice try, pal. Toll agencies don't text you a weird link over four dollars. Pops knows.",
}
VOICES = {
    "ko-KR": ["ko-KR-Chirp3-HD-Charon", "ko-KR-Chirp3-HD-Fenrir", "ko-KR-Chirp3-HD-Orus",
              "ko-KR-Neural2-C", "ko-KR-Wavenet-D"],
    "en-US": ["en-US-Chirp3-HD-Charon", "en-US-Chirp3-HD-Orus", "en-US-Chirp3-HD-Algenib",
              "en-US-Neural2-J", "en-US-Wavenet-B"],
}


def main():
    key = os.environ.get("GOOGLE_TTS_KEY", "").strip()
    if not key:
        sys.exit("GOOGLE_TTS_KEY is not set")
    out = ROOT / "senior" / "samples"
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for lang, names in VOICES.items():
        for name in names:
            audio = {"audioEncoding": "MP3"}
            if "Chirp" not in name:  # Chirp HD voices take no pitch/rate tuning
                audio.update(speakingRate=0.92, pitch=-2.0)
            r = requests.post(URL, params={"key": key}, timeout=60, json={
                "input": {"text": LINES[lang]}, "voice": {"languageCode": lang, "name": name}, "audioConfig": audio})
            if r.status_code != 200:
                print("skip", name, r.status_code, r.text[:200])
                continue
            (out / f"{name}.mp3").write_bytes(base64.b64decode(r.json()["audioContent"]))
            print("ok", name)
            made += 1
    if not made:
        sys.exit("no voice worked; check the key and that Cloud Text-to-Speech API is enabled")


if __name__ == "__main__":
    main()
