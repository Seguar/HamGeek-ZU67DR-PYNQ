# Single-channel DFE loopback for the HamGeek XCZU67DR

Connect **DAC0/J44 to ADC0/J36**. The DAC transmits a 78.125 MHz sine when enabled. Capture returns 1,024 consecutive valid complex samples from the selected stream. At unity DFE rate this represents 3.2768 µs. Use separate acquisitions to compare the RFDC and filtered streams. Their starting phases depend on software trigger timing.

```text
128-sample sine ROM → DAC tile 227, block 0 → J44
                                              │ coax
                                              ↓
J36 → ADC tile 224, block 0 → RFDC real-to-I/Q, decimate ×8 ─┬→ raw
                                                            └→ DFE uplink mixer → DFE channel filter
                                                                raw or filtered ↓
                                              1024 × 32-bit dual-clock snapshot RAM
                                                                   ↓ AXI4-Stream + TLAST
                                                   AXI DMA S2MM → HP0 → PS DDR
```

## Clocks and converter settings

Use the RowTiming r5 250 MHz LMK04828 profile with 6.25 MHz SYSREF. Tile 226 receives the 250 MHz reference, runs at 5.0 GS/s and supplies the sample clock to 224 and 225. Its converter output is discarded. DAC tile 228 forwards its 250 MHz reference to 227. Both DAC PLLs run at 10 GS/s. All DAC slices use real data, interpolation 1, 16 samples per beat and fixed 20 mA for the 2.5 V AVTT rail (`DAC_VOP_Mode=0`, `DAC_Output_Current=0`). Only `s00_axis` receives tone data. Its package pins are N2/N1 (+/−). ADC00 uses AK2/AK1 (+/−).

PL reference E12/D12 drives the r5 MMCM. PL SYSREF E14/D14 follows r5's 250 → 62.5 → 312.5 / 625 MHz sampling chain. Both quad ADC tiles and both DAC tiles have MTS enabled. The HWH records the r5 PS and DDR configuration. AXI-Lite and the DMA use PS pl_clk0 at 100 MHz.

