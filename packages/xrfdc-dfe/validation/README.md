# RowTiming r5 RFdc validation

Run the launcher on the campaign coordinator. It needs Python 3.11+ and NumPy. Supply the RF directory from the 2026-11-26 acceptance stage, including its original manifest. The runner checks the pinned manifest and every member before importing the board helpers.

```bash
./run_all.sh --dry-run --bundle "$RF_BUNDLE" --adc-avcc 0.93 --output ./offline-results
python3 -B test_failures.py "$RF_BUNDLE"
```

For hardware acceptance, supply the integrated wheel with `--wheel` to install it under the private stage, or preinstall xrfdc in the board's PYNQ venv. Connect DAC0/J44 to ADC0/J36 with the diagonal loop fixture, leave fixture USB unpowered, and confirm the recorded TP16 value and 2.5 V DAC AVTT configuration. The rail argument passes the original acceptance check on the operator's measurement. The acceptance guard has no live rail sensor. Use the shared campaign BOARD.lock path on the coordinator. The output directory must be new.

```bash
./run_all.sh --board "$BOARD_ALIAS" --ssh-config "$SSH_CONFIG" \
  --lock "$CAMPAIGN_DIR/BOARD.lock" --bundle "$RF_BUNDLE" \
  --adc-avcc 0.93 --output ./board-results
```

The launcher creates the campaign lock exclusively before SSH and checks its ticket before the worker starts. The staged copy must match. Each board run gets a private directory under /data. The optional /dev/shm stage requires executable mounts for the C helper. SSH uses the configured key. The worker uses sudo noninteractively, optionally taking the board password from BOARD_SUDO_PASSWORD. It sources the acceptance XRT environment. A timeout bounds the worker. If the connection drops or final idle cannot be verified, inspect the printed stage and confirm idle before releasing the retained coordinator lock.

## Measurements

- GetTileLayout and IPStatus enable bits are checked against the compact layout and HWH. Per-tile readbacks include sample rate, min/max bounds and PLL status. ADC0/1 receive distributed clocks. Their raw local PLL lock bit is zero while the driver reports the external clock path as locked.
- StartUp and CustomStartUp run on ADC0, with all five tile states checked after each call. The ADC0 block 0 Nyquist zone is toggled and restored. All eight DAC block current, coupling and digital scaler reads precede playback. The fixed-current gate allows one driver code (43.75 µA) around 20 mA. The prior tile-227 C readback was 20,037 µA.
- The runner phase-locks RowTiming, checks MTS enable, and synchronizes DAC then ADC tiles 0 and 1. For fixed and auto modes it records fresh C-helper and Python per-tile latency/offset pairs. Each run must match one of the complete signatures observed in 12 C reloads per mode. Independent sync calls can select different ADC FIFO offsets even on the same bring-up. Accepted fixed values are DAC 432 and ADC 448. Fixed ADC offsets are [8,4] or [8,8], and DAC offsets are [16,16]. Auto gives DAC 416 with [0,0] and ADC 440 with [0,0] or 444 with [4,0].
- Only DAC0 plays a finite 100 MHz tone at −12 dBFS. The independent FFT peak must fall within one bin at 2.5 GS/s. Windowed amplitude at 100 MHz must be within 3 dB of the prior C-helper diagonal probe (−18.9703 dBFS on ADC0). The peak must remain below −3 dBFS. The separate 100 MHz full-scale sweep found −6.9906 dB loop gain.
- Teardown sends STOP, clears enables and loop masks, and checks busy, armed, running and fault. A failure stops subsequent measurements. Numbered JSON files and report.json record expected and measured values, plus mode and overall verdict in the combined report.

Offline mode uses real bundle verification and waveform compilation with simulated RFdc, clock, playback and capture. Hardware timing, DMA, MMIO, SSH and rail measurements require board integration.
