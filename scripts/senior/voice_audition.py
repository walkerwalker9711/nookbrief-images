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
    # mid_f: a mother in her early 60s (owner 10-31: the 80-year-old grandma voice was far too old for a 63-year-old)
    "mid_f": ["A Korean woman aged 62, a warm mother's voice, mature and gentle, clearly in her early sixties but "
              "not frail or elderly, steady breath, speaks softly and emotionally in natural Korean.",
              "A Korean mother in her early sixties, soft warm alto with a little maturity in the tone, healthy and "
              "clear, not shaky, natural standard Korean, emotional and tender."],
    # elder_m: a man in his 90s (owner 11-03: the deep Rei voice was "최홍만", pitched up it was "too young")
    "elder_m": ["A very old Korean grandfather aged 93. Thin, frail, breathy voice with a dry rasp and a slight tremble, "
                "weak air support, words come out slowly and a little slurred, warm and gentle, natural Korean, "
                "clearly in his nineties, never deep or booming, never young.",
                "A Korean man in his early nineties, small and frail. Light, papery, wavering old voice, a little "
                "wheezy and hoarse, soft chuckles, speaks slowly with pauses, kind and humble, natural standard Korean."],
    # US (Pops Knows) roles, 11-04. Designed only and NOT saved (voice slots): the pick is saved later with
    # "audition us save <role> <n>".
    "us_narr_m": ["A warm American grandfather in his early seventies from a small Midwestern town, telling a true story "
                  "at the kitchen table. Gravelly but clear, unhurried, a little dry humor, gentle, natural American "
                  "English, clearly older but still strong.",
                  "An American man around 72, a small-town storyteller with a deep warm voice and a light rasp, calm "
                  "and steady pace, folksy Midwestern accent, sincere, never theatrical."],
    "us_elder_m": ["A frail American widower in his mid eighties from Indiana. Soft, thin, slightly shaky old voice, a "
                   "little hoarse, speaks slowly, holding back tears, natural Midwestern American English, clearly very old.",
                   "An elderly American man around 86, gentle and lonely, light papery wavering voice with a dry rasp, "
                   "slow with pauses, kind small-town Indiana accent, never deep or booming."],
    "us_adult_m": ["An American man around sixty from Indiana, friendly everyday Midwestern voice, warm and sincere, "
                   "medium-low pitch with a bit of gravel, natural conversational American English, not a narrator.",
                   "A regular guy in his early sixties from the Indianapolis suburbs, easygoing and kind, a little "
                   "choked up, plain Midwestern accent, relaxed conversational pace."],
    "us_teen_f": ["A feisty seventeen-year-old American high school cheerleader, sharp and sassy, quick confident "
                  "talk with attitude, bright youthful voice, natural American English.",
                  "A spirited American teenage girl around seventeen, a firecracker who tells a boy off, crisp and "
                  "fast, clear young voice, playful but annoyed, natural American accent."],
    "old_m": ["A Korean grandfather in his late 70s. Low, rough, aged voice, a little hoarse, speaks slowly in natural Korean."],
}
# Voice Design needs at least 100 characters of sample text
LONG = {"ko": "아이고, 내가 무슨 잘못을 했다고 그래요. 나는 통장에 돈 넣어 놓고 그냥 산 것밖에 없는데. 은행 가서 돈을 찾아 오라고요? "
              "그게 무슨 소리예요, 공무원이라면서. 가만있어 봐요, 우리 아들한테 먼저 전화 좀 해 보고.",
        "en": "Well, I'll tell you what. We built that first house with our own two hands, and she picked out every "
              "single curtain. Those were good years. Real good years."}
WANT = ("grandm", "grandp", "elder", "old", "aged", "senior", "할머니", "할아버지", "노인")


def library(lang, gender, n, age="old"):
    params = {"page_size": 100, "language": lang, "gender": gender, "age": age}
    r = requests.get(f"{API}/shared-voices", headers=headers(), params=params, timeout=30)
    vs = r.json().get("voices", []) if r.ok else []
    print("library", age, gender, lang, len(vs), r.status_code)
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


