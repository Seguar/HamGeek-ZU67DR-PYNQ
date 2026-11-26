# PL DDR4 test

**Historical RC2 overlay.** The released two-controller overlay uses the vendor PDF pinout and timed out during calibration on the tested rev 2.1 card. The verified x32 build uses the [corrected pinout](../../docs/pl-ddr4-pinout.md). The commands below document the RC2 bundle and its expected status interface.

To inspect the historical bundle, download and extract `pl-ddr4.tar.xz`. Verify the hashes and confirm both 200 MHz DDR4 reference clocks before running. The Si5341 status utility temporarily selects the I²C mux route and restores it. Use status-only first to verify both memory controllers calibrate.

```sh
cd pl-ddr4
sha256sum -c artifacts.sha256
PYNQ_PY=/usr/local/share/pynq-venv/bin/python
sudo "$PYNQ_PY" si5341_status.py
sudo "$PYNQ_PY" -u test_ddr.py pl_ddr4_test.bit --status-only
```

The memory test overwrites the selected dedicated PL DDR4 windows. With both controllers calibrated, the default test writes and reads four patterns at five 16 KiB windows in each bank.

```sh
sudo "$PYNQ_PY" -u test_ddr.py pl_ddr4_test.bit --window-kib 16
```

Vivado 2025.2 routed sign-off passed (+0.121 ns setup and +0.011 ns hold), and DRC reported zero errors. Pattern testing uses 32-bit MMIO and measures no sustained DDR4 throughput.
