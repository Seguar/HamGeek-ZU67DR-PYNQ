# SPDX-License-Identifier: BSD-3-Clause
"""Program the card's LMK04828 over PS SPI1.

Adapted from the HamGeek bench overlay's clock_setup.py (device-tree overlay that
binds spidev to the LMK04828 on spi@ff050000, PS GPIO for SYNC / reference select /
reset). Needs `lmk04828.dtbo` beside this file (dtc -@ -I dts -O dtb lmk04828.dts),
Requires Python gpiod v2 and spidev.
"""

from contextlib import closing, contextmanager
from pathlib import Path
from time import sleep

import lmk_profile as clk

_SPI_NODE = Path("/sys/firmware/devicetree/base/axi/spi@ff050000/lmk04828@0")
_OVERLAY_NAME = "hamgeek-test-lmk04828"


@contextmanager
def _clock_spi():
    import spidev
    overlays = Path("/sys/kernel/config/device-tree/overlays")
    if not overlays.is_dir():
        raise RuntimeError("Device-tree overlay configfs is unavailable")
    directory = overlays / _OVERLAY_NAME
    directory.mkdir()
    try:
        directory.joinpath("dtbo").write_bytes(Path(__file__).with_name("lmk04828.dtbo").read_bytes())
        candidates = [p for p in Path("/sys/bus/spi/devices").glob("spi*")
                      if p.joinpath("of_node").resolve() == _SPI_NODE]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one LMK04828 on SPI1, found {len(candidates)}")
        target = candidates[0]
        target.joinpath("driver_override").write_text("spidev\n")
        Path("/sys/bus/spi/drivers/spidev/bind").write_text(target.name + "\n")
        bus, cs = map(int, target.name.removeprefix("spi").split("."))
        with closing(spidev.SpiDev()) as device:
            device.open(bus, cs)
            device.mode = 0
            device.max_speed_hz = 500000
            yield device
    finally:
        directory.rmdir()


@contextmanager
def configured_clock(words, log=print):
    """Program the profile and keep the control lines requested while the caller works."""
    import gpiod
    from gpiod.line import Direction, Value
    chips = [p for p in Path("/sys/bus/gpio/devices").glob("gpiochip*")
             if "ff0a0000.gpio" in p.resolve().parts]
    if len(chips) != 1:
        raise RuntimeError("Could not identify the ZynqMP PS GPIO controller")
    act, ina = Value.ACTIVE, Value.INACTIVE
    g = clk.LMK_GPIO
    levels = {g["sync"]: ina, g["ref0"]: act, g["ref1"]: ina, g["reset"]: act}
    settings = {pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=v) for pin, v in levels.items()}
    with _clock_spi() as spi, gpiod.request_lines(f"/dev/{chips[0].name}", consumer="hamgeek-test-lmk",
                                                   config=settings) as pins:
        def write(word):
            spi.xfer2(list(word.to_bytes(3, "big")))

        def read3(addr):
            return spi.xfer2([0x80 | (addr >> 8), addr & 0xFF, 0])[2]

        sleep(0.01)
        pins.set_value(g["reset"], ina)
        sleep(0.5)
        if not clk.program(write, read3, words, log=log):
            log("PLL2 did not lock with this profile; retrying with the vendor OSCin_FREQ value 1")
            alt = [(w & ~0x1C) | (clk.VENDOR_OSCIN_FREQ_FIELD << 2) if (w >> 8) == 0x162 else w for w in words]
            if not clk.program(write, read3, alt, log=log):
                raise TimeoutError("LMK04828 PLL2 did not lock with the selected profile")
        sleep(0.2)
        yield
