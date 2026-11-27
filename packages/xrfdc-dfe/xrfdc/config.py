# Copyright (c) 2018, Xilinx, Inc.
# SPDX-License-Identifier: BSD-3-Clause
"""Translate Vivado RFDC parameters using the rfdc v13 config table layout."""

from collections.abc import Mapping
from weakref import WeakKeyDictionary


_TILE = {
    "Enable": "Enable", "PLLEnable": "PLL_Enable", "SamplingRate": "Sampling_Rate",
    "RefClkFreq": "Refclk_Freq", "FabClkFreq": "Fabric_Freq", "FeedbackDiv": "FBDIV",
    "OutputDiv": "OutDiv", "RefClkDiv": "Refclk_Div", "MultibandConfig": "Band",
    "MaxSampleRate": "Fs_Max", "NumSlices": "Slices",
}
_FLOAT = {"SamplingRate", "RefClkFreq", "FabClkFreq", "MaxSampleRate", "NCOFreq"}
_NAMES = WeakKeyDictionary()


def _integer(value):
    raw = str(value).lower()
    if raw in ("true", "false"):
        return int(raw == "true")
    return int(raw, 0)


def parse_rfdc_params(params: dict) -> dict:
    """Return the SDT XRFdc_Config layout from an IP description or HWH parameters."""
    values = {k.lower(): v for k, v in params.get("parameters", params).items()}

    def read(key, field="", default=None):
        key = "c_" + key.lower()
        value = values.get(key, default)
        if value is None:
            raise ValueError(f"Missing RFDC parameter {key}")
        try:
            return float(value) if field in _FLOAT else _integer(value)
        except ValueError as exc:
            raise ValueError(f"Invalid RFDC parameter {key}={value!r}") from exc

    version = params.get("type", "xilinx.com:ip:usp_rf_data_converter:2.6").split(":")[-1]
    master = read("Sysref_Master", default=0)
    source = read("Sysref_Source")
    config = {
        "Name": f"xlnx,usp-rf-data-converter-{version}",
        "BaseAddr": read("BASEADDR", default=params.get("phys_addr")),
        "ADCType": read("High_Speed_ADC"), "IPType": read("IP_Type"),
        "SiRevision": read("Silicon_Revision"),
        "MasterADCTile": master, "MasterDACTile": master,
        "ADCSysRefSource": source, "DACSysRefSource": source,
    }
    for kind in ("DAC", "ADC"):
        tiles = []
        config[kind + "Tile_Config"] = tiles
        for i in range(4):
            prefix = f"{kind}{i}_"
            tile = {field: read(prefix + suffix, field) for field, suffix in _TILE.items()}
            if kind == "DAC":
                tile["LinkCoupling"] = read(prefix + "Link_Coupling")
            analog, digital = [], []
            tile[kind + "Block_Analog_Config"] = analog
            tile[kind + "Block_Digital_Config"] = digital
            for j in range(4):
                index = f"{i}{j}"
                available = read(f"{kind}_Slice{index}_Enable")
                a = {"BlockAvailable": available, "MixMode": read(f"{kind}_Mixer_Mode{index}")}
                d = {
                    "MixerInputDataType": read(f"{kind}_Data_Type{index}"),
                    "DataWidth": read(f"{kind}_Data_Width{index}"),
                    "MixerType": read(f"{kind}_Mixer_Type{index}"),
                    "NCOFreq": read(f"{kind}_NCO_Freq{index}", "NCOFreq"),
                    "FifoEnable": read(f"{kind}_Fifo{index}_Enable", default=values.get(
                        f"c_{kind.lower()}{index}_dig_port", available)),
                }
                if kind == "DAC":
                    a["InvSyncEnable"] = read(f"DAC_Invsinc_Ctrl{index}")
                    a["DecoderMode"] = read(f"DAC_Decoder_Mode{index}")
                    d["AdderEnable"] = read(f"DAC_Adder{index}_Enable", default=0)
                    d["InterpolationMode"] = read(f"DAC_Interpolation_Mode{index}")
                else:
                    d["DecimationMode"] = read(f"ADC_Decimation_Mode{index}")
                analog.append(a)
                digital.append(d)
            tiles.append(tile)
    return config


def populate_config(obj, params, ffi=None):
    """Populate a cffi config pointer in place. Accept either argument order."""
    if isinstance(obj, Mapping):
        obj, params = params, obj
    if ffi is None:
        from cffi import FFI
        ffi = FFI()
    fields = parse_rfdc_params(params)
    name = fields.pop("Name")
    if hasattr(obj, "Name"):
        # The C struct only holds the pointer. Tie its storage to the config.
        storage = ffi.new("char[]", name.encode())
        obj.Name = storage
        _NAMES[obj] = storage
    else:
        raw = params.get("parameters", params)
        obj.DeviceId = _integer(raw.get("DEVICE_ID", raw.get("C_DEVICE_ID", 0)))
    for field, value in fields.items():
        setattr(obj, field, value)
    return obj
