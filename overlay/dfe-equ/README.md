# Single-channel DFE equalizer

The PS drives a simple AXI DMA through HP0. MM2S fills a 2,048-word stimulus RAM. After the packet arrives the frame controller plays one signed IQ pair per accepted sample, starting at address zero. In parallel it records the equalizer output into a second RAM from the same clock edge. S2MM drains that RAM with backpressure and TLAST. The idle input is complex zero. The datapath, AXI control and both DMA channels use the 100 MHz PS clock. This overlay uses digital patterns exclusively and requires no converter or external clock setup.

The IP settings are one antenna, 16-bit I and Q, four complex taps and one TUSER bit. I occupies the low halfword. TUSER[0] pulses once every 16 clocks for activation and bank updates. The equalizer runs continuously between frames. Include leading and trailing zeros to observe complete transients. Send exactly 2,048 uint32 words (8,192 bytes) per packet.

## Build

Use Vivado 2025.2 and the RowTiming r5 vendor PS preset. The Tcl verifies its SHA-256 digest. From a Vivado shell run

```sh
vivado -mode batch -source build.tcl -tclargs /path/to/vendor-ps.tcl /path/to/new-output
```

The output directory contains dfe_equ.bit, the matching HWH, the hardware platform, a SHA-256 manifest and routed reports under run/.

## Run

Install the branch's pynq-dfe package and make libxdfeequ.so available to its loader. Set EQU_BITFILE to the matched bitstream path, EQU_OUTPUT to the measurements directory and add packages/pynq-dfe/examples/equ to PYTHONPATH. Execute notebooks/dfe-equ.ipynb. Each row compares against the programmed coefficients, with one latency determined from the identity impulse. Captures and JSON results are saved before the notebook checks the acceptance limits.

The example uses four-tap arrays in the 2025.2 driver's real-half then imaginary-half order and alternates complex bank pairs. It stages the NEXT_CONTROL complex-mode bit before Initialize because this version computes the new register value without storing it. The example checks CURRENT_CONTROL after initialization and after every bank switch.

See AMD PG394 for [data representation](https://docs.amd.com/r/en-US/pg394-rfsoc-dfe-equalizer/Data-Format) and [coefficient loading](https://docs.amd.com/r/en-US/pg394-rfsoc-dfe-equalizer/Coefficient-Loading-and-Configuration).
