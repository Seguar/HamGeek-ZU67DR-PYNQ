# Standalone DFE FFT on XCZU67DR

AXI DMA connects the PS buffers to xdfe_fft 1.0 in both directions on the 100 MHz PL clock. The transform control is a 16-bit AXI stream with fields for log2 size, direction and an optional new maximum size. The example drives 0x0018 for a forward 256-point transform using the configured maximum of 256. The input is a packet of 256 signed 16-bit I/Q pairs. The core produces unscaled, bit-reversed output. Each component occupies 29 signed bits in a zero-padded 32-bit lane. Software sign-extends bit 28 and reverses the eight address bits before comparing with NumPy.

Build with Vivado 2025.2 using the r5 PS preset from the mixer/CCF example.

```sh
vivado -mode batch -source /path/to/overlay/dfe-fft/build.tcl -tclargs /path/to/vendor-ps.tcl ./fft-build
```

Use the matching bit and HWH files together. Set DFE_BITFILE to the bitstream path and DFE_EXAMPLES to the package examples directory, then execute the dfe-ofdm-standalone-fft notebook. It saves the raw and decoded samples and checks bin, amplitude and EVM. The FFT has no AXI-Lite register bank. [PG390](https://docs.amd.com/r/en-US/pg390-rfsoc-dfe-fft)

The board returned 1,048,576 codes at bin 37, −0.000109 dB from the quantized-input NumPy prediction, with −88.96 dB full-vector EVM. All 256 complex bins matched the AMD bit-accurate model. One of 18 DFE_FFT sites was used. Setup and hold slack were +5.603 ns and +0.010 ns with zero failing endpoints and zero critical CDC endpoints.
