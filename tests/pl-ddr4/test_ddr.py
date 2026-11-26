"""Destructive memory-pattern test of both dedicated PL DDR4 devices."""
import argparse
from time import monotonic, sleep

STATUS = 0x82000000
SIZE = 1 << 31
BANKS = {"pl_ddr0": 0x0400000000, "pl_ddr1": 0x0500000000}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bitfile")
    parser.add_argument("--status-only", action="store_true", help="check MIG calibration without writing DDR")
    parser.add_argument("--window-kib", type=int, default=16)
    args = parser.parse_args()
    if not 4 <= args.window_kib <= 16384 or args.window_kib % 4:
        parser.error("window must be 4 to 16384 KiB and page aligned")

    from pynq import MMIO, Overlay

    overlay = Overlay(args.bitfile, download=False)
    calib = overlay.ip_dict.get("calibration_status", {})
    if (calib.get("phys_addr"), calib.get("addr_range")) != (STATUS, 65536):
        raise RuntimeError("calibration GPIO does not match HWH")
    for bank, expected in BANKS.items():
        item = overlay.mem_dict.get(bank, overlay.ip_dict.get(bank, {}))
        if (item.get("phys_addr"), item.get("addr_range")) != (expected, SIZE):
            raise RuntimeError(f"unexpected HWH memory map for {bank}: {item}")

    overlay.download()
    calibration = MMIO(STATUS, 65536)
    deadline = monotonic() + 30
    while calibration.read(0) & 3 != 3:
        if monotonic() >= deadline:
            raise TimeoutError(f"PL DDR calibration bits {calibration.read(0) & 3:02b}")
        sleep(0.02)
    print("Both MIGs calibrated")
    if args.status_only:
        return

    nbytes = args.window_kib * 1024
    offsets = (0, SIZE // 4, SIZE // 2, 3 * SIZE // 4, SIZE - nbytes)
    windows = [(bank, offset, MMIO(base + offset, nbytes))
               for bank, base in BANKS.items() for offset in offsets]
    for address_pattern in (True, False):
        for invert in (0, 0xFFFFFFFF):
            label = ("address" if address_pattern else "checkerboard") + (" inverted" if invert else "")

            def pattern(window, byte):
                word = byte // 4
                if address_pattern:
                    value = ((word * 0x9E3779B9) ^ ((window + 1) * 0x11111111)) & 0xFFFFFFFF
                else:
                    value = 0x55555555 if word & 1 else 0xAAAAAAAA
                return value ^ invert

            for i, (_, _, mmio) in enumerate(windows):
                for byte in range(0, nbytes, 4):
                    mmio.write(byte, pattern(i, byte))
            for i, (bank, offset, mmio) in enumerate(windows):
                if calibration.read(0) & 3 != 3:
                    raise RuntimeError("MIG lost calibration during the test")
                for byte in range(0, nbytes, 4):
                    expected = pattern(i, byte)
                    actual = mmio.read(byte)
                    if actual != expected:
                        raise RuntimeError(f"{bank}+{offset + byte:#x}: got {actual:#010x}, "
                                           f"expected {expected:#010x} ({label})")
            print(f"PASS {label}, both banks, {len(windows) * nbytes:,} bytes")
