# PYNQ hard DFE drivers

Python bindings for the RFSoC DFE mixer 2.0, channel filter 1.1, equalizer 1.0, NR PRACH 2.0 and OFDM 2.2. The native libraries and generated declarations use AMD embeddedsw `xlnx_rel_v2025.2` (c3b3132f6e1e202e275b8dd77b3804f3b449528c), Linux non-SDT, AArch64.

## Installation on PYNQ 4.0.0

Build the five native libraries using the companion build_libs.sh and LIBS.md. Build the binding wheel in this directory with `python -m pip wheel --no-deps .`. Stage the wheel in /data/dfe and the five libxdfe*.so files in /data/dfe/lib. In the activated board venv use the following commands. /dev/shm can replace /data for a temporary installation.

```sh
mkdir -p /data/dfe/python /data/dfe/tmp
TMPDIR=/data/dfe/tmp python -m pip install --no-cache-dir --no-index --no-deps \
    --target /data/dfe/python /data/dfe/pynq_dfe-*.whl
export PYTHONPATH="/data/dfe/python${PYTHONPATH:+:$PYTHONPATH}"
export PYNQ_DFE_LIBDIR=/data/dfe/lib
python -c 'import pynq, numpy, cffi, pynq_dfe'
```

Use the same package path and environment in the notebook kernel. The wheel contains the Python bindings and measured layouts. It requires cffi and NumPy in the venv. SciPy is optional. The kernel process needs permission to map PL registers through /dev/mem.

## Overlay use

Import pynq_dfe before constructing the Overlay so PYNQ registers the five DefaultIP subclasses. Substitute the instance names from your overlay. Each IP's `.dfe` owns one native handle. Close it before unloading the overlay and serialize access to each handle.

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
