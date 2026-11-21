# SPDX-License-Identifier: BSD-3-Clause
"""Capture one frame of native ADC00/J36 samples on the HamGeek PCIe V1 card."""

import argparse
from pathlib import Path
from time import monotonic, sleep

import numpy as np

SAMPLE_RATE_HZ = 2_457_600_000
SAMPLES_PER_FRAME = 32768
COMMAND_ADDRESS = 0x82040000
DATA_ADDRESS = 0x82050000


class ADC00:
    """Load the capture overlay after the board reference clock has locked."""

    def __init__(self, bitstream):
        from pynq import MMIO, Overlay

        self.overlay = Overlay(str(bitstream))
        for instance, address in (("command_status", COMMAND_ADDRESS),
                                  ("sample_buffer", DATA_ADDRESS)):
            metadata = self.overlay.ip_dict.get(instance) or self.overlay.mem_dict.get(instance)
            if metadata is None or metadata["phys_addr"] != address:
                raise ValueError(f"Unexpected {instance} address in overlay metadata")
        self.control = MMIO(COMMAND_ADDRESS, 0x10000)
        self.buffer = MMIO(DATA_ADDRESS, SAMPLES_PER_FRAME * 2)
        self._command = 0

    def capture(self, timeout=1.0):
        """Return a copy of a consecutive frame of signed 16-bit RFDC samples."""
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if (self.control.read(8) & 1) != self._command:
            raise RuntimeError("Capture already outstanding. Check RFDC clock or reload overlay.")
        self._command ^= 1
        self.control.write(0, self._command)
        deadline = monotonic() + timeout
        while (self.control.read(8) & 1) != self._command:
            if monotonic() >= deadline:
                raise TimeoutError("No complete ADC frame. Check the LMK clock and RFDC startup.")
            sleep(0.001)
        return self.buffer.array.view("<i2").copy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitstream", type=Path, default=Path("adc00.bit"))
    parser.add_argument("--output", type=Path, default=Path("adc00.npz"))
    clock = parser.add_mutually_exclusive_group(required=True)
    clock.add_argument("--vendor-vitis-zip", type=Path, help="Configure the clock from adda_loop.zip")
    clock.add_argument("--clock-ready", action="store_true", help="Use an already locked clock")
    args = parser.parse_args()
    if args.vendor_vitis_zip:
        from clock_setup import configured_clock

        with configured_clock(args.vendor_vitis_zip):
            samples = ADC00(args.bitstream).capture()
    else:
        samples = ADC00(args.bitstream).capture()
    np.savez(args.output, samples=samples, sample_rate_hz=SAMPLE_RATE_HZ, connector="J36")
    print(f"Saved {samples.size} raw samples to {args.output}")


if __name__ == "__main__":
    main()