Quad ADCs sample at 2.5 GS/s. Each enabled quad slice uses the same real-to-complex fine mixer, initial NCO 0 Hz, 8× decimation and two 16-bit words per cycle. This preserves the 312.5 MHz MTS fabric clock. The mixer consumes ADC00 only. Each 32-bit beat holds signed I in bits 15–0 and signed Q in bits 31–16. DAC playback uses 16 consecutive signed samples per 625 MHz beat, with peak code 8192. [AMD PG269 data formats](https://docs.amd.com/r/en-US/pg269-rf-data-converter/Interface-Data-Formats)

## Software interface

| HWH instance | Base | Range | Function |
|---|---|---|---|
| rfdc | 0x82000000 | 256 KiB | RF data converter 2.6 |
| control | 0x84000000 | 64 KiB | AXI GPIO output, data register at offset 0 |
| dma | 0x84010000 | 64 KiB | AXI DMA 7.1 simple S2MM, 40-bit addresses |
| mixer | 0x84040000 | 256 KiB | xdfe_cc_mixer 2.0 |
| ccf | 0x84080000 | 256 KiB | xdfe_cc_filter 1.1 |

All three GPIO bits reset to zero. Bit 0 enables the DAC tone. Bit 1 requests one capture on **either transition**. Bit 2 selects raw RFDC (1) or channel-filter output (0). Keep a software shadow of the three-bit register. Write the source selection first and keep it stable throughout capture. Start a DMA receive into a contiguous 4,096-byte buffer, then toggle bit 1 while preserving bits 0 and 2. Wait for DMA completion before issuing the next request. Invalidate the receive buffer before reading it. Clear bit 0 after playback and preserve the trigger state when doing so. The RAM absorbs the full-rate sample burst. The host side drains the completed snapshot with backpressure and marks its last word with TLAST.

For the filtered path, configure and activate both DFE blocks through their drivers. Use immediate triggers, one active CCID (0), one antenna, unity carrier rate and an initial zero mixer offset. Load a known FIR coefficient set before enabling filtered capture. The uplink input has constant TUSER=0 and TLAST=1 for the single-antenna cycle. Mixer TID, TLAST, TUSER, TDATA and TVALID feed the CCF. During acquisition use a steady configuration that accepts each scheduled carrier beat. An inactive filter can leave a receive pending. Use bounded polling in bring-up software.

| HWH parameter | mixer | ccf |
|---|---|---|
| CLOCK_FREQUENCY (MHz) | 312.50 | 312.50 |
| NUM_ANTENNA / ANTENNA_INTERLEAVE | 1 / 1 | 1 / 1 |
| SAMPLE_WIDTH_IN / SAMPLE_WIDTH_OUT | 16 / 16 | 16 / 16 |
| TUSER_WIDTH | 8 | 8 |
| MAX_USEABLE_CCIDS | 4 | 2 |
| MODE / MIXER_CPS | Uplink / 1 | — |
| NUM_NCO / NUM_AUXILIARY | 1 / 0 | — |
| N_CH_X1 / X2 / X4 / X8 / X16 | 1 / 0 / 0 / 0 / 0 | — |
| NUM_TAPS / SWITCHABLE | — | 16 / false |

The HWH also exposes synthesized model parameters. The driver-relevant names include `C_MODE`, `C_MAX_USEABLE_CCIDS`, `C_MIXER_CPS`, `C_PE_NUM_NCO` for the mixer and `C_NUM_CC_PER_ANTENNA`, `C_PE_NUM_TAPS`, `C_SWITCHABLE` for the filter. Both expose `C_DATA_IWIDTH`, `C_DATA_OWIDTH`, `C_TUSER_WIDTH`, `C_NUM_ANTENNA` and `C_ANTENNA_INTERLEAVE`. See [addrmap.json](addrmap.json) for the exported values.

## Rebuild

From this directory in a Vivado 2025.2 Linux shell, use the archived r5 PS preset or extract it from the card's original adaloop Vivado archive with the repository helper. The build checks the preset digest.

```sh
python3 ../extract_ps.py /path/to/rfevm_rf_adaloop.zip /tmp/vendor-ps.tcl
vivado -mode batch -source build.tcl -tclargs /tmp/vendor-ps.tcl /path/to/new-output-directory
```

The output directory contains the matched dfe_mixer_ccf.bit, dfe_mixer_ccf.hwh and dfe_mixer_ccf.xsa, plus implementation reports under run/. Keep the bitstream and HWH together when loading the overlay in PYNQ.

## Implementation and verification

Vivado routed all 20,944 routable nets. WNS was +0.126 ns, WHS +0.012 ns and WPWS 0.000 ns, with zero failing setup, hold or pulse-width endpoints. Utilization was 11,007 CLB LUTs, 11,689 CLB registers, four block RAM tiles, one DFE_DUC_DDC and one DFE_FIR. See the [timing](run/timing.rpt), [route](run/route.rpt) and [utilization](run/utilization.rpt) reports.

Default DRC lists four warnings: three NO_CHANGE RAM collision advisories inside the DMA FIFO and one group of loadless nets including RFDC status outputs. The methodology report flags an unknown CDC and the r5 MMCM SYSREF capture on CLKOUT2. The CDC report marks five reset paths into RFDC clock-valid synchronizers as critical (CDC-11), and two RFDC internal control paths into ADC hard primitives as critical (CDC-13). These findings remain open for board bring-up. [DRC](run/drc.rpt) · [Methodology](run/methodology.rpt) · [CDC](run/cdc.rpt)

XSim verified both capture selections with valid gaps and DMA stalls, including TLAST on the 1,024th word. A separate simulation checked all 128 DAC codes across two periods, stalls and disable. Offline PYNQ metadata parsing found all five addresses. The exported bitstream and HWH match the XSA contents byte for byte. Hardware loopback and runtime DFE configuration await a board test. [Artifact SHA-256 manifest](run/artifacts.sha256)
