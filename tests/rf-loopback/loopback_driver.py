# SPDX-License-Identifier: BSD-3-Clause
"""Board driver for the RF loopback overlay (PYNQ 4.0 on the HamGeek XCZU67DR).

Everything here touches hardware except `hwh_addresses` / `check_hwh`.
"""

from pathlib import Path
from clock_guard import check_fabric, check_rfdc, progress, verify_bundle
import subprocess
from time import monotonic, sleep
import xml.etree.ElementTree as ET

import numpy as np

from loopback_registers import REG, STATUS_BITS, ID_VALUE

# Addresses the driver relies on; check_hwh() compares them with the HWH.
EXPECTED = {
    "rfdc": (0x82000000, 0x40000),
    "rf_control": (0x84000000, 0x10000),
    "dma": (0x84010000, 0x10000),
    "host_firewall": (0x84030000, 0x10000),
}
LOAD_DAC_SEG, LOAD_DAC_TABLE = range(2)


def hwh_addresses(hwh):
    """{instance: (base, size)} for the PS data address space, read-only."""
    root = ET.parse(hwh).getroot()
    out = {}
    for module in root.iter("MODULE"):
        if module.get("INSTANCE") != "zynq_ultra_ps_e_0":
            continue
        for r in module.iter("MEMRANGE"):
            if r.get("MEMTYPE") not in ("REGISTER", "MEMORY"):
                continue
            lo, hi = int(r.get("BASEVALUE"), 16), int(r.get("HIGHVALUE"), 16)
            out[r.get("INSTANCE")] = (lo, hi - lo + 1)
    return out


def check_hwh(hwh):
    found = hwh_addresses(hwh)
    rows, ok = [], True
    for name, (base, size) in EXPECTED.items():
        got = found.get(name)
        good = got == (base, size)
        ok &= good
        rows.append((name, hex(base), hex(size), None if got is None else (hex(got[0]), hex(got[1])), good))
    return ok, rows


