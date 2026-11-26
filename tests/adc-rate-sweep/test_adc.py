"""Capture both quad ADC tiles into PS DDR and save the eight raw channels."""
import argparse
from contextlib import nullcontext
from pathlib import Path
import subprocess
from time import sleep

import numpy as np

from clock_guard import progress, verify_bundle
from lmk_profile import profile_for_rate
from adc_capture import AdcCapture, check_hwh
from lmk_spi import configured_clock

CLOCKS = {2.5: (312.5, 6.25, 480), 2.9375: (367.1875, 0.78125, 3840),
          2.94912: (368.64, 3.84, None)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bitfile", type=Path)
    parser.add_argument("--rate", type=float, choices=CLOCKS, required=True)
    parser.add_argument("--adc-avcc", type=float, required=True, help="measured TP16 rail in volts")
    parser.add_argument("--words", type=int, default=8192)
    parser.add_argument("--mts-target", type=int, default=-1)
    parser.add_argument("--program-lmk", action="store_true")
    parser.add_argument("--vendor-vitis-zip", type=Path, help="your copy of adda_loop.zip")
    parser.add_argument("--output", type=Path, default=Path("adc_capture.npz"))
    parser.add_argument("--status-only", action="store_true",
                        help="download and check PS-clocked status without accessing RFDC or DMA")
    args = parser.parse_args()
    fabric, sysref, divider = CLOCKS[args.rate]
    if not 0.980 <= args.adc_avcc <= 1.040:
        parser.error("TP16 must be within the DS926 0.980 to 1.040 V range")
    if not 1 <= args.words <= 8192 or args.mts_target < -1:
        parser.error("capture words must be 1 to 8192 and MTS target at least -1")
    progress("Verify ADC bundle and clock topology")
    selected_rate, selected_fabric = verify_bundle(args.bitfile)
    # Vivado serializes the RFDC fabric frequency to three decimal places in HWH.
    if selected_rate != args.rate or abs(selected_fabric - fabric) > 0.001:
        parser.error(f"overlay is {selected_rate} GS/s with {selected_fabric} MHz fabric clock")
    matches, rows = check_hwh(args.bitfile.with_suffix(".hwh"))
    if not matches:
        raise RuntimeError(f"HWH address validation failed: {rows}")
    clock = nullcontext()
    if args.program_lmk:
        if args.vendor_vitis_zip is None:
            parser.error("--program-lmk requires --vendor-vitis-zip")
        profile = profile_for_rate(args.vendor_vitis_zip, args.rate, divider)
        clock = configured_clock(words=profile, log=progress)
    helper = args.bitfile.resolve().with_name("synchronize-rfdc")
    progress("Program LMK profile and wait for PLL2" if args.program_lmk else "Use the current LMK profile")
    with clock:
        rt = AdcCapture(args.bitfile, expected_rate=args.rate, expected_sysref=sysref,
                       status_only=args.status_only)
        if args.status_only:
            return
        try:
            progress("Start ADC MTS")
            mts = subprocess.run([str(helper), str(args.mts_target)], stdout=subprocess.PIPE,
                                 text=True, timeout=30, check=True)
            progress(mts.stdout.strip())
            sleep(0.01)
            progress("Arm and capture eight ADC channels")
            rt.run(cap_words=args.words)
            data = rt.capture_all(args.words)
            progress(f"Save capture to {args.output}")
            with args.output.open("xb") as output:
                np.savez(output, samples=data, fs_hz=args.rate * 1e9,
                         mts=mts.stdout, adc_avcc_v=args.adc_avcc)
            progress(f"{data.shape[0]} channels × {data.shape[1]} samples at {args.rate} GS/s")
        finally:
            progress("Stop capture engine")
            rt.stop()


if __name__ == "__main__":
    main()
