"""Voiceover, caption timing and background music for a NookBrief short.

  python3 voice.py <props.json> <out_dir>

Reads props["scenes"][i]["vo"] (what the narrator says in that scene), writes out_dir/vo<i>.wav
with Kokoro TTS (Apache-2.0, runs locally), out_dir/music.wav (synthesized here, no licensing),
and prints JSON {"scenes": [{"frames", "words": [[word, start_frame, end_frame], ...]}], "music": ...}.
"""
import json
import os
import re
import sys
import urllib.request

import numpy as np
import soundfile as sf

FPS = 30
SR = 24000
CACHE = os.path.expanduser("~/.cache/nookbrief-tts")
MODEL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
VOICE = os.environ.get("NB_VOICE", "af_heart")
PAD = 0.08  # seconds of air after each line


def kokoro():
    from kokoro_onnx import Kokoro
    os.makedirs(CACHE, exist_ok=True)
    for f in ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin"):
        if not os.path.exists(os.path.join(CACHE, f)):
            urllib.request.urlretrieve(MODEL + f, os.path.join(CACHE, f))
    return Kokoro(os.path.join(CACHE, "kokoro-v1.0.int8.onnx"), os.path.join(CACHE, "voices-v1.0.bin"))


def trim(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    return a[max(idx[0] - 240, 0):idx[-1] + 480] if len(idx) else a


def word_times(text, seconds):
    """Spread words over the line by length, with a little extra after punctuation."""
    words = text.split()
    weight = [len(re.sub(r"\W", "", w)) + 2 + (3 if re.search(r"[.,?!:]$", w) else 0) for w in words]
    total, t, out = sum(weight), 0.0, []
    for w, k in zip(words, weight):
        d = seconds * k / total
        out.append([w, round(t * FPS), round((t + d) * FPS)])
        t += d
    return out


def music(seconds, bpm=118):
    """Upbeat pop loop: Am-F-C-G, four-on-the-floor kick, claps, hats, bass, plucks, pumping pad."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    beat = 60 / bpm
    out = np.zeros(n)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G (MIDI)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)

    def hit(start, length, wave):
        i = int(start * SR)
        if i >= n:
            return
        j = min(n, i + len(wave))
        out[i:j] += wave[:j - i]

    # kick
    kt = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * (50 * kt + 90 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 8) * 1.3
    # clap and hat from noise
    rng = np.random.default_rng(7)
    ct = np.arange(int(0.2 * SR)) / SR
    clap = rng.standard_normal(len(ct)) * np.exp(-ct * 25) * 0.35
    ht = np.arange(int(0.05 * SR)) / SR
    hat = np.diff(rng.standard_normal(len(ht) + 1)) * np.exp(-ht * 90) * 0.12
    bar = beat * 4
    b = 0.0
    while b < seconds:
        ch = chords[int(b / bar) % 4]
        for k in range(4):
            hit(b + k * beat, 0.35, kick)
            if k in (1, 3):
                hit(b + k * beat, 0.2, clap)
        for k in range(8):
            hit(b + k * beat / 2 + beat / 4, 0.05, hat * (1.3 if k % 2 else 0.8))
        # bass: root, eighth notes
        for k in range(8):
            bt = np.arange(int(beat / 2 * SR)) / SR
            f = hz(ch[0] - 24)
            bass = (np.sin(2 * np.pi * f * bt) + 0.3 * np.sin(4 * np.pi * f * bt)) * np.exp(-bt * 4) * 0.42
            hit(b + k * beat / 2, beat / 2, bass)
        # plucks: arpeggio on sixteenths
        for k in range(16):
            pt = np.arange(int(0.25 * SR)) / SR
            f = hz(ch[k % 3] + 12 * (k // 8 % 2) + 12)
            pl = (np.sin(2 * np.pi * f * pt) + 0.5 * np.sin(4 * np.pi * f * pt)) * np.exp(-pt * 12) * 0.11
            hit(b + k * beat / 4, 0.25, pl)
        b += bar
    # pad, ducked on every beat like a sidechain
    pad = np.zeros(n)
    for i, ch in enumerate(chords * int(seconds / bar / 4 + 2)):
        s, e = int(i * bar * SR), int((i + 1) * bar * SR)
        if s >= n:
            break
        seg = t[s:min(e, n)]
        pad[s:min(e, n)] = sum(np.sin(2 * np.pi * hz(m) * seg + np.sin(2 * np.pi * 0.3 * seg)) for m in ch) * 0.07
    duck = 1 - 0.7 * np.exp(-((t % beat) / beat) * 6)
    out += pad * duck
    fade = np.minimum(1, np.minimum(t / 0.3, (seconds - t) / 1.2))
    out *= np.clip(fade, 0, 1)
    return out / (np.abs(out).max() + 1e-9) * 0.8


def main(props_path, out_dir):
    props = json.load(open(props_path, encoding="utf-8"))
    os.makedirs(out_dir, exist_ok=True)
    tts = kokoro()
    scenes, total = [], 0
    for i, s in enumerate(props["scenes"]):
        if not s.get("vo"):
            scenes.append({"frames": s.get("frames", 60), "words": []})
            total += scenes[-1]["frames"]
            continue
        audio, sr = tts.create(s["vo"], voice=s.get("voice", VOICE), speed=s.get("speed", 1.25), lang="en-us")
        audio = trim(audio)
        sf.write(os.path.join(out_dir, f"vo{i}.wav"), audio, sr)
        sec = len(audio) / sr
        frames = max(int((sec + PAD + s.get("hold", 1.5 if s.get("kind") == "cta" else 0)) * FPS) + 1, s.get("min_frames", 0))
        scenes.append({"frames": frames, "words": word_times(s["vo"], sec), "vo": f"vo{i}.wav"})
        total += frames
    sf.write(os.path.join(out_dir, "music.wav"), music(total / FPS + 0.5), SR)
    print(json.dumps({"scenes": scenes, "music": "music.wav", "frames": total}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
