"""Read a script line with the channel's ElevenLabs voice (senior/voices.json).

  python el_voice.py kr "아, 아. ..." out.mp3     (needs ELEVENLABS_API_KEY)
  python el_voice.py kr --check                   (prints the voice name the key can see)

The model id in voices.json is tried first; if the API rejects it, eleven_multilingual_v2 is used
and the fallback is printed so the config can be fixed.
"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.elevenlabs.io/v1"
FALLBACK_MODEL = "eleven_multilingual_v2"


def cfg(channel):
    c = json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel]
    if not c.get("voice_id"):
        sys.exit(f"no voice chosen for {channel} yet")
    return c


def headers():
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    return {"xi-api-key": key}


def speak(channel, text, out):
    c = cfg(channel)
    for model in (c["model_id"], FALLBACK_MODEL):
        r = requests.post(f"{API}/text-to-speech/{c['voice_id']}", headers=headers(), timeout=120,
                          params={"output_format": "mp3_44100_128"},
                          json={"text": text, "model_id": model,
                                "voice_settings": {"speed": c.get("speed", 1.0)}})
        if r.status_code == 200:
            Path(out).write_bytes(r.content)
            print("ok", channel, model, out, len(r.content), "bytes")
            return
        print("model", model, "->", r.status_code, r.text[:300])
    sys.exit("ElevenLabs refused every model")


def check(channel):
    c = cfg(channel)
    r = requests.get(f"{API}/voices/{c['voice_id']}", headers=headers(), timeout=30)
    print(r.status_code, r.json().get("name") if r.ok else r.text[:300])
    u = requests.get(f"{API}/user/subscription", headers=headers(), timeout=30)
    if u.ok:
        s = u.json()
        print("tier", s.get("tier"), "chars", s.get("character_count"), "/", s.get("character_limit"))
    if not r.ok:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[2] == "--check":
        check(sys.argv[1])
    elif len(sys.argv) == 4:
        speak(*sys.argv[1:])
    else:
        sys.exit(__doc__)
