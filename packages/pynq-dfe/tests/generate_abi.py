"""Regenerate declarations and C-measured layouts on the target Linux ABI."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from cffi import FFI

ABI = Path(__file__).resolve().parents[1] / "pynq_dfe" / "abi"


def generate(driver, drivers, metal, shim, destination, check=False):
    src = drivers / ("dfe" + driver) / "src"
    header = "xdfe" + driver + ".h"
    # Preprocess only the public declarations. Linux and metal internals stay opaque.
    raw = re.sub(r'^#include .*$', '', (src / header).read_text(), flags=re.M)
    declarations = subprocess.check_output(["cc", "-E", "-P", "-x", "c", "-"],
                                           input=raw, text=True)
    declarations = re.sub(r'\b__(u|s)(8|16|32|64)\b',
                          lambda m: ("u" if m[1] == "u" else "") + "int" + m[2] + "_t",
                          declarations)
    declarations = re.sub(r'(?<=\d)U\b', '', declarations)
    prefix = "XDfe" + driver.capitalize()
    declarations = "typedef unsigned long metal_phys_addr_t;\n" + declarations
    notice = (src / header).read_text().split("*/", 1)[0] + "*/\n"
    entrypoints = re.findall(rf"^[^#;\n]+\bxdfe_{driver}_mmio_(?:open|close)\([^;]+;", shim.read_text(), re.M)
    if len(entrypoints) != 2:
        raise ValueError(f"Expected open and close declarations for {driver} in {shim}")
    declarations = notice + declarations + "\n".join(entrypoints) + "\n"
    ffi = FFI()
    ffi.cdef(declarations)
    probe = ['#include <stddef.h>', '#include <stdio.h>', f'#include "{header}"',
             'int main(void) {']
    for typename in ffi.list_types()[0]:
        t = ffi.typeof(typename)
        if t.kind == "struct":
            probe.append(f'printf("{typename} %zu\\n", sizeof({typename}));')
            for field, _ in t.fields:
                probe.append(f'printf("{typename}.{field} %zu\\n", offsetof({typename}, {field}));')
    probe.append('}')
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "layout"
        subprocess.run(["cc", "-I", str(src), "-I", str(metal), "-x", "c", "-", "-o", exe],
                       input="\n".join(probe), text=True, check=True)
        lines = subprocess.check_output([exe], text=True).splitlines()
    layout = {key: int(value) for key, value in (line.split() for line in lines)}
    for suffix, content in [("h", declarations), ("json", json.dumps(layout, indent=2) + "\n")]:
        path = destination / f"{driver}.{suffix}"
        if check:
            if path.read_text() != content:
                raise SystemExit(f"ABI drift in {path}")
        else:
            path.write_text(content)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("drivers", type=Path)
    p.add_argument("metal_include", type=Path)
    p.add_argument("shim", type=Path)
    p.add_argument("--check", action="store_true")
    p.add_argument("--out", type=Path, default=ABI)
    args = p.parse_args()
    for driver in ("mix", "ccf", "equ", "prach", "ofdm"):
        generate(driver, args.drivers, args.metal_include, args.shim, args.out, args.check)
