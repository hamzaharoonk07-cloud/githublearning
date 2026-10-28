"""Synthesizes the launch film's sound effects from cues.json (written by render.mjs).

No music and no samples: every sound is built here from noise, sine sweeps and filters.
    python3 sfx.py  ->  sfx.wav (48 kHz stereo)
"""
import json
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
rng = np.random.default_rng(11)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def filt(x, kind, f):
    sos = butter(2, f, btype=kind, fs=SR, output='sos')
    return sosfilt(sos, x)


def decay(dur, tau, attack=.002):
    t = t_axis(dur)
    return np.minimum(t / attack, 1) * np.exp(-t / tau)


def sweep(f0, f1, dur, curve='exp'):
    """Sine whose pitch glides f0 -> f1."""
    t = t_axis(dur)
    k = t / dur
    f = f0 * (f1 / f0) ** k if curve == 'exp' else f0 + (f1 - f0) * k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def svf_bandpass(x, freqs, q=1.2):
    """Bandpass with a cutoff that moves every sample (for whooshes and risers)."""
    y = np.zeros_like(x)
    low = band = 0.0
    damp = 1 / q
    for i in range(len(x)):
        f = 2 * np.sin(np.pi * min(freqs[i], SR / 6) / SR)
        high = x[i] - low - damp * band
        band += f * high
        low += f * band
        y[i] = band
    return y


def bell(n, peak=.55, sharp=2.0):
    k = np.linspace(0, 1, n)
    up = (k / peak) ** sharp
    down = ((1 - k) / (1 - peak)) ** (sharp * .8)
    return np.where(k < peak, up, down)


def stereo(x, pan=0.0, width=0.0):
    """Equal-power pan; `pan` may be an array to move the sound across the field."""
    pan = np.clip(pan, -1, 1)
    a = (pan + 1) * np.pi / 4
    left, right = x * np.cos(a), x * np.sin(a)
    if width:  # tiny decorrelation so wide sounds don't sit dead centre
        d = int(.004 * SR)
        right = (1 - width) * right + width * np.concatenate([np.zeros(d), right[:-d]])
    return np.stack([left, right], 1)


# ───────── sounds ─────────
def whoosh(dur=.6, pan=0.0, big=0, **_):
    n = int(dur * SR)
    env = bell(n, .62, 2.2)
    freqs = 250 + 3200 * env ** 1.4
    body = svf_bandpass(noise(dur), freqs, q=1.6) * env
    air = filt(noise(dur), 'highpass', 4000) * env ** 2 * .25
    x = body * 1.4 + air
    if big:
        x += filt(noise(dur), 'lowpass', 160) * env * 2.6
    p = np.linspace(-pan, pan, n)
    return stereo(x, p, .3)


def swish(pitch=1.0, **_):
    dur = .26
    n = int(dur * SR)
    env = bell(n, .45, 1.8)
    x = svf_bandpass(noise(dur), (1200 + 4500 * env) * pitch, q=2.2) * env
    return stereo(x * 1.2, np.linspace(-.3, .3, n), .3)


def thud(pitch=1.0, **_):
    dur = .5
    body = sweep(120 * pitch, 42 * pitch, dur) * decay(dur, .12)
    click = filt(noise(dur), 'lowpass', 2500) * decay(dur, .006)
    return stereo(body * 1.1 + click * .5)


def snap(pitch=1.0, pan=0.0, **_):
    dur = .12
    crack = filt(noise(dur), 'highpass', 1800) * decay(dur, .007, .0005)
    tone = sweep(2000 * pitch, 900 * pitch, dur) * decay(dur, .018)
    knock = sweep(420 * pitch, 260 * pitch, dur) * decay(dur, .03)
    return stereo(crack * .9 + tone * .35 + knock * .5, pan)


def tick(pitch=1.0, **_):
    dur = .05
    x = np.sin(2 * np.pi * 2600 * pitch * t_axis(dur)) * decay(dur, .006, .0005)
    x += filt(noise(dur), 'highpass', 5000) * decay(dur, .002, .0003) * .5
    return stereo(x, 0, .2)


