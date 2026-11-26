# HamGeek ZU67DR PYNQ

Experimental PYNQ 4.0.0 image for the HamGeek XCZU67DR PCIe V1 card (XCZU67DR-2FSVE1156I). The image uses Ubuntu 24.04, Vivado 2025.2 and AMD EDF.

The HamGeek listing covers the ZU27DR, ZU47DR and ZU67DR family. This repository targets the revision 2.1 card fitted with the XCZU67DR. [HamGeek product listing](https://www.hgeek.com/products/xczu27dr-rfsoc-pcie-rf-wireless-development-board-for-zynq-onboard-gnss-module-support-pps-output?variant=47644053504165)

![Top view of the tested HamGeek XCZU67DR revision 2.1 PCIe card](docs/images/board-rev21.jpg)

## Download and boot

[RC2](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1-rc2) provides two images. Verify the archive against `SHA256SUMS` and the expanded file against `RAW-SHA256SUMS`. The standard image needs **8,266,973,184 bytes** of media. The 8 GB image needs **7,645,691,904 bytes** and fits the 7,818,182,656-byte eMMC measured on the tested board. Check the media's actual capacity before writing. Use a raw disk writer and select SD1 2.0 boot for microSD. The compact RC2 image was written to eMMC and verified by read-back on the tested card. Fresh RC2 hardware boot is pending for both media.

See the [bring-up instructions](bring-up.md) for the boot switches and serial console, the [board support files](port/README.md) for image preparation, and the [bench report](https://seguar.github.io/hamgeek-zu67dr-bringup/) for the measured results.

## Board revision 2.1 findings and resolutions

### ADC_AVCC at TP16

TP16 measured **0.93 V**, below the XCZU67DR recommended **0.980–1.040 V** range. The released ADC utilities require an in-range measurement. U82 (TPS74901) sets ADC_AVCC according to `Vout = 0.8 V × (1 + R_top/R_bottom)`. The V1 schematic shows 750 Ω over 4.7 kΩ, which predicts 0.928 V. The following rework is calculated and awaits hardware verification. Hardware modifications are at the owner's risk. [AMD DS926](https://docs.amd.com/r/en-US/ds926-zynq-ultrascale-plus-rfsoc/Recommended-Operating-Conditions) · [TI TPS74901](https://www.ti.com/lit/ds/symlink/tps74901.pdf)

1. Power off and disconnect the card. On revision 2.1, check R610, R487 and R485 next to U82. Use continuity and resistance measurements to identify the output-to-FB resistor (R_top) and confirm the FB-to-ground resistor (R_bottom) is 4.7 kΩ before selecting a replacement.
2. Replace R_top with a 1% resistor matching the fitted pads (0402 or 0603). With a 4.7 kΩ bottom resistor, 1.24 kΩ (E96) gives 1.011 V nominal and 1.21 kΩ gives 1.006 V. Leave U80 (DAC_AVCC) at its measured, in-spec 0.925 V.
3. Power up with a current limit. Verify U82 VIN (nominal 1.2 V) and BIAS (nominal 5 V). The 5 V bias meets the device's 2.7 V minimum and provides more than 1.6 V above the target output. Measure **1.00–1.02 V at TP16** before running RF tests.

### DAC_AVTT at TP17

TP17 measured **2.5 V**. Use the fixed **20 mA** DAC setting on this board. The vendor's 40 mA VOP example requires 3.0 V. For VOP or fixed 32 mA operation, a candidate hardware modification is to set U78 (TPS74801) to 3.0 V. With power disconnected, identify and measure the fitted feedback divider near R703/R482/R707. Select the top resistor for the measured bottom resistor using `R_top = R_bottom × (3.0/0.8 − 1)`. Verify the result at TP17 on current-limited power before changing DAC mode. Check the supplies under load. VCC3V3 gives 0.3 V nominal input headroom, and the 5 V BIAS supply gives 2 V above the output. Confirm both meet dropout requirements at the intended load. This rework also awaits hardware verification. [AMD RF-DAC VOP compatibility](https://docs.amd.com/r/en-US/pg269-rf-data-converter/VOP-Backwards-Compatibility-Gen-3/DFE) · [TI TPS74801](https://www.ti.com/lit/ds/symlink/tps74801.pdf)

| Symptom or finding | How to resolve |
| --- | --- |
| RC1 sees microSD as write-protected and fails to mount the ext4 root (EROFS). The socket lacks a write-protect line. | Use RC2, or add `disable-wp` to SDHCI1 and deploy the rebuilt Linux DTB. The patched DTB booted on the tested card. |
| LMK04828 PLL1 cannot discipline the fixed 19.2 MHz OCXO. | Use the onboard clock with PLL2 locked and PLL1 in holdover. External distribution through J35 and a VCXO rework are options below. |
| Incorrect RF-ADC Nyquist parity degrades calibration and SFDR. | Select 1 for an odd input zone or 2 for an even zone. Read back the setting and let calibration settle. [ADC00 Nyquist helper](tests/adc-nyquist/) |
| The tested 8 GB Kioxia eMMC showed prior use. | Back up its contents first. Check the actual capacity, then use the RC2 8 GB image if it fits. |
| Earlier r2/r4 rate-sweep overlays could hang during AXI access. | Use only matched r5 bundles. Run status-only before RFDC setup and capture. [Rate-sweep instructions](tests/adc-rate-sweep/) |
| The tested board lacks a battery-backed clock. | Check `timedatectl status` after boot. If NTP is blocked, set UTC from a trusted source before TLS, package installation or timestamped measurements. |

### DAC2 / J48

DAC2 has a hardware fault in its output path. A scope, spectrum analyzer and direct RF loop measured the same high-pass-shaped loss. Direct loop peak levels were about 29 dB low at 500 MHz and 37 dB low at 100 MHz relative to the healthy loops. RFDC settings matched the other DAC blocks on the tile. ADC2 responded normally to an independent source. Visual inspection of J48 and the output components is pending. [Bring-up report](https://seguar.github.io/hamgeek-zu67dr-bringup/#dac2-verdict)

## PL DDR4

The vendor PDF's PL DDR4 pinout is incorrect for the tested card. Its build failed memory calibration. The [corrected pinout](docs/pl-ddr4-pinout.md) was recovered by boundary scan on the sister XCZU47DR and verified on the XCZU67DR. The PL memory is **one x32 DDR4-2400 interface, 2 GiB**. DQ, DQS and DM are in bank 66. Command and address are in bank 65, with **RESET_n on AE16**. The corrected build calibrated and passed 31 addresses in each polarity plus five full 2 GiB passes with zero mismatches.

## Clock and SYSREF input options

J35 (CLK1_IN) is a 50 Ω terminated, AC-coupled input to LMK04828 CLKin1. J32 (CLK_OUT) carries LMK SDCLKOUT5, nominally 245.76 MHz in the 245.76 MHz plan. J64 (PPS_IN) reaches a PL pin. The unfitted J66 SMA, J67 selection jumper and U48 TCXO footprints provide a path to LMK CLKin0 on the net named SYSREF_IN. PS GPIO 26 drives LMK SYNC.

**Measured on one card.** The onboard 3000 MHz VCO plan supported MTS at 2.5 and 2.9375 GS/s. The 250 MHz reference plan uses 6.25 MHz SYSREF at 2.5 GS/s and 0.78125 MHz SYSREF at 2.9375 GS/s. The 245.76 MHz reference plan uses 3.84 MHz SYSREF and supported MTS at 2.94912 GS/s.

**External timing options awaiting hardware verification**

| Objective | Candidate configuration |
| --- | --- |
| Use an external sample reference | Feed a compatible source into J35. Configure CLKin1 as the PLL2 reference or use distribution mode with an external clock at the required frequency. |
| Supply or trigger SYSREF | Populate J66/J67 and configure the CLKin0 path for external SYSREF, or configure the LMK to generate SYSREF on a SYNC event from PS GPIO 26. |
| Timestamp PPS | Capture J64 edges in the PL and timestamp them against the acquisition clock. |
| Discipline the onboard oscillator to 10 MHz | Rework the fixed OCXO path for a compatible VCXO and verify PLL1 tuning range, loop response and lock against the external reference. |
| Synchronize multiple cards | Distribute a common sample reference and coherently timed SYSREF to each card. Account for cable and distribution skew, run MTS on each card and measure inter-card phase and latency across restarts. |

TODO: System requirements to be confirmed.

## Measured r5 ADC rate sweep

Each run on the bring-up installation captured **8 × 65,536 samples** with MTS. ADC0 received a 150 MHz tone at −6 dBm. The generators were unfiltered and ADC_AVCC measured **0.93 V**, outside the recommended range.

| Sample rate (GS/s) | MTS latency (tiles 0/1) | ADC0 SNR relative to full scale (dB) | ADC0 NSD (dBFS/Hz) |
| ---: | ---: | ---: | ---: |
| 2.5 | 80/80 | 61.5 | −152.52 |
| 2.9375 | 76/76 | 61.0 | −152.63 |
| 2.94912 | 76/76 | 61.0 | −152.65 |

Measured crosstalk was ≤ −73 dBc relative to the driven channel at the tested tones (150 and 400 MHz). The largest coupled tone was on ADC2 with ADC1 driven at 400 MHz.

## Home-bench results

- Eight DAC-to-ADC loops were measured with ADC_AVCC at 0.93 V. Median absolute agreement with the lab prediction was 0.34 dB. Healthy-loop phase span was at most 0.131° at 100 MHz over ten warm reloads.
- PCIe-edge GTY lanes 0–3 passed 60 s of PRBS31 at 7.8125, 10, 10.3125, 15.625 and 20 Gb/s per lane using the Si5341 reference and an unpowered fixture. The 20 Gb/s soak stopped after 111.1 s with one lane 3 error.

[Interactive bench report](https://seguar.github.io/hamgeek-zu67dr-bringup/) · [Measured-characteristics datasheet (PDF)](https://seguar.github.io/hamgeek-zu67dr-bringup/HamGeek-ZU67DR-measured-characteristics-v1.1.pdf)

## RF and DDR test tools

Download the matching archives from the [RC2 release](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1-rc2). Verify each archive against `SHA256SUMS` and the extracted files against the bundle's `artifacts.sha256`.

- [ADC00/J36](overlay/README.md) captures 32,768 real samples at 2.4576 GS/s and remains available from its [overlay prerelease](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/adc00-v0.1.0-rc1).
- [r5 ADC rate-sweep overlays](tests/adc-rate-sweep/) cover 2.5, 2.9375 and 2.94912 GS/s, with status checks before RFDC setup and capture.
- [8-DAC/8-ADC RF loopback](tests/rf-loopback/) uses the fixed 20 mA DAC mode, with a status-only entry point.
- [ADC Nyquist helper](tests/adc-nyquist/) reads or sets ADC00 Nyquist parity and calibration mode.
- [PL DDR4 test](tests/pl-ddr4/) describes the historical RC2 bundle. Its vendor-map overlay failed calibration. The verified build uses the [corrected pinout](docs/pl-ddr4-pinout.md).

## Validation

RC2 passed offline partition, FAT/ext4, device-tree and AArch64 QEMU checks. Fresh boot and hardware I/O on the published RC2 bytes are pending. The r5 ADC hardware measurements used a separate bring-up installation. The [RC1 build inputs](build-inputs.json), [RC1 release manifest](release-manifest.json) and [validation directory](validation/) describe the base image. The RC2 download includes its own manifest and checksums.
