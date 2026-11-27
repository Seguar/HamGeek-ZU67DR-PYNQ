"""Static one-antenna hard PC-CFR v8.0 control, using PYNQ MMIO.

Offsets and field packing follow the generated hard-IP demonstration testbench.
The caller must quiesce the input before configuring the active coefficient bank.
"""

from operator import index


class HardCFR:
    """Three peak-cancellation stages followed by a 384-sample WCFR window."""

    def __init__(self, mmio):
        self.mmio = mmio

    def configure(self, coefficients, threshold, *, window=False):
        """Load an odd Hermitian pulse in signed Q14, then check the threshold.

        Coefficients are (I, Q) integer pairs in time order on the fourfold sample grid. Threshold is the
        complex-envelope amplitude in signed sample counts.
        """
        threshold = index(threshold)
        taps = [(index(i), index(q)) for i, q in coefficients]
        if not 1 <= threshold <= 32767:
            raise ValueError("threshold outside 1..32767 counts")
        if not 3 <= len(taps) <= 8191 or len(taps) % 2 != 1:
            raise ValueError("expected an odd pulse length in 3..8191")
        if any(not -32768 <= v <= 32767 for tap in taps for v in tap):
            raise ValueError("coefficient exceeds signed 16 bits")
        if taps != [(i, -q) for i, q in reversed(taps)]:
            raise ValueError("pulse must be conjugate symmetric")
        if taps[len(taps) // 2] != (16384, 0):
            raise ValueError("Q14 pulse must have unit center amplitude")

        # Four phases occupy successive RAM regions. Pad symmetrically so
        # each region has equal depth and the last value is the pulse center.
        pad = ((-1 - len(taps)) % 8) // 2
        taps = [(0, 0)] * pad + taps + [(0, 0)] * pad
        half = taps[:len(taps) // 2 + 1]
        packed = [pair for phase in range(4) for pair in half[phase::4]]
        write = self.mmio.write
        write(0x040, 0)  # Interface configuration
        write(0x044, 15)  # Initialize all stages before writing their parameters
        write(0x1E4, 1)  # 384-sample WCFR window
        write(0, len(taps))
        write(4, 0)  # Bank zero
        for offset in (0x008, 0x1DC, 0x1E0):
            write(offset, threshold)
        for stage, generators in enumerate((8, 6, 4)):
            write(0x00C + 4 * stage, (generators << 20) | (32 << 10) | 9)
        for tap, (i, q) in enumerate(packed):
            write(0x8000 + tap * 4, (i & 0xffff) | ((q & 0xffff) << 16))
        write(0x380, 0xffffffff)
        write(0x380, 0)
        write(0x044, 15 if window else 7)
        actual = self.mmio.read(8)
        if actual != threshold:
            raise RuntimeError(f"threshold readback {actual}, expected {threshold}")