def tap(pitch=1.0, **_):
    dur = .08
    x = filt(noise(dur), 'bandpass', [1500, 6000]) * decay(dur, .003, .0003)
    x += np.sin(2 * np.pi * 1150 * pitch * t_axis(dur)) * decay(dur, .012) * .6
    x += sweep(300, 160, dur) * decay(dur, .02) * .5
    return stereo(x)


def pop(pitch=1.0, **_):
    dur = .14
    x = sweep(820 * pitch, 260 * pitch, dur) * decay(dur, .035, .001)
    x += filt(noise(dur), 'highpass', 3000) * decay(dur, .002, .0003) * .3
    return stereo(x)


def check(pitch=1.0, **_):
    dur = .22
    chirp = sweep(780 * pitch, 1500 * pitch, dur) * decay(dur, .05, .002)
    return stereo(chirp * .7) + pad(tick(pitch * 1.1), len(chirp)) * .6


def stamp(pitch=1.0, pan=0.0, **_):
    dur = .35
    body = sweep(190 * pitch, 70 * pitch, dur) * decay(dur, .07)
    slap = filt(noise(dur), 'bandpass', [300, 2500]) * decay(dur, .025, .0008)
    paper = filt(noise(dur), 'highpass', 3500) * decay(dur, .01, .0005)
    return stereo(body + slap * .9 + paper * .35, pan, .2)


def hit(pitch=1.0, **_):
    dur = .45
    body = sweep(150 * pitch, 55 * pitch, dur) * decay(dur, .09)
    crack = filt(noise(dur), 'bandpass', [500, 5000]) * decay(dur, .015, .0005)
    return stereo(body * 1.1 + crack * .6, 0, .2)


def impact(pitch=1.0, big=0, **_):
    dur = 1.6 if big else 1.0
    sub = sweep(85 * pitch, 32 * pitch, dur) * decay(dur, .32 if big else .2)
    crack = filt(noise(dur), 'lowpass', 4000) * decay(dur, .03, .0008)
    rumble = filt(noise(dur), 'lowpass', 220) * decay(dur, .35 if big else .2) * 1.5
    return stereo(sub * 1.3 + crack * .8 + rumble, 0, .4)


def boom(**_):
    dur = 2.4
    sub = sweep(62, 30, dur) * decay(dur, .7, .004)
    rumble = filt(noise(dur), 'lowpass', 180) * decay(dur, .6, .01) * 1.8
    crack = filt(noise(dur), 'bandpass', [200, 3000]) * decay(dur, .04, .001) * .7
    return stereo(sub * 1.3 + rumble + crack, 0, .5)


def suck(**_):
    dur = .22
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    x = svf_bandpass(noise(dur), 400 + 5000 * k ** 2, q=2) * k ** 3
    return stereo(x * 1.4, 0, .3)


def riser_short(**_):
    dur = .22
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    x = svf_bandpass(noise(dur), 800 + 6000 * k ** 2, q=3) * k ** 2
    return stereo(x, 0, .3)


def riser(dur=1.4, **_):
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    x = svf_bandpass(noise(dur), 300 * (25 ** k), q=2.5) * k ** 1.6
    # a fluttering "processing" texture that speeds up towards the end
    flutter = .6 + .4 * np.sin(2 * np.pi * np.cumsum(6 + 30 * k ** 2) / SR)
    tone = sweep(160, 900, dur) * k ** 2 * .18
    return stereo(x * flutter * 1.2 + tone, np.sin(k * 9) * .3 * k, .3)


def slice_(**_):
    dur = .9
    t = t_axis(dur)
    metal = sum(np.sin(2 * np.pi * f * (1 - .02 * t) * t + i) * np.exp(-t / (.25 + i * .04)) / (i + 1.5)
                for i, f in enumerate([2870, 4130, 5310, 6720, 8190]))
    zip_ = svf_bandpass(noise(dur), 9000 * np.exp(-t / .05) + 1500, q=2) * decay(dur, .06, .001)
    return stereo(metal * .9 + zip_ * 1.2, np.linspace(-.6, .6, len(t)), .4)


