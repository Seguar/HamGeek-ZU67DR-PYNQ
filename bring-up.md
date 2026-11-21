# HamGeek XCZU67DR PCIe V1 PYNQ bring-up

The image uses PYNQ 4.0.0, Ubuntu 24.04 and AMD EDF 2025.2. The board schematic and vendor Vivado project identify the part as XCZU67DR-2FSVE1156I. The build uses the vendor PS preset and its 4 GiB memory map.

The first image boots the processing system. It provides the FPGA manager and XRT so compatible overlays can be loaded separately. ADC00/J36 capture requires a card-specific RFDC overlay and clock setup. The vendor bare-metal application and its bitstream are kept outside the SD image.

Use a 16 GB or larger microSD. The final image must fit the card's reported byte capacity. Verify the compressed and expanded image against the supplied SHA-256 files. Flash the expanded disk image to the whole microSD using the workstation's SD-card writer.

Use SD1 2.0 boot. The schematic lists MIO MODE[3:0] = 0101 for this setting. Follow the schematic and board markings for switch orientation. Connect the PS UART at 115200 baud, 8N1, and the RJ45 port to a DHCP-enabled bench network. Expect FSBL, U-Boot, Linux and then the PYNQ/Jupyter service. Consult the DHCP leases for the board's IP address and open Jupyter on that address. Use the standard PYNQ factory credentials on an isolated bench network.

Record the serial log from power-on, board model, root mount, block device list and IP address. Run pynq-selftest for the installed image checks. Save the exact image SHA-256 with the log. The physical card was offline during image preparation.
