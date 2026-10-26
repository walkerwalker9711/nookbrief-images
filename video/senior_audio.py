"""Music beds and effects for the senior warning Shorts (한국이장님 / Pops Knows), synthesized here.

  python senior_audio.py <out_dir> <seconds> <mood> [seed]
mood: alert (scam weeks: low pulse, ticking clock, minor drone) or warm (tips, benefits, nostalgia).
Writes music.wav plus fx-*.wav and prints {"music": ..., "sfx": {...}} as JSON.
"""
import json
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beds import BEDS, Track, bass, bell, env, hz, kick, noise_hit, pad  # noqa: E402

SR = 24000


def alert(seconds, seed=7, bpm=100):
    """Tension under a warning: minor drone, pulsing eighth-note bass, clock tick, a low hit every two bars."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    roots = [45, 45, 41, 43] if seed % 2 else [45, 41, 46, 44]  # Am drone, moving under it
    tick = (np.sin(2 * np.pi * 3200 * env(0.03)) * np.exp(-env(0.03) * 160)) * 0.6
    b, i = 0.0, 0
    while b < seconds:
        r = roots[i % 4]
        tr.hit(b, pad(hz(r + 12), bar, 0.15), 0.05)
        tr.hit(b, pad(hz(r + 15), bar, 0.15), 0.035)
        for k in range(8):
            tr.hit(b + k * beat / 2, bass(hz(r - 12), beat / 2 * 0.9, 6), 0.33 if k % 2 == 0 else 0.22)
        for k in range(4):
            tr.hit(b + k * beat, tick, 0.18 if k % 2 else 0.1)
        if i % 2 == 0:
            tr.hit(b, kick(1.3, 0.9), 0.55)
            tr.hit(b, noise_hit(rng, 0.6, 7, hp=False), 0.06)
        b, i = b + bar, i + 1
    tr.out += rng.standard_normal(tr.n) * 0.002
    return tr.done(0.3, 1.2)


def warm(seconds, seed=11):
    """Friendly bed for tips and nostalgia: rotates through the gentle NookBrief beds."""
    name = ["marimba", "acoustic", "bossa", "lofi"][seed % 4]
    return BEDS[name](seconds, key=[0, 2, -3, 5][seed % 4], seed=seed)


def sfx():
    rng = np.random.default_rng(3)
    # two-tone alarm, three quick pairs
    t = env(0.11)
    beep = lambda f: np.sign(np.sin(2 * np.pi * f * t)) * 0.25 * np.minimum(1, t / 0.005) * np.minimum(1, (t[-1] - t) / 0.01)
    alarm = np.concatenate([np.concatenate([beep(1320), beep(990)]) for _ in range(3)])
    # stamp: low thump + paper slap
    tt = env(0.5)
    thud = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt * 12) + 45) / SR) * np.exp(-tt * 9)
    slap = rng.standard_normal(len(tt)) * np.exp(-tt * 60) * 0.6
    stamp = (thud + slap) * 0.9
    # message arrived
    notify = bell(hz(84), 0.6) * 0.45 + bell(hz(91), 0.6) * 0.35
    # whoosh between scenes
    tw = env(0.32)
    n = rng.standard_normal(len(tw))
    whoosh = n * np.sin(np.pi * tw / tw[-1]) ** 2 * 0.3
    # tick for checklist items, and a buzz for the wrong ones
    tp = env(0.09)
    pop = np.sin(2 * np.pi * np.cumsum(900 * np.exp(-tp * 30) + 300) / SR) * np.exp(-tp * 40) * 0.8
    tb = env(0.28)
    buzz = np.sign(np.sin(2 * np.pi * 110 * tb)) * np.exp(-tb * 8) * 0.25
    # mic feedback "삐-" for the village chief opening
    tm = env(0.45)
    mic = np.sin(2 * np.pi * 1150 * tm) * np.minimum(1, tm / 0.02) * np.minimum(1, (tm[-1] - tm) / 0.08) * 0.3
    return {"alarm": alarm, "stamp": stamp, "notify": notify, "whoosh": whoosh, "pop": pop, "buzz": buzz, "mic": mic}


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main(out_dir, seconds, mood, seed=7):
    os.makedirs(out_dir, exist_ok=True)
    write(os.path.join(out_dir, "music.wav"), (alert if mood == "alert" else warm)(seconds, seed=seed))
    fx = {}
    for name, x in sfx().items():
        write(os.path.join(out_dir, f"fx-{name}.wav"), x)
        fx[name] = f"fx-{name}.wav"
    print(json.dumps({"music": "music.wav", "sfx": fx}))


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 7)
