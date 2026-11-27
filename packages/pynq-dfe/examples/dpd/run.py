"""Exercise both hard NLF grids on periodic DMA frames."""
import json
import os
from pathlib import Path
import shutil
import time

import matplotlib.pyplot as plt
import numpy as np
from pynq import Clocks, Overlay, allocate
from pynq_dfe import NlfIP
from pynq_dfe.dpd import (N, actuator_tables, envelope_index, identity,
                          learn, metrics, pa_input, pa_tables, papr, reference, waveform)


def configure(ip, lut, delays):
    ip.configure_luts(range(len(lut)), delays, scale=1)
    ip.write_lut_bank(lut, 0)
    ip.write(8, 3)
    ip.write(0x14, 1)
    ip.write(0x1004, (1 << len(lut))-1)


def signed25(words):
    return ((words.astype(np.int64) & 0x1ffffff) ^ 0x1000000) - 0x1000000


def capture(ol, mode, x):
    with allocate((N, 4), np.uint32) as tx, allocate((N,), np.uint64) as rx:
        tx[:] = 0
        tx[:, 0] = (x.real.astype(int) & 65535) | ((x.imag.astype(int) & 65535) << 16)
        tx[:, 1] = envelope_index(x)
        ol.control.write(0, mode)
        dma = ol.dma
        dma.recvchannel.transfer(rx)
        dma.sendchannel.transfer(tx)
        until = time.monotonic() + 5
        while not (dma.recvchannel.idle and dma.sendchannel.idle):
            if time.monotonic() > until:
                raise TimeoutError(f"frame status {ol.control.read(8):#x}")
            time.sleep(.001)
        dma.recvchannel.wait()
        dma.sendchannel.wait()
        status = ol.control.read(8)
        if status != N << 3 or ol.nlf.read(16) or ol.pa.read(16):
            raise RuntimeError(f"frame/overflow {status:#x}/{ol.nlf.read(16)}/{ol.pa.read(16)}")
        words = np.array(rx)
    return signed25(words) + 1j * signed25(words >> 25)


def teardown(ol):
    for ip in (ol.nlf, ol.pa):
        ip.write(0x1004, 0)
        assert ip.read(0x1004) == 0
    dma = ol.dma
    for ctrl in (0, 0x30):
        dma.write(ctrl, dma.read(ctrl) & ~1)
    assert all(dma.read(offset) & 1 for offset in (4, 0x34))
    assert ol.control.read(8) & 7 == 0
    print("Both NLF unit masks zero, frame idle, DMA MM2S and S2MM halted.")


def accuracy(measured, expected):
    err = measured - expected
    ratio = np.sum(abs(err)**2) / np.sum(abs(expected)**2)
    return dict(max_code_error=float(max(max(abs(err.real)), max(abs(err.imag)))),
                nmse_db=float(10*np.log10(ratio)) if ratio else None)


def matched(lut):
    return [(m, m) for m in range(len(lut))]


