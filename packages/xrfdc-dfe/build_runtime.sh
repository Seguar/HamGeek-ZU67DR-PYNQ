#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-3-Clause
set -euo pipefail
cd "$(dirname "$0")"
: "${RFDC_RUNTIME_ROOT:?Set RFDC_RUNTIME_ROOT to the native dependency tree}"
: "${EMBEDDEDSW_DIR:?Set EMBEDDEDSW_DIR to the embeddedsw checkout}"
release=xlnx_rel_v2025.2
commit=c3b3132f6e1e202e275b8dd77b3804f3b449528c
tag=xilinx_v2025.2
tag_commit=145cea8fcf98268c8b163f732c181f008e887e53
[[ $(uname -m) == aarch64 ]]
[[ $(git -C "$EMBEDDEDSW_DIR" rev-parse "$tag^{commit}") == "$tag_commit" ]]
src=XilinxProcessorIPLib/drivers/rfdc/src
libmetal=ThirdParty/sw_services/libmetal/src/libmetal
git -C "$EMBEDDEDSW_DIR" diff --exit-code "$tag" "$commit" -- "$src" "$libmetal"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
rf="$work/rfdc"
metal="$work/metal-install"
mkdir -p "$rf" "$work/metal-src" build
git -C "$EMBEDDEDSW_DIR" archive "$commit:$src" | tar -x -C "$rf"
git -C "$EMBEDDEDSW_DIR" archive "$commit:$libmetal" | tar -x -C "$work/metal-src"
sysfs=$(realpath "${SYSFS_SYSROOT:-$RFDC_RUNTIME_ROOT/sysroot}")
syslib="$sysfs/usr/lib/aarch64-linux-gnu/libsysfs.so.2"
cc="${CC:-cc}"
sources=("$rf"/xrfdc{,_ap,_clock,_dp,_intr,_mb,_mixer,_mts,_sinit}.c)
echo "$release $commit; $tag $tag_commit"
"$cc" --version | head -1
cmake -S "$work/metal-src" -B "$work/metal-build" -DCMAKE_INSTALL_PREFIX="$metal" \
    -DCMAKE_C_COMPILER="$cc" -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DCMAKE_C_FLAGS="-ffile-prefix-map=$work=. -ffile-prefix-map=$sysfs=sysroot" \
    -DWITH_TESTS=OFF -DWITH_DOC=OFF -DWITH_SHARED_LIB=OFF \
    -DLIBSYSFS_LIBRARY="$syslib" -DLIBSYSFS_INCLUDE_DIR="$sysfs/usr/include"
cmake --build "$work/metal-build" --parallel 4
cmake --install "$work/metal-build"
(
    cd "$work"
    find rfdc metal-src metal-install/include -type f -print0 | sort -z | xargs -0 sha256sum
    sha256sum metal-install/lib/libmetal.a
    cd "$sysfs"
    sha256sum usr/lib/aarch64-linux-gnu/libsysfs.so.2 usr/include/sysfs/*.h
) >build/native-inputs.sha256
python tools/cdef.py "$rf" "$metal/include" "$sysfs/usr/include"
"$cc" -O2 -fPIC -shared -DMETAL_INTERNAL -Werror=implicit-function-declaration \
    -I"$rf" -I"$metal/include" -I"$sysfs/usr/include" \
    -ffile-prefix-map="$work"=. -ffile-prefix-map="$sysfs"=sysroot \
    tools/mmio.c "${sources[@]}" "$metal/lib/libmetal.a" "$syslib" \
    -Wl,--exclude-libs,ALL,-z,defs -lm -pthread -o "$work/libxrfdc.so"
install -m755 "$work/libxrfdc.so" xrfdc/libxrfdc.so
sha256sum tools/{mmio.c,mmio.h,cdef.py} build_runtime.sh setup.py xrfdc/*.py xrfdc/xrfdc_functions.c >>build/native-inputs.sha256
sha256sum xrfdc/libxrfdc.so
