"""Read a script line with the channel's ElevenLabs voice (senior/voices.json).

  python el_voice.py kr "아, 아. ..." out.mp3     (needs ELEVENLABS_API_KEY)
  python el_voice.py kr --check                   (prints the voice name the key can see)

The model id in voices.json is tried first; if the API rejects it, eleven_multilingual_v2 is used
and the fallback is printed so the config can be fixed.
"""
import json
import os
import re
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


# Second voice for the scammer in the 참교육 dramas: voices.json "scammer_voice_id", else the first of these
# ElevenLabs premade voices the account has.
SCAMMER_PREFS = ["Callum", "Clyde", "Liam", "Harry", "Adam", "Josh"]
_scammer = None


def scammer_voice(channel):
    global _scammer
    c = json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel]
    if c.get("scammer_voice_id"):
        return c["scammer_voice_id"]
    if _scammer is None:
        r = requests.get(f"{API}/voices", headers=headers(), timeout=30)
        voices = r.json().get("voices", []) if r.ok else []
        by_name = {v["name"].split(" ")[0]: v["voice_id"] for v in voices if v.get("category") == "premade"}
        _scammer = next((by_name[n] for n in SCAMMER_PREFS if n in by_name), None)
        if not _scammer:
            sys.exit("no premade voice for the scammer")
        print("scammer voice", next(n for n in SCAMMER_PREFS if n in by_name))
    return _scammer


def speak_timed(channel, text, out, role="host", delivery=""):
    """Like speak(), but also returns word timings [(word, start_sec, end_sec)] from ElevenLabs' alignment.
    role "scammer" reads with the second voice. delivery is an acting tag like "[sarcastic]": the v3/v4 models
    act it out (and it is cut from the timings); older models would read it aloud, so they never get it."""
    import base64
    c = cfg(channel) if role == "host" else {**json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel],
                                             "voice_id": scammer_voice(channel), "speed": 1.05}
    tag = delivery.strip() if delivery.strip().startswith("[") and delivery.strip().endswith("]") else ""
    for model in (c["model_id"], FALLBACK_MODEL):
        acted = tag and re.match(r"eleven_v[3-9]", model)
        # owner 10-26: the first drafts sounded flat, so the expressive models run at the "creative" end
        for settings in ({"speed": c.get("speed", 1.0), "stability": 0.0 if role == "scammer" else 0.5},
                         {"speed": c.get("speed", 1.0)}):
            r = requests.post(f"{API}/text-to-speech/{c['voice_id']}/with-timestamps", headers=headers(), timeout=120,
                              params={"output_format": "mp3_44100_128"},
                              json={"text": f"{tag} {text}" if acted else text, "model_id": model,
                                    "voice_settings": settings})
            if r.status_code != 422 and r.status_code != 400:
                break
            print("settings", settings, "->", r.status_code, r.text[:200])
        if r.status_code == 200:
            data = r.json()
            Path(out).write_bytes(base64.b64decode(data["audio_base64"]))
            a = data.get("alignment") or data.get("normalized_alignment") or {}
            words, cur, start, end, depth = [], "", None, None, 0
            for ch, s, e in zip(a.get("characters", []), a.get("character_start_times_seconds", []),
                                a.get("character_end_times_seconds", [])):
                if ch in "[]":
                    depth += 1 if ch == "[" else -1
                    continue
                if depth > 0:
                    continue
                if ch.isspace():
                    if cur:
                        words.append((cur, start, end))
                    cur, start = "", None
                    continue
                if start is None:
                    start = s
                cur, end = cur + ch, e
            if cur:
                words.append((cur, start, end))
            print("ok", channel, model, out, len(words), "words", tag if acted else "")
            return words
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
