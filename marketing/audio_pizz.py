"""Sneaky pizzicato + bassoon theme for the 엄마 몰래 폰겜 reel -> out/music.wav.
It tiptoes at 100 bpm, freezes on every smack, and plays a comic 'gotcha' sting."""
import json, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'out', 'events.json'))); DUR, EV = data['duration'], data['events']
SR = 44100; N = int(SR * (DUR + .6)); rng = np.random.default_rng(2); noise = rng.uniform(-1, 1, SR)
mtof = lambda n: 440.0 * 2 ** ((n - 69) / 12)
at = lambda n, d=DUR: next((e[1] for e in EV if e[0] == n), d)
music = np.zeros(N); sfx = np.zeros(N)
def add(buf, t, s, g=1.):
    i = int(t * SR)
    if i >= N or i + len(s) <= 0: return
    a, b = max(0, i), min(N, i + len(s)); buf[a:b] += s[a - i:b - i] * g
def env(n, a=.003, d=.1, sus=0.):
    t = np.arange(n) / SR; e = np.minimum(1, t / a) * (sus + (1 - sus) * np.exp(-t / d)); r = min(n, int(.02 * SR)); e[-r:] *= np.linspace(1, 0, r); return e
def osc(kind, f, n, f2=None):
    t = np.arange(n) / SR; fr = np.full(n, f) if f2 is None else f * (f2 / f) ** (t / (n / SR)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return {'sine': np.sin(ph), 'saw': (ph / np.pi) % 2 - 1, 'tri': 2 / np.pi * np.arcsin(np.sin(ph)), 'sq': np.sign(np.sin(ph))}[kind]
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); acc = 0.
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y
def pizz(t, note, g=1.):   # plucked string: bright attack, quick decay
    n = int(.35 * SR); f = mtof(note); tt = np.arange(n) / SR
    s = (osc('tri', f, n) * .8 + osc('saw', f, n) * .25 * np.exp(-tt / .02)) * env(n, .002, .09)
    add(music, t, s, .22 * g)
def bassoon(t, note, d):
    n = int(d * SR); s = lp(osc('saw', mtof(note), n) + osc('sq', mtof(note) * .5, n) * .3, 700) * env(n, .02, d * .6, .6)
    add(music, t, s, .2)
BPM = 100; B = 60 / BPM; E = B / 2
MEL = [57, None, 60, None, 64, 63, 64, None, 57, None, 60, None, 65, 64, 62, None, 55, None, 59, None, 62, 61, 62, None, 55, None, 59, 62, 64, 62, 60, None]
BASS = [45, 45, 40, 40, 43, 43, 40, 45]
stops = [e[1] for e in EV if e[0] in ('smack', 'over')]
def silent(t): return any(s <= t < s + 1.2 for s in stops)
t, k = 0., 0
T_END = at('endcard')
while t < DUR + .3:
    tt = t if t < T_END else t
    if not silent(t):
        n = MEL[k % 32]
        if n: pizz(t, n + (12 if t >= T_END else 0))
        if k % 4 == 0: bassoon(t, BASS[(k // 4) % 8], B * 1.6)
        if k % 2 == 1: add(music, t, (noise[:800] - lp(noise[:800], 5000)) * env(800, .001, .01), .05)   # brushed tick
    k += 1; t += E
# sfx
def blip(t, f, d, g, kind='sine', f2=None): n = int(d * SR); add(sfx, t, osc(kind, f, n, f2) * env(n, .002, d / 3), g)
for name, t in EV:
    if name == 'press': blip(t, 1400, .04, .08, 'sq')
    if name == 'release': blip(t, 700, .05, .08, 'tri')
    if name == 'warn': blip(t, 1200, .08, .1, 'sq'); blip(t + .12, 1200, .08, .1, 'sq')
    if name == 'safe': [blip(t + i * .06, f, .2, .12) for i, f in enumerate([988, 1319, 1568])]
    if name == 'snitch': blip(t, 700, .14, .16, 'tri', 950); blip(t + .16, 950, .22, .16, 'tri', 650)
    if name == 'cut': n = int(.12 * SR); add(sfx, t, (noise[:n] - lp(noise[:n], 1500)) * np.sin(np.linspace(0, np.pi, n)), .25)
    if name == 'smack':
        n = int(.12 * SR); add(sfx, t, (noise[:n] - lp(noise[:n], 900)) * env(n, .001, .03), 1.0)   # the slap
        blip(t, 140, .3, .5, 'sine', 50)
        for i, nt in enumerate([72, 71, 70]): blip(t + .25 + i * .14, mtof(nt), .16, .1, 'sq')         # "gotcha" sting
    if name == 'over':
        for dt, nt, d in [(.2, 62, .4), (.65, 61, .4), (1.1, 60, .4), (1.55, 59, .9)]:
            n = int(d * SR); add(sfx, t + dt, lp(osc('saw', mtof(nt - 12), n), 900) * env(n, .03, d * .9, .6), .3)
mix = music + sfx
mix = mix / (np.percentile(np.abs(mix), 99.5) + 1e-9) * .8; mix = np.tanh(mix * 1.3) / np.tanh(1.3) * .92
f = int(.5 * SR); mix[-f:] *= np.linspace(1, 0, f)
d = int(.012 * SR); st = np.clip(np.stack([mix + np.concatenate([np.zeros(d), music[:-d]]) * .1, mix], 1), -1, 1)
with wave.open(os.path.join(HERE, 'out', 'music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('music.wav', round(N / SR, 2))
