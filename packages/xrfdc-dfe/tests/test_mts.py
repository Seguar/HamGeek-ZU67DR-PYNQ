# SPDX-License-Identifier: BSD-3-Clause
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest


MTSMixin = runpy.run_path(str(Path(__file__).resolve().parents[1] / "xrfdc/mts.py"))["MTSMixin"]


class FFI:
    NULL = None

    def new(self, ctype):
        if ctype == "unsigned int *":
            return [0]
        assert ctype == "XRFdc_MultiConverter_Sync_Config *"
        return SimpleNamespace(Latency=[0] * 4, Offset=[0] * 4)


class RFdc(MTSMixin):
    _ffi = FFI()
    _instance = object()

    def __init__(self):
        self._lib = self
        self.status = 0
        self.auto_adc = 440

    def XRFdc_MultiConverter_Init(self, cfg, pll, t1, ref):
        assert pll is None and t1 is None
        cfg.RefTile = ref
        return 0

    def XRFdc_MultiConverter_Sync(self, instance, kind, cfg):
        assert instance is self._instance and cfg.RefTile == 0 and cfg.Tiles == 3
        measured = [self.auto_adc, 416][kind] if cfg.Target_Latency == -1 else cfg.Target_Latency
        cfg.Latency[:2] = [measured] * 2
        cfg.Offset[:2] = [3, 4]
        return self.status

    def XRFdc_MTS_Sysref_Config(self, instance, dac, adc, enable):
        self.gate = (dac.Tiles, adc.Tiles, enable)
        return 0

    def XRFdc_GetMTSEnable(self, instance, kind, tile, output):
        assert instance is self._instance
        output[0] = int(kind == 0 and tile < 2)
        return self.status


@pytest.mark.parametrize("adc_auto", [440, 444])
def test_sync(adc_auto):
    rf = RFdc()
    rf.auto_adc = adc_auto
    for method, fixed, auto in [(rf.mts_dac_sync, 432, 416), (rf.mts_adc_sync, 448, adc_auto)]:
        for target, expected in [(fixed, fixed), (None, auto)]:
            assert method([0, 1], target) == {
                "Latency": expected, "tiles": {0: {"Latency": expected, "Offset": 3},
                                               1: {"Latency": expected, "Offset": 4}},
            }
    rf.mts_sysref_disable()
    assert rf.gate == (3, 3, 0)
    rf.mts_sysref_enable(1, [1])
    assert rf.gate == (1, 2, 1)
    assert rf.get_mts_enable(0, 1)
    assert not rf.get_mts_enable(1, 1)


def test_status():
    rf = RFdc()
    rf.status = 2 | 32 | 256
    with pytest.raises(RuntimeError, match="TIMEOUT.*TARGET_LOW.*unknown bits 0x100"):
        rf.mts_adc_sync(3)
    with pytest.raises(RuntimeError, match="GetMTSEnable"):
        rf.get_mts_enable(0, 1)


@pytest.mark.parametrize("tiles,target", [(0, None), ([4], None), (16, None), (3, -2)])
def test_invalid_input(tiles, target):
    with pytest.raises(ValueError):
        RFdc().mts_adc_sync(tiles, target)
