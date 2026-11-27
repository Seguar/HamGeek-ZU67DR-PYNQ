"""One 256-point transform with a quantized complex tone at bin 37."""
import json
import time
from pathlib import Path

import numpy as np


def run(bitfile, output):
    from pynq import Overlay, allocate

    ol = Overlay(str(bitfile))
    dma = ol.dma
    n = np.arange(256)
    iq = 4096 * np.exp(2j * np.pi * 37 * n / len(n))
    i, q = np.rint(iq.real).astype(np.int16), np.rint(iq.imag).astype(np.int16)
    expected = np.fft.fft(i + 1j*q)
    reverse = [int(f"{k:08b}"[::-1], 2) for k in n]
    with allocate((256, 2), np.int16) as tx, allocate((256, 2), np.uint32) as rx:
        tx[:, 0], tx[:, 1] = i, q
        dma.recvchannel.transfer(rx)
        dma.sendchannel.transfer(tx)
        try:
            deadline = time.monotonic() + 3
            while not (dma.recvchannel.idle and dma.sendchannel.idle):
                if time.monotonic() > deadline:
                    raise TimeoutError(f"DMA status MM2S={dma.read(4):#x} S2MM={dma.read(52):#x}")
            dma.sendchannel.wait()
            dma.recvchannel.wait()
            assert dma.recvchannel.transferred == rx.nbytes
            raw = rx.copy()
        finally:
            # Reset both engines even on timeout before releasing their buffers.
            dma.write(0, 4)
            deadline = time.monotonic() + 1
            while dma.read(0) & 4:
                if time.monotonic() > deadline:
                    raise RuntimeError("AXI DMA reset timed out")
    words = raw[reverse].astype(np.int64)
    signed = ((words & 0x1fffffff) ^ 0x10000000) - 0x10000000
    actual = signed[:, 0] + 1j * signed[:, 1]
    peak = int(np.argmax(abs(actual)))
    mag_db = float(20 * np.log10(abs(actual[37]) / abs(expected[37])))
    evm_db = float(20 * np.log10(max(1e-30, np.linalg.norm(actual-expected)) / np.linalg.norm(expected)))
    result = dict(bin=peak, expected_bin=37, magnitude=abs(actual[37]), predicted=abs(expected[37]),
                  magnitude_error_db=mag_db, evm_db=evm_db,
                  passed=bool(peak == 37 and abs(mag_db) <= 0.1 and evm_db < -50))
    out = Path(output)
    np.savez(out / "tone.npz", input=i+1j*q, raw=raw, measured=actual, predicted=expected)
    (out / "result.json").write_text(json.dumps(result, indent=2))
    return result
