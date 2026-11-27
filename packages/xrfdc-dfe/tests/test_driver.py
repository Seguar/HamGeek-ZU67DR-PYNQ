# SPDX-License-Identifier: BSD-3-Clause
"""Exercise the wheel's native Linux driver on a RAM-backed MMIO window."""
import ctypes
import importlib
import os
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from xml.etree import ElementTree as ET

import pytest


class DefaultIP:
    def __init__(self, description):
        length = description["addr_range"]
        self.buffer = ctypes.create_string_buffer(length)
        array = SimpleNamespace(nbytes=length, ctypes=SimpleNamespace(data=ctypes.addressof(self.buffer)))
        self.mmio = SimpleNamespace(base_addr=description["phys_addr"], array=array)


@pytest.fixture(scope="module")
def driver():
    with pytest.MonkeyPatch.context() as patch:
        pynq = ModuleType("pynq")
        pynq.DefaultIP = DefaultIP
        patch.setitem(sys.modules, "pynq", pynq)
        # Only for the C branch before its sibling config/MTS commit is merged.
        package = Path(__file__).resolve().parents[1] / "xrfdc"
        if not (package / "config.py").exists():
            def populate(obj, desc, ffi):
                params = desc["parameters"]
                obj.IPType = int(params["C_IP_Type"])
                for kind in ("ADC", "DAC"):
                    for i, tile in enumerate(getattr(obj, kind + "Tile_Config")):
                        tile.NumSlices = int(params[f"C_{kind}{i}_Slices"])
                        tile.MaxSampleRate = float(params[f"C_{kind}{i}_Fs_Max"])
            patch.setitem(sys.modules, "xrfdc.config", SimpleNamespace(populate_config=populate))
            patch.setitem(sys.modules, "xrfdc.mts", SimpleNamespace(MTSMixin=type("MTSMixin", (), {})))
        yield importlib.import_module("xrfdc")


@pytest.fixture
def description():
    if "ROWTIMING_HWH" not in os.environ:
        pytest.skip("set ROWTIMING_HWH to the RowTiming r5 HWH")
    module = ET.parse(os.environ["ROWTIMING_HWH"]).find(".//MODULE[@MODTYPE='usp_rf_data_converter']")
    params = {p.get("NAME"): p.get("VALUE") for p in module.findall("PARAMETERS/PARAMETER")}
    base = int(params["C_BASEADDR"], 0)
    return dict(type=module.get("VLNV"), parameters=params, phys_addr=base,
                addr_range=int(params["C_HIGHADDR"], 0) - base + 1)


def test_all_native_exports(driver):
    names = re.findall(r"\b(XRFdc_\w+)\(", driver.header_text)
    assert len(names) >= 100
    for name in names:
        assert callable(getattr(driver._lib, name)), name
    for cls, methods in [
        (driver.RFdc, ["GetTileLayout"]),
        (driver.RFdcTile, ["CustomStartUp", "GetMinSampleRate", "GetMaxSampleRate"]),
        (driver.RFdcBlock, ["SetConnectedIQData", "GetCoupling"]),
        (driver.RFdcDacBlock, ["SetDACDataScaler", "GetDACDataScaler"]),
        (driver.RFdcAdcBlock, ["SetSignalDetector", "GetSignalDetector"]),
    ]:
        for name in methods:
            assert callable(getattr(cls, name))


def test_rowtiming_native(driver, description):
    ip = driver.RFdc(description)
    lib = driver._lib
    assert description["type"] in ip.bindto
    assert ip.GetTileLayout() == lib.XRFDC_3ADC_2DAC_TILES
    assert [len(t.blocks) for t in ip.adc_tiles] == [4, 4, 2]
    assert [len(t.blocks) for t in ip.dac_tiles] == [4, 4]
    adc, dac = ip.adc_tiles[0], ip.dac_tiles[0]
    assert adc.GetMaxSampleRate() == 2950
    assert dac.GetMaxSampleRate() == 10000
    assert 0 < dac.GetMinSampleRate() < dac.MaxSampleRate

    block = dac.blocks[0]
    block.SetConnectedIQData(2, -1)
    state = ip._instance.DAC_Tile[0].DACBlock_Digital_Datapath[0]
    assert (state.ConnectedIData, state.ConnectedQData) == (2, -1)
    # These registers are read-only in silicon. Seed the emulated enable bits.
    for offset, value in ((lib.XRFDC_TILES_ENABLED_OFFSET, 0x37),
                          (lib.XRFDC_DAC_PATHS_ENABLED_OFFSET, 1),
                          (lib.XRFDC_ADC_PATHS_ENABLED_OFFSET, 1)):
        ctypes.c_uint32.from_buffer(ip.buffer, offset).value = value
    block.SetDACDataScaler(1)
    assert block.GetDACDataScaler() == 1
    block.DACDataScaler = 0
    assert block.DACDataScaler == 0
    with pytest.raises(RuntimeError, match="SetDACDataScaler"):
        block.DACDataScaler = 2
    assert block.GetCoupling() in (0, 1)
    detector = adc.blocks[0].GetSignalDetector()
    detector["Threshold"] = 3
    assert adc.blocks[0].SignalDetector["Threshold"] == 3


def test_full_layout(driver, description):
    params = description["parameters"]
    for kind in ("ADC", "DAC"):
        for i in range(4):
            params[f"C_{kind}{i}_Slices"] = "4"
    ip = driver.RFdc(description)
    assert ip.GetTileLayout() == driver._lib.XRFDC_4ADC_4DAC_TILES
    assert [len(t.blocks) for t in ip.adc_tiles + ip.dac_tiles] == [4] * 8


def test_short_window(driver, description):
    description["addr_range"] = 4096
    with pytest.raises(RuntimeError, match="MMIO window"):
        driver.RFdc(description)