def list_voices():
    """'audition kr list x': our saved voices and which ones voices.json uses (voice slots run out on the plan)."""
    used = json.dumps(json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8")))
    r = requests.get(f"{API}/voices", headers=headers(), timeout=30)
    vs = r.json().get("voices", [])
    print("voices", r.status_code, len(vs))
    for v in vs:
        print(v.get("category"), v["voice_id"], "USED" if v["voice_id"] in used else "-", v.get("name"))
    r = requests.get(f"{API}/user/subscription", headers=headers(), timeout=30)
    if r.ok:
        j = r.json()
        print("slots", j.get("voice_slots_used"), "/", j.get("voice_limit"), "professional", j.get("professional_voice_slots_used"))


def clean():
    """'audition kr clean x': delete our designed (generated) voices that voices.json does not use. They are rejected
    audition candidates and they hold the plan's 10 voice slots (11-03: elder_m designs could not be saved)."""
    used = json.dumps(json.loads((ROOT / "senior" / "voices.json").read_text(encoding="utf-8")))
    for v in requests.get(f"{API}/voices", headers=headers(), timeout=30).json().get("voices", []):
        if v.get("category") == "generated" and v["voice_id"] not in used and str(v.get("name", "")).startswith(("kr ", "us ")):
            r = requests.delete(f"{API}/voices/{v['voice_id']}", headers=headers(), timeout=30)
            print("deleted", v["voice_id"], v.get("name"), r.status_code)


def clone(channel, text):
    """'audition kr clone elder_m 6': save the picked candidate as our own voice from its sample (instant voice
    clone). Designed previews were never saved when the slots were full (11-03), so the sample is all we have.
    The new id goes into <role>.json as "saved_voice_id"; Claude copies it to voices.json."""
    role, n = text.split()[:2]
    mp3 = OUT / f"{role}_{n}.mp3"
    with open(mp3, "rb") as f:
        r = requests.post(f"{API}/voices/add", headers={k: v for k, v in headers().items() if k.lower() != "content-type"},
                          data={"name": f"{channel} {role} {n} (picked)", "remove_background_noise": "false",
                                "description": "owner pick 2026-11-03, cloned from the audition sample"},
                          files={"files": (mp3.name, f, "audio/mpeg")}, timeout=120)
    print("clone", r.status_code, r.text[:300])
    if r.ok:
        js = OUT / f"{role}.json"
        found = json.loads(js.read_text(encoding="utf-8"))
        for c in found:
            if str(c["n"]) == n:
                c["saved_voice_id"] = r.json()["voice_id"]
        js.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")


def save(channel, text):
    """'audition us save us_elder_m 2': save one unsaved designed candidate (from its preview, else clone the sample)."""
    role, n = text.split()[:2]
    js = OUT / f"{role}.json"
    found = json.loads(js.read_text(encoding="utf-8"))
    for c in found:
        if str(c["n"]) == n:
            r = requests.post(f"{API}/text-to-voice", headers=headers(), timeout=60,
                              json={"voice_name": f"{channel} {role} {n} (picked)", "voice_description": c["about"][:500],
                                    "generated_voice_id": c.get("generated_voice_id", "")})
            print("save", r.status_code, r.text[:300])
            if r.ok and r.json().get("voice_id"):
                c["saved_voice_id"] = r.json()["voice_id"]
                js.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
                return
    return clone(channel, text)


def main(channel, role, text):
    if role == "save":
        return save(channel, text)
    if role == "clone":
        return clone(channel, text)
    if role == "list":
        return list_voices()
    if role == "clean":
        clean()
        return list_voices()
    design_only = role.endswith("!") or channel == "us"  # "elder_m!": only new designed voices (library samples already made)
    role = role.rstrip("!")
    OUT.mkdir(parents=True, exist_ok=True)
    lang = {"kr": "ko", "us": "en"}[channel]
    gender = "male" if role.endswith("_m") else "female"
    found, n = [], (0 if channel == "us" else 3 if design_only else 0)
    for v in ([] if design_only else library(lang, gender, 3, "middle_aged" if role.startswith("mid") else "old")):
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
            if channel == "us":  # keep slots free: save only the owner's pick later
                found.append({"n": n, "name": f"designed {n}", "source": "voice design (unsaved)", "voice_id": None,
                              "generated_voice_id": p["generated_voice_id"], "about": desc})
                continue
            r = requests.post(f"{API}/text-to-voice", headers=headers(), timeout=60,
                              json={"voice_name": f"{channel} {role} designed {n}", "voice_description": desc,
                                    "generated_voice_id": p["generated_voice_id"]})
            if not r.ok:
                r = requests.post(f"{API}/text-to-voice/create-voice-from-preview", headers=headers(), timeout=60,
                                  json={"voice_name": f"{channel} {role} designed {n}", "voice_description": desc,
                                        "generated_voice_id": p["generated_voice_id"]})
            vid = r.json().get("voice_id") if r.ok else None
            print("saved designed voice", n, r.status_code, vid, "" if r.ok else r.text[:300])
            found.append({"n": n, "name": f"designed {n}", "source": "voice design", "voice_id": vid, "about": desc})
    (OUT / f"{role}.json").write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
    print(len(found), "candidates")


if __name__ == "__main__":
    main(*sys.argv[1:4])
