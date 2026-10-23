"""Music beds for NookBrief shorts, synthesized here (no samples, no licensing).

Each bed takes (seconds, key, seed) and returns a mono float array at SR. `key` transposes in
semitones, `seed` changes the noise, the voicings and small rhythm choices, so the same style
still sounds different from one video to the next. voice.py picks the bed from props["music"].
"""
import numpy as np

SR = 24000


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


class Track:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.out = np.zeros(self.n)
        self.seconds = seconds

    def hit(self, start, wave, gain=1.0):
        i = int(start * SR)
        if 0 <= i < self.n:
            j = min(self.n, i + len(wave))
            self.out[i:j] += wave[:j - i] * gain

    def done(self, fade_in=0.5, fade_out=1.4):
        t = np.arange(self.n) / SR
        self.out *= np.clip(np.minimum(t / fade_in, (self.seconds - t) / fade_out), 0, 1)
        return self.out / (np.abs(self.out).max() + 1e-9) * 0.8


def env(sec):
    return np.arange(int(sec * SR)) / SR


def pluck(f, sec=1.2, bright=1.0):
    """Guitar-ish pluck: harmonics that die faster the higher they are."""
    t = env(sec)
    w = sum(np.sin(2 * np.pi * f * k * t) * (0.7 ** k) * np.exp(-t * (2.5 + k * 1.8 * bright)) for k in range(1, 7))
    return w * np.minimum(1, t / 0.003)


def ep(f, sec):
    """Electric piano: sine + soft bell partial, tremolo."""
    t = env(sec)
    w = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(2 * np.pi * f * 7.02 * t) * np.exp(-t * 6)
    return w * (0.8 + 0.2 * np.sin(2 * np.pi * 4.2 * t)) * np.exp(-t * 0.9) * np.minimum(1, t / 0.01)


def mallet(f, sec=0.5):
    """Marimba: fundamental + 4th partial, quick decay."""
    t = env(sec)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 18)) * np.exp(-t * 7)


def bell(f, sec=1.6):
    t = env(sec)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)) * np.exp(-t * 2.2)


def pad(f, sec, vib=0.3):
    t = env(sec)
    a = np.minimum(1, t / 0.8) * np.minimum(1, (sec - t) / 0.8)
    return (np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * vib * t)) + 0.3 * np.sin(2 * np.pi * f * 1.003 * t)) * a


def kick(depth=1.0, sec=0.4):
    t = env(sec)
    return np.sin(2 * np.pi * (45 * t + 70 * depth * (1 - np.exp(-t * 28)) / 28)) * np.exp(-t * 8)


def noise_hit(rng, sec, decay, hp=True):
    t = env(sec)
    x = rng.standard_normal(len(t) + 1)
    x = np.diff(x) if hp else x[:-1]
    return x * np.exp(-t * decay)


def bass(f, sec, decay=2.0):
    t = env(sec)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.exp(-t * decay) * np.minimum(1, t / 0.005)


# chord progressions as MIDI voicings around C4; transposed by `key`
PROG = {
    "lofi": [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],      # Fmaj7 Em7 Dm7 Cmaj7
    "chillhop": [[48, 51, 55, 58], [53, 57, 60, 63], [46, 50, 53, 57], [51, 55, 58, 62]],  # Cm7 F7 Bbmaj7 Ebmaj7
    "acoustic": [[55, 59, 62], [50, 54, 57], [52, 55, 59], [48, 52, 55]],                  # G D Em C
    "house": [[57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62]],      # Am7 Fmaj7 G7 Em7
    "ambient": [[50, 57, 60, 64], [46, 53, 57, 62], [48, 55, 59, 62], [45, 52, 55, 60]],    # Dsus/add9 Bb C Am
    "bossa": [[50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59], [45, 49, 52, 55]],      # Dm7 G7 Cmaj7 A7
    "marimba": [[48, 52, 55], [45, 48, 52], [53, 57, 60], [55, 59, 62]],                   # C Am F G
}


