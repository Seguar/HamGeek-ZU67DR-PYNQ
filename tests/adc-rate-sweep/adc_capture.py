# SPDX-License-Identifier: BSD-3-Clause
"""PYNQ driver for the ADC capture overlay."""

from pathlib import Path
from clock_guard import check_fabric, check_rfdc, progress, verify_bundle
from time import monotonic, sleep
import xml.etree.ElementTree as ET

import numpy as np

from adc_registers import REG, STATUS_BITS, ID_VALUE

# Addresses the driver relies on; check_hwh() compares them with the HWH.
EXPECTED = {
    "rfdc": (0x82000000, 0x40000),
    "rowtiming": (0x84000000, 0x10000),
    "dma": (0x84010000, 0x10000),
    "host_firewall": (0x84030000, 0x10000),
}

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

class AdcCapture:
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
        progress("Map PS-clocked capture control and read identity")
        self.regs = MMIO(EXPECTED["rowtiming"][0], EXPECTED["rowtiming"][1])
        if self.rd("ID") != ID_VALUE:
            raise RuntimeError("Capture core ID mismatch")
        self.clock_measurements = check_fabric(self, fabric, expected_sysref)
        if status_only:
            return
        check_rfdc(self.folder)
        progress("Bind the AXI DMA")
        self.dma = self.overlay.dma
        self._buf = {}
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
        """Fabric clock and PL SYSREF rate measured against the CPU clock."""
        c0, s0, t0 = self.rd("CLK_COUNT"), self.rd("SYSREF_COUNT"), monotonic()
        sleep(interval)
        c1, s1, t1 = self.rd("CLK_COUNT"), self.rd("SYSREF_COUNT"), monotonic()
        dt = t1 - t0
        return dict(fabric_mhz=((c1 - c0) & 0xFFFFFFFF) / dt / 1e6,
                    sysref_mhz=((s1 - s0) & 0xFFFFFFFF) / dt / 1e6)

    def _buffer(self, nbytes, key):
        from pynq import allocate
        b = self._buf.get(key)
        if b is None or b.nbytes < nbytes:
            b = allocate(shape=(max(nbytes, 4096),), dtype=np.uint8)
            self._buf[key] = b
        return b

    def run(self, cap_words, timeout=5.0):
        self.wr("DAC_ENABLE", 0)
        self.wr("GTY_ENABLE", 0)
        self.wr("GTY_IDLE", 0)
        self.wr("LOOP", 0)
        self.wr("START_DELAY", 50)
        self.wr("ADC_DELAY", 0)
        self.wr("CAP_WORDS", cap_words)
        self.wr("CLEAR_FAULT", 1)
        runs = self.rd("RUN_COUNT")
        self.wr("ARM", 1)
        self.wait("cap_done", timeout=timeout)
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
