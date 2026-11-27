"""Periodic-frame, power-indexed complex memory LUTs and indirect learning."""
import numpy as np

N = 1024
BINS = 160
LEVEL = 16384
GAIN = 0.82
POWER = np.arange(256) / 256


def iqround(x):
    return np.rint(x.real) + 1j * np.rint(x.imag)


def envelope_index(x):
    return np.clip(np.floor((x.real**2 + x.imag**2) / 2**20), 0, 255).astype(int)


def waveform(seed):
    """Deterministic independent 160-subcarrier 16-QAM periods, >=10 dB PAPR."""
    rng = np.random.default_rng(seed)
    while True:
        spectrum = np.zeros(N, complex)
        qam = rng.choice([-3, -1, 1, 3], (2, BINS))
        spectrum[np.arange(-BINS//2, BINS//2)] = qam[0] + 1j*qam[1]
        x = np.fft.ifft(spectrum)
        x = iqround(x * (0.71 * LEVEL / np.max(abs(x))))
        if papr(x) >= 10:
            return x


def papr(x):
    return 10*np.log10(max(abs(x)**2) / np.mean(abs(x)**2))


def tables(gain):
    """Convert effective complex gains into two signed Q1.15 LUTs at OUT_SCALE=1."""
    codes = iqround(np.asarray(gain) * 16384)
    if np.max(np.maximum(abs(codes.real), abs(codes.imag))) > 32767:
        raise ValueError("LUT gain outside signed coefficient range")
    return codes


def identity():
    g = np.zeros((1, 2, 256), complex)
    g[0, 0] = 1
    return tables(g)


def pa_tables():
    """Sample a Saleh-type complex gain curve, plus a delayed compression term."""
    g = np.zeros((2, 2, 256), complex)
    g[0, 0] = GAIN / (1 + 0.58 * POWER) * np.exp(1j * 0.52 * POWER / (1 + POWER))
    g[1, 0] = (0.04 - 0.025j) * POWER
    return tables(g)


def actuator_tables():
    g = np.zeros((16, 2, 256), complex)
    # Polynomial envelope orders 0..4 (total signal orders 1..5),
    # evaluated on both matched and cross-delayed envelope addresses.
    r = np.sqrt(POWER)
    for m in range(16):
        c = np.exp(1j * (m + 1)) / (12 + m)
        g[m, 0] = c * (0.3 + r + 0.5*r**2)
        g[m, 1] = c.conjugate() * (0.4*r**3 + 0.6*r**4)
    g[0, 0] += 0.55
    return tables(g)


def reference(x, lut, delays):
    idx = envelope_index(x)
    acc = np.zeros_like(x, dtype=complex)
    for m, pair in enumerate(delays):
        gain = sum(lut[m, k, np.roll(idx, d)] for k, d in enumerate(pair))
        acc += np.roll(x, m) * gain
    return iqround(acc / 2048)  # scale=1, Q25.18 integer output


def pa_input(raw):
    return np.floor(raw.real / 8) + 1j * np.floor(raw.imag / 8)


def learn(inputs, outputs):
    """Fit post-inverse input = F(output/GAIN), with three memory taps.

    Solve jointly on training captures. Clamp the polynomial beyond supported
    training amplitudes before quantizing its extension into unused LUT bins.
    """
    columns = []
    domain = 0
    for output in outputs:
        z = output / GAIN
        p = envelope_index(z) / 256
        domain = max(domain, np.max(p))
        columns.append(np.stack([np.roll(z * p**k, m) for m in range(3)
                                 for k in range(4)], axis=1))
    coef = np.linalg.lstsq(np.concatenate(columns), np.concatenate(inputs), rcond=1e-7)[0]
    g = np.zeros((3, 2, 256), complex)
    for m, row in enumerate(coef.reshape(3, 4)):
        g[m, 0] = np.polynomial.polynomial.polyval(np.minimum(POWER, domain), row)
    return tables(g)


def metrics(x, y):
    ideal = GAIN*x
    mse = np.mean(abs(y-ideal)**2) / np.mean(abs(ideal)**2)
    power = abs(np.fft.fft(y))**2
    bins = np.arange(-BINS//2, BINS//2)
    acpr = [10*np.log10(power[bins + offset].sum()/power[bins].sum())
            for offset in (-BINS, BINS)]
    return dict(acpr_left_db=acpr[0], acpr_right_db=acpr[1], worst_acpr_db=max(acpr),
                nmse_db=10*np.log10(mse), evm_pct=100*np.sqrt(mse))