def run(ol, output):
    report, raw = {}, {}
    def save():
        (output/'measurements.json').write_text(json.dumps(report, indent=2, allow_nan=False))
        np.savez_compressed(output/'captures.npz', **raw)

    ident = identity()
    for ip in (ol.nlf, ol.pa):
        configure(ip, ident, matched(ident))
    impulse = np.zeros(N, complex)
    impulse[0] = 4096
    delays = [int(np.argmax(abs(capture(ol, mode, impulse)))) for mode in (0, 1)]
    report.update(pipeline_delays=delays, sample_clock_mhz=float(Clocks.fclk0_mhz),
                  actuator={}, pa_reference=[], iterations=[])
    frames = [waveform(seed) for seed in (21, 32, 43, 65)]
    x = frames[-1]
    raw['input'] = x
    report['papr_db'] = papr(x)
    lut = actuator_tables()
    taps = [(m, (m+1) % 16) for m in range(16)]
    configure(ol.nlf, lut, taps)
    # Register bank bit selects the write target, opposite RAM supplies data.
    other = -lut
    ol.nlf.write_lut_bank(other, 1)
    for name, ctrl, mode, coeff in [('a', 3, 0, lut), ('b', 2, 0, other),
                                    ('switch', 0, 2, None)]:
        ol.nlf.write(8, ctrl)
        y = capture(ol, mode, x)
        if coeff is not None:
            expected = np.roll(reference(x, coeff, taps), delays[0])
        else:
            # Direct bank port changes at frame addresses 0 and 512.
            port = np.roll(np.arange(N) >= N//2, 17)
            expected = np.where(port, raw['a_expected'], raw['b_expected'])
        raw[name], raw[name+'_expected'] = y, expected
        report['actuator'][name] = accuracy(y, expected)
        save()
    configure(ol.pa, pa_tables(), [(0,0),(1,1)])
    lut = ident
    for iteration in range(4):
        configure(ol.nlf, lut, matched(lut))
        us, ys = [], []
        for j, stimulus in enumerate(frames):
            actuator = np.roll(capture(ol, 0, stimulus), -delays[0])
            pa = np.roll(capture(ol, 1, stimulus), -delays[1])
            us.append(pa_input(actuator))
            ys.append(pa / 8)
            raw[f'x{j}'] = stimulus
            raw[f'u{iteration}_{j}'] = us[-1]
            raw[f'y{iteration}_{j}'] = ys[-1]
        # Independently check the implemented PA transfer on the held-out input.
        report['pa_reference'].append(accuracy(ys[-1]*8, reference(us[-1], pa_tables(), [(0,0),(1,1)])))
        raw[f'lut{iteration}'] = lut
        report['iterations'].append(metrics(x, ys[-1]))
        save()
        if iteration < 3:
            lut = learn(us[:-1], ys[:-1])
    first, last = report['iterations'][0], report['iterations'][-1]
    report['acpr_improvement_db'] = first['worst_acpr_db'] - last['worst_acpr_db']
    report['nmse_improvement_db'] = first['nmse_db'] - last['nmse_db']
    report['pass'] = bool(all(v['max_code_error'] <= 2 and (v['nmse_db'] is None or v['nmse_db'] < -60)
                              for v in report['actuator'].values())
                          and report['acpr_improvement_db'] >= 10 and report['nmse_improvement_db'] >= 15)
    save()
    print(json.dumps(report, indent=2))
    fig, ax = plt.subplots(3, 1, figsize=(9, 10), constrained_layout=True)
    fs = Clocks.fclk0_mhz
    for k in (0,3):
        y = raw[f'y{k}_3']
        spec = np.fft.fftshift(abs(np.fft.fft(y)))/N
        ax[0].plot(np.fft.fftshift(np.fft.fftfreq(N))*fs,20*np.log10(np.maximum(spec,1e-12)/32768),label=f'Iteration {k}')
        ax[1].scatter(abs(x)/32768, abs(y)/32768, s=4, label=f'Iteration {k}')
        ax[2].scatter(abs(x)/32768, np.angle(y*x.conj(), deg=True), s=4, label=f'Iteration {k}')
    ax[0].set(xlabel='Frequency (MHz)',ylabel='Spectrum (dBFS/bin)')
    ax[1].set(xlabel='Input magnitude (FS)',ylabel='Output magnitude (FS)')
    ax[2].set(xlabel='Input magnitude (FS)',ylabel='Phase shift (degrees)')
    for panel in ax:
        panel.legend()
    fig.savefig(output/'response.png')
    plt.show()
    return report


def main():
    output = Path(os.environ['DFE_OUTPUT'])
    output.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage('/').free < 60*1024**2:
        raise RuntimeError("overlay download requires 60 MiB free on root")
    ol = Overlay(os.environ['DFE_BITFILE'])
    try:
        assert isinstance(ol.nlf, NlfIP) and isinstance(ol.pa, NlfIP)
        result = run(ol, output)
    finally:
        teardown(ol)
    assert result['pass'], "See measurements.json for acceptance failures"
