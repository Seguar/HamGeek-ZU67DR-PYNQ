# SPDX-License-Identifier: BSD-3-Clause
"""Offline regression tests. Set ROWTIMING_HWH to the acceptance r5 HWH."""
import gc
import os
import re
import runpy
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[3]
CONFIG = runpy.run_path(str(Path(__file__).resolve().parents[1] / "xrfdc/config.py"))
parse = CONFIG["parse_rfdc_params"]


@pytest.fixture
def hwh():
    if "ROWTIMING_HWH" not in os.environ:
        pytest.skip("set ROWTIMING_HWH for the r5 regression")
    return Path(os.environ["ROWTIMING_HWH"])


@pytest.fixture
def params(hwh):
    module = ET.parse(hwh).find(".//MODULE[@MODTYPE='usp_rf_data_converter']")
    return {p.get("NAME"): p.get("VALUE") for p in module.findall("PARAMETERS/PARAMETER")}


def test_rowtiming(params):
    cfg = parse(params)
    assert cfg["IPType"] == 2
    assert cfg["MasterADCTile"] == cfg["MasterDACTile"] == 0
    assert cfg["ADCSysRefSource"] == cfg["DACSysRefSource"] == 1
    adc, dac = cfg["ADCTile_Config"], cfg["DACTile_Config"]
    assert [t["Enable"] for t in adc] == [1, 1, 1, 0]
    assert [t["Enable"] for t in dac] == [1, 1, 0, 0]
    assert [t["SamplingRate"] for t in adc[:3]] == [2.5, 2.5, 5]
    assert [t["RefClkFreq"] for t in adc[:3]] == [2500, 2500, 250]
    assert [t["NumSlices"] for t in adc] == [4, 4, 2, 0]
    assert [t["NumSlices"] for t in dac] == [4, 4, 0, 0]
    for tile in dac[:2]:
        assert (tile["SamplingRate"], tile["RefClkFreq"], tile["LinkCoupling"]) == (10, 250, 0)
    assert [params[f"C_DAC{i}_VOP"] for i in range(2)] == ["20.0", "20.0"]
    assert params["C_DAC_Output_Current"] == params["C_DAC_VOP_Mode"] == "0"
    assert params["C_DAC_VOP_RTS"] == "false"
    assert [params[f"C_ADC{i}_Clock_Source"] for i in range(3)] == ["2"] * 3
    assert [params[f"C_DAC{i}_Clock_Source"] for i in range(2)] == ["4"] * 2


def test_explicit_tcl_parameters(params):
    params.update(C_Sysref_Master="1", C_ADC_Fifo00_Enable="0", C_DAC_Adder11_Enable="1",
                  C_DAC_NCO_Freq11="-2.75", C_DAC0_Link_Coupling="1")
    cfg = parse({"parameters": params})
    assert cfg["MasterADCTile"] == cfg["MasterDACTile"] == 1
    assert cfg["ADCTile_Config"][0]["ADCBlock_Digital_Config"][0]["FifoEnable"] == 0
    assert cfg["DACTile_Config"][0]["LinkCoupling"] == 1
    block = cfg["DACTile_Config"][1]["DACBlock_Digital_Config"][1]
    assert (block["AdderEnable"], block["NCOFreq"]) == (1, -2.75)


def test_against_adc_nyquist(hwh, params):
    """Compare every explicit scalar in the actual generated C initializer."""
    generate = runpy.run_path(str(ROOT / "tests/adc-nyquist/adc_rfdc_config.py"))["generate"]
    cfg = parse(params)
    dest = cfg
    count = 0
    for line in generate(hwh).splitlines():
        tile = re.match(r"\s*\[(\d+)\] =", line)
        array = re.match(r"\s*\.(ADCBlock_\w+_Config) = \{", line)
        if tile:
            dest = cfg["ADCTile_Config"][int(tile[1])]
        elif array:
            rows = iter(dest[array[1]])
        row = next(rows) if line.lstrip().startswith("{.") else dest
        for key, raw in re.findall(r"\.(\w+) = (-?(?:0x[\da-fA-F]+|[\d.eE+-]+))", line):
            number = int(raw, 16) if raw.startswith("0x") else float(raw)
            assert row[key] == number, (key, raw)
            count += 1
    assert count == 133


def test_populate_v13(params):
    """Set RFDC_HEADER to check the actual layout from the embeddedsw checkout."""
    if "RFDC_HEADER" not in os.environ:
        pytest.skip("set RFDC_HEADER to v13 xrfdc.h")
    from cffi import FFI
    header = Path(os.environ["RFDC_HEADER"]).read_text()
    start = header.rindex("typedef struct {", 0, header.index("} XRFdc_DACBlock_AnalogDataPath_Config"))
    end = header.index("} XRFdc_Config;") + len("} XRFdc_Config;")
    structs = re.sub(r"#ifndef SDT.*?#else(.*?)#endif", r"\1", header[start:end], flags=re.S)
    ffi = FFI()
    ffi.cdef("typedef unsigned int u32; typedef unsigned long metal_phys_addr_t;" + structs)
    ptr = ffi.new("XRFdc_Config *")
    CONFIG["populate_config"](ptr, params, ffi)
    gc.collect()

    def compare(cobj, expected):
        for field, value in expected.items():
            actual = getattr(cobj, field)
            if isinstance(value, list):
                assert len(actual) == len(value)
                for item, row in zip(actual, value):
                    compare(item, row)
            elif field == "Name":
                assert ffi.string(actual).decode() == value
            else:
                assert actual == value

    compare(ptr, parse(params))
