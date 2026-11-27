# XCZU67DR hard-NLF digital predistortion

Two single-phase xdfe_nlf 1.1 instances run at one complex sample per 100 MHz clock. DMA preloads 1024 pairs of signed I/Q codes and unsigned 8-bit envelope addresses. The frame engine repeats the period three times and captures the last period from either the actuator or the digital PA. The PA input is the actuator output truncated from 18 to 15 fractional bits. Programmable logic generates the PA envelope address from the squared magnitude of that exact input. The notebook checks flow, conversion range and hard-block overflow on every capture.

The actuator test exercises 16 delays, two complex 256-entry LUTs per delay, and a fabric-controlled switch every 512 samples. Both LUTs share a signal tap. One envelope tap matches the signal delay and the other is delayed independently. Power indexing uses floor((I² + Q²)/2²⁰), saturated to 255. Coefficients are Q1.15 with OUT_SCALE=1. A separate identity impulse establishes the common transport delay before comparison.

The digital PA applies a sampled Saleh-type AM/AM and AM/PM curve plus a delayed complex power term. Three indirect-learning updates fit a third-degree polynomial in power at each of three delays using captured PA input and gain-normalized output. The last of four independent OFDM periods is reserved for evaluation. ACPR integrates 160 consecutive bins on either side of the 160 occupied bins. EVM and NMSE refer to the scaled complex time-domain waveform. This experiment measures linearization of the known digital PA model. It uses no RF converter or physical amplifier.

## Reproduce

Use the same vendor PS preset as the resampler/NLF overlay. From a fresh output directory run `vivado -mode batch -source build.tcl -tclargs /path/to/vendor-ps.tcl /path/to/output` with Vivado 2025.2. Deploy the matching dfe_dpd.bit and dfe_dpd.hwh together. Use PYNQ with the repository's pynq_dfe package on PYTHONPATH. Set DFE_REPO to the repository root, DFE_BITFILE to the bitstream, and DFE_OUTPUT to a writable data directory. Run notebooks/dfe-dpd.ipynb. Captures, measurements, quantized learned tables, and plots are written to DFE_OUTPUT.

See [PG401](https://docs.amd.com/r/en-US/pg401-xdfe-nlf) for the one-phase delay registers, complex LUT packing and direct-port bank-switch timing.

## Measured on XCZU67DR

The 10.33 dB PAPR held-out period matched both static banks and both edges of a live bank switch exactly across all 1024 complex samples (zero maximum component-code error). The actuator delay was 17 clocks and the complete cascade delay was 36 clocks. The PA transfer also matched its quantized model exactly on the held-out period at every iteration. Frame count, range, and overflow checks passed. The first three periods trained the inverse.

| Update | Worst-side ACPR (dBc) | Waveform NMSE (dB) | RMS EVM (%) |
|---|---:|---:|---:|
| Identity | −33.13 | −21.60 | 8.314 |
| 1 | −41.77 | −35.46 | 1.686 |
| 2 | −47.49 | −41.33 | 0.858 |
| 3 | −55.50 | −48.31 | 0.384 |

Implementation used two of the device's 16 DFE_NL_FIR primitive locations. Routed setup slack was +5.510 ns and hold slack was +0.011 ns, with zero failing endpoints and zero critical CDC endpoints. The experiment covers this waveform and digital PA curve.
