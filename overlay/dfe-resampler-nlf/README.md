# Resampler and linear FIR on XCZU67DR

Build with Vivado 2025.2 and the archived vendor PS preset used by the mixer/CCF overlay.
Supply the preset and a fresh output directory as the two Tcl arguments to
`vivado -mode batch -source build.tcl -tclargs vendor-ps.tcl out`. The script checks the
preset hash and each IP licence property. It writes filter_test.bit, .hwh and .xsa,
their SHA-256 manifest, and implementation reports in the output directory.

The shared 100 MHz PS fabric clock drives DMA, control, both resamplers and the FIR.
All data paths stay in PL and PS DDR. One input DMA transfer loads 1024 beats
of 128 bits each. The frame engine replays three periods, honoring input ready.
It counts output-valid beats over the third accepted input period and buffers the first
1024 returns for the output DMA. Both the count and any stream faults must be
checked before using the capture. The independent count detects missing or extra
beats even though the DMA output buffer always has length 8192 bytes.
Keep the GPIO mode fixed through both transfers.

| GPIO mode | Selected stream | Input per beat, low bits first | Output per beat |
|---|---|---|---|
| 0 | PG392 uplink 2/3 | 3 complex 16-bit I/Q pairs | 2 complex 16-bit I/Q pairs |
| 1 | PG392 downlink 2× | 1 complex 16-bit I/Q pair | 2 complex 16-bit I/Q pairs |
| 2 | PG401 one-grid FIR | 1 complex 16-bit I/Q pair | 25-bit I followed by 25-bit Q |

GPIO channel 2 reports FSM state in [2:0], observed output beats in [13:3] and
fault bits in [18:15] (short input frame, input stall during measurement,
FIFO error if present, arithmetic overflow). The PG392 common-clock configurations
omit the rate-change CDC FIFO and its error pin.

The notebooks take the absolute bitfile path in `DFE_BITFILE`, repository root in
`DFE_REPO`, and output directory in `DFE_OUTPUT`. Install pynq-dfe or put
`packages/pynq-dfe` on PYTHONPATH. Keep the matching HWH next to the bitfile.
Each notebook independently downloads the overlay and runs its tests.

The resampler models are generated on x86-64 using Vivado's PG392 Linux
bit-accurate C model. Extract the archive in a private working directory and build
`examples/resampler/golden.cpp` there with `g++ -I. golden.cpp -L.
-lIp_xdfe_resampler_v1_0_bitacc_cmodel -Wl,-rpath,. -o golden`. From that directory
run the example's make_golden.py to regenerate its compressed NumPy reference vectors.
The NLF model uses integer Q1.15 coefficients and signed 25-bit outputs with 18
fractional bits at OUT_SCALE=0.

[PG392 configuration](https://docs.amd.com/r/en-US/pg392-rfsoc-dfe-resampler/Configuration-Tab)
· [PG401 register map](https://docs.amd.com/r/en-US/pg401-xdfe-nlf/Memory-Address-Map)
· [PG401 output format](https://docs.amd.com/r/en-US/pg401-xdfe-nlf/Output-Data-Fixed-Point-Format)
