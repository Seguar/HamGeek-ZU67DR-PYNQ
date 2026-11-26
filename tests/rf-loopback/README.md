# 8-DAC/8-ADC test overlay

**Built, not yet run on hardware.** The r5 overlay drives eight DACs at 10 GS/s in fixed 20 mA mode and captures eight ADC channels at 2.5 GS/s. The test controls the RF data path only. Download `rf-loopback-r5.tar.xz`, extract it and verify its hashes.

Measure TP16 and TP17. Use a measured `TP16_V` of 0.980–1.040 V and a 2.5 V DAC_AVTT. Set `VENDOR_ZIP` to your own `adda_loop.zip` for runtime clock configuration. Run status-only with the RF paths disconnected first.

```sh
cd rf-loopback-r5
sha256sum -c artifacts.sha256
: "${TP16_V:?Set TP16_V to the measured ADC_AVCC voltage}"
: "${VENDOR_ZIP:?Set VENDOR_ZIP to your adda_loop.zip}"
PYNQ_PY=/usr/local/share/pynq-venv/bin/python
sudo "$PYNQ_PY" -u test_loopback.py rf_loopback.bit --adc-avcc "$TP16_V" \
  --program-lmk --vendor-vitis-zip "$VENDOR_ZIP" --status-only
```

After the status check passes at 312.5 MHz fabric and 6.25 MHz SYSREF, connect the RF paths with attenuation appropriate for the ADC inputs. The default test starts with a digital amplitude of 0.1 and uses eight tones from 100 to 800 MHz.

```sh
sudo "$PYNQ_PY" -u test_loopback.py rf_loopback.bit --adc-avcc "$TP16_V" \
  --program-lmk --vendor-vitis-zip "$VENDOR_ZIP" --amplitude 0.1 --output rf_loopback.npz
```

The bundle uses the [common LMK clock helper](../adc-rate-sweep/). Vivado 2025.2 routed timing passed and DRC reported zero errors. The packaged HWH uses generic instance and net names while preserving the implemented addresses and timings.
