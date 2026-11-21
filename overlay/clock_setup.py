# SPDX-License-Identifier: BSD-3-Clause
"""Program the HamGeek clock with a local copy of the vendor Vitis example."""

from contextlib import closing, contextmanager
from pathlib import Path
import re
from time import monotonic, sleep
from zipfile import ZipFile

_SPI_NODE = Path("/sys/firmware/devicetree/base/axi/spi@ff050000/lmk04828@0")
_OVERLAY_NAME = "hamgeek-lmk04828"


def vendor_profile(archive):
    """Read exactly the 245.76 MHz clock table used by the vendor example."""
    with ZipFile(archive) as source:
        contents = source.read("adda_loop_app/src/devices/spi_ctrl.c").decode()
    match = re.search(r"lmk04828_init_data_245p76\s*\[\s*\]\s*=\s*\{([^}]*)\}", contents)
    if not match:
        raise ValueError("Missing vendor LMK04828 245.76 MHz profile")
    table = re.sub(r"//[^\r\n]*|/\*.*?\*/", "", match[1], flags=re.S)
    tokens = [token.strip() for token in table.split(",") if token.strip()]
    if (len(tokens) != 136 or any(not re.fullmatch(r"0x[0-9a-fA-F]{1,6}", t) for t in tokens)):
        raise ValueError("Unexpected LMK04828 table format or length")
    words = [int(token, 16) for token in tokens]
    if words[0] != 0x90 or words[-1] != 0x1FFF53 or any(word >= 0x800000 for word in words):
        raise ValueError("Unexpected LMK04828 profile or non-write command")
    return words


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
        candidates = [path for path in Path("/sys/bus/spi/devices").glob("spi*")
                      if path.joinpath("of_node").resolve() == _SPI_NODE]
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
def configured_clock(archive):
    """Keep clock control lines requested throughout ADC capture."""
    import gpiod
    from gpiod.line import Direction, Value

    profile = vendor_profile(archive)
    chips = [path for path in Path("/sys/bus/gpio/devices").glob("gpiochip*")
             if "ff0a0000.gpio" in path.resolve().parts]
    if len(chips) != 1:
        raise RuntimeError("Could not identify the ZynqMP PS GPIO controller")
    active, inactive = Value.ACTIVE, Value.INACTIVE
    sync, ref0, ref1, reset = 26, 33, 34, 43
    levels = {sync: inactive, ref0: active, ref1: inactive, reset: active}
    settings = {pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=value)
                for pin, value in levels.items()}

    with _clock_spi() as spi, gpiod.request_lines(
        f"/dev/{chips[0].name}", consumer="hamgeek-adc00", config=settings
    ) as pins:
        def write(word):
            spi.xfer2(list(word.to_bytes(3, "big")))

        def pll2_locked():
            return bool(spi.xfer2([0x81, 0x83, 0])[2] & 2)

        sleep(0.01)
        pins.set_value(reset, inactive)
        sleep(0.5)
        for word in profile:
            write(word)
            sleep(0.01)
        write(0x014B1E)
        write(0x014C40)

        deadline = monotonic() + 8.0
        stable_reads = 0
        while stable_reads < 8:
            if monotonic() >= deadline:
                raise TimeoutError("LMK04828 PLL2 did not lock with the vendor clock profile")
            stable_reads = stable_reads + 1 if pll2_locked() else 0
            sleep(0.02)

        pins.set_value(sync, active)
        sleep(0.001)
        pins.set_value(sync, inactive)
        sleep(0.5)
        yield
