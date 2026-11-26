# Board support and RC2 image preparation

[board.dtsi](HamGeekZU67DR/edf_bsp/board.dtsi) is the board-specific include for the PYNQ 4.0.0 AMD EDF port. RC2 adds `disable-wp` on SDHCI1. The port uses a separately obtained hardware handoff for the PS build. See [RC1 build inputs](../build-inputs.json) and [PYNQ's EDF build documentation](https://github.com/Xilinx/PYNQ/blob/v4.0.0/sdbuild/README.md).

RC2 was prepared from the clean RC1 raw image and a compact derivative of that image. It keeps RC1's kernel and BOOT.BIN and applies the same SDHCI1 property directly to the packaged Linux DTB. The FAT partition's extlinux stanza selects the ext4 root via MBR PARTUUID. On first boot the growth script follows the active MMC root device and the boot script uses the boot partition on the same image.

The [image preparation script](image/prepare-rc2.sh) checks its input image hash before copying it to a new directory. Use Ubuntu 24.04 with device-tree-compiler, dosfstools, e2fsprogs, util-linux, and AArch64 binfmt/QEMU support. Prepare the dependency files locally and pass their directory to the script. It builds the spidev extension and installs both packages offline into the image's PYNQ virtual environment. The required artifacts and hashes are pinned in [clock-deps.txt](image/clock-deps.txt). [gpiod 2.6.0](https://pypi.org/project/gpiod/2.6.0/) · [spidev 3.8](https://pypi.org/project/spidev/3.8/)

```sh
python3 -m pip download --no-deps --only-binary=:all: --platform manylinux2014_aarch64 \
  --implementation cp --python-version 3.12 --abi cp312 -d wheels gpiod==2.6.0
python3 -m pip download --no-deps --no-binary=:all: -d wheels spidev==3.8
sudo ./port/image/prepare-rc2.sh HamGeekZU67DR-PYNQ-4.0.0-rc1.img standard wheels output-standard
# From the compact RC1 raw image with the input hash recorded in prepare-rc2.sh:
sudo ./port/image/prepare-rc2.sh HamGeekZU67DR-PYNQ-4.0.0-rc1-8GB-bench.img 8GB wheels output-8GB
```

Use the full image for cards with at least 8,266,973,184 bytes. The 8 GB image needs 7,645,691,904 bytes and keeps the usual package and runtime installation with smaller filesystem reserve and regenerable caches removed. Each variant has a separate disk ID. Two copies of the same variant share IDs, so expose only one of them to the board at boot.
