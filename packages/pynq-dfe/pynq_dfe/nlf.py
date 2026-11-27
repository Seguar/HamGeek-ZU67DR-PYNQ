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
