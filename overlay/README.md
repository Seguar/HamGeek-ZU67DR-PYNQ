# ADC00/J36 capture overlay

This optional PYNQ 4.0.0 overlay captures a single software-triggered frame from J36 on the HamGeek XCZU67DR PCIe V1. It maps J36 to tile 224, block 0. Tile 226 accepts the card's 245.76 MHz LMK reference and forwards the sampling clock through tile 225 to tile 224. The capture path uses real 16-bit RFDC words at 2.4576 GS/s. It records 32,768 samples, about 13.33 µs, in PL block RAM. Each acquisition is a new snapshot. The software trigger has no defined phase relationship to a bench generator.

## Use on the card

Place `adc00.bit` and `adc00.hwh` beside `adc00.py` from the same release. The Python script writes a NumPy archive with signed raw samples, sample rate and connector metadata. Use the PYNQ virtual environment. Clock setup and hardware access need the privileges provided by the image's PYNQ environment.

If the board clock is already configured for the 245.76 MHz reference and locked, run:

```sh
python adc00.py --clock-ready --output adc00.npz
```

With the original HamGeek `adda_loop.zip` Vitis package, the clock helper reads the vendor 245.76 MHz table locally. Keep `clock_setup.py` and the release's `lmk04828.dtbo` beside the capture script. Install Python `gpiod` version 2 and `spidev` in the PYNQ environment. The helper uses the image's SPI1 controller at `ff050000` and waits for LMK PLL2 lock before loading the bitstream.

```sh
python adc00.py --vendor-vitis-zip /path/to/adda_loop.zip --output adc00.npz
```

To check the setup, capture a known in-band tone and verify its frequency using the sample rate in the archive. The fixed frame and raw sample format support bench analysis without a DMA driver. The overlay provides no DAC output and has no external-trigger or simultaneous multichannel capture path.

## Build

Use Vivado 2025.2 and the original vendor `rfevm_rf_adaloop.zip` for the PS preset. The extractor runs locally so the vendor archive and preset can stay with the card owner.

```sh
python extract_ps.py /path/to/rfevm_rf_adaloop.zip vendor-ps.tcl
vivado -mode batch -source build.tcl -tclargs "$PWD/vendor-ps.tcl"
dtc -@ -I dts -O dtb -o output/lmk04828.dtbo lmk04828.dts
```

The RTL simulation uses two successive acquisitions on independent clocks and checks every memory word, including a gap in stream valid. Run it with the Vivado tools:

```sh
xvlog -sv capture.v capture_tb.v
xelab -timescale 1ns/1ps capture_tb -s capture_tb
xsim capture_tb -runall
```

See AMD's [RF Data Converter product guide](https://docs.amd.com/r/en-US/pg269-rf-data-converter) for the RFDC clock and data interfaces. Physical capture and clock programming remain pending.
