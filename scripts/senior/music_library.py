"""Background music library for the senior dramas (owner 10-29: "many high-quality tracks, used in rotation,
by genre and situation"). Tracks are made once with ElevenLabs Music and kept in video/music_lib/, so later
videos cost nothing for music.

  python music_library.py check            remaining ElevenLabs credits
  python music_library.py make <id> ...    make these tracks (skips ones that already exist)

draft.py calls pick() and bed() to put a library track under a video; with no track for the mood it keeps
the synthesized bed from video/senior_audio.py.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "video" / "music_lib"
API = "https://api.elevenlabs.io/v1"
SECONDS = 90
COMMON = ("Instrumental only, no vocals, no choir words. Background score under spoken Korean dialogue for a "
          "short webtoon drama: leave the 1-4 kHz speech range open, no loud peaks, steady level, ends cleanly.")

# id: (mood, situation, prompt). alert = scam dramas, touching = heartwarming true stories
TRACKS = {
    "alert-threat": ("alert", "협박 전화 긴장", "Tense thriller underscore, low staccato strings, soft taiko pulse, dark minor key, 100 bpm, phone-scam suspense."),
    "alert-mystery": ("alert", "미스터리 저음", "Mysterious investigation underscore, low piano notes, muted synth pulse, sparse ticking, slow 80 bpm, uneasy and curious."),
    "alert-pressure": ("alert", "시간 압박", "Ticking-clock pressure cue, fast pizzicato strings, rising synth arpeggio, heartbeat-like kick, 120 bpm, urgent but not loud."),
    "alert-chase": ("alert", "검거·추격 클라이맥스", "Police stakeout and arrest climax, driving cinematic percussion, brass swells kept low, 125 bpm, triumphant tension that resolves."),
    "alert-aftermath": ("alert", "반전 직후", "Aftermath of a twist, slow minor strings with a hopeful major turn at the end, 70 bpm, reflective."),
    "alert-explain": ("alert", "차분한 해설", "Calm news-explainer bed, soft electric piano and light synth pad, gentle 90 bpm pulse, serious but reassuring."),
    "touching-piano": ("touching", "따뜻한 피아노", "Warm solo piano, gentle major key melody, 70 bpm, tender and heartfelt, like a Korean human-interest documentary."),
    "touching-strings": ("touching", "현악 고조", "Emotional strings that start quiet and build to a moving swell, piano under, 72 bpm, uplifting, cinematic Korean drama."),
    "touching-guitar": ("touching", "어쿠스틱 기타 일상", "Light acoustic guitar fingerpicking with soft glockenspiel, everyday small-town warmth, 92 bpm, kind and simple."),
    "touching-hope": ("touching", "슬픔에서 희망으로", "Starts sad with cello and piano, turns hopeful halfway with warm strings and soft piano, 68 bpm."),
    "touching-family": ("touching", "가족·추억", "Nostalgic family memories theme, music box and piano, soft strings, 3/4 waltz feel, gentle and loving."),
    "touching-ending": ("touching", "잔잔한 엔딩", "Quiet closing theme, sustained warm pad, soft piano chords, slow 60 bpm, peaceful and grateful."),
}


def headers():
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}


def check():
    r = requests.get(f"{API}/user/subscription", headers=headers(), timeout=60)
    r.raise_for_status()
    s = r.json()
    print("tier", s.get("tier"), "credits used", s.get("character_count"), "of", s.get("character_limit"),
          "left", (s.get("character_limit") or 0) - (s.get("character_count") or 0), "reset", s.get("next_character_count_reset_unix"))


def make(ids):
    LIB.mkdir(parents=True, exist_ok=True)
    for tid in ids:
        mood, situation, prompt = TRACKS[tid]
        out = LIB / f"{tid}.mp3"
        if out.exists():
            print("have", tid)
            continue
        for wait in (0, 20, 60, 120, 240):  # 429 "system_busy" comes and goes (10-29)
            time.sleep(wait)
            r = requests.post(f"{API}/music", headers=headers(), timeout=600,
                              json={"prompt": f"{prompt} {COMMON}", "music_length_ms": SECONDS * 1000, "model_id": "music_v1"})
            if r.status_code != 429:
                break
            print(tid, "busy, retrying")
        if r.status_code != 200:
            sys.exit(f"{tid}: {r.status_code} {r.text[:400]}")
        raw = out.with_suffix(".raw.mp3")
        raw.write_bytes(r.content)
        # one loudness for every track, a little under the old synth beds so the voice stays on top
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "loudnorm=I=-22:TP=-3:LRA=9",
                        "-ar", "44100", "-b:a", "160k", str(out)], check=True)
        raw.unlink()
        print("made", tid, situation)
    index = {t: {"mood": m, "situation": s} for t, (m, s, _) in TRACKS.items() if (LIB / f"{t}.mp3").exists()}
    (LIB / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")


def pick(mood, want="", avoid=""):
    """A library track for this mood: the one the script asks for, else the next one after the last used."""
    have = sorted(t for t, (m, _, _) in TRACKS.items() if m == mood and (LIB / f"{t}.mp3").exists())
    if not have:
        return None
    if want in have:
        return want
    last = LIB / f"last-{mood}.txt"
    prev = last.read_text().strip() if last.exists() else avoid
    nxt = have[(have.index(prev) + 1) % len(have)] if prev in have else have[0]
    if nxt == avoid and len(have) > 1:
        nxt = have[(have.index(nxt) + 1) % len(have)]
    last.write_text(nxt)
    return nxt


def bed(tid, seconds, out):
    """The track looped with a 3 s crossfade to cover `seconds`, faded out at the end."""
    src = LIB / f"{tid}.mp3"
    loops = int(seconds // (SECONDS - 3)) + 1
    chain, inputs = "", []
    for k in range(loops):
        inputs += ["-i", str(src)]
    label = "[0:a]"
    for k in range(1, loops):
        chain += f"{label}[{k}:a]acrossfade=d=3[x{k}];"
        label = f"[x{k}]"
    chain += f"{label}atrim=0:{seconds},afade=t=out:st={max(0, seconds - 2)}:d=2[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", chain, "-map", "[out]",
                    "-ar", "24000", "-ac", "1", str(out)], check=True)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "check":
        check()
    elif sys.argv[1] == "make":
        make(sys.argv[2:] or list(TRACKS))
