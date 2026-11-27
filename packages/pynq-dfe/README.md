# PYNQ hard DFE drivers

Python bindings for the RFSoC DFE mixer 2.0, channel filter 1.1, equalizer 1.0, NR PRACH 2.0 and OFDM 2.2. The native libraries and generated declarations use AMD embeddedsw `xlnx_rel_v2025.2` (c3b3132f6e1e202e275b8dd77b3804f3b449528c), Linux non-SDT, AArch64.

## Board results

The mixer and CCF share the DAC0/J44 → ADC0/J36 analog loopback. The remaining overlays move digital test vectors through the hard blocks and return their output to PS memory. All eight overlays were tested with Vivado 2025.2.

| Hard block | Overlay | Driver or control | Notebook | Measured on XCZU67DR |
|---|---|---|---|---|
| Mixer | [dfe-mixer-ccf](../../overlay/dfe-mixer-ccf/README.md) | MixerIP | [mixer-ccf](../../notebooks/dfe-mixer-ccf.ipynb) | 78.125 MHz translated to +4.8828125 MHz with a 73.2421875 MHz NCO. |
| Channel filter (CCF) | [dfe-mixer-ccf](../../overlay/dfe-mixer-ccf/README.md) | ChannelFilterIP | [mixer-ccf](../../notebooks/dfe-mixer-ccf.ipynb) | 53.09 dB two-tone rejection, matching the FIR prediction. |
| Equalizer | [dfe-equ](../../overlay/dfe-equ/README.md) | EqualizerIP | [equ](../../notebooks/dfe-equ.ipynb) | 21/21 cases passed at 12 clocks of delay. All six impulse and step responses had zero component error. |
| OFDM DL → UL | [dfe-ofdm](../../overlay/dfe-ofdm/README.md) | OfdmIP | [ofdm](../../notebooks/dfe-ofdm.ipynb) | All 5,088 complex values across two lanes and two vectors matched the fixed-point model. QPSK round-trip EVM was −79.78 dB. |
| Standalone FFT | [dfe-fft](../../overlay/dfe-fft/README.md) | AXI DMA, fixed stream control | [ofdm-standalone-fft](../../notebooks/dfe-ofdm-standalone-fft.ipynb) | 256/256 complex bins matched the fixed-point model. Bin 37 measured 1,048,576 codes. |
| NR PRACH | [dfe-prach](../../overlay/dfe-prach/README.md) | PrachIP | [prach](../../notebooks/dfe-prach.ipynb) | 21/21 checks passed. All 4,096 output samples matched the fixed-point model after a common one-sample alignment. |
| P/Q resampler, decimation (2/3) | [dfe-resampler-nlf](../../overlay/dfe-resampler-nlf/README.md) | ResamplerIP | [resampler](../../notebooks/dfe-resampler.ipynb) | 3,072 → 2,048 samples. Alias rejection was 101.81 dB at the tested frequency. |
| P/Q resampler, interpolation (2×) | [dfe-resampler-nlf](../../overlay/dfe-resampler-nlf/README.md) | ResamplerIP | [resampler](../../notebooks/dfe-resampler.ipynb) | 1,024 → 2,048 samples. First-image rejection was 89.81 dB at the tested frequency. |
| NLF, two-tap FIR | [dfe-resampler-nlf](../../overlay/dfe-resampler-nlf/README.md) | NlfIP.load_fir | [nlf](../../notebooks/dfe-nlf.ipynb) | Both 1,024-sample captures matched the predicted I/Q codes exactly at a common delay of 23 samples. |
| NLF, DPD actuator | [dfe-dpd](../../overlay/dfe-dpd/README.md) | NlfIP and pynq_dfe.dpd | [dpd](../../notebooks/dfe-dpd.ipynb) | Three Python updates reduced held-out EVM from 8.314% to 0.384% and improved worst-side ACPR by 22.36 dB. |
| pc_cfr → DFE_CFR | [dfe-cfr](../../overlay/dfe-cfr/README.md) | HardCFR | [cfr](../../notebooks/dfe-cfr.ipynb) | Three PC stages reduced PAPR from 10.765 to 6.232 dB. PC and PC + WCFR each passed 9/9 checks. |

DPD datapath (hard DFE_NLF) tested; AMD's adaptation product not used; adaptation implemented in Python; linearises a known digital PA model, not a real amplifier

All seven critical mixer/CCF endpoints also occur in the deployed RowTiming r5 design. Sign-off remains open for five CDC-11 clock-valid reset fanouts. AMD’s generated RFDC XDC covers the two CDC-13 MTS FIFO enables. [Endpoint review](../../overlay/dfe-mixer-ccf/CDC.md)

## Overlay binaries

Build each overlay from its linked directory with the documented RowTiming r5 PS preset. The repository tracks build sources and SHA-256 manifests. Each overlay’s `run/artifacts.sha256` identifies the board-tested bitstream, HWH and XSA. Run `sha256sum -c artifacts.sha256` alongside those three artifacts to verify a copy of the tested build. A fresh build produces its own manifest.

