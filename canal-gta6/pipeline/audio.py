"""Música synthwave original generada por código + efectos + mezcla con ducking."""
import numpy as np
from scipy.signal import lfilter, butter, resample_poly

SR = 48000
rng = np.random.default_rng(7)


def _lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "low")
    return lfilter(b, a, x)


def _hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high")
    return lfilter(b, a, x)


def _saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0, detune):
        ph = (t * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / 3


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
    return e


NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)

# Progresiones (raíces MIDI y acordes) por estilo
STYLES = {
    "sunset": dict(bpm=100, prog=[(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]),  # Am F C G
    "night":  dict(bpm=94,  prog=[(52, [52, 55, 59]), (48, [48, 52, 55]), (50, [50, 54, 57]), (47, [47, 50, 54])]),  # Em C D Bm
    "ocean":  dict(bpm=98,  prog=[(50, [50, 53, 57]), (46, [46, 50, 53]), (53, [53, 57, 60]), (48, [48, 52, 55])]),  # Dm Bb F C
    "money":  dict(bpm=104, prog=[(55, [55, 58, 62]), (51, [51, 55, 58]), (53, [53, 57, 60]), (50, [50, 53, 57])]),  # Gm Eb F Dm
    "alert":  dict(bpm=108, prog=[(52, [52, 55, 59]), (52, [52, 55, 59]), (48, [48, 52, 55]), (50, [50, 54, 57])]),  # Em Em C D
}


def music_loop(style="sunset"):
    st = STYLES[style]
    beat = 60 / st["bpm"]
    bar = 4 * beat
    nbar = int(bar * SR)
    total = nbar * 8
    mix = np.zeros(total)
    # kick
    kn = int(0.35 * SR)
    tk = np.arange(kn) / SR
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 9)
    # snare / clap
    sn = int(0.25 * SR)
    snare = _hp(rng.standard_normal(sn), 1200) * _env(sn, 0.001, 0.06) * 0.5
    # hat
    hn = int(0.06 * SR)
    hat = _hp(rng.standard_normal(hn), 7000) * _env(hn, 0.0005, 0.015) * 0.25
    for b in range(8 * 4):
        p = int(b * beat * SR)
        mix[p:p + kn] += kick[: total - p] * 0.9
        if b % 2 == 1:
            mix[p:p + sn] += snare[: total - p]
        for h in (0, 0.5):
            q = int((b + h) * beat * SR)
            mix[q:q + hn] += hat[: total - q] * (1.0 if h else 0.6)
    # bajo en corcheas + pad
    for i in range(8):
        root, chord = st["prog"][i % 4]
        p0 = i * nbar
        en = int(beat / 2 * SR)
        for k in range(8):
            f = NOTE(root - 12 + (12 if k % 4 == 3 else 0))
            seg = _saw(f, en, 0.003) * _env(en, 0.003, 0.12)
            q = p0 + k * en
            mix[q:q + en] += _lp(seg, 900) * 0.45
        pad = sum(_saw(NOTE(m), nbar, 0.006) for m in chord) / 3
        att = np.minimum(1, np.arange(nbar) / (0.4 * SR)) * np.minimum(1, (nbar - np.arange(nbar)) / (0.2 * SR))
        mix[p0:p0 + nbar] += _lp(pad, 1800) * att * 0.30
        # arpegio brillante
        an = int(beat / 4 * SR)
        notes = chord + [chord[1] + 12]
        for k in range(16):
            f = NOTE(notes[k % 4] + 12)
            t = np.arange(an) / SR
            seg = (np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t)) * _env(an, 0.002, 0.05)
            q = p0 + k * an
            mix[q:q + an] += _lp(seg, 3000) * 0.10
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.8
    return mix


def music_bed(duration, style):
    loop = music_loop(style)
    n = int(duration * SR)
    reps = n // len(loop) + 1
    m = np.tile(loop, reps)[:n]
    fade_in = np.minimum(1, np.arange(n) / (0.8 * SR))
    fade_out = np.minimum(1, (n - np.arange(n)) / (2.5 * SR))
    return m * fade_in * fade_out


def whoosh():
    n = int(0.45 * SR)
    x = rng.standard_normal(n)
    t = np.arange(n) / n
    out = np.zeros(n)
    # barrido de filtro por bloques
    blk = 1024
    for i in range(0, n, blk):
        fc = 400 + 5000 * np.sin(np.pi * min(1, i / n)) ** 2
        out[i:i + blk] = _lp(x[i:i + blk], fc, 1)
    env = np.sin(np.pi * t) ** 2
    return out * env * 0.35


def pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 3000 * t) * t) * np.exp(-t * 45) * 0.25


def to_sr(x, sr_in):
    if sr_in == SR:
        return x
    from math import gcd
    g = gcd(SR, sr_in)
    return resample_poly(x, SR // g, sr_in // g)


def mix(voice, duration, style, whoosh_at=(), pop_at=()):
    """voice: array a SR. Devuelve estéreo float32."""
    n = int(duration * SR)
    v = np.zeros(n)
    v[: min(n, len(voice))] = voice[:n]
    m = music_bed(duration, style)
    # ducking: envolvente de la voz suavizada
    env = np.abs(v)
    k = int(0.25 * SR)
    c = np.concatenate([[0], np.cumsum(env)])
    idx = np.arange(n)
    lo = np.clip(idx - k // 2, 0, n)
    hi = np.clip(idx + k // 2, 0, n)
    env = (c[hi] - c[lo]) / k
    env = np.clip(env / 0.05, 0, 1)
    gain = 0.22 - 0.13 * env  # 0.22 sin voz, 0.09 con voz
    out = v * 1.0 + m * gain
    w = whoosh()
    for t in whoosh_at:
        p = int(t * SR) - len(w) // 2
        if 0 <= p < n - len(w):
            out[p:p + len(w)] += w
    pp = pop()
    for t in pop_at:
        p = int(t * SR)
        if 0 <= p < n - len(pp):
            out[p:p + len(pp)] += pp
    out = out / max(1.0, np.abs(out).max() / 0.95)
    st = np.stack([out, out], 1).astype(np.float32)
    return st
