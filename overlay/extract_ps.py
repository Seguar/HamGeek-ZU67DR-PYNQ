# SPDX-License-Identifier: BSD-3-Clause
"""Extract the PS preset from the original HamGeek Vivado example locally."""

import argparse
import json
from pathlib import Path
import re
from zipfile import ZipFile


def extract(archive):
    with ZipFile(archive) as source:
        matches = [name for name in source.namelist() if name.endswith("/bd/system/system.bd")]
        if len(matches) != 1:
            raise ValueError("Expected the original rfevm_rf_adaloop Vivado project")
        design = json.loads(source.read(matches[0]))["design"]

    part = design["design_info"]["device"]
    ps = design["components"]["zynq_ultra_ps_e_0"]
    if part != "xczu67dr-fsve1156-2-i" or ps["vlnv"] != "xilinx.com:ip:zynq_ultra_ps_e:3.5":
        raise ValueError("Vendor preset is for a different board or PS core")
    preset = [f"set part {part}", f"set ps_ip {ps['vlnv']}", "set vendor_config [list \\"]
    for name, parameter in sorted(ps["parameters"].items()):
        value = parameter["value"]
        if isinstance(value, list):
            # Vivado regenerates these serialized MIO display trees.
            continue
        if not re.fullmatch(r"[A-Za-z0-9_]+", name) or any(c in value for c in "{}\r\n"):
            raise ValueError(f"Unsupported Tcl literal for {name}")
        preset.append(f"    CONFIG.{name} {{{value}}} \\")
    return "\n".join(preset + ["]", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vendor_vivado_zip", type=Path)
    parser.add_argument("preset_tcl", type=Path)
    args = parser.parse_args()
    args.preset_tcl.write_text(extract(args.vendor_vivado_zip))
