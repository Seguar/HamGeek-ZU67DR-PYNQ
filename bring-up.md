# HamGeek XCZU67DR PCIe V1 PYNQ bring-up

The image uses PYNQ 4.0.0, Ubuntu 24.04 and AMD EDF 2025.2. The board schematic and vendor Vivado project identify the part as XCZU67DR-2FSVE1156I. The build uses the vendor PS preset and its 4 GiB memory map.

The first image boots the processing system. It provides the FPGA manager and XRT so compatible overlays can be loaded separately. ADC00/J36 capture requires a card-specific RFDC overlay and clock setup. The vendor bare-metal application and its bitstream are kept outside the SD image.

Use the [standard release image](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1) on media with at least 8,266,973,184 bytes. The compact variant requires 7,645,691,904 bytes and passed boot from the fitted eMMC. Check the archive and expanded image against the supplied SHA-256 files. Write to the whole target device. Connect one copy of a given image at boot to keep its partition IDs unique.

With power off, set SW1 in pole order 1–4. Up (ON, marked “1”) is logic 1. Pole 1 is MODE bit 0.

| Medium | MODE[3:0] | Pole 1 | Pole 2 | Pole 3 | Pole 4 |
| --- | --- | --- | --- | --- | --- |
| microSD (SD1) | `0101` | Up | Down | Up | Down |
| eMMC (eMMC18) | `0110` | Down | Up | Up | Down |

Connect the PS UART at 115200 baud, 8N1, and the RJ45 port to a DHCP-enabled bench network. Expect FSBL, U-Boot, Linux and then Jupyter on port 9090. Use the standard PYNQ factory credentials on an isolated bench network.

Record the serial log from power-on, board model, root mount, block device list and exact image SHA-256. Run `pynq-selftest` for the installed image checks.
