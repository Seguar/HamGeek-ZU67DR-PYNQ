"""Run in a private r5 stage prepared by run_all.sh."""
import argparse
from contextlib import nullcontext
from hashlib import file_digest
import json
import math
import os
from pathlib import Path
import re
import signal
import sys

import numpy as np

MANIFEST = "ec37b175962ac30c1e7e1d4febdee0277ba9935a7d92e756c9d72b5f65c5868d"
RATES = {"ADC": (2.5, 2.5, 5.0), "DAC": (10., 10.)}


class Report:
    def __init__(self, folder, fake):
        self.folder = folder
        self.records = []
        self.mode = "offline fake" if fake else "board"

    def check(self, name, value, expected, ok=None):
        passed = bool(value == expected if ok is None else ok)
        record = dict(check=name, measured=value, expected=expected,
                      status="PASS" if passed else "FAIL")
        self.records.append(record)
        (self.folder / f"{len(self.records):03}.json").write_text(json.dumps(record) + "\n")
        if not passed:
            raise ValueError(f"{name}: {value!r}, expected {expected!r}")

    def finish(self):
        passed = all(r["status"] == "PASS" for r in self.records)
        data = dict(mode=self.mode, status="PASS" if passed else "FAIL", checks=self.records)
        (self.folder / "report.json").write_text(json.dumps(data, indent=2) + "\n")
        return 0 if passed else 1


def processes():
    ancestors = set()
    pid = os.getpid()
    while pid:
        ancestors.add(pid)
        pid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
    found = []
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        if int(path.parent.name) in ancestors:
            continue
        try:
            command = path.read_bytes().lower().replace(b"\0", b" ")
        except (FileNotFoundError, ProcessLookupError):
            continue
        if re.search(rb"rowtiming|\bmts|[_/-]mts|sweep|acqui[rs]|synchronize-rfdc|test_loopback|validate\.py", command):
            found.append(path.parent.name)
    return found


def idle(rt):
    state = rt.status()
    return {**{k: rt.rd(k) for k in ("DAC_ENABLE", "GTY_ENABLE", "LOOP", "FAULT")},
            **{k: int(state[k]) for k in ("busy_dac", "busy_gty", "armed", "running")}}


def tone(rt, report):
    from rt250_seq import DAC, Program, dac_segment, tone as sine
    wave = dac_segment("tone", sine(100e6, 800, amplitude=10**(-12/20)))
    program = Program(DAC, (wave,))
    program[0].at_unit("tone", 0, repeat=12500)
    rt.load_program(program.compile())
    rt.run(dac_enable=1, gty_enable=0, adc_delay=64)
    data = np.array(rt.readback(0), dtype=float) / 32768
    rt.stop()
    report.check("ADC0 record length", data.size, 65536)
    peak = float(np.max(np.abs(data)))
    report.check("ADC0 peak FS", peak, "< -3 dBFS", peak < 10**(-3/20))
    window = np.hanning(data.size)
    spectrum = abs(np.fft.rfft((data-data.mean()) * window))
    spacing = 2.5e9 / data.size
    measured = float(np.argmax(spectrum) * spacing)
    report.check("ADC0 spectral peak Hz", measured, "100 MHz within one FFT bin",
                 abs(measured - 100e6) <= spacing)
    phase = np.exp(-2j*np.pi*np.arange(data.size)*100e6/2.5e9)
    amplitude = 2 * abs(np.dot(data*window, phase)) / window.sum()
    level = 20*math.log10(amplitude)
    expected = -18.970265284262624
    report.check("ADC0 tone dBFS", level, {"reference": expected, "tolerance_db": 3},
                 abs(level-expected) <= 3)


def sync(rt, rf, report, adc, dac):
    # Separate MTS calls remeasure FIFO delays. These complete tile-pair
    # signatures were measured by the C helper over 12 r5 reloads per mode.
    signatures = {
        ("DAC", 432): [[432, 432, 16, 16]],
        ("DAC", None): [[416, 416, 0, 0]],
        ("ADC", 448): [[448, 448, 8, 4], [448, 448, 8, 8]],
        ("ADC", None): [[440, 440, 0, 0], [444, 444, 4, 0]],
    }
    reference = rt.mts(adc or -1, dac or -1)
    for kind, target in (("DAC", dac), ("ADC", adc)):
        c = re.search(rf"^{kind} target={target or -1} latency=\[(\d+),(\d+)\] offset=\[(\d+),(\d+)\]", reference, re.M)
        if c is None:
            raise ValueError(f"unexpected C helper output: {reference}")
        allowed = signatures[kind, target]
        label = f"{kind} MTS {target or 'auto'}"
        c_pair = list(map(int, c.groups()))
        report.check(label+" C latencies and offsets", c_pair, allowed, c_pair in allowed)
        sync_fn = rf.mts_dac_sync if kind == "DAC" else rf.mts_adc_sync
        result = sync_fn([0, 1], target_latency=target)
        pair = [int(result["tiles"][tile][key]) for key in ("Latency", "Offset") for tile in (0, 1)]
        report.check(label+" Python latencies and offsets", pair, allowed, pair in allowed)
        report.check(label+" summary latency", result["Latency"], pair[0])


