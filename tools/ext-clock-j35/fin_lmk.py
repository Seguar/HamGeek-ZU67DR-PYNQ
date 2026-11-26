"""PS-only LMK programming using the RowTiming r5 SPI transport."""
from contextlib import contextmanager
from pathlib import Path
from time import sleep

PROFILES = {mhz: Path(__file__).with_name(f"lmk04828_fin{mhz}.txt") for mhz in (1500, 3000)}
DIVIDER_REGS = tuple(range(0x100, 0x131, 8))
CHANGES = {
    0x138: (0x41, "VCO_MUX=2, route CLKin1 Fin into distribution"),
    0x13F: (0x02, "FB_MUX_EN=0, disable unused feedback mux"),
    0x140: (0xF0, "PLL1, VCO LDO, VCO and OSCin off; SYSREF and delay still on"),
    0x147: (0x13, "manual CLKin1, CLKin1 to Fin, unused CLKin0 off"),
    0x14B: (0x00, "disable PLL1 tracking, forced holdover and manual DAC"),
    0x166: (0x04, "inhibit internal VCO calibration on PLL2 N write"),
    0x173: (0x60, "power down PLL2 and its prescaler"),
}


def fin_words(stock):
    result = []
    for word in stock:
        address = word >> 8
        if address in CHANGES:
            word = (word & ~0xFF) | CHANGES[address][0]
        result.append(word)
    return result


def fin1500_words(stock):
    """1.5 GHz Fin, preserving the stock 250 MHz device clock and 6.25 MHz SYSREF."""
    result = []
    for word in fin_words(stock):
        addr = word >> 8
        if addr in DIVIDER_REGS:
            if word & 0x1F != 12:
                raise ValueError(f"Expected a stock /12 divider at {addr:#x}")
            word = (word & ~0x1F) | 6
        elif addr == 0x13A:
            word &= ~0xFF
        elif addr == 0x13B:
            word = (word & ~0xFF) | 0xF0
        result.append(word)
    return result


def status(read):
    pll1, pll2, clkin = (read(a) for a in (0x182, 0x183, 0x184))
    if (pll1 | pll2) & 0x02:
        raise RuntimeError(f"Unexpected LMK lock indication: 0x182={pll1:#04x}, 0x183={pll2:#04x}")
    return {
        "r182": pll1, "r183": pll2, "r184": clkin,
        "pll1_locked": bool(pll1 & 2), "pll2_locked": bool(pll2 & 2),
        "clkin1_los_raw": bool(clkin & 2), "los_valid": False,
    }


def program_fin(write, read, words, sync, pause=sleep):
    regs = {w >> 8: w & 0xFF for w in words}
    for word in words:
        write(word)
        pause(0.01)
    # Check SPI identity and clock routing before running the stock divider SYNC.
    expected = {0x003: 0x06, 0x004: 0xD0, 0x005: 0x5B}
    expected.update({addr: regs[addr] for addr in (
        0x138, 0x139, 0x13A, 0x13B, 0x13F, 0x140, 0x143, 0x144, 0x146,
        0x147, 0x14B, 0x166, 0x173, *DIVIDER_REGS,
    )})
    for address, value in expected.items():
        actual = read(address)
        if actual != value:
            raise RuntimeError(f"LMK {address:#05x} read {actual:#04x}, expected {value:#04x}")
    status(read)
    sync(write)
    for address, value in ((0x139, 0x03), (0x143, 0x11), (0x144, 0xFF)):
        if read(address) != value:
            raise RuntimeError(f"LMK post-SYNC readback mismatch at {address:#05x}")
    return status(read)


@contextmanager
def configured_fin(frequency_mhz):
    """Hold the rt250 GPIO/SPI resources through the externally clocked cycle."""
    import gpiod
    from gpiod.line import Direction, Value
    import rt250_clock as clk
    from rt250_lmk_hw import _clock_spi

    words = clk.load_profile_file(PROFILES[frequency_mhz])
    stock = clk.load_profile_file(Path(clk.__file__).with_name("lmk04828_vco3000.txt"))
    expected = fin1500_words(stock) if frequency_mhz == 1500 else fin_words(stock)
    if words != expected:
        raise ValueError("Fin profile differs from the approved edits to the stock r5 profile")
    chips = [p for p in Path("/sys/bus/gpio/devices").glob("gpiochip*")
             if "ff0a0000.gpio" in p.resolve().parts]
    if len(chips) != 1:
        raise RuntimeError("Could not identify ZynqMP PS GPIO")
    g = clk.LMK_GPIO
    levels = {g["sync"]: Value.INACTIVE, g["ref0"]: Value.ACTIVE,
              g["ref1"]: Value.INACTIVE, g["reset"]: Value.ACTIVE}
    settings = {pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=value)
                for pin, value in levels.items()}
    with _clock_spi() as spi, gpiod.request_lines(
            f"/dev/{chips[0].name}", consumer="rt250-lmk-fin", config=settings) as pins:
        def write(word):
            spi.xfer2(list(word.to_bytes(3, "big")))

        def read(address):
            return spi.xfer2([0x80 | (address >> 8), address & 0xFF, 0])[2]

        sleep(0.01)
        pins.set_value(g["reset"], Value.INACTIVE)
        sleep(0.5)
        initial = program_fin(write, read, words, clk.sync_and_start_sysref)
        yield initial, lambda: status(read)
