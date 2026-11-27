# OFDM loopback on XCZU67DR

The block design uses two xdfe_ofdm 2.2 cores, one DL and one UL, connected by the carrier sample, ID, valid and TUSER lines. Both process two parallel antenna lanes with interleave one, 16-bit I/Q, FR1, no phase compensation and RE-mapped packet order. AXI DMA loads a 1272-element frequency-domain symbol into replay RAM. The hardware sends the symbol once per OFDM symbol period. PS software arms a one-packet snapshot of the UL output. All RF converters are outside this digital path.

The 100 MHz PS clock drives the DMA. Cascaded clock generators produce 96 MHz and then 491.52 MHz. The timebase drives frame bit zero every 10 ms. CCID 0 uses one of 16 sample slots for 30.72 MS/s. At 15 kHz spacing each symbol has 2048 samples, plus 160 prefix samples on symbols 0 and 7 of each slot and 144 elsewhere. The selected 106 resource blocks occupy 1272 subcarriers. DMA input order starts at DC, continues through positive frequencies, and finishes with the negative-frequency half. Bits 15:0 are I and bits 31:16 are Q. Lane one occupies the high word.

Build from a fresh directory using Vivado 2025.2 and the r5 PS preset specified in the mixer/CCF example.

```sh
vivado -mode batch -source /path/to/overlay/dfe-ofdm/build.tcl -tclargs /path/to/vendor-ps.tcl ./ofdm-build
```

Use the matching bit and HWH files together. Run the dfe-ofdm notebook with the pynq_dfe Python bindings and libxdfeofdm.so available. Set DFE_BITFILE to the bitstream path and DFE_EXAMPLES to the package examples directory. The notebook writes raw and predicted samples in its working directory.

Carrier parameters and packet ordering follow [PG434](https://docs.amd.com/r/en-US/pg434-rfsoc-dfe-ofdm). The fixed-point model uses 32/1024 DL scale, 16/1024 UL scale, convergent rounding and signed 16-bit saturation after each transform. The product of the two scales and the transform length is one. The numerical acceptance criteria are in the notebook and reference code.

On XCZU67DR, both parallel lanes returned bin 37 at 16,385 codes (NumPy prediction 16,385). Seeded QPSK round-trip EVM was −79.78 dB relative to the transmitted symbol, and −79.11 dB relative to the quantized NumPy prediction. The AMD bit-accurate model matched all 1,272 complex outputs in each lane for both vectors. Sequence, saturation and overflow flags were zero during the capture windows. Timing closed at +0.016 ns setup and +0.010 ns hold with zero failing endpoints and zero critical CDC endpoints. Four of 18 DFE_FFT sites were used.