def exercise(rt, rf, params, r):
    state = idle(rt)
    r.check("initial idle", state, dict.fromkeys(state, 0))
    r.check("stream status", rt.rd("RFDC_STREAM_STATUS"), 15)
    r.check("HWH DFE IP type", int(params["c_ip_type"]), 2)
    r.check("DFE tile layout", rf.GetTileLayout(), 1)
    r.check("exposed tile counts", [len(rf.adc_tiles), len(rf.dac_tiles)], [3, 2])
    for kind, rates in RATES.items():
        status = rf.IPStatus[kind+"TileStatus"]
        enables = [int(v["IsEnabled"]) for v in status]
        expected = [int(params[f"c_{kind.lower()}{i}_enable"]) for i in range(4)]
        r.check(kind+" enables", enables, expected)
        for i, rate in enumerate(rates):
            tile = getattr(rf, kind.lower()+"_tiles")[i]
            label = f"{kind}{i}"
            r.check(label+" PLL lock API", tile.PLLLockStatus, 2)
            pll_required = params[f"c_{kind.lower()}{i}_pll_enable"] == "true"
            r.check(label+" raw PLL state", int(status[i]["PLLState"]), int(pll_required))
            fs = tile.PLLConfig["SampleRate"]
            r.check(label+" sample rate GS/s", fs, rate, abs(fs-rate) < 0.001)
            limits = [tile.GetMinSampleRate(), tile.GetMaxSampleRate()]
            r.check(label+" rate bounds MS/s", limits, f"0 < min <= {rate*1000} <= max",
                    0 < limits[0] <= rate*1000 <= limits[1])
    # Exercise state transitions on a consumer, leaving the clock source running.
    tile = rf.adc_tiles[0]
    for name, operation in (("StartUp", tile.StartUp), ("CustomStartUp", lambda: tile.CustomStartUp(1, 15))):
        operation()
        states = {k: [v["TileState"] for v in rf.IPStatus[k+"TileStatus"][:len(rates)]]
                  for k, rates in RATES.items()}
        r.check(name, states, {k: [15]*len(rates) for k, rates in RATES.items()})
    block = tile.blocks[0]
    original = block.NyquistZone
    r.check("initial ADC zone", original, [1, 2], original in (1, 2))
    try:
        block.NyquistZone = 3-original
        r.check("changed ADC zone", block.NyquistZone, 3-original)
    finally:
        block.NyquistZone = original
        r.check("restored ADC zone", block.NyquistZone, original)
    for i in range(2):
        for j, block in enumerate(rf.dac_tiles[i].blocks):
            label = f"DAC{i}.{j}"
            current = block.OutputCurr
            r.check(label+" output current uA", current, "20000 within one 43.75 uA code",
                    abs(current-20000) <= 43.75)
            coupling = block.GetCoupling()
            r.check(label+" coupling", coupling, [0, 1], coupling in (0, 1))
            scaler = block.DACDataScaler
            r.check(label+" scaler", scaler, [0, 1], scaler in (0, 1))
    for kind in (0, 1):
        for index in (0, 1):
            r.check(f"MTS enabled type {kind} tile {index}", rf.get_mts_enable(kind, index), True)
    rt.lock_phase()
    sync(rt, rf, r, 448, 432)
    sync(rt, rf, r, None, None)
    tone(rt, r)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fake", action="store_true")
    p.add_argument("--adc-avcc", required=True, type=float)
    p.add_argument("--ticket", required=True)
    args = p.parse_args()
    stage = Path.cwd()
    r = Report(stage, args.fake)
    bit = stage / "bundle/rowtiming250_avtt25.bit"
    try:
        r.check("board lock ticket", (stage/"BOARD.lock").read_text().strip(), args.ticket)
        r.check("competing processes", [] if args.fake else processes(), [])
        r.check("operator TP16 V", args.adc_avcc, 0.93)
        r.check("acceptance manifest SHA256", digest(bit.parent/"artifacts.sha256"), MANIFEST)
        for line in (bit.parent/"artifacts.sha256").read_text().splitlines():
            sha, name = line.split()
            r.check(name+" SHA256", digest(bit.parent/name), sha)
        sys.path.insert(0, str(bit.parent))
        from test_loopback import verify_overlay
        from rfdc_config import fixed_dac_parameters
        from clock_guard import verify_bundle
        from rt250_driver import check_hwh
        hwh = verify_overlay(bit)
        params = fixed_dac_parameters(hwh)
        r.check("fixed 20 mA, VOP disabled", True, True)
        r.check("verified topology ADC/fabric", list(verify_bundle(bit)), [2.5, 312.5])
        r.check("r5 address map", check_hwh(hwh)[0], True)
        if args.fake:
            from fake import FakeRT as RowTiming, FakeRF as RFdc
            clock = nullcontext()
        else:
            from rt250_driver import RowTiming
            from rt250_lmk_hw import configured_clock
            from xrfdc import RFdc
            clock = configured_clock()
        with clock:
            rt = RowTiming(bit, expected_rate=2.5, expected_sysref=6.25)
            try:
                rf = rt.overlay.rfdc
                r.check("RFdc binding", isinstance(rf, RFdc), True)
                exercise(rt, rf, params, r)
            finally:
                rt.stop()
                for reg in ("DAC_ENABLE", "GTY_ENABLE", "LOOP"):
                    rt.wr(reg, 0)
                state = idle(rt)
                r.check("final idle", state, dict.fromkeys(state, 0))
    except (Exception, KeyboardInterrupt) as exc:
        if not r.records or r.records[-1]["status"] != "FAIL":
            try:
                r.check("execution", repr(exc), "completed")
            except ValueError:
                pass
    if not args.fake:
        try:
            r.check("final competing processes", processes(), [])
        except ValueError:
            pass
    return r.finish()


if __name__ == "__main__":
    def interrupted(*_):
        raise KeyboardInterrupt("termination requested")
    signal.signal(signal.SIGTERM, interrupted)
    sys.exit(main())
