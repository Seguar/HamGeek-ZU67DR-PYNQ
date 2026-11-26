# J35 external device-clock tools

Use the [setup and commands in the repository README](../../README.md#external-device-clock-j35).
The supported frequency is **1.5 GHz** on the revision 2.1 card with the fixed-20 mA
RowTiming r5 bundle from [v4.0.0-zu67dr.1](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/v4.0.0-zu67dr.1).
The 3 GHz profile is included for diagnosis. It failed the J32 gate on the tested card.

## What the runner does

- Verifies the release bundle and makes a temporary copy for the original r5
  guards, which expect bare filenames in the checksum manifest.
- Programs and reads back the LMK over PS SPI. It uses the r5 divider SYNC
  sequence, then requires a fresh physical 250 MHz observation at J32 before
  it loads the overlay. With `--confirm-j32`, the operator must type `250MHz`
  after measuring J32 on every warm reload. Press Enter to abort.
- In analyzer mode, `--analyzer-host` supplies the raw SCPI endpoint and
  `--analyzer-port` defaults to 5025. The Keysight X-Series analyzer must be
  in spectrum-analyzer mode with J32 connected to its RF input. The script
  configures trace 1, 20 dB input attenuation, preamp off, 100 kHz span and
  1 kHz RBW. The peak must be within ±5 kHz of 250 MHz, between −75 and
  0 dBm, and at least 15 dB above the trace median. The runner sweeps again
  before RFDC access and again before MTS. Use a dedicated analyzer or use the manual gate.
- Checks fabric and SYSREF counters and the four RFDC stream flags through
  the PS-clocked status path. A full cycle then locks MMCM phase and runs
  DAC and ADC multi-tile sync (MTS) without a second overlay download.
  It checks for equal tile latencies, zero offsets and repeatability across
  warm cycles. Playback stays off. The historical DAC7 phase measurement
  used a separate oscilloscope setup.
- Writes each completed cycle to `cycle-NNN/result.json` in the requested new
  output directory. It attempts a PS-only stock restore after any Fin
  programming attempt, including on a failed J32 check or Ctrl+C. Leave the
  source on until the runner reports that stock PLL2 has locked.

## Recovery

If the stock restore fails and Linux is responsive, leave the J35 source on
and retry the README's `restore` command. If Linux or a worker is stuck, use an
operator power cycle to recover. Clock checks sample the signal at specific
points. Keep the source running throughout the test. After a verified restore,
the stock clock is available and an application can initialize its overlay
again.

## Offline checks

From this folder, run `python3 -B -m unittest -v test_offline`. For the release
integration check, add `J35_BUNDLE="$BUNDLE"` before the command and point
`BUNDLE` at the extracted release bundle. That check requires NumPy and verifies
both profiles against the release stock settings, and runs both stock r5
overlay guards on the staged files. Tests use mocked board and instrument I/O.

See [clock notes](CLOCK_NOTES.md) for the register selections and input limits.
