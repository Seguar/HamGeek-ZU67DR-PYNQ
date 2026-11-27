# Single-antenna hard CFR

Tested with Vivado 2025.2. The block design selects the PC-CFR 8.0 hard implementation with three cancellation iterations and a 384-sample window postprocessor. All streaming, AXI-Lite, DMA and memory interfaces share the 100 MHz PS fabric clock. One signed IQ word (I low, Q high) is accepted per cycle. The frame controller loads 16,384 words from MM2S, plays them continuously, captures the corresponding output clocks into RAM, then drains through S2MM with TLAST. Between frames the CFR receives complex zeros. The RF converters are outside this design.

Build with the RowTiming r5 vendor PS preset and a new output directory.

```sh
vivado -mode batch -source build.tcl -tclargs /path/to/vendor-ps.tcl /path/to/output
```

The script checks the preset hash and routed primitive count, writes timing, routing, utilization and CDC reports, and exports matching bit, HWH and XSA files. AMD describes the selectable hard-core configurations in [PB008](https://docs.amd.com/r/en-US/pb008_pc_cfr/DFE-CFR-Primitive). The generated static-mode demonstration testbench defines the register protocol used by the Python driver.

Install the branch's pynq-dfe package on the board. Set CFR_BITFILE to the bit file alongside its matching HWH. Open notebooks/dfe-cfr.ipynb and run all cells. Set CFR_EXAMPLE to the examples/cfr directory when running outside notebooks/. CFR_OUTPUT selects the destination for raw captures, measurements and the two-panel CCDF and spectrum plot. The committed expectations.json contains limits fixed with the NumPy reference before acquisition.

The main measurement enables three PC stages (enable register value 7). A second acquisition enables WCFR too (value 15). The driver accepts chronological, Hermitian Q14 coefficients at four times the input sample rate. It pads to a length of 8k−1 and writes each of the four fractional phases contiguously. An isolated-peak measurement identified the phase-bank order. A simple chronological RAM write gives an incorrect cancellation pulse between integer sample positions.
