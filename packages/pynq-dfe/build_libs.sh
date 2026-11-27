#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src=$here/csrc
drivers=${EMBEDDEDSW_ROOT:?Set EMBEDDEDSW_ROOT to the 2025.2 checkout}/XilinxProcessorIPLib/drivers
runtime=${RFDC_RUNTIME_ROOT:?Set RFDC_RUNTIME_ROOT to the RFDC dependency tree}
sysfs=${SYSFS_SYSROOT:-$runtime/sysroot}
out=${DFE_LIB_DIR:-$here/build}
mkdir -p "$out"
out=$(cd "$out" && pwd)
(cd "$drivers" && sha256sum -c "$src/embeddedsw.sha256")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
metal=$tmp/metal-install
sysfs_a=$sysfs/usr/lib/aarch64-linux-gnu/libsysfs.a
printf '%s  %s\n' 8ee9a9e970f52fe587dc7753b036c594024dfe04d17b138e1533dc4fac3f2008 "$sysfs_a" | sha256sum -c -
# Same Linux libmetal sources as the RFDC runtime, rebuilt as PIC.
commit=c3b3132f6e1e202e275b8dd77b3804f3b449528c
git -C "$EMBEDDEDSW_ROOT" archive --mtime=2000-01-01T00:00:00Z \
    "$commit:ThirdParty/sw_services/libmetal/src/libmetal" > "$tmp/metal.tar"
(cd "$tmp" && echo '293daa64e9b144a67ff2120fbdb206de68aa88a20d2dfe519d22d3e95451acd1  metal.tar' | sha256sum -c -)
mkdir "$tmp/source"
tar xf "$tmp/metal.tar" -C "$tmp/source"
cmake -S "$tmp/source" -B "$tmp/build" -DCMAKE_INSTALL_PREFIX="$metal" \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_C_FLAGS="-ffile-prefix-map=$tmp=libmetal" \
    -DWITH_SHARED_LIB=OFF -DWITH_STATIC_LIB=ON -DWITH_DOC=OFF -DWITH_TESTS=OFF \
    -DLIBSYSFS_INCLUDE_DIR="$sysfs/usr/include" -DLIBSYSFS_LIBRARY="$sysfs_a"
cmake --build "$tmp/build" --parallel 4
cmake --install "$tmp/build"
metal_a=$metal/lib/libmetal.a
sha256sum "$metal_a"
"${CC:-gcc}" -shared -fPIC "$src/tests/devmem_fixture.c" -o "$tmp/fixture.so"
truncate -s $((0x100000014 + 65536)) "$tmp/registers"
includes=()
for driver in mix ccf equ prach ofdm; do
    includes+=(-I"$drivers/dfe$driver/src")
done
for driver in mix ccf equ prach ofdm; do
    name=libxdfe$driver.so
    dir=$drivers/dfe$driver/src
    flags=(-O2 -fPIC "-ffile-prefix-map=$drivers=drivers" "-ffile-prefix-map=$here=pynq-dfe"
        "-ffile-prefix-map=$metal=metal" -I"$metal/include" -I"$sysfs/usr/include" "${includes[@]}")
    "${CC:-gcc}" "${flags[@]}" -shared "-Wl,-soname,$name,-Bsymbolic,-z,defs,-z,text" \
        "$dir"/*.c "$src/${driver}_shim.c" -Wl,-u,metal_init,-u,metal_finish "$metal_a" "$sysfs_a" -lm -pthread -o "$tmp/$name"
    "${CC:-gcc}" "${flags[@]}" -DTEST_${driver^^} -DTYPE=XDfe${driver^} -DPREFIX=XDFE${driver^^} \
        -DOPEN=xdfe_${driver}_mmio_open -DOPEN_BUFFER=xdfe_${driver}_mmio_open_buffer -DCLOSE=xdfe_${driver}_mmio_close \
        -DHEADER="\"xdfe$driver.h\"" -DHW_HEADER="\"xdfe${driver}_hw.h\"" \
        "$src/tests/test_mmio.c" -L"$tmp" -lxdfe"$driver" -Wl,-rpath,'$ORIGIN' -o "$tmp/test"
    LD_PRELOAD="$tmp/fixture.so" DFE_TEST_FILE="$tmp/registers" "$tmp/test"
done
install -m 755 "$tmp"/libxdfe*.so "$out/"
(cd "$out" && sha256sum libxdfe{mix,ccf,equ,prach,ofdm}.so)