For PYNQ, place the matching same-stem `.bit` and `.hwh` files together and keep the `.xsa` in the build directory. PYNQ 4.0 changes its metadata parser when a same-stem XSA is beside the bitstream. Each overlay guide gives its notebook environment variables.

## Board installation

Install the [DFE v0.1.1 release](https://github.com/Seguar/HamGeek-ZU67DR-PYNQ/releases/tag/dfe-v0.1.1) on the stable image `v4.0.0-zu67dr.1`. Download all release assets into one directory on the mounted data partition or in `/dev/shm`. From that directory run:

```sh
sha256sum -c SHA256SUMS
sudo bash install.sh
```

The installer requires 60 MB free on eMMC and installs both wheels and five native libraries in the PYNQ venv. Restart existing Jupyter kernels after installation. Overlays default to `/data/overlays/dfe`. Without a mounted microSD, the software installs and overlays are skipped. Use `--overlay-dir /absolute/path` for an empty directory on another mounted data volume. An upgrade removes the v0.1.0 path registration and deletes its old payload when the card is mounted. Rerun with the card mounted to finish any deferred cleanup. Run `sudo bash install.sh --uninstall` from the release directory to remove either layout.

## Overlay use

Import pynq_dfe before constructing the Overlay so PYNQ registers the native-driver IP classes and the NLF and resampler classes. Substitute the instance names from your overlay. Each native-driver IP’s `.dfe` owns one handle. Close it before unloading the overlay and serialize access to each handle.

```python
import pynq_dfe
from pynq import Overlay

overlay = Overlay("design.bit")
with overlay.mixer_0.dfe as mix:
    mix.reset()
    model = mix.configure()
    mix.initialize(Sequence={"Length": 4}, TuserSelect=0)
    triggers = mix.triggers()
    triggers.Activate.Mode = 0
    mix.set_triggers(triggers)
    mix.activate()
    try:
        print(mix.versions())  # (driver, hardware), each (major, minor, revision, patch)
        print(model.ModelParams.MaxUseableCcids)
    finally:
        mix.deactivate()
```

The shim opens the address and span from ip_dict. HWH parameters populate the instance Config using the driver's Tcl names, SDT equivalents and Vivado property names where available. Configure then reads hardware model registers, including derived fields absent from the HWH. Model parameters in its result govern subsequent operations. Configure triggers before activate. Closing a handle releases its mapping. Deactivate an operational block explicitly when that is intended.

For the mixer or channel filter, use current_cc_config() to edit the existing schedule or empty_cc_config() for a new one. Use new("CarrierCfg", {...}) with vendor field names and add_cc_to_config(cfg, ccid, bitmap, carrier) to stage a carrier. The mixer takes an additional new("NCO", {...}) argument. Use update_cc_in_config(), remove_cc_from_config() and commit_cc_config(cfg) to stage and trigger changes. add_cc(), update_cc() and remove_cc() perform immediate driver transactions. Choose carrier IDs, slots, NCO assignments and triggers valid for the hardware model. On switchable cores, the paired downlink/uplink vendor operations are available through call().

Mixer set_nco(cfg, ccid, frequency={...}, phase={...}) accepts the Frequency and Phase struct fields, including TriggerUpdateFlag for each. Commit cfg to write the assigned NCO. set_antenna_gain accepts 0 or 1. The channel filter provides set_antenna_enabled, set_cc_gain and load_coefficients(bank, shift, taps, symmetric=True). lowpass_taps(num_taps, cutoff, sample_rate) returns signed Q1.15 taps using a Hamming window. Supply the full symmetric vector. sequence_bitmap(sequence, ccid) maps slot zero to the least significant bit, and mixer_rate returns the encoded conversion ratio for the slot allocation, antenna interleave and mixer CPS.

All five wrappers expose call("Operation", *args) for the exact 2025.2 driver entry point with the instance supplied by the wrapper. new("Type", fields) allocates an owning cffi pointer, including nested structs and arrays. For example, use eq.initialize(DatapathMode=0), ofdm.initialize(CCSequenceLength=4), or prach.initialize(Sequence=[{"Length": 4}]) for one enabled band. Raw calls follow the C preconditions and return conventions, including vendor assertions. Use status(), interrupt_mask() and set_interrupt_mask() on the mixer/filter and call("ClearEventStatus", status) to clear selected events.

## Offline verification

With PYNQ_DFE_LIBDIR pointing at the native build, run `python -m pytest tests`. Tests use the shim's open_buffer symbol and a fake overlay IP description. The buffer holds register words and allows control transactions without programming a board.

At first use cffi checks every public struct size and field offset against the packaged C measurements. To check against an actual native build's inputs, set DRIVERS to its XilinxProcessorIPLib/drivers directory and METAL_INCLUDE to its libmetal include directory. Make the sysfs headers available through CPATH if needed.

```sh
python tests/generate_abi.py "$DRIVERS" "$METAL_INCLUDE" csrc/xdfe_mmio_shim.h --check
```

Omit --check to regenerate the declarations and measurements for an intentional ABI update. Rebuild the libraries and wheel together. The layout check uses reference C measurements and cannot identify an arbitrary swapped shared object.
