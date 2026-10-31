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


# Stand-in host voices (premade, older male) until the owner picks one in voices.json
HOST_PREFS = {"us": ["Bill", "George", "Brian"]}


def premade(names):
    r = requests.get(f"{API}/voices", headers=headers(), timeout=30)
    voices = r.json().get("voices", []) if r.ok else []
    by_name = {v["name"].split(" ")[0]: v["voice_id"] for v in voices if v.get("category") == "premade"}
    return next(((n, by_name[n]) for n in names if n in by_name), (None, None))


def cfg(channel):
    c = json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel]
    if not c.get("voice_id"):
        name, vid = premade(HOST_PREFS.get(channel, []))
        if not vid:
            sys.exit(f"no voice chosen for {channel} yet")
        print("stand-in host voice", name)
        c = {**c, "voice_id": vid}
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


def native_villain(channel):
    """A native-speaker scammer voice from the ElevenLabs voice library (owner 10-26: the English premade voice
    reading Korean sounded soft and foreign). Added to the account once and saved in voices.json."""
    lang = {"kr": "ko", "us": "en"}[channel]
    want = ("intense", "deep", "gruff", "menacing", "dark", "rough", "confident", "serious")
    for age in ("middle_aged", "young", None):
        params = {"page_size": 40, "gender": "male", "language": lang, "sort": "trending"}
        if age:
            params["age"] = age
        r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
        if r.status_code == 400:  # the accepted sort names have changed before; fall back to the default order
            params.pop("sort")
            r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
        if not r.ok:
            print("shared voices ->", r.status_code, r.text[:200])
            return None
        host = cfg(channel)["voice_id"]
        voices = [v for v in r.json().get("voices", []) if v.get("voice_id") != host]
        pick = next((v for v in voices if any(w in (v.get("descriptive", "") + " " + v.get("description", "")).lower()
                                              for w in want)), None)
        if pick:
            break
    else:
        return None
    r = requests.post(f"{API}/voices/add/{pick['public_owner_id']}/{pick['voice_id']}", headers=headers(), timeout=30,
                      json={"new_name": f"{channel} scammer - {pick['name']}"[:60]})
    if not r.ok:
        print("adding voice ->", r.status_code, r.text[:200])
        return None
    vid = r.json().get("voice_id") or pick["voice_id"]
    path = ROOT / "senior" / "voices.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data[channel].update({"scammer_voice_id": vid, "scammer_voice_name": pick["name"],
                          "scammer_chosen": "picked automatically from the voice library, 2026-10-26"})
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("scammer voice (library)", pick["name"], "-", pick.get("descriptive"), pick.get("accent"))
    return vid


def extra_voice(channel, gender="female", old=False):
    """A third voice for a short reenacted line by someone else in a true story (owner 10-27: the bank clerk asks
    again). A native library voice, added once and saved in voices.json: extra_voice_id (female) or extra_m_voice_id
    (male, owner 10-28: the shop manager on screen is a man, so his line needs a man's voice). old=True picks an
    older voice for the grandma / grandpa of the webtoon drama: extra_old_voice_id / extra_old_m_voice_id."""
    path = ROOT / "senior" / "voices.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    key = "extra" + ("_old" if old else "") + ("" if gender == "female" else "_m") + "_voice"
    if data[channel].get(f"{key}_id"):
        return data[channel][f"{key}_id"]
    taken = {v for k, v in data[channel].items() if k.endswith("voice_id")}
    lang = {"kr": "ko", "us": "en"}[channel]
    want = ("grandm", "grandp", "elder", "old", "aged", "warm") if old else ("calm", "professional", "friendly", "clear", "natural", "warm")
    params = {"page_size": 40, "gender": gender, "language": lang, "sort": "trending", **({"age": "old"} if old else {})}
    r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
    if r.status_code == 400:
        params.pop("sort")
        r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
    voices = [v for v in (r.json().get("voices", []) if r.ok else []) if v["voice_id"] not in taken]
    if not voices and old:  # no "old" Korean voice listed: take the closest by description
        params.pop("age")
        r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
        voices = [v for v in (r.json().get("voices", []) if r.ok else []) if v["voice_id"] not in taken]
    pick = next((v for v in voices if any(w in (v.get("descriptive", "") + " " + v.get("description", "")).lower()
                                          for w in want)), voices[0] if voices else None)
    if not pick:
        sys.exit("no library voice for the extra role")
    r = requests.post(f"{API}/voices/add/{pick['public_owner_id']}/{pick['voice_id']}", headers=headers(), timeout=30,
                      json={"new_name": f"{channel} extra - {pick['name']}"[:60]})
    vid = (r.json().get("voice_id") if r.ok else None) or pick["voice_id"]
    data[channel].update({f"{key}_id": vid, f"{key}_name": pick["name"],
                          f"{key.replace('_voice', '')}_chosen": "picked automatically from the voice library"})
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("extra voice (library)", pick["name"], "-", pick.get("descriptive"), pick.get("accent"))
    return vid


def scammer_voice(channel):
    global _scammer
    c = json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel]
    if c.get("scammer_voice_id"):
        return c["scammer_voice_id"]
    if _scammer is None:
        _scammer = native_villain(channel)
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
    saved = json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8"))[channel]
    c = cfg(channel) if role == "host" else {**saved,
                                             # extra_m2: second man in one drama; extra_mid_f: a woman in her 60s
                                             # (owner 10-31); both read voices.json <role>_voice_id
                                             "voice_id": (saved.get(f"{role}_voice_id") or scammer_voice(channel))
                                             if role in ("extra_m2", "extra_mid_f") else
                                             extra_voice(channel, "male" if role.endswith("_m") else "female",
                                                         "_old" in role)
                                             if role.startswith("extra") else scammer_voice(channel),
                                             "speed": 1.0 if role.startswith("extra") else 1.05}
    tag = delivery.strip() if delivery.strip().startswith("[") and delivery.strip().endswith("]") else ""
    for model in (c["model_id"], FALLBACK_MODEL):
        acted = tag and re.match(r"eleven_v[3-9]", model)
        # owner 10-26/27: flat and weak voices, so the host and scammer run at the expressive "creative" end.
        # Drama people run at "natural": at 0.0 one man's line came out as another person (owner 10-29)
        for settings in ({"speed": c.get("speed", 1.0), "stability": 0.5 if role.startswith("extra") else 0.0},
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
