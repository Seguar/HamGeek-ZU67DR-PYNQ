# Single-channel NR PRACH extraction

This PL-only overlay uses the XCZU67DR hard DFE_PRACH, one antenna, one active component carrier, one physical RACH channel, and signed 16-bit I/Q. The smallest legal catalog capacity is two CC IDs. ID 0 carries one sample every 16 clocks. ID 1 occupies the unused slots. One static schedule spans all ten 15 kHz slots in each 10 ms radio frame. The frame and the RACH update use separate TUSER bits, with the update in the middle of the preceding frame.

The PS uploads 1,024 packed samples (I in the low halfword) over AXI DMA MM2S. A BRAM replays them at 15.36 MS/s. Two MMCMs derive 96 MHz and then 245.76 MHz from the existing 100 MHz PL clock. The RACH NCO mixes down a positive 3.84 MHz offset and the DDC decimates by four. The expected output is 3.84 MS/s. The dfeprach driver uses a fixed 30.72 MHz normalization for its frequency calculation. At this clock, setting UserFreq to 1024 yields a signed 32-bit phase increment of −2³⁰.

The capture RAM counts every valid output in clocks 131072 through 196607 of a radio frame. It saves the first 1,024 records for S2MM and exposes the independent 17-bit count in GPIO channel 2, with the done flag in bit 17. Each 64-bit record contains I/Q in bits 31:0, the frame clock in 53:32, output TID in 61:54 and core TLAST in bit 62. GPIO output bit 0 enables replay and bit 1 arms the capture. Clear both before replacing the waveform. DMA TLAST marks the end of the snapshot.

## Build and run

Use Vivado 2025.2 and the r5 PS preset obtained with the repository's overlay/extract_ps.py. From this directory run:

```sh
vivado -mode batch -source build.tcl -tclargs /path/to/vendor-ps.tcl /path/to/new-output
```

The script checks core licensing and routed setup/hold timing before exporting the bitstream, HWH, XSA and hashes. On the board, make the PR #9 pynq_dfe package and libxdfeprach.so available. Set PRACH_BITFILE to the matching bitstream next to its HWH, PRACH_OUTPUT to a writable data directory, and run notebooks/dfe-prach.ipynb. PRACH_EXAMPLES can override the relative path to the example Python modules.

The model uses the same quantized input as playback, the actual NCO word, an ideal antialias filter and the published 4.25-output-sample group delay. It compares correlation-domain metrics because the model does not contain the hardware filter coefficients. A reference capture establishes the common pipeline delay before measuring a 37-output-sample offset. The short-preamble test repeats the 139-element root's useful OFDM symbol with deterministic noise. It tests extraction rather than cyclic-prefix removal or MAC scheduling. See [AMD PG391](https://docs.amd.com/r/en-US/pg391-rfsoc-dfe-prach/Configuring-RACH-Extraction).

## Board result

Hardware 2.0.6.0 and driver 1.8.0.0 passed all 21 checks. All four acquisitions returned 1,024 samples, uniformly 64 clocks apart. The +3.84 MHz tone landed in the DC bin. The shifted preamble peak was 0.8833 with 16.65 dB peak-to-sidelobe, at a measured relative delay of 38 samples for an injected 37. The noise-only peak was 0.1629. The bit-accurate AMD model reproduced all four captures with a common one-sample circular alignment. Routed WNS/WHS were +0.915/+0.010 ns, with no failing endpoints or critical CDC paths.