def crumble(**_):
    dur = .8
    out = np.zeros((int(dur * SR), 2))
    fall = filt(noise(dur), 'lowpass', 900) * bell(int(dur * SR), .3, 1.5) * .4
    out += stereo(fall, 0, .3)
    for i in range(14):
        at = int((i / 14) ** 1.3 * .6 * SR)
        s = stamp(pitch=.8 + rng.random() * .9, pan=rng.uniform(-.7, .7)) * (.35 - i * .018)
        s = s[:len(out) - at]
        out[at:at + len(s)] += s
    return out


def shimmer(**_):
    dur = .9
    t = t_axis(dur)
    env = bell(len(t), .25, 1.4)
    x = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * (.5 + .5 * np.sin(2 * np.pi * (7 + i * 3) * t))
            for i, f in enumerate([3520, 4710, 5930, 7040, 8380]))
    x = x / 5 + filt(noise(dur), 'highpass', 7000) * .5
    return stereo(x * env, np.sin(t * 9) * .5, .4)


def success(**_):
    def strike(f0, dur=1.3):
        t = t_axis(dur)
        return sum(np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / (.45 / (j + 1))) * a
                   for j, (r, a) in enumerate([(1, 1), (2.76, .45), (5.4, .2)]))
    a = strike(1318.5)
    b = strike(1975.5)
    off = int(.09 * SR)
    x = np.zeros(len(a) + off)
    x[:len(a)] += a
    x[off:] += b * .9
    return stereo(x * .45, 0, .4)


def burst(**_):
    dur = .9
    out = np.zeros((int(dur * SR), 2))
    out[:int(.2 * SR)] += stereo(filt(noise(.2), 'bandpass', [400, 6000]) * decay(.2, .02, .0005))
    for _ in range(26):
        at = int(rng.random() ** 1.6 * .7 * SR)
        s = tick(pitch=.6 + rng.random() * 1.2) * stereo(np.ones(1), rng.uniform(-.9, .9))[0] * 2 * rng.uniform(.2, .5)
        out[at:at + len(s)] += s[:len(out) - at]
    return out


def pad(x, n):
    out = np.zeros((n, 2))
    out[:min(n, len(x))] = x[:n]
    return out


SOUNDS = {
    'whoosh': whoosh, 'swish': swish, 'thud': thud, 'snap': snap, 'tick': tick, 'tap': tap, 'pop': pop,
    'check': check, 'stamp': stamp, 'hit': hit, 'impact': impact, 'boom': boom, 'suck': suck,
    'riserShort': riser_short, 'riser': riser, 'slice': slice_, 'crumble': crumble, 'shimmer': shimmer,
    'success': success, 'burst': burst,
}


def main():
    spec = json.load(open('cues.json'))
    dry = np.zeros((int((spec['duration'] + 3) * SR), 2))
    for c in spec['cues']:
        opts = {k: v for k, v in c.items() if k not in ('t', 'type', 'gain')}
        s = SOUNDS[c['type']](**opts) * c.get('gain', 1)
        at = int(c['t'] * SR)
        dry[at:at + len(s)] += s[:len(dry) - at]

    # small-room reverb so the hits sit in one space
    ir_t = t_axis(1.1)
    ir = np.stack([filt(noise(1.1), 'lowpass', 5000) * np.exp(-ir_t / .28) for _ in range(2)], 1)
    ir /= np.abs(ir).sum(0).max() / 6
    wet = np.stack([fftconvolve(dry[:, i], ir[:, i])[:len(dry)] for i in range(2)], 1)
    mix = filt(dry + wet * .22, 'highpass', 28)  # clear DC / sub rumble below hearing

    mix /= np.abs(mix).max()
    mix = np.tanh(mix * 1.6) / np.tanh(1.6)  # gentle saturation keeps transients punchy
    mix *= 10 ** (-1 / 20)
    n = int(spec['duration'] * SR)
    mix = mix[:n]
    fade = int(.5 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]

    with wave.open('sfx.wav', 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())


if __name__ == '__main__':
    main()
