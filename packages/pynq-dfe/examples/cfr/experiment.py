"""Repeatable one-carrier CFR experiment. All powers are complex sample powers."""
import json
from pathlib import Path
import numpy as np

FS = 100e6
BW = 20e6
N = 4096
BLOCKS = 64
RMS = 6000
THRESHOLD = 12000
PROBS = (1e-2, 1e-3, 1e-4)
FREQ = np.fft.fftfreq(N, 1 / FS)
INBAND = abs(FREQ) < BW / 2


def iqround(x):
    return np.rint(x.real) + 1j * np.rint(x.imag)


def stimulus():
    rng = np.random.default_rng(6708)
    spectrum = np.zeros((BLOCKS, N), complex)
    spectrum[:, INBAND] = np.exp(2j * np.pi * rng.random((BLOCKS, INBAND.sum())))
    x = np.fft.ifft(spectrum, axis=1)
    return iqround(x * (RMS / np.sqrt(np.mean(abs(x)**2))))


def pulse():
    # A unit-peak band-limited cancellation pulse at the occupied bandwidth.
    # The hard-IP demonstration latency uses ceil(L/8) input clocks for
    # the half-pulse delay. Store four fractional samples per input clock.
    k = np.arange(-124, 125)
    return np.rint(16384 * np.sinc(k * BW / (4 * FS)) * np.kaiser(len(k), 6)).astype(int)


def predict(x):
    # Three cancellation passes on periodic symbols. At each local maximum
    # subtract the excess complex amplitude convolved with the very same CP.
    h = pulse()[::4] / 16384
    kernel = np.zeros(N)
    kernel[np.arange(-31, 32) % N] = h
    spectrum = np.fft.fft(kernel)
    y = x.copy()
    for _ in range(3):
        mag = abs(y)
        peaks = (mag > THRESHOLD) & (mag >= np.roll(mag, 1, 1)) & (mag > np.roll(mag, -1, 1))
        excess = y * peaks * (1 - THRESHOLD / np.maximum(mag, 1))
        y -= np.fft.ifft(np.fft.fft(excess, axis=1) * spectrum, axis=1)
    return y


def db(p):
    return 10 * np.log10(np.maximum(p, 1e-30))


def metrics(x, y):
    p = abs(y)**2
    par = db(p / np.mean(p))
    s = np.mean(abs(np.fft.fft(y, axis=1))**2, axis=0)
    e = np.mean(abs(np.fft.fft(y-x, axis=1))**2, axis=0)
    ref = np.mean(abs(np.fft.fft(x, axis=1))**2, axis=0)
    inpower = s[INBAND].sum()
    return dict(ccdf_dB=[float(np.quantile(par, 1-q)) for q in PROBS],
                papr_dB=float(par.max()), inband_power_dBFS=float(db(inpower / (N*32768)**2)),
                evm_pct=float(100*np.sqrt(e[INBAND].sum()/ref[INBAND].sum())),
                aclr_dB=[float(db(inpower / s[(side*FREQ >= BW/2) & (side*FREQ < 1.5*BW)].sum()))
                         for side in (-1, 1)])


def expectations(x):
    ref = metrics(x, predict(x))
    band = [0.4 * ref['evm_pct'], 2 * ref['evm_pct']]
    return dict(reference=ref, evm_band_pct=band, ccdf_tolerance_dB=0.8,
                tail_max_dB=float(20*np.log10(THRESHOLD/RMS)+0.5),
                min_aclr_dB=35, max_low_peak_error_lsb=3, min_input_papr_dB=10)


def compare(x, y, low_error, frozen):
    before, after = metrics(x, x), metrics(x, y)
    rows = []
    def row(name, prediction, measured, passed):
        rows.append(dict(test=name, expected=prediction, measured=measured, passed=bool(passed)))
    row('input PAPR dB', '>=10', before['papr_dB'], before['papr_dB'] >= 10)
    for q, m, p in zip(PROBS, after['ccdf_dB'], frozen['reference']['ccdf_dB']):
        row(f'CCDF {q:g} dB', f'{p:.3f} +/- 0.8', m, abs(m-p) <= frozen['ccdf_tolerance_dB'])
    m, limit = after['ccdf_dB'][-1], frozen['tail_max_dB']
    row('tail cap dB', f'<= {limit:.3f}', m, m <= limit)
    lo, hi = frozen['evm_band_pct']
    row('in-band RMS EVM %', f'{lo:.3f}..{hi:.3f}', after['evm_pct'], lo <= after['evm_pct'] <= hi)
    for side, m in zip(('lower', 'upper'), after['aclr_dB']):
        row(side+' ACLR dB', '>=35', m, m >= frozen['min_aclr_dB'])
    row('low-level peak IQ error counts', '<=3', low_error, low_error <= 3)
    return dict(before=before, after=after, rows=rows)


def acquire(bitfile, folder):
    from pynq import Overlay
    from pynq_dfe.cfr import HardCFR
    from dma_frame import transfer
    out = Path(folder)
    out.mkdir(exist_ok=True)
    x = stimulus()
    frozen = json.loads((out/'expectations.json').read_text())
    ol = Overlay(str(bitfile))
    cfr = HardCFR(ol.cfr.mmio)
    cfr.configure([(i, 0) for i in pulse()], THRESHOLD)
    low = iqround(x[0] / 8)
    # Use a phase-modulated constant envelope for an unambiguous correlation.
    low = iqround(2048 * np.exp(1j * np.angle(low)))
    raw_low = transfer(ol.dma, np.tile(low, 4))
    last = raw_low[-N:]
    lag = int(np.argmax(abs(np.fft.ifft(np.fft.fft(last)*np.fft.fft(low).conj()))))
    low_error = float(np.max(abs(np.roll(last, -lag)-low)))
    raw = np.stack([transfer(ol.dma, np.tile(symbol, 4)) for symbol in x])
    y = np.roll(raw[:, -N:], -lag, axis=1)
    np.savez_compressed(out/'captures.npz', source=x, raw=raw, raw_low=raw_low,
                        low=low, aligned=y, latency_mod_period=lag)
    result = compare(x, y, low_error, frozen)
    result.update(latency_mod_period=lag, threshold_counts=THRESHOLD,
                  low_input_papr_dB=float(db(max(abs(low)**2)/np.mean(abs(low)**2))))
    (out/'measurements.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def plot(folder):
    import matplotlib.pyplot as plt
    out = Path(folder)
    data = np.load(out/'captures.npz')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for label, key in [('Input', 'source'), ('CFR output', 'aligned')]:
        signal = data[key]
        p = abs(signal.ravel())**2
        axes[0].semilogy(np.sort(db(p/p.mean())), np.arange(len(p), 0, -1)/len(p), label=label)
        s = np.mean(abs(np.fft.fft(signal, axis=1))**2, axis=0)
        axes[1].plot(np.fft.fftshift(FREQ)/1e6, np.fft.fftshift(db(s/(FS*N*32768**2))), label=label)
    axes[0].set(xlabel='Instantaneous power / mean (dB)', ylabel='Exceedance probability', xlim=(0, 13))
    axes[1].set(xlabel='Baseband frequency (MHz)', ylabel='PSD (dBFS/Hz)')
    for ax in axes:
        ax.legend()
        ax.grid(True)
    fig.tight_layout()
    fig.savefig(out/'ccdf-spectrum.png', dpi=150)
    return fig
