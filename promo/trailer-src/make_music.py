#!/usr/bin/env python3
"""Synthesize the trailer soundtrack — boring open, excited reveal.

Narrative map (segment starts incl. 0.45s crossfades):
  0.00  beige PowerPoint     ── BORING: dull drone + clock ticks
  1.75  "every deck..."      ── still boring (drone sags lower)
  4.10  Harvard cover        ── WHOOSH -> groove starts, builds
 11.60  Body of Mine         ── full groove (arp joins)
 22.45  constellation map    ── percussion thins, pad blooms + sparkle
 28.55  CTA                  ── drums out, bell motif, pad resolves, fade
 33.15  end
"""
import numpy as np
import wave

SR = 44100
DUR = 33.15
N = int(SR * DUR)
t = np.arange(N) / SR
mix = np.zeros(N)

def env_exp(n, decay):
    return np.exp(-np.arange(n) / (SR * decay))

def add(sig, at, buf=mix):
    i = int(at * SR)
    j = min(N, i + len(sig))
    if i < N:
        buf[i:j] += sig[:j - i]

def sine(f, n, ph=0.0):
    return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)

# ── Section 1: boring (0 – 4.1s) ────────────────────────────────────────────
n1 = int(4.1 * SR)
wob = 0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t[:n1])          # tired wobble
drone = (sine(55, n1) + 0.6 * sine(55.7, n1) + 0.25 * sine(110, n1)) * (0.05 + 0.03 * wob)
drone *= np.linspace(1.0, 0.75, n1)                          # sagging
add(drone, 0)
rng = np.random.default_rng(7)
for k in range(4):                                           # clock ticks
    tick = rng.standard_normal(int(0.004 * SR)) * env_exp(int(0.004 * SR), 0.002) * 0.16
    add(tick, 0.55 + k * 1.0)

# ── Whoosh into the reveal (3.7 – 4.5s) ─────────────────────────────────────
wn = int(0.8 * SR)
noise = rng.standard_normal(wn)
bright = np.diff(noise, prepend=0)                           # high-passed noise
sweep = np.linspace(0, 1, wn) ** 2
whoosh = (noise * (1 - sweep) * 0.3 + bright * sweep * 0.5) * np.hanning(wn) * 0.4
add(whoosh, 3.7)

# ── Sections 2-4: the groove (4.5 – 28.55s) ─────────────────────────────────
BPM = 116
beat = 60 / BPM                  # 0.5172s
bar = 4 * beat
G0 = 4.5                         # groove start
G_END = 28.55                    # drums stop at CTA
# A-minor uplift: Am F C G, roots in Hz (A1=55, F1=43.65, C2=65.41, G1=49)
prog = [55.0, 43.65, 65.41, 49.0]
chords = [[220.0, 261.63, 329.63],      # Am
          [174.61, 220.0, 261.63],      # F
          [261.63, 329.63, 392.0],      # C
          [196.0, 246.94, 293.66]]      # G

def kick(n=int(0.16 * SR)):
    f = np.linspace(120, 48, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.05) * 0.85

def hat(n=int(0.04 * SR)):
    return np.diff(rng.standard_normal(n + 1)) * env_exp(n, 0.012) * 0.16

def pluck(f, n=int(0.22 * SR)):
    s = sine(f, n) + 0.45 * sine(2 * f, n) + 0.2 * sine(3 * f, n)
    return s * env_exp(n, 0.06) * 0.16

def bassnote(f, n=int(0.24 * SR)):
    s = sine(f, n) + 0.35 * sine(2 * f, n)
    return s * env_exp(n, 0.1) * 0.32

nbeats = int((G_END - G0) / beat)
for b in range(nbeats):
    at = G0 + b * beat
    bar_i = int(b // 4)
    chord_i = bar_i % 4
    build = min(1.0, 0.45 + bar_i * 0.06)                    # layers swell in
    in_map = at >= 22.45                                     # map section: thin out
    if not in_map or b % 2 == 0:
        add(kick() * (0.8 if in_map else 1.0) * build, at)
    if bar_i >= 1 and not in_map:                            # hats from bar 2
        add(hat(), at + beat / 2)
        if bar_i >= 3:
            add(hat() * 0.6, at + beat / 4)
    add(bassnote(prog[chord_i]) * build, at)                 # bass on beats
    if at >= 11.6:                                           # arp from Body of Mine
        ch = chords[chord_i]
        for s16 in range(2):
            note = ch[(b * 2 + s16) % 3] * (2 if (b + s16) % 4 == 3 else 1)
            amp = 0.55 if in_map else 1.0
            add(pluck(note) * amp * build, at + s16 * beat / 2)

# pad: slow chords under the groove, blooming in the map section
pn = int((DUR - G0) * SR)
pad = np.zeros(pn)
tp = np.arange(pn) / SR
for i in range(int((DUR - G0) / bar) + 1):
    ch = chords[i % 4]
    s, e = int(i * bar * SR), min(pn, int((i + 1) * bar * SR + SR // 4))
    if s >= pn:
        break
    seg = e - s
    a = np.minimum(np.arange(seg) / (0.6 * SR), 1.0) * np.minimum((seg - np.arange(seg)) / (0.5 * SR), 1.0)
    for f in ch:
        pad[s:e] += (sine(f, seg) + 0.5 * sine(f * 1.004, seg) + 0.5 * sine(f * 0.996, seg)) * a
pad_amp = np.interp(tp + G0, [G0, 11.6, 22.45, 28.55, DUR], [0.010, 0.020, 0.045, 0.05, 0.035])
add(pad * pad_amp, G0)

# ── CTA: bell motif + resolve (28.55 – end) ─────────────────────────────────
def bell(f, n=int(1.4 * SR)):
    return (sine(f, n) + 0.4 * sine(f * 2.76, n) * env_exp(n, 0.18)) * env_exp(n, 0.5) * 0.22

add(bell(880), 28.7)            # the deck's playBing register
add(bell(1108.7), 29.25)        # C#6 — major-third lift
add(bell(1318.5), 29.8)         # E6
add(bell(880) * 0.7, 31.2)

# ── Master: fade out, normalize, gentle soft-clip ───────────────────────────
fade = np.ones(N)
fo = int(1.6 * SR)
fade[-fo:] = np.linspace(1, 0, fo)
fi = int(0.15 * SR)
fade[:fi] = np.linspace(0, 1, fi)
mix *= fade
mix = np.tanh(mix * 1.4)
mix = mix / np.max(np.abs(mix)) * 0.84

# subtle width: delay one channel's high content slightly
right = np.roll(mix, int(0.0006 * SR))
stereo = np.stack([mix, 0.92 * right + 0.08 * mix], axis=1)
pcm = (stereo * 32767).astype(np.int16)
with wave.open("/tmp/sd-trailer/trailer-music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote trailer-music.wav — {DUR}s")