class RfLoopback:
    def __init__(self, bitfile, download=True, *, expected_rate=None, expected_sysref=None, status_only=False):
        from pynq import MMIO, Overlay
        self.folder = Path(bitfile).resolve().parent
        rate, fabric = verify_bundle(bitfile)
        if expected_rate is not None and rate != expected_rate:
            raise RuntimeError(f"Overlay ADC rate {rate} GS/s differs from requested {expected_rate} GS/s")
        progress("Parse PYNQ overlay metadata")
        self.overlay = Overlay(str(bitfile), download=False)
        for name, (base, size) in EXPECTED.items():
            item = self.overlay.ip_dict.get(name)
            if item is None or item["phys_addr"] != base or item["addr_range"] != size:
                raise RuntimeError(f"Overlay metadata for {name} differs from the driver ({item})")
        if download:
            progress("Download verified bitstream through PYNQ")
            self.overlay.download()
            progress("PYNQ download complete")
        elif not self.overlay.is_loaded():
            raise RuntimeError("Requested overlay is not loaded")
        progress("Map PS-clocked RfLoopback control and read identity")
        self.regs = MMIO(EXPECTED["rf_control"][0], EXPECTED["rf_control"][1])
        if self.rd("ID") != ID_VALUE:
            raise RuntimeError("rf_control core ID mismatch")
        g = self.rd("GEOMETRY")
        self.geometry = dict(dac_words=1 << (g & 0xFF), gty_words=1 << ((g >> 8) & 0xFF),
                             entries=1 << ((g >> 16) & 0xFF), cap_words=1 << ((g >> 24) & 0xFF))
        self.clock_measurements = check_fabric(self, fabric, expected_sysref)
        if status_only:
            return
        check_rfdc(self.folder)
        progress("Bind the AXI DMA")
        self.dma = self.overlay.dma
        self._buf = {}

    # ------------------------------------------------------------ registers
    def rd(self, name):
        return self.regs.read(REG[name])

    def wr(self, name, value):
        self.regs.write(REG[name], int(value) & 0xFFFFFFFF)

    def status(self):
        s = self.rd("STATUS")
        d = {k: bool(s >> b & 1) for k, b in STATUS_BITS.items()}
        d["phase_code"] = (s >> 3) & 3
        d["busy_dac"] = (s >> 16) & 0xFF
        d["busy_gty"] = (s >> 24) & 0xFF
        d["fault"] = self.rd("FAULT")
        return d

    def wait(self, bit, value=True, timeout=2.0):
        t = monotonic() + timeout
        while self.status()[bit] != value:
            if monotonic() > t:
                raise TimeoutError(f"{bit} did not become {value}: {self.status()}")
            sleep(0.001)

    def frequencies(self, interval=0.25):
        """312.5 MHz fabric clock and PL SYSREF rate measured against the CPU clock."""
        c0, s0, t0 = self.rd("CLK_COUNT"), self.rd("SYSREF_COUNT"), monotonic()
        sleep(interval)
        c1, s1, t1 = self.rd("CLK_COUNT"), self.rd("SYSREF_COUNT"), monotonic()
        dt = t1 - t0
        return dict(fabric_mhz=((c1 - c0) & 0xFFFFFFFF) / dt / 1e6,
                    sysref_mhz=((s1 - s0) & 0xFFFFFFFF) / dt / 1e6)

    # ------------------------------------------------------------ clocks and links
    def lock_phase(self, target=0, tries=64, log=print):
        """Reset the MMCM until the 312.5 MHz phase code equals `target` (needs PL SYSREF)."""
        for n in range(1, tries + 1):
            self.wr("CTRL", self.rd("CTRL") | 1)
            sleep(0.001)
            self.wr("CTRL", self.rd("CTRL") & ~1)
            self.wait("mmcm_locked", timeout=1.0)
            self.wait("phase_stable", timeout=1.0)
            code = self.status()["phase_code"]
            if code == target:
                log(f"MMCM phase code {code} after {n} reset(s)")
                return n
        raise RuntimeError(f"phase code never reached {target} in {tries} resets")

    def mts(self, adc_target=-1, dac_target=-1, helper="synchronize-rfdc", timeout=30):
        """Run RFDC multi-tile sync (DAC then ADC); -1 -1 measures latency."""
        r = subprocess.run([str(self.folder / helper), str(adc_target), str(dac_target)],
                           stdout=subprocess.PIPE, text=True, timeout=timeout)
        if r.returncode:
            raise RuntimeError(f"RFDC MTS exited {r.returncode}: {r.stdout.strip()}")
        return r.stdout

    # ------------------------------------------------------------ DMA loading
    def _buffer(self, nbytes, key):
        from pynq import allocate
        b = self._buf.get(key)
        if b is None or b.nbytes < nbytes:
            b = allocate(shape=(max(nbytes, 4096),), dtype=np.uint8)
            self._buf[key] = b
        return b

    def load(self, target, mask, row, data, row_bytes):
        data = bytes(data)
        rows = len(data) // row_bytes
        pad = (-len(data)) % 16
        buf = self._buffer(len(data) + pad, "tx")
        buf[:len(data)] = np.frombuffer(data, np.uint8)
        buf[len(data):len(data) + pad] = 0
        buf.flush()
        self.wr("LOAD_TARGET", target | (mask << 8))
        self.wr("LOAD_LIMIT", rows)
        self.wr("LOAD_ADDR", row)
        self.dma.sendchannel.transfer(buf, nbytes=len(data) + pad)
        self.dma.sendchannel.wait()
        beats = (len(data) + pad) // 16
        slots = {LOAD_DAC_SEG: beats // 4, LOAD_GTY_SEG: beats * (128 // self.gtw)}.get(target, beats)
        t = monotonic() + 1.0
        while self.rd("LOAD_ROWS") != slots or not self.status()["load_idle"]:
            if monotonic() > t:
                raise TimeoutError(f"load stalled at {self.rd('LOAD_ROWS')} of {slots} entries")
        return rows

    def load_program(self, prog):
        n = 0
        for mask, row, data in prog.load_plan():
            n += self.load(LOAD_DAC_SEG, mask, row, data, 64)
        for ch in range(8):
            tb = prog.table_bytes(ch)
            if tb:
                self.load(LOAD_DAC_TABLE, 1 << ch, 0, tb, 16)
            self.wr(f"DAC_N{ch}", len(prog.entries[ch]))
        return n

    # ------------------------------------------------------------ run and capture
    def run(self, start_delay=50, adc_delay=0, cap_words=None, dac_loop=0, timeout=5.0):
        self.wr("DAC_ENABLE", 0xFF)
        self.wr("GTY_ENABLE", 0)
        self.wr("GTY_IDLE", 0)
        self.wr("LOOP", dac_loop)
        self.wr("START_DELAY", start_delay)
        self.wr("ADC_DELAY", adc_delay)
        self.wr("CAP_WORDS", self.geometry["cap_words"] if cap_words is None else cap_words)
        self.wr("CLEAR_FAULT", 1)
        runs = self.rd("RUN_COUNT")
        self.wr("ARM", 1)
        self.wait("cap_done", timeout=timeout)
        if not dac_loop:
            self.wait("run_done", timeout=timeout)
        f = self.rd("FAULT")
        if f:
            raise RuntimeError(f"run fault register 0x{f:08x}")
        return self.rd("RUN_COUNT") - runs

    def stop(self):
        self.wr("STOP", 1)

    def readback(self, channel, words=None, addr=0):
        words = self.rd("CAP_WORDS") if words is None else words
        nbytes = words * 16
        buf = self._buffer(nbytes, f"rx{channel}")
        self.dma.recvchannel.transfer(buf, nbytes=nbytes)
        self.wr("RB_CHANNEL", channel)
        self.wr("RB_ADDR", addr)
        self.wr("RB_WORDS", words)
        self.wr("RB_START", 1)
        self.dma.recvchannel.wait()
        buf.invalidate()
        return np.frombuffer(bytes(buf[:nbytes]), dtype="<i2").copy()

    def capture_all(self, words=None):
        return np.stack([self.readback(ch, words) for ch in range(8)])