def lofi(seconds, key=0, seed=3, bpm=82):
    """Mellow lo-fi: soft kick, rim, swung hats, electric-piano 7ths, vinyl hiss."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["lofi"]
    bar = beat * 4
    rim = (np.sin(2 * np.pi * 1700 * env(0.12)) * 0.3 + rng.standard_normal(len(env(0.12))) * 0.3) * np.exp(-env(0.12) * 45)
    hat = noise_hit(rng, 0.04, 110)
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        for k, off in enumerate((0, 1.5, 2.5)):
            tr.hit(b + off * beat, kick(0.8), 0.8 if k == 0 else 0.55)
        tr.hit(b + beat, rim, 0.25)
        tr.hit(b + 3 * beat, rim, 0.25)
        for k in range(8):
            tr.hit(b + k * beat / 2 + (beat * 0.12 if k % 2 else 0), hat, 0.07)
        for m in ch:
            tr.hit(b, ep(hz(m), bar), 0.055)
        tr.hit(b, bass(hz(ch[0] - 24), beat * 2, 1.5), 0.35)
        tr.hit(b + beat * 2, bass(hz(ch[0] - 24), beat * 2, 1.5), 0.3)
        b, i = b + bar, i + 1
    tr.out += rng.standard_normal(tr.n) * 0.004
    return tr.done(0.6, 1.5)


def chillhop(seconds, key=0, seed=5, bpm=88):
    """Boom-bap chillhop: dusty kick/snare, jazzy minor 7ths, walking-ish bass, little melody."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["chillhop"]
    bar = beat * 4
    snare = noise_hit(rng, 0.22, 18, hp=False) * 0.5 + np.sin(2 * np.pi * 190 * env(0.22)) * np.exp(-env(0.22) * 22) * 0.4
    hat = noise_hit(rng, 0.05, 80)
    sw = 0.16 * beat
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        tr.hit(b, kick(1.0), 0.85)
        tr.hit(b + 2.5 * beat, kick(1.0), 0.6)
        if rng.random() < 0.5:
            tr.hit(b + 1.75 * beat, kick(1.0), 0.4)
        tr.hit(b + beat, snare, 0.5)
        tr.hit(b + 3 * beat, snare, 0.5)
        for k in range(8):
            tr.hit(b + k * beat / 2 + (sw if k % 2 else 0), hat, 0.06 if k % 2 else 0.09)
        for off in (0, 1.5 + (0.25 if rng.random() < 0.5 else 0)):
            for m in ch:
                tr.hit(b + off * beat, ep(hz(m), beat * 1.4), 0.05)
        for k, d in enumerate((0, 7, 12, 10)):
            tr.hit(b + k * beat, bass(hz(ch[0] - 24 + d), beat, 3.0), 0.33)
        if i % 2:
            for k in range(3):
                tr.hit(b + (2 + k * 0.5) * beat + sw * (k % 2), mallet(hz(ch[(k + int(rng.integers(0, 3))) % 4] + 12), 0.5), 0.07)
        b, i = b + bar, i + 1
    tr.out += rng.standard_normal(tr.n) * 0.003
    return tr.done()


def acoustic(seconds, key=0, seed=11, bpm=96):
    """Fingerpicked guitar, shaker, light clap on 2 and 4. No kick, airy and bright."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["acoustic"]
    bar = beat * 4
    shaker = noise_hit(rng, 0.08, 45)
    clap = noise_hit(rng, 0.18, 26, hp=False)
    pattern = [0, 2, 1, 2, 0, 2, 1, 2] if seed % 2 else [0, 1, 2, 1, 0, 2, 1, 2]
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        tr.hit(b, pluck(hz(ch[0] - 12), 2.0), 0.22)
        for k, p in enumerate(pattern):
            tr.hit(b + k * beat / 2, pluck(hz(ch[p] + (12 if k in (3, 7) else 0)), 1.2), 0.13)
        for k in range(8):
            tr.hit(b + k * beat / 2, shaker, 0.05 if k % 2 else 0.03)
        if i >= 1:
            tr.hit(b + beat, clap, 0.12)
            tr.hit(b + 3 * beat, clap, 0.12)
        b, i = b + bar, i + 1
    return tr.done(0.3, 1.4)


def house(seconds, key=0, seed=13, bpm=118):
    """Soft deep house: four-on-the-floor, offbeat open hat, offbeat chord stabs, rolling bass."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["house"]
    bar = beat * 4
    ohat = noise_hit(rng, 0.14, 30)
    clap = noise_hit(rng, 0.16, 28, hp=False)
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        for k in range(4):
            tr.hit(b + k * beat, kick(1.2, 0.35), 1.0)
            tr.hit(b + k * beat + beat / 2, ohat, 0.1)
            if k in (1, 3):
                tr.hit(b + k * beat, clap, 0.22)
            for m in ch:
                tr.hit(b + k * beat + beat / 2, ep(hz(m), beat * 0.45) * np.exp(-env(beat * 0.45) * 8), 0.07)
        for k in range(8):
            tr.hit(b + k * beat / 2 + beat / 4, bass(hz(ch[0] - 24 + (12 if k == 6 else 0)), beat / 2, 5), 0.38)
        b, i = b + bar, i + 1
    return tr.done(0.4, 1.4)


