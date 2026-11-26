# J35 Fin clock plan

## D · LMK04828 distribution mode

J35 feeds the AC-coupled CLKin1/Fin pins. The profile uses the bipolar input
(`CLKin1_TYPE=0`, 0x146[1]) and selects the Fin route with
`CLKin1_OUT_MUX=0` and `VCO_MUX=2`. TI specifies 0.001–3100 MHz for
Fin, 0.25–2.0 Vpp at the pin for a single-ended signal, and 0.15 V/ns
minimum 20–80% slew. TI recommends at least 0.5 V/ns for the stated jitter
performance. The ordinary PLL-reference CLKin path has a separate 750 MHz
limit. PLL2's reference input is OSCin. [TI LMK04828, §§7.5 and 9.4.5](https://www.ti.com/lit/ds/symlink/lmk04828.pdf#page=12)

| Address | Stock → Fin | Change |
| --- | --- | --- |
| 0x138 | 0x21 → 0x41 | Select Fin for clock distribution. |
| 0x13F | 0x03 → 0x02 | Disable the feedback mux. |
| 0x140 | 0x00 → 0xF0 | Power down PLL1, the VCO LDO, VCO and OSCin. Keep SYSREF and its delay circuit on. |
| 0x147 | 0x3A → 0x13 | Route CLKin1 to Fin and turn off the CLKin0 output mux. |
| 0x14B | 0x1E → 0x00 | Disable PLL1 holdover and tracking, the manual DAC, and LOS. |
| 0x166 | 0x00 → 0x04 | Suppress internal VCO calibration on the PLL2 N write. |
| 0x173 | 0x00 → 0x60 | Power down PLL2 and its prescaler. |

The helper verifies routing and power settings before using the stock r5
SYNC sequence to align dividers and start continuous SYSREF. PLL1 and PLL2
lock bits should both be clear. LMK loss-of-signal detection requires MOS
input mode, so the raw LOS field cannot validate the bipolar Fin signal.
The presence gate uses SDCLKout5 at J32. [TI LMK04828, §§9.3.2.1 and 9.7](https://www.ti.com/lit/ds/symlink/lmk04828.pdf#page=37)

## CALC · Rates, levels and delays

At 1.5 GHz, the device dividers at 0x100–0x130 (stride 8) are /6 and
SYSREF_DIV (0x13A:0x13B) is /240. At 3 GHz those ratios are /12 and /480.
Both yield 250 MHz device references and 6.25 MHz SYSREF. SDCLKout5 follows
the DCLKout4 divider. Output formats, enable states and muxes match the
stock r5 clock plan. Delay codes remain the same and their time increments
depend on the Fin period. Software SYNC sets the divider epoch, so frequency
lock to 10 MHz alone does not establish the same phase on a cold boot.

A +3 dBm sine into a matched 50 Ω load is 0.894 Vpp. The pin swing depends
on the J35 launch, termination, coupling capacitor and Fin input
impedance. The transfer at high frequency remains open. See the
[3 GHz register diff against stock r5](fin3000.diff) and the
[documented bench results](../../README.md#external-device-clock-j35).
