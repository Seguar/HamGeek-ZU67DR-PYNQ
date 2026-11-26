# SPDX-License-Identifier: BSD-3-Clause
"""Generate the ADC-only XRFdc_Config used by adc-nyquist."""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

TILE_FIELDS = {
    "Enable": "Enable",
    "NumSlices": "Slices",
    "PLLEnable": "PLL_Enable",
    "SamplingRate": "Sampling_Rate",
    "RefClkFreq": "Refclk_Freq",
    "FabClkFreq": "Fabric_Freq",
    "FeedbackDiv": "FBDIV",
    "OutputDiv": "OutDiv",
    "RefClkDiv": "Refclk_Div",
    "MultibandConfig": "Band",
    "MaxSampleRate": "Fs_Max",
}
DIGITAL_FIELDS = {
    "MixerInputDataType": "Data_Type",
    "DataWidth": "Data_Width",
    "DecimationMode": "Decimation_Mode",
    "MixerType": "Mixer_Type",
    "NCOFreq": "NCO_Freq",
}


def generate(hwh):
    root = ET.parse(hwh)
    modules = root.findall(".//MODULE[@MODTYPE='usp_rf_data_converter']")
    if len(modules) != 1:
        raise ValueError("expected a single RF Data Converter in the HWH")
    module = modules[0]
    values = {
        node.attrib["NAME"].lower(): node.attrib["VALUE"]
        for node in module.findall("./PARAMETERS/PARAMETER")
    }

    def number(name):
        raw = values.get(("C_" + name).lower())
        value = {"true": "1", "false": "0"}.get(raw, raw)
        if value is None or not re.fullmatch(
            r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", value
        ):
            raise ValueError(f"invalid numeric RFDC field C_{name}={raw!r}")
        return value

    ranges = {
        (int(node.attrib["BASEVALUE"], 0), int(node.attrib["HIGHVALUE"], 0))
        for node in root.findall(".//MEMRANGE")
        if node.get("INSTANCE") == module.get("INSTANCE")
        and node.get("SLAVEBUSINTERFACE", "").lower() == "s_axi"
    }
    if len(ranges) != 1:
        raise ValueError("expected a unique RFDC AXI register range")
    base, high = ranges.pop()
    if base < 0 or high < base:
        raise ValueError("invalid RFDC AXI register range")

    out = [
        "/* Generated from the overlay HWH by adc_rfdc_config.py. */",
        f"#define RFDC_MMIO_SPAN {high - base + 1:#x}U",
        "",
        "static XRFdc_Config config = {",
        f"    .BaseAddr = {base:#x}ULL,",
        f"    .ADCType = {number('High_Speed_ADC')},",
        f"    .IPType = {number('IP_Type')},",
        f"    .SiRevision = {number('Silicon_Revision')},",
        "    .ADCTile_Config = {",
    ]
    enabled_blocks = 0
    for tile in range(4):
        if number(f"ADC{tile}_Enable") == "0":
            continue
        slices = int(number(f"ADC{tile}_Slices"))
        if slices not in (2, 4):
            raise ValueError(f"ADC tile {tile} has unsupported slice count {slices}")

        indices = [f"{tile}{block}" for block in range(4)]
        available = [int(number(f"ADC_Slice{index}_Enable")) for index in indices]
        if any(flag not in (0, 1) for flag in available) or any(available[slices:]):
            raise ValueError(f"invalid ADC slice enables on tile {tile}")
        enabled_blocks += sum(available)

        out.append(f"        [{tile}] = {{")
        for field, param in TILE_FIELDS.items():
            out.append(f"            .{field} = {number(f'ADC{tile}_{param}')},")
        out.append("            .ADCBlock_Analog_Config = {")
        for flag, index in zip(available, indices):
            out.append(
                f"                {{.BlockAvailable = {flag}, "
                f".MixMode = {number(f'ADC_Mixer_Mode{index}')}}},"
            )
        out.append("            },")
        out.append("            .ADCBlock_Digital_Config = {")
        for index in indices:
            fields = [
                f".{field} = {number(f'ADC_{param}{index}')}"
                for field, param in DIGITAL_FIELDS.items()
            ]
            fields.append(f".FifoEnable = {number(f'ADC{index}_Dig_Port')}")
            out.append("                {" + ", ".join(fields) + "},")
        out.extend(("            },", "        },"))
    if not enabled_blocks:
        raise ValueError("the HWH contains no enabled analog ADC blocks")
    return "\n".join(out + ["    },", "};", ""])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} HWH OUTPUT_HEADER")
    try:
        Path(sys.argv[2]).write_text(generate(Path(sys.argv[1])))
    except (ValueError, OSError, KeyError, ET.ParseError) as exc:
        sys.exit(str(exc))