def ambient(seconds, key=0, seed=17, bpm=70):
    """No drums: slow pad chords, soft bell arpeggio, low drone. For calm, explain-y videos."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["ambient"]
    bar = beat * 4
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        for m in ch:
            tr.hit(b, pad(hz(m), bar + 0.8, 0.2 + 0.1 * rng.random()), 0.05)
        tr.hit(b, pad(hz(ch[0] - 12), bar + 0.8, 0.1), 0.08)
        order = rng.permutation(len(ch))
        for k in range(6):
            tr.hit(b + k * beat * 2 / 3, bell(hz(ch[order[k % len(ch)]] + 12)), 0.06)
        b, i = b + bar, i + 1
    for d, g in ((0.29, 0.3), (0.47, 0.2)):  # two soft echoes for space
        k = int(d * SR)
        tr.out[k:] += tr.out[:-k].copy() * g
    return tr.done(1.0, 1.8)


def bossa(seconds, key=0, seed=19, bpm=128):
    """Bossa nova: nylon chord pattern on the clave, bass on 1 and 3 (root-fifth), rim, shaker."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["bossa"]
    bar = beat * 4
    rim = np.sin(2 * np.pi * 2200 * env(0.06)) * np.exp(-env(0.06) * 60)
    shaker = noise_hit(rng, 0.06, 55)
    comp = [0, 1.5, 3, 4.5, 6] if seed % 2 else [0, 1.5, 3.5, 5, 6.5]  # in eighths over two bars
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[(i // 2) % 4]]
        for e in (comp if i % 2 == 0 else []):
            for m in ch:
                tr.hit(b + e * beat / 2, pluck(hz(m), 0.6, 1.4), 0.07)
        for k in (0, 2):
            tr.hit(b + k * beat, bass(hz(ch[0] - 24 + (7 if k else 0)), beat * 1.5, 2.5), 0.35)
        for k in (0, 1.5, 3) if i % 2 == 0 else (1, 2.5):
            tr.hit(b + k * beat, rim, 0.12)
        for k in range(8):
            tr.hit(b + k * beat / 2, shaker, 0.045 if k % 2 else 0.025)
        b, i = b + bar, i + 1
    return tr.done(0.3, 1.4)


def marimba(seconds, key=0, seed=23, bpm=108):
    """Bright marimba riff, finger snaps, light kick. Upbeat, tidy, a bit playful."""
    tr, rng = Track(seconds), np.random.default_rng(seed)
    beat, prog = 60 / bpm, PROG["marimba"]
    bar = beat * 4
    snap = noise_hit(rng, 0.07, 60) + np.sin(2 * np.pi * 1300 * env(0.07)) * np.exp(-env(0.07) * 70) * 0.5
    riff = [0, 2, 1, 2, 0, 1, 2, 1] if seed % 3 else [0, 1, 2, 0, 2, 1, 0, 2]
    b, i = 0.0, 0
    while b < seconds:
        ch = [m + key for m in prog[i % 4]]
        for k, p in enumerate(riff):
            if k == 5 and i % 2:
                continue
            tr.hit(b + k * beat / 2, mallet(hz(ch[p] + 12)), 0.16)
        tr.hit(b, kick(0.8, 0.3), 0.6)
        tr.hit(b + 2 * beat, kick(0.8, 0.3), 0.5)
        tr.hit(b + beat, snap, 0.18)
        tr.hit(b + 3 * beat, snap, 0.18)
        tr.hit(b, bass(hz(ch[0] - 24), beat * 1.5, 2.5), 0.3)
        tr.hit(b + 2.5 * beat, bass(hz(ch[0] - 24), beat, 3), 0.25)
        b, i = b + bar, i + 1
    return tr.done(0.3, 1.4)


BEDS = {"lofi": lofi, "chillhop": chillhop, "acoustic": acoustic, "house": house,
        "ambient": ambient, "bossa": bossa, "marimba": marimba}
