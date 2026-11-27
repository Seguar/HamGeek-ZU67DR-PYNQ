# xrfdc for RFSoC DFE

This port retains the PYNQ 4.0.0 `xrfdc` module and RFdc tile/block API. Import
`xrfdc` before opening the overlay so PYNQ registers the RFDC 2.3, 2.4 and 2.6
VLNVs. Supply the matching HWH. The driver attaches a libmetal IO region to
the local PYNQ MMIO array and retains it for the instance lifetime.

## Board installation

The PYNQ 4.0.0 image venv uses Python 3.12.3 and includes cffi 2.1.0 and
wurlitzer 3.1.1. The Ubuntu 24.04 arm64 package manifest includes `libsysfs2`. The wheel contains a native Linux aarch64 library, a private copy
of libmetal and ABI-mode cffi declarations. Stage the wheel and dependency
wheels on `/data` or `/dev/shm`. With the wheelhouse in `/data/wheels`, use
the existing PYNQ venv and keep the install itself on the data partition:

```sh
python=/usr/local/share/pynq-venv/bin/python
"$python" -c 'import pynq; print(pynq.__version__)'
"$python" -m pip install --no-index --no-cache-dir --no-deps --target /data/xrfdc-site \
    /data/wheels/xrfdc-*.whl
export PYTHONPATH="/data/xrfdc-site${PYTHONPATH:+:$PYTHONPATH}"
"$python" -c 'import cffi, wurlitzer, xrfdc; print(xrfdc.RFdc.bindto)'
```

If the venv lacks cffi or wurlitzer, install their staged wheels (and
pycparser for cffi) to the same target. Set PYTHONPATH before starting the
notebook kernel or Python process. A target under /dev/shm lasts until reboot.

## Native build and offline checks

Build on native Ubuntu 24.04 aarch64 with Python 3.12, GCC, CMake, Make, Git
and the Ubuntu libsysfs2/libsysfs-dev headers and shared library. Use
`RFDC_RUNTIME_ROOT/sysroot` from the project's adc-nyquist native runtime, or
set `SYSFS_SYSROOT=/` with both Debian packages installed on the build host.

```sh
git clone --filter=blob:none --sparse -b xlnx_rel_v2025.2 https://github.com/Xilinx/embeddedsw.git
export EMBEDDEDSW_DIR="$(realpath embeddedsw)"
git -C "$EMBEDDEDSW_DIR" fetch origin tag xilinx_v2025.2
export RFDC_RUNTIME_ROOT="$(realpath runtime)"
# Or use the host packages: export RFDC_RUNTIME_ROOT=/ SYSFS_SYSROOT=/
python3 -m venv build-venv
. build-venv/bin/activate
python -m pip install 'setuptools>=70.1' wheel build cffi pytest wurlitzer
cd packages/xrfdc-dfe
export SOURCE_DATE_EPOCH=1764547200
python -m build --wheel --no-isolation
sha256sum dist/*.whl
export ROWTIMING_HWH=/path/to/rowtiming250_avtt25.hwh
git -C "$EMBEDDEDSW_DIR" show c3b3132:XilinxProcessorIPLib/drivers/rfdc/src/xrfdc.h >build/xrfdc.h
export RFDC_HEADER="$PWD/build/xrfdc.h"
# With an extracted sysroot on the build host:
export LD_LIBRARY_PATH="${SYSFS_SYSROOT:-$RFDC_RUNTIME_ROOT/sysroot}/usr/lib/aarch64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python -m pytest -q tests
```

The wheel builder runs `build_runtime.sh`. It extracts RFDC and libmetal from
release branch commit `c3b3132f6e1e202e275b8dd77b3804f3b449528c` and
checks both source trees against tag `xilinx_v2025.2` at
`145cea8fcf98268c8b163f732c181f008e887e53`. It builds libmetal as PIC
and links the board's libsysfs.so.2. Input hashes are in
`build/native-inputs.sha256`. The Python starting point is PYNQ v4.0.0 at
`d90670c69f7b71ea1a5d23aaa3e0ec713ff5fa9f`.

The build preprocesses xrfdc.h (which includes xrfdc_hw.h and contains the
MTS API in this release). The native Linux driver uses packed RFDC structures
and the DeviceId form of XRFdc_Config. Name is the SDT variant. The build
compares declarations with the checked-in cdef and validates size, alignment,
field size and offset against native C. After a deliberate header change,
use `tools/cdef.py --generate RFDC_SRC METAL_INCLUDE SYSROOT_INCLUDE` and
review the generated diff. The offline driver tests map ordinary RAM and use
the real shared library. With the wheel installed and the image's PYNQ packages
available, run `python tests/pynq_image_smoke.py "$ROWTIMING_HWH"` to exercise
PYNQ's HWH parser, driver registration and MMIO class with a RAM-backed device.

## API additions

| Object | API |
| --- | --- |
| RFdc | GetTileLayout(), mts_adc_sync(), mts_dac_sync(), mts_sysref_config(), mts_sysref_enable(), mts_sysref_disable(), get_mts_enable() |
| ADC or DAC tile | CustomStartUp(start_state, end_state), MinSampleRate, MaxSampleRate, GetMinSampleRate(), GetMaxSampleRate() (MS/s) |
| ADC or DAC block | Coupling, GetCoupling(), SetConnectedIQData(i, q) |
| DAC block | DACDataScaler, GetDACDataScaler(), SetDACDataScaler(enable) |
| ADC block | SignalDetector settings dictionary, GetSignalDetector(), SetSignalDetector(settings) |

Tile indices follow the physical layout. RowTiming r5 exposes three ADC
tiles (4, 4, 2 blocks) and two four-block DAC tiles. Enable state still depends
on the overlay. The ClkDistribution property translates the PYNQ
ADC/DAC/DistributionStatus dictionary to v13 clock domains. As in the upstream
driver, PLLSettings.SampleRate readback is in GS/s and configuration requests
use MS/s. Each domain is applied with a separate driver call.
