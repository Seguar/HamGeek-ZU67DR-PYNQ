"""Program the PRACH channel and capture timestamped DMA records."""
import json
from pathlib import Path
from time import monotonic, sleep

import numpy as np
from pynq import Overlay, allocate
from pynq_dfe.binding import Device
from model import CASES, analyze, stimulus


def wait(predicate, name, timeout=1.0):
    deadline = monotonic() + timeout
    while not predicate():
        if monotonic() > deadline:
            raise TimeoutError(name)
        sleep(0.001)


def events(dev):
    mask = dev.new("StatusMask")
    dev.call("GetEventStatus", mask)
    result = {}
    for name, field in dev.ffi.typeof(mask[0]).fields:
        value = getattr(mask, name)
        result[name] = list(value) if field.type.kind == "array" else int(value)
    return result


def setup(dev):
    dev.reset()
    cfg = dev.configure()
    params = cfg.ModelParams
    actual = (params.NumBands, params.NumAntenna[0], params.NumAntennaSlots[0],
              params.NumRachChannels, params.NumRachLanes)
    if actual != (1, 1, 1, 1, 1):
        raise ValueError(f"Unexpected PRACH hardware discovery {actual}")
    dev.initialize(Sequence=[{"Length": 16}], EnableStaticSchedule=True)
    triggers = dev.new("TriggerCfg")
    for t, bit, mode in [(triggers.Activate, 0, 1), (triggers.RachUpdate, 1, 1),
                         (triggers.FrameInit[0], 2, 2)]:
        t.Mode, t.TUSERBit, t.TuserEdgeLevel, t.StateOutput = mode, bit, 3, 1
    dev.call("SetTriggersCfg", triggers)
    dev.activate()
    wait(lambda: dev.call("ReadReg", 0x10) & 1, "activation")
    cc, rc = dev.new("CCCfg"), dev.new("RCCfg")
    dev.call("GetEmptyCCCfg", cc)
    dev.call("GetEmptyRCCfg", rc)
    ddc = dev.new("DDCCfg", {"DecimationRate": 2, "UserSCS": 0})
    # dfeprach uses 30.72 MS/s as its 1x base. At 245.76 MHz the real
    # carrier rate is half that, so 1024 half-subcarriers gives Fs/4.
    nco = dev.new("NCO", {"UserFreq": 1024})
    schedule = dev.new("Schedule", {"PatternPeriod": 1, "Duration": 9})
    dev._checked("AddCCtoCCCfg", cc, 0, 1, dev.new("CarrierCfg", {"SCS": 0}))
    dev._checked("AddRCtoRCCfg", rc, 0, 0, 0, ddc, nco, schedule, cc)
    if rc.NcoCfg[0].Frequency != -(1 << 30):
        raise RuntimeError(f"Unexpected NCO word {rc.NcoCfg[0].Frequency}")
    dev.call("ClearEventStatus", dev.new("StatusMask", {"RachUpdate": 1}))
    dev._checked("SetNextCfg", cc, rc)
    wait(lambda: events(dev)["RachUpdate"], "RACH update")
    wait(lambda: events(dev)["FrameInitTrigger"][0], "band 0 frame trigger")
    sleep(0.04)
    # Discard initial status from the changeover. Check fresh sticky events
    # across all four captures once the configuration is active.
    dev.call("ClearEventStatus", dev.new("StatusMask", events(dev)))


def run(bitfile, destination):
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    ol = Overlay(str(bitfile))
    control = ol.control
    control.write(0, 0)
    dma = ol.dma
    vectors, captures, counts = {}, {}, {}
    with Device("prach", ol.ip_dict["prach"]) as dev:
        try:
            versions = dev.versions()
            if versions[1][:2] != (2, 0):
                raise RuntimeError(f"Unexpected PRACH version {versions}")
            setup(dev)
            for case in CASES:
                vectors[case] = stimulus(case)
                control.write(0, 0)
                with allocate((1024,), np.uint32) as tx:
                    tx[:] = vectors[case]
                    dma.sendchannel.transfer(tx)
                    wait(lambda: dma.sendchannel.idle, "MM2S transfer")
                    dma.sendchannel.wait()
                control.write(0, 1)
                sleep(0.025)
                control.write(0, 3)
                wait(lambda: control.read(8) & (1 << 17), "capture window")
                counts[case] = control.read(8) & 0x1ffff
                if counts[case] < 1024:
                    raise RuntimeError(f"{case}: {counts[case]} samples, events={events(dev)}")
                with allocate((1024,), np.uint64) as rx:
                    dma.recvchannel.transfer(rx)
                    wait(lambda: dma.recvchannel.idle, "S2MM transfer")
                    dma.recvchannel.wait()
                    captures[case] = np.array(rx)
                np.save(out / (case + "-input.npy"), vectors[case])
                np.save(out / (case + "-capture.npy"), captures[case])
            flags = events(dev)
            rows = analyze(vectors, captures, counts)
            errs = [flags[k] for k in ("DecimatorOverflow","MixerOverflow","DecimatorOverrun","SelectorOverrun")]
            errs += flags["CCSequenceError"][:1] + flags["FrameError"][:1]
            rows.append(dict(test="sticky errors", predicted=0, measured=sum(errs), passed=not any(errs)))
            result = dict(versions=versions, events=flags, rows=rows)
            (out / "measurements.json").write_text(json.dumps(result, indent=2))
            return result
        finally:
            control.write(0, 0)
            if dev.call("GetStateID") == dev.lib.XDFEPRACH_STATE_OPERATIONAL:
                dev.deactivate()
                wait(lambda: not (dev.call("ReadReg", 0x10) & 1), "deactivation")
            dma.sendchannel.stop()
            dma.recvchannel.stop()
            if control.read(0) or control.read(8):
                raise RuntimeError("Capture harness did not return to idle")
