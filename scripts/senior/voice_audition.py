"""Candidate voices for one drama role, each reading the same line, so the owner picks by ear
(owner 10-28: the auto-picked "grandma" voice sounded like a woman in her 20s-30s).

  python voice_audition.py kr old_f "아이고, 이게 무슨 소리래요? 내 통장이 범죄에 쓰였다고요?"

Writes senior/samples/audition/<role>_<n>.mp3 and <role>.json (name, source, voice id). Candidates: Korean library
voices tagged old (best described first) and voices designed from a description with ElevenLabs Voice Design.
"""
import base64
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from el_voice import API, headers  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "senior" / "samples" / "audition"
DESIGN = {
    "old_f": ["A Korean grandmother in her late 70s from a rural town. Thin, slightly shaky, aged voice with a soft "
              "rasp, warm but worried, speaks slowly in natural Korean.",
              "An elderly Korean woman around 80, frail and breathy, a bit hoarse, gentle countryside accent, "
              "talks slowly and hesitantly."],
    # mid_m: a worn-out man in his late 50s (owner 10-30: the 57-year-old sounded like a young man)
    "mid_m": ["A Korean man aged 57, worn out by years of hardship. Low, husky, slightly hoarse middle-aged voice with "
              "audible age and fatigue, speaks slowly and emotionally in natural Korean, never youthful.",
              "A weathered Korean man in his late fifties, rough tired voice with a gravelly texture, quiet and "
              "choked with emotion, clearly middle-aged, natural Korean."],
    "old_m": ["A Korean grandfather in his late 70s. Low, rough, aged voice, a little hoarse, speaks slowly in natural Korean."],
}
# Voice Design needs at least 100 characters of sample text
LONG = {"ko": "아이고, 내가 무슨 잘못을 했다고 그래요. 나는 통장에 돈 넣어 놓고 그냥 산 것밖에 없는데. 은행 가서 돈을 찾아 오라고요? "
              "그게 무슨 소리예요, 공무원이라면서. 가만있어 봐요, 우리 아들한테 먼저 전화 좀 해 보고."}
WANT = ("grandm", "grandp", "elder", "old", "aged", "senior", "할머니", "할아버지", "노인")


def library(lang, gender, n):
    params = {"page_size": 100, "language": lang, "gender": gender, "age": "old"}
    r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
    vs = r.json().get("voices", []) if r.ok else []
    print("library old", gender, lang, len(vs), r.status_code)
    # native speakers first (the first run picked Somali and African American voices that also list Korean)
    native = lambda v: 3 * (str(v.get("locale", "")).lower().startswith(lang) or any(
        k in (v.get("accent", "") or "").lower() for k in ("korean", "seoul", "standard", "gyeong", "jeolla", "busan")))
    score = lambda v: native(v) + sum(w in (v.get("descriptive", "") + v.get("description", "") + v.get("name", "")).lower() for w in WANT)
    for v in vs:
        print(" ", v["name"], "|", v.get("accent"), v.get("locale"), "|", v.get("descriptive"), "|", (v.get("description") or "")[:80])
    return [v for v in sorted(vs, key=score, reverse=True) if native(v)][:n]


def speak(vid, text, out):
    r = requests.post(f"{API}/text-to-speech/{vid}", headers=headers(), timeout=120, params={"output_format": "mp3_44100_128"},
                      json={"text": text, "model_id": "eleven_v3"})
    if r.status_code != 200:
        r = requests.post(f"{API}/text-to-speech/{vid}", headers=headers(), timeout=120,
                          params={"output_format": "mp3_44100_128"}, json={"text": text, "model_id": "eleven_multilingual_v2"})
    if r.status_code == 200:
        out.write_bytes(r.content)
        return True
    print("tts", vid, r.status_code, r.text[:200])
    return False


def design(desc, text):
    for url, body in ((f"{API}/text-to-voice/design", {"voice_description": desc, "text": text, "model_id": "eleven_ttv_v3"}),
                      (f"{API}/text-to-voice/design", {"voice_description": desc, "text": text}),
                      (f"{API}/text-to-voice/create-previews", {"voice_description": desc, "text": text})):
        r = requests.post(url, headers=headers(), json=body, timeout=180)
        if r.ok:
            return r.json().get("previews", [])
        print("design", url, r.status_code, r.text[:200])
    return []


def main(channel, role, text):
    OUT.mkdir(parents=True, exist_ok=True)
    lang = {"kr": "ko", "us": "en"}[channel]
    gender = "male" if role.endswith("_m") else "female"
    found, n = [], 0
    for v in library(lang, gender, 3):
        r = requests.post(f"{API}/voices/add/{v['public_owner_id']}/{v['voice_id']}", headers=headers(), timeout=30,
                          json={"new_name": f"{channel} {role} - {v['name']}"[:60]})
        vid = (r.json().get("voice_id") if r.ok else None) or v["voice_id"]
        n += 1
        if speak(vid, text, OUT / f"{role}_{n}.mp3"):
            found.append({"n": n, "name": v["name"], "source": "library", "voice_id": vid,
                          "about": (v.get("descriptive") or "") + " " + (v.get("description") or "")[:120]})
    long = text if len(text) >= 100 else (text + " " + LONG.get(lang, ""))[:400]
    for desc in DESIGN.get(role, []):
        for p in design(desc, long)[:2]:
            n += 1
            (OUT / f"{role}_{n}.mp3").write_bytes(base64.b64decode(p.get("audio_base_64") or p.get("audio_base64")))
            r = requests.post(f"{API}/text-to-voice", headers=headers(), timeout=60,
                              json={"voice_name": f"{channel} {role} designed {n}", "voice_description": desc,
                                    "generated_voice_id": p["generated_voice_id"]})
            if not r.ok:
                r = requests.post(f"{API}/text-to-voice/create-voice-from-preview", headers=headers(), timeout=60,
                                  json={"voice_name": f"{channel} {role} designed {n}", "voice_description": desc,
                                        "generated_voice_id": p["generated_voice_id"]})
            vid = r.json().get("voice_id") if r.ok else None
            print("saved designed voice", n, r.status_code, vid)
            found.append({"n": n, "name": f"designed {n}", "source": "voice design", "voice_id": vid, "about": desc})
    (OUT / f"{role}.json").write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
    print(len(found), "candidates")


if __name__ == "__main__":
    main(*sys.argv[1:4])
