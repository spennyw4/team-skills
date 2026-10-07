"""Synthesizes the 15s, 128 BPM soundtrack for the reel. Pure numpy → showreel_audio.wav"""
import wave
import numpy as np

SR, DUR = 48000, 15.0
B = 60 / 128
BAR = 4 * B
N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N)
R = np.zeros(N)
duck = np.ones(N)


def idx(t):
    return int(round(t * SR))


def lp(x, fc):
    """One-pole lowpass; fc may be scalar or per-sample array."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s)
        y[i] = s
    return y


def hp(x, fc):
    return x - lp(x, fc)


def add(sig, t, gain=1.0, pan=0.0):
    i = idx(t)
    if i >= N:
        return
    sig = sig[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * l * 1.414
    R[i:i + len(sig)] += sig * gain * r * 1.414


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def tt(sec):
    return np.arange(int(sec * SR)) / SR


# ── instruments ─────────────────────────────────────────────────────────────
def kick(big=False):
    t = tt(1.4 if big else 0.5)
    f = 42 + 140 * np.exp(-t * 30) + (40 * np.exp(-t * 6) if big else 0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / (0.55 if big else 0.22))
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.4
    return np.tanh(2.2 * (body + click))


def clap():
    t = tt(0.35)
    n = hp(rng.standard_normal(len(t)), 900)
    e = sum(np.exp(-np.maximum(0, t - o) * 140) * (t >= o) for o in (0, 0.011, 0.022))
    e = e + 0.6 * np.exp(-np.maximum(0, t - 0.03) * 22) * (t >= 0.03)
    return lp(n * e, 6000) * 0.8


def hat(open_=False):
    t = tt(0.25 if open_ else 0.06)
    n = hp(hp(rng.standard_normal(len(t)), 7000), 7000)
    return n * np.exp(-t / (0.07 if open_ else 0.015))


def crash(d=1.6):
    t = tt(d)
    n = hp(rng.standard_normal(len(t)), 3000)
    return n * np.exp(-t / (d / 4)) * 0.6


def boom(d=2.5):
    t = tt(d)
    f = 30 + 60 * np.exp(-t * 8)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d / 3))


def whoosh(d, f0, f1, rev=False):
    t = tt(d)
    n = rng.standard_normal(len(t))
    fc = f0 * (f1 / f0) ** (t / d)
    s = lp(hp(n, fc * 0.3), fc)
    e = (t / d) ** 2 if not rev else np.exp(-t / (d / 3))
    return s * e / (np.abs(s).max() + 1e-9)


def saw(freq, sec, detune=0.0):
    t = tt(sec)
    out = 0
    for dt in (-detune, 0, detune):
        ph = (t * freq * (1 + dt)) % 1
        out = out + (2 * ph - 1)
    return out / 3


def blip(freq, sec=0.08):
    t = tt(sec)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t / (sec / 4))


def mx(*sigs):
    out = np.zeros(max(len(x) for x in sigs))
    for x in sigs:
        out[:len(x)] += x
    return out


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


# ── arrangement ─────────────────────────────────────────────────────────────
# Bar 1 (intro): pop, line zip, slit impact
add(mx(blip(880, 0.15), blip(1760, 0.1) * 0.4), 0.03, 0.35)
add(whoosh(0.45, 400, 9000), 0.47, 0.25, -0.3)
add(kick(), 0.94, 0.9); add(crash(1.2), 0.94, 0.35); add(boom(1.2), 0.94, 0.5)
add(kick(), 0.94 + B, 0.6)
add(whoosh(0.4, 300, 6000), BAR - 0.4, 0.3, 0.3)

# Drums bars 2-7
for bar in range(1, 7):
    for b in range(4):
        t = bar * BAR + b * B
        if not (bar == 6 and b == 3):
            add(kick(), t, 0.95)
            duck[idx(t):idx(t) + int(0.25 * SR)] = np.minimum(duck[idx(t):idx(t) + int(0.25 * SR)], 1 - 0.75 * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.09))
        if b in (1, 3) and bar < 6:
            add(clap(), t, 0.5)
        add(hat(open_=(b == 3)), t + B / 2, 0.16 if b != 3 else 0.1, 0.4)
        for s in (1, 3):
            add(hat(), t + s * B / 4, 0.06, -0.4)

# bar-start impacts
for bar in range(1, 7):
    add(crash(1.0), bar * BAR, 0.22)
    add(whoosh(0.35, 250, 8000), (bar + 1) * BAR - 0.35, 0.22, 0.2 * (-1) ** bar)

# Bar 2 type slams: extra pitched hits per word
for b in range(4):
    add(blip(note(77 + [0, 3, 7, 12][b]), 0.12), BAR + b * B, 0.18)

# Bar 3 grid pops: a cascade of plucks
for j in range(16):
    add(blip(note(72 + [0, 3, 7, 10, 12, 15][j % 6]), 0.06), 2 * BAR + j * B / 4, 0.09, (j % 4 - 1.5) / 2)

# Bar 4 particle burst + sparkle arp
add(whoosh(1.0, 9000, 300, rev=True), 3 * BAR, 0.35)
for j in range(16):
    add(blip(note(84 + [0, 7, 3, 10, 12, 7, 15, 10][j % 8]), 0.1), 3 * BAR + j * B / 4, 0.08, 0.6 * np.sin(j))

# Bar 5 fluid: wet, low "bloop"s
for j in range(8):
    t = tt(0.25)
    f = 300 + 500 * np.exp(-t * 25)
    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.06), 4 * BAR + j * B / 2 + 0.02, 0.18, 0.5 * (-1) ** j)

# Bar 6 editorial: a snare/tom on every half-beat word, glitch stutter, stripe swish
for j in range(6):
    add(mx(clap() * 0.8, blip(note(60 + [0, 7, 0, 10, 0, 12][j]), 0.1) * 0.8), 5 * BAR + j * B / 2, 0.45)
for j in range(8):
    if j % 3 != 2:
        add(mx(hp(rng.standard_normal(int(0.025 * SR)), 2000) * 0.7, blip(2000 + 900 * j, 0.025)), 5 * BAR + 3 * B + j * B / 16, 0.25, (-1) ** j * 0.6)
add(whoosh(0.23, 500, 12000), 5 * BAR + 3.5 * B, 0.3)

# Bar 7 build: snare roll + riser, kicks on beats (already), cut before drop
roll_t = 6 * BAR
for k, step in ((0, B / 2), (2, B / 4), (3, B / 8)):
    for j in range(int(B / step)):
        t = roll_t + k * B + j * step
        add(clap() * 0.7, t, 0.18 + 0.25 * (t - roll_t) / BAR)
for j in range(4):
    add(clap() * 0.7, roll_t + B + j * B / 4, 0.25)
t = tt(BAR - 0.1)
rise = lp(rng.standard_normal(len(t)), 300 * (40 ** (t / t[-1])))
add(rise / np.abs(rise).max() * (t / t[-1]) ** 2, 6 * BAR, 0.4)
sweep = np.sin(2 * np.pi * np.cumsum(200 * 6 ** (t / t[-1])) / SR) * (t / t[-1]) ** 2
add(sweep, 6 * BAR, 0.12)

# Bar 8 drop: everything at once, then a long tail
D = 7 * BAR
add(kick(big=True), D, 1.0); add(boom(2.0), D, 0.9); add(crash(2.0), D, 0.5)
for m, pan in ((53, -0.5), (60, 0.5), (63, -0.3), (67, 0.3), (72, 0.0)):
    s = saw(note(m), DUR - D, 0.004)
    s = lp(s, 2500 * np.exp(-tt(DUR - D) * 1.5) + 200) * np.exp(-tt(DUR - D) / 1.1)
    add(s, D, 0.12, pan)
for j in range(9):
    add(blip(note(84 + [0, 3, 7, 10, 12, 15, 19, 22, 24][j]), 0.18), D + 0.25 + j * 0.06, 0.08 * (1 - j / 12), (j - 4) / 5)

# ── bass + pad, bars 2–7 (sidechained) ──────────────────────────────────────
roots = [53, 49, 56, 51, 53, 48]          # F, Db, Ab, Eb, F, C
chords = [[65, 68, 72, 75], [61, 65, 68, 72], [68, 72, 75, 79], [63, 67, 70, 74], [65, 68, 72, 77], [60, 64, 67, 70]]
music_L, music_R = np.zeros(N), np.zeros(N)
for bi in range(6):
    t0 = (bi + 1) * BAR
    for e8 in range(8):
        if e8 % 2 == 0:
            continue
        n = saw(note(roots[bi] - 12), B / 2 * 0.95)
        n = lp(n, 900 * np.exp(-tt(B / 2 * 0.95) * 10) + 120) * env(len(n), 0.003, 0.12)
        i = idx(t0 + e8 * B / 2)
        music_L[i:i + len(n)] += n * 0.55; music_R[i:i + len(n)] += n * 0.55
    sub_n = np.sin(2 * np.pi * note(roots[bi] - 24) * tt(BAR)) * 0.35
    i = idx(t0); music_L[i:i + len(sub_n)] += sub_n; music_R[i:i + len(sub_n)] += sub_n
    for k, m in enumerate(chords[bi]):
        p = lp(saw(note(m), BAR, 0.006), 1400) * 0.07
        p *= np.minimum(1, tt(BAR) / 0.05) * np.minimum(1, (BAR - tt(BAR)) / 0.05)
        (music_L if k % 2 else music_R)[i:i + len(p)] += p
        (music_R if k % 2 else music_L)[i:i + len(p)] += p * 0.5
L += music_L * duck
R += music_R * duck

# ── cheap stereo reverb send on the whole mix ───────────────────────────────
ir_t = tt(1.4)
for ch in (L, R):
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.35)
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    wet = np.fft.irfft(np.fft.rfft(hp(ch, 300), 2 ** 21) * np.fft.rfft(ir, 2 ** 21))[:N]
    ch += wet * 0.22

# ── master: glue, soft clip, fades, normalize ───────────────────────────────
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.1)
fade = np.ones(N); fi = idx(0.01); fo = idx(0.35)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix *= 0.89 / np.abs(mix).max()
pcm = (mix * 32767).astype('<i2')
with wave.open('showreel_audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', mix.shape)
