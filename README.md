# HamGeek ZU67DR PYNQ

Experimental PYNQ 4.0.0 image for the HamGeek XCZU67DR PCIe V1 card (XCZU67DR-2FSVE1156I). The image uses Ubuntu 24.04, Vivado 2025.2 and AMD EDF.

## Download and boot

[RC2](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1-rc2) provides two images. Verify the archive against `SHA256SUMS` and the expanded file against `RAW-SHA256SUMS`. The standard image needs **8,266,973,184 bytes** of media. The 8 GB image needs **7,645,691,904 bytes** and fits the 7,818,182,656-byte eMMC measured on the tested board. Check the media's actual capacity before writing. Use a raw disk writer and select SD1 2.0 boot for microSD. Fresh RC2 hardware boot is pending for both media.

See the [bring-up instructions](bring-up.md) for the boot switches and serial console, the [board support files](port/README.md) for image preparation, and the [bench report](https://seguar.github.io/hamgeek-zu67dr-bringup/) for the measured results.

## Board revision 2.1 findings / known issues

- The inspected board lacks the J66/J67 reference selection and U48 10 MHz oscillator. The fitted 19.2 MHz OCXO is fixed, so LMK04828 PLL1 cannot steer it into lock. The onboard clock flow uses PLL2 lock with PLL1 in holdover.
- ADC_AVCC measured **0.93 V** at TP16, below the **0.980–1.040 V** recommended range for ZU6xDR. The released ADC test utilities require an in-range measured voltage. [AMD DS926](https://docs.amd.com/r/en-US/ds926-zynq-ultrascale-plus-rfsoc/Recommended-Operating-Conditions)
- DAC_AVTT measured **2.5 V** at TP17. Use the Gen 3 fixed **20 mA** setting. The vendor examples use 40 mA VOP, which requires a 3.0 V rail. [AMD RF-DAC VOP compatibility](https://docs.amd.com/r/en-US/pg269-rf-data-converter/VOP-Backwards-Compatibility-Gen-3/DFE)
- The tested board has an **8 GB Kioxia eMMC** with evidence of prior use. Hardware and capacity can vary. Back up existing eMMC contents before repurposing it.
- Set RF-ADC Nyquist parity to match the input band. Use setting 1 for odd zones and 2 for even zones. Incorrect parity degraded interleaving calibration and SFDR in the measured sweep. [ADC Nyquist helper](tests/adc-nyquist/)
- The microSD socket has no write-protect line. On the tested board, RC1 saw the card as read-only and failed to mount the ext4 root with EROFS. The patched Linux DTB booted after adding `disable-wp` to SDHCI1. RC2 includes the property in the board source and packaged DTB.
- The tested board has no battery-backed clock. RC2 retains Ubuntu's existing time synchronization service. Check `timedatectl status` after boot. If the network blocks NTP, set UTC from a trusted source before using TLS, package managers or measurement timestamps.

## RF and DDR test tools

Download the matching archives from the [RC2 release](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1-rc2). Verify each archive against `SHA256SUMS` and the extracted files against the bundle's `artifacts.sha256`.

- [ADC00/J36](overlay/README.md) captures 32,768 real samples at 2.4576 GS/s and remains available from its [overlay prerelease](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/adc00-v0.1.0-rc1).
- [r5 ADC rate-sweep overlays](tests/adc-rate-sweep/) cover 2.5, 2.9375 and 2.94912 GS/s, with status checks before RFDC setup and capture.
- [8-DAC/8-ADC RF loopback](tests/rf-loopback/) uses the fixed 20 mA DAC mode, with a status-only entry point.
- [ADC Nyquist helper](tests/adc-nyquist/) reads or sets ADC00 Nyquist parity and calibration mode.
- [PL DDR4 test](tests/pl-ddr4/) checks calibration and exercises dedicated PL DDR4 windows.

## Validation

RC2 passed offline partition, FAT/ext4, device-tree and AArch64 QEMU checks. Fresh boot and hardware I/O on the published RC2 bytes are pending. The r5 ADC hardware measurements used a separate bring-up installation. The [RC1 build inputs](build-inputs.json), [RC1 release manifest](release-manifest.json) and [validation directory](validation/) describe the base image. The RC2 download includes its own manifest and checksums.
