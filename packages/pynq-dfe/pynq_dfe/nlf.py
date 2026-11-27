"""PG401 single-grid, single-phase real-coefficient FIR configuration."""
from operator import index

from pynq import DefaultIP


class NlfIP(DefaultIP):
    bindto = ["xilinx.com:ip:xdfe_nlf:1.1"]

    def load_fir(self, coefficients):
        """Load 1–16 contiguous real signed Q1.15 taps with the stream idle.

        The output is two signed 25-bit components with 18 fractional bits.
        Unit i selects delay tap 3+i. Each enabled LUT has a constant
        coefficient at every index, so the response is linear.
        """
        taps = tuple(map(index, coefficients))
        if not 1 <= len(taps) <= 16 or any(not -32768 <= x <= 32767 for x in taps):
            raise ValueError("expected 1–16 signed 16-bit coefficients")
        if self.read(0x24) & 0xfff != 0x101:
            raise ValueError("requires one phase, one NLF, AXI-Lite LUT access")
        self.write(0x1004, 0)       # Disable the units while changing delay taps
        self.write(0x1008, 0)       # Direct bank selection
        self.write(0x008, 2)        # Write PONG
        self.write(0x1110, 0)       # LUT0 only
        self.write(0x1114, 0)       # Single-phase delay line
        self.write(0x1118, 0)       # Q25.18 output
        self.write(0x111c, 0)       # Internal index
        for unit, coefficient in enumerate(taps):
            self.write(0x100c + 4 * unit, 3 + unit)
            self.write(0x108c + 4 * unit, 3 | (3 << 16))
            self.write(0x104, unit << 16)
            for _ in range(256):
                self.write(0x108, coefficient & 0xffff)
        self.write(0x008, 3)        # Read the programmed PONG bank
        self.write(0x014, 1)        # Clear grid 1 overflow flags
        self.write(0x1004, (1 << len(taps)) - 1)

    def configure_luts(self, signal_delays, index_delays, scale=0):
        """Configure an idle one-phase grid for external per-sample indexing.

        Each signal delay has two independently delayed index taps (0..15).
        Both LUTs contribute. Leave units disabled until their RAMs are loaded.
        """
        signals = tuple(map(index, signal_delays))
        indices = tuple(tuple(map(index, pair)) for pair in index_delays)
        if not 1 <= len(signals) <= 16 or len(indices) != len(signals):
            raise ValueError("one index-delay pair per signal tap required")
        if any(len(pair) != 2 for pair in indices):
            raise ValueError("expected two index delays")
        if any(d not in range(16) for d in (*signals, *(d for pair in indices for d in pair))):
            raise ValueError("delay outside the single-phase grid")
        if index(scale) not in range(13) or self.read(0x24) & 0xfff != 0x101:
            raise ValueError("invalid scale or incompatible NLF configuration")
        self.write(0x1004, 0)
        self.write(0x1008, 0)
        self.write(0x1110, (1 << len(signals)) - 1)
        self.write(0x1114, 0)
        self.write(0x1118, scale)
        self.write(0x111c, 1)
        for unit, (signal, (a, b)) in enumerate(zip(signals, indices)):
            self.write(0x100c + 4 * unit, 3 + signal)
            self.write(0x108c + 4 * unit, (3 + a) | ((3 + b) << 16))

    def write_lut_bank(self, tables, write_bank):
        """Write complex integer Q1.15 tables of shape (units, 2, 256).

        Selecting a write bank makes the opposite bank active for reading.
        After programming, select the new read bank before starting a frame.
        """
        import numpy as np
        values = np.asarray(tables)
        if (values.ndim != 3 or values.shape[1:] != (2, 256)
                or not 1 <= len(values) <= 16 or write_bank not in (0, 1)):
            raise ValueError("invalid bank or LUT shape")
        for part in (values.real, values.imag):
            if not np.all((part >= -32768) & (part <= 32767) & (part == np.rint(part))):
                raise ValueError("expected signed 16-bit coefficient codes")
        words = ((values.real.astype(np.int64) & 65535)
                 | ((values.imag.astype(np.int64) & 65535) << 16))
        self.write(0x008, 2 + write_bank)
        for unit, pair in enumerate(words):
            for lut, table in enumerate(pair):
                self.write(0x104, (unit << 16) | (lut << 8))
                for word in table:
                    self.write(0x108, int(word))
