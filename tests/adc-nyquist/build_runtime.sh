#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-3-Clause
set -euo pipefail

if [[ $# != 1 ]]; then
    echo "Usage: $0 HWH" >&2
    exit 2
fi

here=$(cd "$(dirname "$0")" && pwd)
runtime=${RFDC_RUNTIME_ROOT:?Set RFDC_RUNTIME_ROOT to the RFDC dependency tree}
rf="$runtime/upstream/XilinxProcessorIPLib/drivers/rfdc_v13_0/src"
metal="$runtime/metal-install"
sysfs=${SYSFS_SYSROOT:-"$runtime/sysroot"}
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT

python3 "$here/adc_rfdc_config.py" "$1" "$build/adc_rfdc_config.h"
# Direct MMIO attaches a metal_io_region, so omit the UIO discovery/config table.
"${CC:-gcc}" -O2 -ffile-prefix-map="$runtime"=. -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra \
    -I"$build" -I"$metal/include" -I"$rf" -I"$sysfs/usr/include" \
    "$here/adc_nyquist.c" "$rf"/xrfdc{,_ap,_clock,_dp,_intr,_mb,_mixer,_mts}.c \
    "$metal/lib/libmetal.a" "$sysfs/usr/lib/aarch64-linux-gnu/libsysfs.a" \
    -lm -pthread -o "$build/adc-nyquist"

cd "$here"
install -m 755 "$build/adc-nyquist" adc-nyquist
sha256sum adc-nyquist > adc-nyquist.sha256
