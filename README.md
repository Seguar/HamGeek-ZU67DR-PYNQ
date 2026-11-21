# HamGeek ZU67DR PYNQ

Experimental PYNQ 4.0.0 microSD image for the HamGeek XCZU67DR PCIe V1 card. The vendor schematic and hardware handoff identify the part as XCZU67DR-2FSVE1156I. This image uses Ubuntu 24.04, Vivado 2025.2 and AMD EDF.

## Download and boot

Download the image from [GitHub Releases](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases). The archive is about 2.0 GiB and expands to 8,266,973,184 bytes. Use a 16 GB or larger microSD card. Check the archive against `SHA256SUMS` and the expanded image against `RAW-SHA256SUMS`. Use an SD writer to flash the expanded disk image to the whole microSD. Select SD1 2.0 boot on the card.

See the [bring-up instructions](bring-up.md) for the mode pins, serial console and Ethernet setup.

## ADC00/J36 overlay

The optional [ADC00 capture overlay](overlay/README.md) captures 32,768 real samples at 2.4576 GS/s from J36. It is available as a separate [overlay prerelease](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/adc00-v0.1.0-rc1) for the PYNQ 4.0.0 SD image.

## Validation

The disk image passed offline partition and filesystem checks. The bootloader headers and device tree were inspected, and PYNQ, NumPy and JupyterLab package metadata were checked under AArch64 userspace emulation. First boot and hardware I/O checks on the target card are pending. RFDC sample capture requires a separate application overlay.

[Build inputs](build-inputs.json), [release manifest](release-manifest.json) and [validation evidence](validation/) record what was built and checked. The operating system and packages are distributed under their respective licenses. See [PYNQ v4.0.0](https://github.com/Xilinx/PYNQ/tree/v4.0.0), the [AMD EDF manifest](https://github.com/Xilinx/yocto-manifests/tree/amd-edf-rel-v25.11.1), the [AMD Linux sources](https://github.com/Xilinx/linux-xlnx) and the [Ubuntu source archives](https://launchpad.net/ubuntu/noble/+sources). Package names and versions are listed in the [Ubuntu package manifest](validation/debian-packages.tsv).
