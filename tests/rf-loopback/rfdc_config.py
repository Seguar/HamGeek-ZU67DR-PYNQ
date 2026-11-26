# SPDX-License-Identifier: BSD-3-Clause
"""Generate an AMD XRFdc_Config initializer from the matching HWH file."""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

DEVICE = {"ADCType": "High_Speed_ADC", "IPType": "IP_Type", "SiRevision": "Silicon_Revision",
          "MasterADCTile": "Sysref_Master", "MasterDACTile": "Sysref_Master",
          "ADCSysRefSource": "Sysref_Source", "DACSysRefSource": "Sysref_Source"}
TILE = {"Enable": "Enable", "PLLEnable": "PLL_Enable", "SamplingRate": "Sampling_Rate",
        "RefClkFreq": "Refclk_Freq", "FabClkFreq": "Fabric_Freq", "FeedbackDiv": "FBDIV",
        "OutputDiv": "OutDiv", "RefClkDiv": "Refclk_Div", "MultibandConfig": "Band",
        "MaxSampleRate": "Fs_Max", "NumSlices": "Slices"}
ANALOG = {"BlockAvailable": "Slice{}_Enable", "MixMode": "Mixer_Mode{}"}
DIGITAL = {"MixerInputDataType": "Data_Type{}", "DataWidth": "Data_Width{}",
           "FifoEnable": "Fifo{}_Enable", "MixerType": "Mixer_Type{}", "NCOFreq": "NCO_Freq{}"}


def fixed_dac_parameters(hwh):
    """Read the configured and generated RFDC fields for this eight-DAC overlay."""
    modules = ET.parse(hwh).findall(".//MODULE[@MODTYPE='usp_rf_data_converter']")
    if len(modules) != 1 or modules[0].get("INSTANCE") != "rfdc":
        raise ValueError("expected a single RFDC named rfdc")
    values = {node.get("NAME").lower(): node.get("VALUE")
              for node in modules[0].findall("./PARAMETERS/PARAMETER")}

    # RFDC 2.6 encodes fixed 20 mA as 0 and fixed 32 mA as 1.
    required = {"DAC_VOP_Mode": "0", "DAC_Output_Current": "0", "DAC_VOP_RTS": "false"}
    required.update({f"DAC{tile}_Enable": str(int(tile < 2)) for tile in range(4)})
    required.update({f"DAC_Slice{tile}{block}_Enable": "true"
                     for tile in range(2) for block in range(4)})
    for name, expected in required.items():
        for prefix in ("", "C_"):
            field = prefix + name
            value = values.get(field.lower())
            if value != expected:
                raise ValueError(
                    f"expected the fixed 20 mA eight-DAC overlay: {field}={value!r}, want {expected!r}"
                )
    return values


def generate(hwh):
    values = fixed_dac_parameters(hwh)

    def number(name, missing=None):
        value = values.get(("C_" + name).lower(), missing)
        if value is None:
            raise ValueError(f"Missing RFDC configuration field {name}")
        value = {"true": "1", "false": "0"}.get(value, value)
        float(value)
        return value

    def block(entries, kind, tile, index):
        key = f"{tile}{index}"
        result = []
        for field, param in entries.items():
            if field == "FifoEnable":
                # HWH describes these stream ports as enabled digital ports.
                flag = number(f"{kind}{key}_Dig_Port", missing="1")
            elif field == "AdderEnable":
                flag = number(kind + "_" + param.format(key), missing="0")
            else:
                flag = number(kind + "_" + param.format(key))
            result.append(f".{field} = {flag}")
        return "            {" + ", ".join(result) + "},"

    out = ["static XRFdc_Config config = {", "    .BaseAddr = 0x82000000,"]
    for field, param in DEVICE.items():
        out.append(f"    .{field} = {number(param, missing='0')},")
    for kind in ("DAC", "ADC"):
        out.append(f"    .{kind}Tile_Config = {{")
        for tile in range(2):
            out.append(f"        [{tile}] = {{")
            fields = TILE | ({"LinkCoupling": "Link_Coupling"} if kind == "DAC" else {})
            for field, param in fields.items():
                out.append(f"            .{field} = {number(f'{kind}{tile}_{param}')},")
            analog = ANALOG | ({"InvSyncEnable": "Invsinc_Ctrl{}", "DecoderMode": "Decoder_Mode{}"}
                               if kind == "DAC" else {})
            digital = DIGITAL | ({"InterpolationMode": "Interpolation_Mode{}", "AdderEnable": "Adder{}_Enable"}
                                 if kind == "DAC" else {"DecimationMode": "Decimation_Mode{}"})
            for path, entries in (("Analog", analog), ("Digital", digital)):
                out.append(f"            .{kind}Block_{path}_Config = {{")
                out.extend(block(entries, kind, tile, i) for i in range(4))
                out.append("            },")
            out.append("        },")
        out.append("    },")
    return "\n".join(out + ["};", ""])


if __name__ == "__main__":
    Path(sys.argv[2]).write_text(generate(Path(sys.argv[1])))
