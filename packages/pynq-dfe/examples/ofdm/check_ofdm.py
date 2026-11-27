"""Measure two parallel antenna lanes on the DL-to-UL OFDM overlay."""
import json
from contextlib import ExitStack
from pathlib import Path
import time

import numpy as np

from model import (DL_SCALE, UL_SCALE, EVM_LIMIT_DB, MAG_LIMIT_DB, SC,
                   reference, evm_db, stimulus)


def configure(device, scale):
    device.reset()
    device.configure()
    device.initialize(CCSequenceLength=16)
    triggers = device.new("TriggerCfg")
    device.call("GetTriggersCfg", triggers)
    for trigger in (triggers.Activate, triggers.CCUpdate):
        trigger.Mode, trigger.TuserEdgeLevel, trigger.TUSERBit = 1, 3, 0
    device.call("SetTriggersCfg", triggers)
    device.call("SetTuserOutFrameLocation", 0)
    device.call("SetTuserCCUpdateTrigger", 1)
    device.activate()
    time.sleep(0.04)
    carrier = device.new("CarrierCfg", dict(Numerology=0, FftSize=11,
                         NumSubcarriers=SC, ScaleFactor=scale, CommsStandard=0))
    ft = device.new("FTSequence", dict(Length=1, CCID=[0]))
    cfg = device.new("CCCfg")
    device.call("GetEmptyCCCfg", cfg)
    assert device.call("AddCCtoCCCfg", cfg, 0, 1, carrier, ft) == 0
    assert device.call("SetNextCCCfgAndTrigger", cfg) == 0
    time.sleep(0.05)
    current = device.new("CCCfg")
    device.call("GetCurrentCCCfg", current)
    if current.CarrierCfg[0].ScaleFactor != scale:
        raise RuntimeError(f"Carrier update timed out (scale {current.CarrierCfg[0].ScaleFactor})")


def wait(channel, dma):
    deadline = time.monotonic() + 2
    while not channel.idle:
        if time.monotonic() > deadline:
            raise TimeoutError(f"DMA MM2S={dma.read(4):#x} S2MM={dma.read(52):#x}")
        time.sleep(.001)
    channel.wait()


def run(bitfile, output):
    from pynq import Overlay, allocate
    import pynq_dfe.ip  # register OFDM IP with Overlay
    ol = Overlay(str(bitfile))
    dma, arm = ol.dma, ol.arm
    out = Path(output)
    results = []
    with ExitStack() as stack:
        dl = stack.enter_context(ol.dl.dfe)
        ul = stack.enter_context(ol.ul.dfe)
        tx = stack.enter_context(allocate((SC, 4), np.int16))
        rx = stack.enter_context(allocate((SC, 4), np.int16))
        try:
            for kind in ("tone", "qpsk"):
                s = stimulus(kind)
                tx[:, 0] = tx[:, 2] = s.real
                tx[:, 1] = tx[:, 3] = s.imag
                arm.write(0, 0)
                dma.sendchannel.transfer(tx)
                wait(dma.sendchannel, dma)
                if kind == "tone":
                    configure(dl, DL_SCALE)
                    configure(ul, UL_SCALE)
                time.sleep(0.04)
                dma.recvchannel.transfer(rx)
                arm.write(0, 1)
                wait(dma.recvchannel, dma)
                arm.write(0, 0)
                assert dma.recvchannel.transferred == rx.nbytes
                data = rx.copy()
                cp, predicted = reference(s)
                np.savez(out / (kind + ".npz"), input=s, time_reference=cp, raw=data, predicted=predicted)
                for a in range(2):
                    measured = data[:, 2*a] + 1j*data[:, 2*a+1]
                    error = float(evm_db(measured, predicted))
                    roundtrip = float(evm_db(measured, s))
                    row = dict(kind=kind, lane=a, evm_db=error, roundtrip_db=roundtrip,
                               passed=error < EVM_LIMIT_DB and roundtrip < EVM_LIMIT_DB)
                    if kind == "tone":
                        row.update(bin=int(np.argmax(abs(measured))), magnitude=float(abs(measured[37])),
                                   predicted_magnitude=float(abs(predicted[37])))
                        row["magnitude_error_db"] = float(20*np.log10(max(row["magnitude"], 1e-30)/row["predicted_magnitude"]))
                        row["passed"] &= row["bin"] == 37 and abs(row["magnitude_error_db"]) <= MAG_LIMIT_DB
                    results.append(row)
        finally:
            arm.write(0, 0)
            dma.write(0, 4)
            deadline = time.monotonic() + 1
            while dma.read(0) & 4:
                if time.monotonic() > deadline:
                    raise RuntimeError("DMA reset timeout")
            for device in (ul, dl):
                if device.call("GetStateID") == 5:
                    device.deactivate()
    (out / "result.json").write_text(json.dumps(results, indent=2))
    return results
