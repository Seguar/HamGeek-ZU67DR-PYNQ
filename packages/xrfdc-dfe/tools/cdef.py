# SPDX-License-Identifier: BSD-3-Clause
"""Generate the Linux ABI declarations and compare every field to native C."""
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

from cffi import FFI

ROOT = Path(__file__).resolve().parents[1]
CDEF = ROOT / "xrfdc/xrfdc_functions.c"


def declarations(cc, rf):
    header = ROOT / "tools/mmio.h"
    source = subprocess.check_output([*cc, "-E", "-P", header], text=True)
    # Skip dependency declarations. Linux puts all RFDC structures in pack(1).
    start = source.index("typedef void (*XRFdc_StatusHandler)")
    types = source[start:]
    if types.count("#pragma pack(1)") != 1 or types.count("#pragma pack()") != 1:
        raise ValueError("RFDC packing changed")
    types = re.sub(r"^#pragma pack\(1?\)\n", "", types, flags=re.M)
    # Linux scalar types (the layout probe also checks these sizes).
    preamble = """/* Copyright (C) 2021 Xilinx, Inc. All rights reserved.
 * SPDX-License-Identifier: MIT
 * Generated from embeddedsw v2025.2, Linux ABI. Load with pack=1.
 */
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int32_t s32;
typedef int16_t s16;
typedef unsigned long long u64;
typedef long long s64;
typedef int8_t s8;
typedef unsigned long metal_phys_addr_t;
struct metal_io_region;
struct metal_device;
"""
    # Export integer literal constants from both xrfdc.h and xrfdc_hw.h.
    macros = subprocess.check_output([*cc, "-dM", "-E", rf / "xrfdc.h"], text=True)
    constants = re.findall(
        r"^#define (XRFDC_\w+) \(?(-?(?:0[xX][\da-fA-F]+|\d+))[uUlL]*\)?$",
        macros, re.M)
    return preamble + types + "".join(f"#define {k} {v}\n" for k, v in sorted(constants))


def check_layout(cc, declarations):
    ffi = FFI()
    ffi.cdef(declarations, pack=1)
    expected = {}
    structs = 0
    for name in ffi.list_types()[0]:
        ctype = ffi.typeof(name)
        expected[f"sizeof({name})"] = ffi.sizeof(name)
        expected[f"_Alignof({name})"] = ffi.alignof(name)
        if ctype.kind == "struct":
            structs += 1
            for field, _ in ctype.fields:
                expected[f"offsetof({name}, {field})"] = ffi.offsetof(name, field)
                expected[f"sizeof((({name}*)0)->{field})"] = ffi.sizeof(
                    dict(ctype.fields)[field].type)
    statements = [f'printf("%zu\\n", (size_t)({expr}));' for expr in expected]
    code = '#include <stddef.h>\n#include <stdio.h>\n#include "xrfdc.h"\nint main(void){\n'
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "layout"
        subprocess.run([*cc, "-x", "c", "-", "-o", exe], check=True,
                       text=True, input=code + "\n".join(statements) + "\n}")
        actual = subprocess.check_output([exe], text=True).splitlines()
    for (expr, want), value in zip(expected.items(), actual, strict=True):
        if int(value) != want:
            raise ValueError(f"{expr}: C={value}, cffi={want}")
    print(f"ABI verified: {structs} structures, {len(expected)} native comparisons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rfdc", type=Path)
    parser.add_argument("includes", type=Path, nargs="+")
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    compiler = [os.environ.get("CC", "cc"), "-I" + str(args.rfdc),
                *["-I" + str(path) for path in args.includes]]
    result = declarations(compiler, args.rfdc)
    if args.generate:
        CDEF.write_text(result)
    elif result != CDEF.read_text():
        raise SystemExit("cdef drift: regenerate with tools/cdef.py --generate and review")
    check_layout(compiler, CDEF.read_text())
