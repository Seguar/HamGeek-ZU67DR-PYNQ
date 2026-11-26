# SPDX-License-Identifier: BSD-3-Clause
"""LMK04828 profile for the single 250 MHz reference (VCO 3000 MHz) on the
HamGeek XCZU67DR, derived from the vendor 245.76 MHz table and the LMK04828
datasheet (TI SNAS605AS).

Evidence tags: V tool/built, CALC calculated, D datasheet, ASSUMED.
"""

import re
from time import monotonic, sleep
from zipfile import ZipFile

# ---------------------------------------------------------------- clock plan
OSCIN_HZ = 19_200_000          # PLL2 reference (card VCXO). CALC: both vendor tables (VCO 2457.6 and
                               # 2400 MHz) only work out with 19.2 MHz at OSCin.
PLL2_R, PLL2_P, PLL2_N = 4, 5, 125
PFD2_HZ = OSCIN_HZ // PLL2_R   # 4.8 MHz (the highest PFD that reaches 3000 MHz from 19.2 MHz) CALC
VCO_HZ = PFD2_HZ * PLL2_P * PLL2_N   # 3000 MHz, inside VCO1 2920-3080 MHz (D)
OUT_DIV = 12
REF_HZ = VCO_HZ // OUT_DIV     # 250 MHz on every clock output CALC
SYSREF_DIV = 480
SYSREF_HZ = VCO_HZ // SYSREF_DIV     # 6.25 MHz CALC
DAC_HZ = 10_000_000_000        # DAC tile PLL x40 (V: IP accepts 250 MHz -> 10 GS/s)
ADC_HZ = 2_500_000_000         # ADC tile 226 PLL x10, distributed to tiles 224 and 225
DAC_FABRIC_HZ = 625_000_000    # 16 samples per word (V)
ADC_FABRIC_HZ = 312_500_000    # 8 samples per word (V)
GTY_GBPS = (20, 10)            # QPLL0 10 GHz = 250 MHz x 40, full / half rate (V)
SYSREF_DDLY_CYCLES = 6         # SDCLKout7 (analog SYSREF) digital delay, code 5
PL_SYSREF_DDLY_CYCLES = 4      # SDCLKout11 (PL SYSREF) digital delay, code 3
SYSREF_LEAD_NS = SYSREF_DDLY_CYCLES * 1e9 / VCO_HZ - 0.080      # 1.92 ns after the DAC reference edge (CALC, D eq. 3)
PL_SYSREF_LEAD_NS = PL_SYSREF_DDLY_CYCLES * 1e9 / VCO_HZ - 0.080   # 1.25 ns after the PL clock edge (CALC)

