"""ABI-mode bindings for AMD embeddedsw xlnx_rel_v2025.2, Linux non-SDT."""
import json
import os
from functools import lru_cache
from pathlib import Path

from cffi import FFI

from .metadata import FIELDS, config_fields, number

ABI = Path(__file__).parent / "abi"


@lru_cache(None)
def checked_ffi(driver):
    if driver not in FIELDS:
        raise ValueError(f"Unknown DFE driver {driver!r}")
    ffi = FFI()
    ffi.cdef((ABI / f"{driver}.h").read_text())
    for key, expected in json.loads((ABI / f"{driver}.json").read_text()).items():
        typename, _, field = key.partition(".")
        actual = ffi.offsetof(typename, field) if field else ffi.sizeof(typename)
        if actual != expected:
            raise RuntimeError(f"ABI mismatch for {key}: cffi={actual}, C={expected}")
    return ffi


class Device:
    """Own a shim handle. Use as a context manager, or explicitly close it."""
    def __init__(self, driver, description):
        self.driver = driver
        self.prefix = "XDfe" + driver.capitalize()
        self.ffi = checked_ffi(driver)
        filename = f"libxdfe{driver}.so"
        directory = os.environ.get("PYNQ_DFE_LIBDIR")
        bundled = Path(__file__).parent / "lib" / filename
        if directory:
            library = str(Path(directory) / filename)
        elif bundled.is_file():
            library = str(bundled)
        else:
            library = filename
        self.lib = self.ffi.dlopen(library)
        values = config_fields(driver, description["parameters"])
        base = number(description["phys_addr"])
        size = number(description["addr_range"])
        name = description["fullpath"].split("/")[-1].encode()
        inst = self._open(name, base, size)
        if inst == self.ffi.NULL:
            raise OSError(self.ffi.errno, f"opening {filename} at {base:#x} ({size:#x} bytes)")
        self._inst = self.ffi.gc(inst, getattr(self.lib, f"xdfe_{driver}_mmio_close"))
        try:
            for (field, index), value in values.items():
                if index is None:
                    setattr(inst.Config, field, value)
                else:
                    getattr(inst.Config, field)[index] = value
        except Exception:
            self.close()
            raise

    def _open(self, name, base, size):
        return getattr(self.lib, f"xdfe_{self.driver}_mmio_open")(name, base, size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self._inst != self.ffi.NULL:
            self.ffi.release(self._inst)
            self._inst = self.ffi.NULL

    def new(self, typename, values=None):
        """Allocate a driver struct. Nested dictionaries and lists initialize its fields."""
        return self.ffi.new(f"{self.prefix}_{typename} *", values)

    def call(self, operation, *args):
        """Invoke the exact driver operation, omitting InstancePtr. Return its raw result."""
        if self._inst == self.ffi.NULL:
            raise RuntimeError("DFE handle is closed")
        if operation.startswith("Instance"):
            raise ValueError("Use the MMIO handle lifecycle")
        return getattr(self.lib, f"{self.prefix}_{operation}")(self._inst, *args)

    def _checked(self, operation, *args):
        result = self.call(operation, *args)
        if result:
            raise RuntimeError(f"{self.prefix}_{operation} returned {result}")

    def _output(self, operation, typename):
        result = self.new(typename)
        self.call(operation, result)
        return result

    def reset(self):
        self.call("Reset")

    def _require_state(self, name):
        state = self.call("GetStateID")
        if state != getattr(self.lib, f"XDFE{self.driver.upper()}_STATE_{name}"):
            raise RuntimeError(f"{self.prefix} requires {name}, current state is {state}")

    def configure(self):
        self._require_state("RESET")
        return self._output("Configure", "Cfg")

    def initialize(self, **fields):
        self._require_state("CONFIGURED")
        init = self.new("EqConfig" if self.driver == "equ" else "Init", fields)
        lengths = []
        if self.driver in ("mix", "ccf"):
            lengths = [init.Sequence.Length]
            if init.TuserSelect > 1:
                raise ValueError("TuserSelect must be zero or one")
        elif self.driver == "ofdm":
            lengths = [init.CCSequenceLength]
        elif self.driver == "prach":
            lengths = [init.Sequence[b].Length for b in range(self._inst.Config.NumBands)]
        elif self.driver == "equ" and init.DatapathMode > 2:
            raise ValueError("DatapathMode must be 0, 1 or 2")
        if any(not 1 <= length <= 16 for length in lengths):
            raise ValueError("Each enabled CC sequence needs 1..16 slots")
        self.call("Initialize", init)

    def activate(self, low_power=False):
        self._require_state("INITIALISED")
        self.call("Activate", low_power)

    def deactivate(self):
        self._require_state("OPERATIONAL")
        self.call("Deactivate")

    def versions(self):
        sw, hw = self.new("Version"), self.new("Version")
        self.call("GetVersions", sw, hw)
        return tuple(tuple(getattr(v, k) for k in ("Major", "Minor", "Revision", "Patch"))
                     for v in (sw, hw))

    def interrupt_mask(self):
        return self._output("GetInterruptMask", "InterruptMask")

    def set_interrupt_mask(self, mask):
        self.call("SetInterruptMask", mask)


class CarrierDevice(Device):
    """Mixer and channel-filter APIs. Configurations are editable cffi structs."""
    @staticmethod
    def _check_ccid(ccid):
        if not 0 <= ccid < 16:
            raise ValueError("CC ID must be in 0..15")

    def empty_cc_config(self):
        return self._output("GetEmptyCCCfg", "CCCfg")

    def current_cc_config(self):
        return self._output("GetCurrentCCCfg", "CCCfg")

    def add_cc(self, ccid, bitmap, carrier, *nco):
        self._require_state("OPERATIONAL")
        self._check_ccid(ccid)
        self._checked("AddCC", ccid, bitmap, carrier, *nco)

    def remove_cc(self, ccid):
        self._require_state("OPERATIONAL")
        self._check_ccid(ccid)
        self._checked("RemoveCC", ccid)

    def update_cc(self, ccid, carrier):
        self._require_state("OPERATIONAL")
        self._check_ccid(ccid)
        self._checked("UpdateCC", ccid, carrier)

    def add_cc_to_config(self, config, ccid, bitmap, carrier, *nco):
        self._check_ccid(ccid)
        self._checked("AddCCtoCCCfg", config, ccid, bitmap, carrier, *nco)

    def remove_cc_from_config(self, config, ccid):
        self._check_ccid(ccid)
        self.call("RemoveCCfromCCCfg", config, ccid)

    def update_cc_in_config(self, config, ccid, carrier):
        self._check_ccid(ccid)
        self._checked("UpdateCCinCCCfg", config, ccid, carrier)

    def commit_cc_config(self, config):
        self._checked("SetNextCCCfgAndTrigger", config)

    def triggers(self):
        return self._output("GetTriggersCfg", "TriggerCfg")

    def set_triggers(self, triggers):
        self._require_state("INITIALISED")
        if triggers.CCUpdate.Mode == 2:
            raise ValueError("Continuous mode is invalid for CC updates")
        self.call("SetTriggersCfg", triggers)

    def status(self):
        return self._output("GetEventStatus", "Status")


class Mixer(CarrierDevice):
    def set_antenna_gain(self, antenna, gain):
        self._require_state("OPERATIONAL")
        if not 0 <= antenna < self._inst.Config.NumAntenna or gain not in (0, 1):
            raise ValueError("Invalid antenna or gain")
        self._checked("SetAntennaGain", antenna, gain)

    def set_nco(self, config, ccid, *, frequency, phase):
        """Edit the NCO assigned to an active CC in a pending configuration."""
        if not 0 <= ccid < len(config.DUCDDCCfg) or config.DUCDDCCfg[ccid].Rate == 0:
            raise ValueError("CC must be active in the supplied configuration")
        nco = config.NCO[config.DUCDDCCfg[ccid].NCOIdx]
        nco.FrequencyCfg = self.new("Frequency", frequency)[0]
        nco.PhaseCfg = self.new("Phase", phase)[0]


class ChannelFilter(CarrierDevice):
    def set_cc_gain(self, ccid, gain):
        self._require_state("OPERATIONAL")
        if not 0 <= ccid < 16 or not 0 <= gain < 65536:
            raise ValueError("CC ID or gain out of range")
        carrier = self.new("CarrierCfg")
        self.call("GetCC", ccid, carrier)
        carrier.Gain = gain
        self.update_cc(ccid, carrier)

    def set_antenna_enabled(self, antenna, enabled):
        self._require_state("OPERATIONAL")
        if not 0 <= antenna < self._inst.Config.NumAntenna:
            raise ValueError("Invalid antenna")
        self._checked("UpdateAntenna", antenna, enabled)

    def load_coefficients(self, bank, shift, taps, symmetric=False):
        """Load full signed-int16 taps. Pack the first half for symmetric filters."""
        from operator import index
        taps = [index(tap) for tap in taps]
        if not 0 <= bank < 8 or not 0 <= shift < 16:
            raise ValueError("Coefficient set or shift outside register range")
        if not 1 <= len(taps) <= (256 if symmetric else 128):
            raise ValueError("Invalid number of filter taps")
        if symmetric and taps != taps[::-1]:
            raise ValueError("Symmetric taps must match in reverse order")
        values = taps[:(len(taps) + 1) // 2] if symmetric else taps
        self.call("LoadCoefficients", bank, shift,
                  self.new("Coefficients", dict(Num=len(taps), Symmetric=symmetric, Value=values)))
