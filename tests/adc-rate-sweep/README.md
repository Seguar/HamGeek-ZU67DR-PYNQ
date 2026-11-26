# Eight-channel ADC rate sweep

Download the matching r5 bundle and verify its hashes before programming. Each archive contains its bit/HWH pair, the RFDC synchronization helper and the Python runner. Keep these files together. Use the PYNQ virtual environment shipped with RC2. When programming clocks, supply your own copy of the board's `adda_loop.zip` as `VENDOR_ZIP`. The profile is derived at runtime.

| Archive | Rate (GS/s) | Fabric (MHz) | SYSREF (MHz) | Run on hardware | MTS latency (tiles 0/1) | ADC0 SNR re FS (dB) | ADC0 NSD (dBFS/Hz) |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `adc25-r5.tar.xz` | 2.5 | 312.5 | 6.25 | Pass | 80/80 | 61.5 | −152.52 |
| `adc29375-r5.tar.xz` | 2.9375 | 367.1875 | 0.78125 | Pass | 76/76 | 61.0 | −152.63 |
| `adc294912-r5.tar.xz` | 2.94912 | 368.64 | 3.84 | Pass | 76/76 | 61.0 | −152.65 |

All three r5 bundles passed status, MTS and capture (8 × 65,536 samples each) on a bring-up installation. ADC0 received 150 MHz at −6 dBm from an unfiltered generator. Measured crosstalk was ≤ −73 dBc at the tested tones. ADC_AVCC was 0.93 V, outside the recommended range. [TP16 diagnosis and rework](../../README.md#adc_avcc-at-tp16)

Use the rate for the extracted bundle and set `TP16_V` to your measured ADC_AVCC within 0.980–1.040 V. Start with status-only. It checks the status aperture and clocks without reaching RFDC register access or DMA.

```sh
cd adc294912-r5
sha256sum -c artifacts.sha256
: "${TP16_V:?Set TP16_V to the measured ADC_AVCC voltage}"
: "${VENDOR_ZIP:?Set VENDOR_ZIP to your adda_loop.zip}"
PYNQ_PY=/usr/local/share/pynq-venv/bin/python
sudo "$PYNQ_PY" -u test_adc.py adc_rate_sweep.bit --rate 2.94912 \
  --adc-avcc "$TP16_V" --program-lmk --vendor-vitis-zip "$VENDOR_ZIP" --status-only
```

After the clock checks pass and the ADC stream mask is `0x3`, run MTS and capture 65,536 samples per channel.

```sh
sudo "$PYNQ_PY" -u test_adc.py adc_rate_sweep.bit --rate 2.94912 \
  --adc-avcc "$TP16_V" --program-lmk --vendor-vitis-zip "$VENDOR_ZIP" --output adc_capture.npz
```

The earlier host AXI reset held its peripherals in reset because an active-low auxiliary input was tied low. r5 synchronizes `pl_resetn0` on the host clock, drives the auxiliary input inactive and adds an AXI Protocol Firewall. The firewall returned a bounded AXI error in simulation. Linux handling of that error remains pending on hardware.

The 2.94912 GS/s r5 bit/HWH pair measured **368.662 MHz** fabric, **3.840 MHz** SYSREF and stream mask **0x3**. A full run reached RFDC startup state 0xf on ADC tiles 0/1/2 with tile 2 PLL locked, synchronized capture tiles 0/1 at latencies 76/76 with offsets 0/0, and captured **8 × 65,536 samples** without a hang. This diagnostic run used **0.93 V ADC_AVCC**, outside the recommended range, with a local voltage-check override. The public runner enforces the data-sheet range. The released bit and HWH match the measured pair. The packaged helper's diagnostic source path and Python runner have been updated for redistribution.
