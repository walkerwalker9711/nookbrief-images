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


def saw(f, sec, decay=18.0, harmonics=8):
    """Bowed-string stab: a band-limited saw that cuts through on phone speakers."""
    t = env(sec)
    x = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, harmonics + 1))
    return x * np.exp(-t * decay) * np.minimum(1, t / 0.004)


def alert(seconds, seed=7, bpm=118):
    """Thriller bed for the scam dramas (owner 10-27: the old low drone was inaudible on phones): staccato
    string ostinato in the mid range, taiko hits on 1 and 3, a high tremolo, a riser into every fourth bar."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat = 60 / bpm
    bar, six = beat * 4, beat / 4
    roots = [57, 57, 53, 55] if seed % 2 else [57, 53, 58, 56]  # A3 based, minor moves
    figure = [0, 0, 3, 0, 7, 0, 3, 0, 0, 0, 3, 0, 8, 7, 3, 0]
    b, i = 0.0, 0
    while b < seconds:
        r = roots[i % 4]
        for k, step in enumerate(figure):
            tr.hit(b + k * six, saw(hz(r + step), six * 0.9), 0.16 if k % 4 == 0 else 0.11)
        for k in range(8):
            tr.hit(b + k * beat / 2, bass(hz(r - 24), beat / 2 * 0.9, 6), 0.22)
        for k in (0, 2):
            tr.hit(b + k * beat, kick(1.6, 0.5), 0.6)
            tr.hit(b + k * beat, noise_hit(rng, 0.25, 18, hp=False), 0.12)
        tr.hit(b + 3.5 * beat, noise_hit(rng, 0.12, 30), 0.1)
        t = env(bar)
        trem = np.sin(2 * np.pi * hz(r + 24) * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t))
        tr.hit(b, trem * np.minimum(1, t / 0.3) * np.minimum(1, (bar - t) / 0.3), 0.035)
        if i % 4 == 3:
            tr.hit(b + bar - 1.2, noise_hit(rng, 1.2, 0.1, hp=True) * np.linspace(0, 1, int(1.2 * 24000)) ** 3, 0.08)
        b, i = b + bar, i + 1
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
    # two slow heartbeats under the scammer's threats
    th = env(0.16)
    lub = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-th * 18) + 38) / SR) * np.exp(-th * 22)
    beat = np.zeros(int(SR * 0.85))
    beat[:len(lub)] += lub
    beat[int(SR * 0.22):int(SR * 0.22) + len(lub)] += lub * 0.7
    heart = np.concatenate([beat, beat]) * 0.9
    # phone ringing: two short bursts of a 440+480 Hz ring
    tr_ = env(0.4)
    burst = (np.sin(2 * np.pi * 440 * tr_) + np.sin(2 * np.pi * 480 * tr_)) * 0.2 * np.minimum(1, tr_ / 0.01) * np.minimum(1, (tr_[-1] - tr_) / 0.02)
    gap = np.zeros(int(SR * 0.2))
    ring = np.concatenate([burst, gap, burst])
    return {"ring": ring, "heart": heart, "alarm": alarm, "stamp": stamp, "notify": notify, "whoosh": whoosh, "pop": pop, "buzz": buzz, "mic": mic}


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
