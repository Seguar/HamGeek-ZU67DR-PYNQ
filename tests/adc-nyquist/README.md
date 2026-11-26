# ADC00 Nyquist zone helper

Use this helper with the [ADC00 overlay](../../overlay/README.md) at 2.4576 GS/s. The packaged helper is built and pending hardware verification as a release asset. It checks the ADC00 RFDC register aperture and expects the overlay to remain loaded with its 245.76 MHz reference. ADC00 J36 is driver tile 0, block 0.

```sh
cd adc-nyquist
sha256sum -c artifacts.sha256
sudo ./adc-nyquist --get
```

Select zone 1 for an odd input band and zone 2 for an even band. Leave the input present for background calibration to settle before capture. Reloading the overlay restores its default parity.

```sh
sudo ./adc-nyquist --set 2 --tile 0 --block 0
sudo ./adc-nyquist --get
```

The optional `--cal-mode 1|2` reruns foreground calibration for the entire affected tile. Stop capture and mute that tile's RF inputs before changing calibration mode. [AMD PG269 calibration modes](https://docs.amd.com/r/en-US/pg269-rf-data-converter/Calibration-Modes)

To rebuild on AArch64 Ubuntu 24.04, set `RFDC_RUNTIME_ROOT` to a tree containing the v13.0 RFDC sources under `upstream/XilinxProcessorIPLib/drivers/rfdc_v13_0/src`, a static libmetal install under `metal-install` and a static libsysfs install under `sysroot`. Run `./build_runtime.sh adc00.hwh` using the HWH from the ADC00 prerelease. [AMD RFDC driver sources](https://github.com/Xilinx/embeddedsw/tree/xilinx_v2025.1/XilinxProcessorIPLib/drivers/rfdc)
