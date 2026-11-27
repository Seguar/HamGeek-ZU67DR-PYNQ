"""Integer-code reference for 20 MHz NR, 15 kHz spacing, 106 RB, CCID 0."""
import numpy as np

N = 2048
SC = 1272
BINS = np.r_[0:SC // 2, N - SC // 2:N]
DL_SCALE = 32
UL_SCALE = 16
MAG_LIMIT_DB = 0.1
EVM_LIMIT_DB = -50.0


def quantize(z):
    def component(x):
        return np.clip(np.rint(x), -32768, 32767)
    return component(z.real) + 1j * component(z.imag)


def reference(symbol, symbol_number=0):
    bins = np.zeros(N, complex)
    bins[BINS] = symbol
    time = quantize(np.fft.ifft(bins) * (N * DL_SCALE / 1024))
    prefix = 160 if symbol_number % 7 == 0 else 144
    with_cp = np.r_[time[-prefix:], time]
    uplink = quantize(np.fft.fft(with_cp[prefix:])[BINS] * (UL_SCALE / 1024))
    return with_cp, uplink


def stimulus(kind):
    if kind == "tone":
        symbol = np.zeros(SC, complex)
        symbol[37] = 16384
        return symbol
    rng = np.random.default_rng(6702)
    alphabet = np.array([-1, 1])
    return 3000 * (rng.choice(alphabet, SC) + 1j * rng.choice(alphabet, SC))


def evm_db(actual, predicted):
    error = np.linalg.norm(actual - predicted)
    return 20 * np.log10(max(error, 1e-30) / np.linalg.norm(predicted))
