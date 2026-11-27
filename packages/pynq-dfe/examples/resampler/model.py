"""Periodic integer IQ test vectors and frequency-domain acceptance metrics."""
import numpy as np

BEATS = 1024
AMPLITUDE = 8192
TONE_BIN = 79
ALIAS_BIN = 1409
GAIN_TOL_DB = 0.15
MIN_REJECTION_DB = 55.0


def stimulus(lanes, kind):
    n = BEATS * lanes
    if kind == "impulse":
        x = np.zeros(n, complex)
        x[0] = AMPLITUDE
        return x
    k = ALIAS_BIN if kind == "alias" else TONE_BIN
    x = AMPLITUDE * np.exp(2j * np.pi * k * np.arange(n) / n)
    return np.rint(x.real) + 1j * np.rint(x.imag)


def spectrum(x):
    return np.abs(np.fft.fft(x)) / len(x)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-15))
