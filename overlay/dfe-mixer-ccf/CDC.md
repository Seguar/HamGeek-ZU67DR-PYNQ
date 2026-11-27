# RFDC clock-domain crossings

Vivado 2025.2 reports seven critical endpoints in the routed mixer/CCF overlay. All seven also occur in the archived RowTiming build `runs/adc226-dac228-r5/cdc.txt` (14:33). The top-level `run/cdc.txt` (11:11) contains five. The 14:33 run's HWH SHA-256 matches the deployed r5 HWH, `38a64abc7fcf8f20d4738f277fd5ccfd8c0967f6a1173d967833120d18d50d2f`. The earlier HWH has ADC slice 20 disabled, no m2 stream clock/reset ports and ADC1 MTS disabled. Both deployed r5 and mixer/CCF enable slice 20 and ADC1 MTS. This explains the apparent additions. Comparing the two designs' HWH parameters shows the intended changes to the quad ADC datapaths. The ADC tile and slice enables and MTS selections match. [Mixer/CCF routed CDC report](run/cdc.rpt)

| Endpoint inside RFDC | Rule | Launch → capture | Earlier report | Deployed r5 | Timing exception and CDC disposition |
|---|---|---|---|---|---|
| ADC0 clock-valid, stage 0 D | CDC-11 | c1 312.5 → PS 100 MHz | Present | Present | XPM stage-0 exception. Fanout finding open |
| ADC1 clock-valid, stage 0 D | CDC-11 | c1 312.5 → PS 100 MHz | Present | Present | XPM stage-0 exception. Fanout finding open |
| ADC2 clock-valid, stage 0 D | CDC-11 | c1 312.5 → PS 100 MHz | Absent | Present | XPM stage-0 exception. Fanout finding open |
| DAC0 clock-valid, stage 0 D | CDC-11 | c0 625 → PS 100 MHz | Present | Present | XPM stage-0 exception. Fanout finding open |
| DAC1 clock-valid, stage 0 D | CDC-11 | c0 625 → PS 100 MHz | Present | Present | XPM stage-0 exception. Fanout finding open |
| ADC0 RFADC CONTROL_COMMON[12] | CDC-13 | PS 100 → c1 312.5 MHz | Present | Present | Exact AMD timing exception. CDC-13 remains visible |
| ADC1 RFADC CONTROL_COMMON[12] | CDC-13 | PS 100 → c1 312.5 MHz | Absent | Present | Exact AMD timing exception. CDC-13 remains visible |

## Five clock-valid levels

The overlay instantiates three `proc_sys_reset` blocks. The ADC and DAC reset generators use the same MMCM output as their respective tile stream clocks. The host reset generator uses PS `clk_pl_0`, which also drives RFDC `s_axi_aclk`. The generated RFDC block takes each tile's AXI stream reset as a clock-valid **level** and instantiates one `xpm_cdc_single` per tile with `SRC_INPUT_REG=0`. The source is already registered at the peripheral reset output. The routed checkpoint has four `ASYNC_REG` stages per tile, all clocked by `clk_pl_0`. The ADC2 port serves enabled slice 20 on the clock-distribution tile. Its stream clock and reset are wired the same way in deployed r5. [PG269 ADC stream ports](https://docs.amd.com/r/en-US/pg269-rf-data-converter/AXI4-Stream-Related-Ports-for-RF-ADCs) · [DAC stream ports](https://docs.amd.com/r/en-US/pg269-rf-data-converter/AXI4-Stream-Related-Ports-for-RF-DACs) · [AXI-Lite reset](https://docs.amd.com/r/en-US/pg269-rf-data-converter/Configuration-Interface-Ports)

One ADC reset register drives three independent synchronizers into the same management clock. One DAC reset register drives two. Vivado identifies this fanout even though each crossing has a synchronizer. Tracing each final Q to its next sequential sinks in the routed design reaches only that tile's power-on sequencer and done flag. Those sinks can observe valid on different management cycles across tiles. The IP's scoped `xpm_cdc_single.tcl` line 6 false-paths the first stage. Register-to-register timing within each chain remains active. The endpoint report shows the effective exception as False Path despite the overlay's general 3.2 ns datapath-only bound between the host and fabric clocks.

This wiring meets the PG269 reset interface requirements. No RFDC-specific CDC-11 waiver was identified for tile startup skew. Leave the five findings open for formal signoff. AMD's general guidance explains the effect of synchronizer fanout. [UG906 Fanout](https://docs.amd.com/r/2025.2-English/ug906-vivado-design-analysis/Fanout) · [PG269 power-up sequence](https://docs.amd.com/r/en-US/pg269-rf-data-converter/Power-up-Sequence)

## Two MTS FIFO enables

The generated RFDC AXI-Lite register `adcN_cmn_control_ff_reg[12]` drives its own RFADC hard primitive's `CONTROL_COMMON[12]` pin directly. The generated RFDC synthesis constraint file `dfe_mixer_ccf_rfdc_0.xdc` lines 229 and 235 explicitly false-path those exact two register-to-pin paths. The adjacent AMD waiver descriptions identify the signal as the MTS FIFO enable. Those waiver commands target CDC-1 and different destination pins. Vivado reports CDC-13 at the hard-primitive pins, where it recognizes zero fabric synchronizer stages. The vendor timing exceptions are justified for these exact paths. The primitive's internal implementation and any CDC-13 waiver approval remain with AMD. [PG269 MTS synchronization sequence](https://docs.amd.com/r/en-US/pg269-rf-data-converter/Synchronization-Steps)

The review found no overlay-owned wiring error among the seven endpoints. Both ADCs already used MTS in r5. Keep the generated timing constraints and the seven structural findings visible. A functional loopback measures the signal path and cannot establish metastability performance.

## Rebuild check

| Routed metric | Original | Rebuild |
|---|---:|---:|
| Critical CDC-11 | 5 | 5 |
| Critical CDC-13 | 2 | 2 |
| WNS / WHS (ns) | +0.060 / +0.010 | +0.060 / +0.010 |
| Setup / hold / pulse-width failing endpoints | 0 / 0 / 0 | 0 / 0 / 0 |

The rebuild reproduced each critical endpoint, clock pair, rule, synchronization depth and effective exception. Its 20,860,100 configuration bytes matched the board-tested payload exactly (SHA-256 `d3700cdc6836235b1a15400032b1f238d9c73ff304cfbbe145cc1f584928db54`). The HWH differed only in its generation timestamp. An offline FFT of the original board captures reproduced all five expected tone bins, 0.0266 dB maximum FIR gain residual and 53.0897 dB input-normalized rejection.
