"""Uses the actual libxdfe drivers. The only substituted operation is MMIO open."""
import importlib
import sys
import types

import pytest

from pynq_dfe import ChannelFilter, Device, Mixer, lowpass_taps, mixer_rate, sequence_bitmap
from pynq_dfe.metadata import config_fields

# v2025.2 read-only model parameter words, one operational band for PRACH.
MODEL = {"mix": 0x01110410, "ccf": 0x10410, "equ": 0x08010101,
         "prach": 0x41011211, "ofdm": 0x10020}


@pytest.fixture
def offline(monkeypatch):
    def open_buffer(self, name, base, size):
        assert base == 0x80000000 and size == 65536 and name == b"unit"
        self.regs = self.ffi.new("uint32_t[]", size // 4)
        self.regs[0] = 0x12345678
        self.regs[2] = MODEL[self.driver]
        self.regs[3] = 0x081010 if self.driver == "mix" else 0x12111211
        symbol = f"xdfe_{self.driver}_mmio_open_buffer"
        self.ffi.cdef(f"{self.prefix} *{symbol}(const char *, void *, uint64_t);", override=True)
        return getattr(self.lib, symbol)(name, self.regs, size)
    monkeypatch.setattr(Device, "_open", open_buffer)
    return dict(fullpath="top/unit", phys_addr=0x80000000, addr_range=65536,
                parameters={"C_NUM_ANTENNA": "2", "C_NUM_BANDS": "1"})


@pytest.mark.parametrize("driver", MODEL)
def test_lifecycle(driver, offline):
    cls = {"mix": Mixer, "ccf": ChannelFilter}.get(driver, Device)
    with cls(driver, offline) as device:
        if driver in ("mix", "ccf"):
            assert device._inst.Config.NumAntenna == 2
        with pytest.raises(RuntimeError):
            device.configure()
        device.reset()
        cfg = device.configure()
        assert cfg.Version.Major == 0x12
        assert device.versions()[1][0] == 0x12
        fields = {"equ": {}, "ofdm": {"CCSequenceLength": 4},
                  "prach": {"Sequence": [{"Length": 4}]}}
        device.initialize(**fields.get(driver, {"Sequence": {"Length": 4}}))
        if driver in ("mix", "ccf"):
            device.set_triggers(device.triggers())
        device.activate()
        device.set_interrupt_mask(device.interrupt_mask())
        if driver in ("mix", "ccf"):
            assert device.status().CCUpdate == 0
            cfg = device.empty_cc_config()
            carrier = device.new("CarrierCfg")
            args = [device.new("NCO")] if driver == "mix" else []
            device.add_cc_to_config(cfg, 1, 1, carrier, *args)
            if driver == "mix":
                carrier.DUCDDCCfg.NCOIdx = 2
            device.update_cc_in_config(cfg, 1, carrier)
            if driver == "mix":
                device.set_antenna_gain(0, 1)
                device.set_nco(cfg, 1, frequency={"FrequencyControlWord": 42}, phase={"PhaseAcc": 99})
                assert cfg.NCO[2].PhaseCfg.PhaseAcc == 99
            else:
                device.set_antenna_enabled(0, True)
                device.load_coefficients(1, 0, [1, 2, 1], symmetric=True)
                assert device.regs[0x3000 // 4] & (1 << 8)
            device.commit_cc_config(cfg)
            device.remove_cc_from_config(cfg, 1)
            device.current_cc_config()
        # Emulate the read-only operational bit which the real block sets after activation.
        offset = {"mix": 0x10, "ccf": 0x20, "equ": 0x38, "prach": 0x10, "ofdm": 0x20}[driver]
        device.regs[offset // 4] = 1
        device.deactivate()
        device._require_state("INITIALISED")
    device.close()
    with pytest.raises(RuntimeError, match="closed"):
        device.versions()


def test_overlay(monkeypatch, offline):
    class DefaultIP:
        def __init__(self, description):
            self.description = description
    monkeypatch.setitem(sys.modules, "pynq", types.SimpleNamespace(DefaultIP=DefaultIP))
    ip = importlib.import_module("pynq_dfe.ip")
    obj = ip.MixerIP(offline)
    with obj.dfe as mixer:
        assert isinstance(obj, DefaultIP)
        assert obj.bindto == ["xilinx.com:ip:xdfe_cc_mixer:2.0"]
        assert mixer._inst.Config.NumAntenna == 2


def test_helpers():
    taps = lowpass_taps(31, 1, 8)
    assert list(taps) == list(reversed(taps))
    assert abs(int(taps.sum()) - 32768) <= len(taps) // 2
    bitmap = sequence_bitmap([4, None, 4, 0], 4)
    assert bitmap == 5 and mixer_rate(4, bitmap) == 2
    with pytest.raises(ValueError):
        mixer_rate(4, 7)
    assert config_fields("prach", {"C_NUM_SLOT_CHANNELS1": "3"}) == {("NumAntennaChannels", 1): 3}
    assert config_fields("mix", {"CONFIG.MODE": "Uplink"}) == {("Mode", None): 1}


def test_layout_drift(tmp_path, monkeypatch):
    import json
    from pynq_dfe import binding
    layout = json.loads((binding.ABI / "mix.json").read_text())
    layout["XDfeMix.Config"] += 4
    (tmp_path / "mix.json").write_text(json.dumps(layout))
    (tmp_path / "mix.h").write_bytes((binding.ABI / "mix.h").read_bytes())
    monkeypatch.setattr(binding, "ABI", tmp_path)
    binding.checked_ffi.cache_clear()
    with pytest.raises(RuntimeError, match="XDfeMix.Config"):
        binding.checked_ffi("mix")