assert VCO_HZ == 3_000_000_000 and REF_HZ == 250_000_000 and SYSREF_HZ == 6_250_000
for _f in (DAC_FABRIC_HZ, ADC_FABRIC_HZ, REF_HZ, ADC_HZ // 16, DAC_HZ // 16):
    assert _f % SYSREF_HZ == 0, _f            # PG269 MTS rule (SYSREF divides every PL / tile clock)

# ---------------------------------------------------------------- register overrides
# address: (mask, value, note). Applied on top of the vendor 245.76 MHz table.
OVERRIDES = {
    0x100: (0x1F, OUT_DIV, "DCLKout0 /12 (FPGA_MCLK F14/F13, unused)"),
    0x108: (0x1F, OUT_DIV, "DCLKout2 /12 -> ADC tile 226 reference"),
    0x110: (0x1F, OUT_DIV, "DCLKout4 /12 divider (feeds SDCLKout5 = GTY reference)"),
    0x114: (0x20, 0x00, "SDCLKout5 = device clock (250 MHz to J32 -> GTY refclk)"),
    0x117: (0x77, 0x50, "SDCLKout5 LVPECL 1600 mV; DCLKout4 off (it lands on tile-226 VIN pins)"),
    0x118: (0x1F, OUT_DIV, "DCLKout6 /12 (unused DAC tile 227 input)"),
    0x11C: (0x3F, 0x2A, "SDCLKout7 = SYSREF, DDLY code 5 (6 VCO cycles) -> analog SYSREF"),
    0x120: (0x1F, OUT_DIV, "DCLKout8 /12 -> PL clock E12/D12 (250 MHz)"),
    0x128: (0x1F, OUT_DIV, "DCLKout10 /12 (output powered down)"),
    0x12C: (0x3F, 0x26, "SDCLKout11 = SYSREF, DDLY code 3 (4 VCO cycles) -> PL SYSREF E14/D14"),
    0x12D: (0x1F, 0x00, "SDCLKout11 analog delay off (trim on the bench)"),
    0x12F: (0x07, 0x00, "DCLKout10 off; SDCLKout11 remains PL SYSREF"),
    0x130: (0x1F, OUT_DIV, "DCLKout12 /12 -> DAC tile 228 (IP DAC1) reference"),
    0x138: (0x60, 0x20, "VCO_MUX = VCO1 (2920-3080 MHz)"),
    0x139: (0x03, 0x00, "SYSREF_MUX = normal SYNC during divider alignment"),
    0x13A: (0x1F, SYSREF_DIV >> 8, "SYSREF_DIV[12:8] (480)"),
    0x13B: (0xFF, SYSREF_DIV & 0xFF, "SYSREF_DIV[7:0] -> 6.25 MHz"),
    0x140: (0x0E, 0x00, "SYSREF, SYSREF DDLY powered"),
    0x143: (0xFF, 0x91, "SYSREF_CLR=1, SYNC_EN=1, SYNC_MODE=1 (manual SYNC by SYNC_POL)"),
    0x144: (0xFF, 0x00, "all dividers take part in SYNC"),
    0x160: (0x0F, PLL2_R >> 8, "PLL2_R[11:8]"),
    0x161: (0xFF, PLL2_R & 0xFF, "PLL2_R = 4 -> PFD 4.8 MHz"),
    0x162: (0xFD, (PLL2_P << 5) | (0 << 2), "PLL2_P = 5, OSCin_FREQ = 0 (0-63 MHz, D; vendor uses 1), doubler off"),
    0x163: (0x03, 0x00, "PLL2_N_CAL[17:16]"),
    0x164: (0xFF, 0x00, "PLL2_N_CAL[15:8]"),
    0x165: (0xFF, PLL2_N & 0xFF, "PLL2_N_CAL = 125 (only used in cascaded zero-delay)"),
    0x166: (0x07, 0x00, "PLL2_FCAL_DIS = 0, PLL2_N[17:16]"),
    0x167: (0xFF, 0x00, "PLL2_N[15:8]"),
    0x168: (0xFF, PLL2_N & 0xFF, "PLL2_N = 125 (write starts VCO calibration)"),
}
VENDOR_OSCIN_FREQ_FIELD = 1     # fallback if PLL2 does not lock with the datasheet value


def vendor_profile(archive):
    """Exactly the vendor 245.76 MHz table (136 writes) from adda_loop.zip."""
    with ZipFile(archive) as source:
        contents = source.read("adda_loop_app/src/devices/spi_ctrl.c").decode()
    return parse_vendor_table(contents)


def parse_vendor_table(contents):
    match = re.search(r"lmk04828_init_data_245p76\s*\[\s*\]\s*=\s*\{([^}]*)\}", contents)
    if not match:
        raise ValueError("Missing vendor LMK04828 245.76 MHz profile")
    table = re.sub(r"//[^\r\n]*|/\*.*?\*/", "", match[1], flags=re.S)
    tokens = [t.strip() for t in table.split(",") if t.strip()]
    words = [int(t, 16) for t in tokens]
    if len(words) != 136 or words[0] != 0x90 or words[-1] != 0x1FFF53:
        raise ValueError("Unexpected LMK04828 table format or length")
    return words


def profile_3000(vendor_words, oscin_freq_field=0):
    """Apply OVERRIDES to the vendor table; returns 24-bit SPI words in vendor order."""
    present = {w >> 8 for w in vendor_words}
    missing = set(OVERRIDES) - present
    if missing:
        raise ValueError(f"vendor table lacks registers {sorted(hex(m) for m in missing)}")
    out = []
    for w in vendor_words:
        a = w >> 8
        if a in OVERRIDES:
            mask, value, _ = OVERRIDES[a]
            if a == 0x162:
                value = (value & ~0x1C) | ((oscin_freq_field & 7) << 2)
            w = (w & ~mask) | (value & mask)
        out.append(w)
    return out


def profile_for_rate(archive, rate, divider):
    """Derive the test profile in the vendor archive's write order."""
    baseline = vendor_profile(archive)
    if rate == 2.94912:
        # Align output modes and SYSREF for the 2457.6 MHz VCO.
        changes = {
            0x117: (0x77, 0x50),
            0x11C: (0x3F, 0x2A),
            0x128: (0x1F, 0x0A),
            0x12C: (0x3F, 0x26),
            0x139: (0x03, 0),
            0x13A: (0x1F, 2),
            0x13B: (0xFF, 0x80),
        }
        return [
            (word & ~changes[word >> 8][0]) | changes[word >> 8][1]
            if word >> 8 in changes else word
            for word in baseline
        ]
    changes = {0x13A: divider >> 8, 0x13B: divider & 0xFF}
    return [
        (word & ~0xFF) | changes[word >> 8] if word >> 8 in changes else word
        for word in profile_3000(baseline)
    ]


def decode(words):
    """Key fields of a profile, for review."""
    r = {w >> 8: w & 0xFF for w in words}
    osc = OSCIN_HZ
    pll2_r = ((r[0x160] & 0x0F) << 8) | r[0x161]
    p = (r[0x162] >> 5) & 7 or 8
    dbl = 2 if r[0x162] & 1 else 1
    n = ((r[0x166] & 3) << 16) | (r[0x167] << 8) | r[0x168]
    vco = osc * dbl / pll2_r * p * n
    sysdiv = ((r[0x13A] & 0x1F) << 8) | r[0x13B]
    fmt = {0: "off", 1: "LVDS", 2: "HSDS6", 3: "HSDS8", 4: "HSDS10", 5: "LVPECL1600", 6: "LVPECL2000", 7: "LCPECL"}
    outs = []
    for x, base in zip(range(0, 14, 2), range(0x100, 0x138, 8)):
        div = r[base] & 0x1F or 32
        dfmt = fmt[r[base + 7] & 7]
        sfmt = fmt[(r[base + 7] >> 4) & 7]
        smux = "SYSREF" if r[base + 4] & 0x20 else "dclk"
        sddly = (r[base + 4] >> 1) & 0xF
        f_s = vco / sysdiv if smux == "SYSREF" else vco / div
        outs.append(dict(dclk=f"DCLKout{x}", div=div, f_mhz=vco / div / 1e6, fmt=dfmt,
                         sdclk=f"SDCLKout{x + 1}", s_src=smux, s_mhz=f_s / 1e6, s_fmt=sfmt,
                         s_ddly_cycles=(sddly + 1) if sddly else 0))
    return dict(vco_mhz=vco / 1e6, pfd2_mhz=osc * dbl / pll2_r / 1e6, pll2_p=p, pll2_n=n,
                vco_sel="VCO1" if (r[0x138] >> 5) & 3 == 1 else "VCO0",
                sysref_div=sysdiv, sysref_mhz=vco / sysdiv / 1e6, outputs=outs)


# ---------------------------------------------------------------- hardware access
LMK_GPIO = dict(sync=26, ref0=33, ref1=34, reset=43)   # PS MIO lines (vendor / other overlay)


def program(spi_write, spi_read3, words, lock_timeout=8.0, log=print):
    """Write a profile, wait for PLL2 lock, align dividers, start continuous SYSREF.

    spi_write(word24); spi_read3(addr) -> byte. Returns True when PLL2 locked.
    """
    for w in words:
        spi_write(w)
        sleep(0.01)
    spi_write(0x014B1E)      # PLL1 holdover with manual DAC (as the vendor flow, no CLKin)
    spi_write(0x014C40)
    deadline = monotonic() + lock_timeout
    stable = 0
    while stable < 8:
        if monotonic() > deadline:
            return False
        stable = stable + 1 if spi_read3(0x183) & 0x02 else 0
        sleep(0.02)
    sync_and_start_sysref(spi_write)
    settings = decode(words)
    log(f"LMK04828: PLL2 locked with programmed VCO {settings['vco_mhz']:.1f} MHz "
        f"and SYSREF {settings['sysref_mhz']:.4f} MHz continuous")
    return True


def sync_and_start_sysref(spi_write):
    """Datasheet 9.3.2.1: SYNC all dividers (SYNC_POL toggle), then lock them out and run SYSREF."""
    spi_write(0x0143B1)      # SYNC_POL = 1 (SYNC edge), SYSREF_CLR held
    sleep(0.001)
    spi_write(0x014391)      # SYNC_POL = 0
    spi_write(0x0144FF)      # SYNC_DIS for every divider: SYSREF no longer resets them
    spi_write(0x014311)      # release SYSREF_CLR (held > 15 distribution cycles)
    spi_write(0x013903)      # SYSREF_MUX = continuous
