"""One repeated NR short-preamble useful symbol in a 15.36 MS/s CC."""
import numpy as np

FS = 15_360_000
DEC = 4
OFFSET = FS / 4
SHIFT = 37  # delay in output samples
N = 1024
ROOT = 25
CASES = ("tone", "reference", "shifted", "noise")
# Bounds chosen before board measurements.
LIMITS = dict(count=1024, clocks=64, dc_hz=3750, tone_coherence=0.98,
              shift_error=1, detection=0.75, noise_max=0.35, psl_error_db=5.0)


def symbol(size):
    k = np.arange(139)
    zc = np.exp(-1j * np.pi * ROOT * k * (k + 1) / 139)
    bins = np.zeros(size, complex)
    bins[(k - 69) % size] = np.fft.fft(zc) / np.sqrt(139)
    return np.fft.ifft(bins) * size / np.sqrt(139)


def stimulus(case):
    rng = np.random.default_rng(2700 + CASES.index(case))
    data = np.zeros(N, complex)
    if case == "tone":
        data[:] = 5000
    elif case in ("reference", "shifted"):
        data = 4500 * np.roll(symbol(N), DEC * SHIFT if case == "shifted" else 0)
    data *= np.exp(2j * np.pi * OFFSET / FS * np.arange(N))
    data += 500 * (rng.normal(size=N) + 1j * rng.normal(size=N))
    i = np.rint(data.real).astype(np.int16).view(np.uint16).astype(np.uint32)
    q = np.rint(data.imag).astype(np.int16).view(np.uint16).astype(np.uint32)
    return i | (q << 16)


def unpack(words):
    return (words.astype(np.int16).astype(float)
            + 1j * (words >> 16).astype(np.int16).astype(float))


def predicted(words):
    # Unity passband, ideal anti-alias cutoff and PG391 4x group delay.
    mixed = unpack(words) * np.exp(-2j * np.pi * OFFSET / FS * np.arange(N))
    f = np.fft.fftfreq(N)
    transfer = (abs(f) < 0.5 / DEC) * np.exp(-2j * np.pi * f * (4.25 * DEC))
    return np.fft.ifft(np.fft.fft(mixed) * transfer)[::DEC]


def correlation(y):
    ref = symbol(N // DEC)
    periods = np.asarray(y).reshape(-1, len(ref))
    denominator = np.linalg.norm(ref) * np.linalg.norm(periods, axis=1)
    corr = np.abs(np.fft.ifft(np.fft.fft(periods) * np.fft.fft(ref).conj()))
    corr = np.mean(corr / np.maximum(denominator[:, None], 1e-15), axis=0)
    lag = int(corr.argmax())
    distance = (np.arange(len(ref)) - lag + 128) % 256 - 128
    psl = 20 * np.log10(max(corr[lag], 1e-15) / max(corr[abs(distance) > 3].max(), 1e-15))
    return lag, float(corr[lag]), float(psl), corr


def analyze(vectors, captures, status_counts):
    rows = []
    def check(name, measured, expected, passed):
        rows.append(dict(test=name, measured=measured, predicted=expected, passed=bool(passed)))
    for case, words in captures.items():
        ticks = ((words >> 32) & 0x3fffff).astype(int)
        stride = np.diff(ticks)
        check(case + " count", status_counts[case], 1024, status_counts[case] == LIMITS["count"])
        check(case + " clocks/sample", [int(stride.min()), int(stride.max())], 64,
              np.all(stride == LIMITS["clocks"]))
        check(case + " RCID/antenna", int(np.max((words >> 54) & 255)), 0,
              np.all(((words >> 54) & 255) == 0))
    tone = unpack(captures["tone"])
    coherence = float(abs(tone.mean()) / max(np.sqrt(np.mean(abs(tone)**2)), 1e-15))
    frequency = float(np.angle(np.vdot(tone[:-1], tone[1:])) * FS / DEC / (2*np.pi))
    check("tone residual Hz", frequency, 0, abs(frequency) <= LIMITS["dc_hz"])
    check("tone DC coherence", coherence, 1, coherence >= LIMITS["tone_coherence"])
    results = {c: correlation(unpack(captures[c])) for c in CASES[1:]}
    models = {c: correlation(predicted(vectors[c])) for c in CASES[1:]}
    shift = (results["shifted"][0] - results["reference"][0]) % 256
    check("preamble delay relative to reference", shift, SHIFT, abs(shift - SHIFT) <= LIMITS["shift_error"])
    for case in CASES[1:3]:
        _, peak, psl, _ = results[case]
        check(case + " normalized peak", peak, models[case][1], peak >= LIMITS["detection"])
        check(case + " peak/sidelobe dB", psl, models[case][2],
              abs(psl - models[case][2]) <= LIMITS["psl_error_db"])
    check("noise normalized peak", results["noise"][1], models["noise"][1],
          results["noise"][1] < LIMITS["noise_max"])
    return rows
