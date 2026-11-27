"""DMA exercise and numerical reference for the single-channel DFE equalizer."""
from pathlib import Path
from time import monotonic, sleep
import json
import numpy as np

N = 2048
FS = 100e6
SHIFT = 6
SCALE = 2 ** (20 - SHIFT)  # PG394: W+19-S fractional bits before quantization
FILTERS = {
    "identity": [1, 0, 0, 0],
    "delay_gain": [0, .5+.25j, 0, 0],
    "shaped": [.5+.125j, .25-.125j, -.125+.0625j, .0625],
}
BINS = [-384, -192, -64, 96, 320]
GAIN_DB, PHASE_DEG, SAMPLE_LSB = .1, 1., 2


def taps_for(name):
    h = np.array(FILTERS[name], dtype=complex)
    return np.rint(h.real*SCALE) + 1j*np.rint(h.imag*SCALE)


def stimuli():
    impulse = np.zeros(N, complex)
    impulse[64] = 8192+4096j
    step = np.zeros(N, complex)
    step[128:1024] = 4096-8192j
    yield "impulse", impulse
    yield "step", step
    for k in BINS:
        tone = 8192 * np.exp(2j*np.pi*k*np.arange(N)/N)
        yield str(k), np.rint(tone.real) + 1j*np.rint(tone.imag)


def response(taps, k):
    return np.sum(taps * np.exp(-2j*np.pi*k*np.arange(len(taps))/N)) / SCALE


def compare(name, case, x, y, latency):
    taps = taps_for(name)
    if case in ("impulse", "step"):
        expected = np.convolve(x, taps / SCALE)[:N-latency]
        error = y[latency:] - expected
        peak = float(max(np.max(abs(error.real)), np.max(abs(error.imag))))
        return dict(filter=name, case=case, max_error_lsb=peak, passed=peak <= SAMPLE_LSB)
    k = int(case)
    idx = np.arange(256, 1280)  # whole cycles, beyond the startup transient
    kernel = np.exp(-2j*np.pi*k*idx/N)
    measured = np.sum(y[idx+latency]*kernel) / np.sum(x[idx]*kernel)
    predicted = response(taps, k)
    def db(z):
        return float(20*np.log10(abs(z))) if z else -999.
    gain_error = db(measured)-db(predicted)
    phase_error = float(np.angle(measured/predicted, deg=True))
    return dict(filter=name, case=case, MHz=k*FS/N/1e6,
                predicted_dB=db(predicted), measured_dB=db(measured),
                predicted_deg=float(np.angle(predicted, deg=True)),
                measured_deg=float(np.angle(measured, deg=True)),
                gain_error_dB=gain_error, phase_error_deg=phase_error,
                passed=abs(gain_error)<=GAIN_DB and abs(phase_error)<=PHASE_DEG)


def wait_for(check, what):
    until = monotonic() + 2
    while not check():
        if monotonic() >= until:
            raise TimeoutError(what)
        sleep(.001)


def configure(dev):
    dev.reset()
    cfg = dev.configure()
    if not cfg.ModelParams.ComplexModel:
        raise ValueError("Expected a complex-capable equalizer")
    # The 2025.2 Initialize routine computes the complex-mode bit but omits
    # its NEXT_CONTROL write. Stage it for Initialize's immediate commit.
    dev.call("WriteReg", 0x24, dev.call("ReadReg", 0x24) | 4)
    dev.initialize(DatapathMode=1)
    wait_for(lambda: dev.call("ReadReg", 0x20) & 4, "complex mode")
    trig = dev.new("TriggerCfg")
    dev.call("GetTriggersCfg", trig)
    for event in (trig.Activate, trig.Update):
        event.Mode, event.TuserEdgeLevel, event.TUSERBit = 1, 3, 0
    dev.call("SetTriggersCfg", trig)
    dev.activate()
    wait_for(lambda: dev.call("ReadReg", 0x38) & 1, "activation")


def load(dev, name):
    taps = taps_for(name)
    bank = 2 if (dev.call("ReadReg", 0x20) >> 4) & 3 == 0 else 0
    coeff = dev.new("Coefficients", dict(Num=4, Set=bank,
                    Coefficients=np.r_[taps.real,taps.imag].astype(int).tolist()))
    dev.call("LoadCoefficients", 1, 1, SHIFT, coeff)
    dev.call("Update", dev.new("EqConfig", dict(DatapathMode=1, RealDatapathSet=bank)))
    wait_for(lambda: dev.call("ReadReg", 0x20) & 0xf4 ==
             ((bank + 1) << 6 | bank << 4 | 4), "bank selection")


def transfer(dma, x):
    from pynq import allocate
    tx = allocate((N,), dtype=np.uint32)
    rx = allocate((N,), dtype=np.uint32)
    try:
        tx[:] = ((x.real.astype(np.int32) & 65535) |
                 (x.imag.astype(np.int32) << 16)).astype(np.uint32)
        dma.recvchannel.transfer(rx)
        dma.sendchannel.transfer(tx)
        for ch in (dma.sendchannel, dma.recvchannel):
            wait_for(lambda: ch.idle or ch.error, "DMA frame")
            ch.wait()
        if dma.recvchannel.transferred != rx.nbytes:
            raise RuntimeError("Short capture")
        words = np.asarray(rx)
        return (words.astype(np.int16).astype(float) +
                1j*(words >> 16).astype(np.int16).astype(float))
    except BaseException:
        dma.write(0, 4)
        wait_for(lambda: not dma.read(0) & 4, "DMA reset")
        raise
    finally:
        tx.freebuffer()
        rx.freebuffer()


def measure(bitfile, output):
    import pynq_dfe.ip
    from pynq import Overlay
    ol = Overlay(str(bitfile))
    out = Path(output)
    out.mkdir(exist_ok=True)
    rows, captures = [], {}
    with ol.equalizer.dfe as dev:
        try:
            configure(dev)
            report = dict(versions=dev.versions(), hardware_latency=dev.call("GetTDataDelay", 0))
            for name in FILTERS:
                load(dev, name)
                for case, x in stimuli():
                    y = transfer(ol.dma, x)
                    captures[f"{name}_{case}"] = y
                    captures[f"input_{case}"] = x
                    if name == "identity" and case == "impulse":
                        latency = int(np.argmax(abs(y))) - 64
                        if not 0 <= latency < 256:
                            np.save(out/"identity-failed.npy", y)
                            raise RuntimeError(f"Unusable identity impulse latency {latency}")
                        report["measured_latency"] = latency
                    rows.append(compare(name, case, x, y, latency))
            report["rows"] = rows
            np.savez(out/"captures.npz", **captures)
            (out/"measurements.json").write_text(json.dumps(report, indent=2)+"\n")
        finally:
            if dev.call("GetStateID") == 5:
                dev.deactivate()
            dev.reset()
    return report
