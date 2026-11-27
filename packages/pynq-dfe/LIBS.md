# RFSoC DFE Linux libraries

Each AArch64 shared object contains the complete 2025.2 Linux driver (core,
interrupt and discovery sources), a direct MMIO adapter, Linux libmetal and
libsysfs. All five build with the upstream driver sources unchanged.

## Native build and test

Use AArch64 Ubuntu 24.04, GCC 13.3, CMake, make and Git 2.43. Set
`EMBEDDEDSW_ROOT` to an embeddedsw checkout at
`c3b3132f6e1e202e275b8dd77b3804f3b449528c` on the AMD release branch
`xlnx_rel_v2025.2`. The sparse checkout needs the five driver directories
and access to the pinned libmetal Git objects. The build verifies the SHA-256
of each driver source, header, Tcl and YAML input against
[csrc/embeddedsw.sha256](csrc/embeddedsw.sha256).

Set `RFDC_RUNTIME_ROOT` as in the ADC Nyquist runtime. This build uses its
`sysroot/usr` sysfs headers and static archive. To recreate that sysroot on
arm64, download Ubuntu Noble's `libsysfs-dev=2.1.1-6build1`, verify the
package SHA-256 below, and extract it with `dpkg-deb -x` into the sysroot.
`SYSFS_SYSROOT` overrides that location. Run:

```sh
./build_libs.sh
export PYNQ_DFE_LIBDIR="$PWD/build"
```

`DFE_LIB_DIR` overrides the output directory. Each build runs C tests on
anonymous memory, checks Ready → Reset → Configured, reads an injected version
and verifies reset writes. A test-only interposer redirects the physical open
to a sparse file and checks address translation and persisted writes at
`0x100000014`. The tests execute locally without accessing hardware.

| Static input | SHA-256 |
|---|---|
| libmetal 1.5.0 source tar (same commit, Git tree e24d0b213ba92375769781a481a0016dd14e2ce4, timestamp normalized by the script) | `293daa64e9b144a67ff2120fbdb206de68aa88a20d2dfe519d22d3e95451acd1` |
| libmetal.a, rebuilt with PIC | `a4efb12d67c1b353797d01bd212149067de89815a04eaed7c22368f764aa3bcc` |
| Ubuntu libsysfs-dev arm64 package | `e3e2168253a7e593497360692c6c0116f51b7d6f4a601540399d8a7668222c9f` |
| libsysfs.a | `8ee9a9e970f52fe587dc7753b036c594024dfe04d17b138e1533dc4fac3f2008` |

## Direct MMIO

[csrc/xdfe_mmio_shim.h](csrc/xdfe_mmio_shim.h) declares the five pairs of
`xdfe_<driver>_mmio_open(name, phys_base, size)` and
`xdfe_<driver>_mmio_close(instance)`. Pass the programmed IP's HWH instance
name, word-aligned physical base and complete byte range. The caller needs
permission to map this range via Linux /dev/mem. Open returns NULL with errno
on argument, mapping or allocation errors. Each successful open owns its
mapping. Serialize access to a physical core and pair each open with its
matching close. The stock InstanceClose API belongs to the discovery path.

The adapter attaches region zero, sets BaseAddr, NodeName and STATE_READY,
and reads Mix, CCF, Equ and PRACH configuration from their model registers.
OFDM's Linux LookupConfig fills BaseAddr alone. Configure reads the OFDM
model. Opening PRACH also clears the 16 NCO phase offsets, matching the
vendor's InstanceInit. Call Reset and then Configure before Initialize.

All five IPs require a PS-accessible AXI4-Lite slave, its running control
clock and released bus reset before open. Use the actual clock frequency and
clock/reset association in the Vivado design. The drivers take no control
clock frequency argument. Direct register reads, writes and polling require
no CPU interrupt. For interrupt delivery route the enabled core interrupt
to the PS interrupt controller and describe it in the overlay device tree.
The direct adapter provides register access only. Stream clocks, resets
and any data-path enables must also be active for signal processing.

| Driver | First compatible string | Minimum range accepted by shim | Model parameters (Vivado C_ prefix) |
|---|---|---:|---|
| mix | xlnx,xdfe-cc-mixer-2.0 | 0x5000 | MODE, NUM_ANTENNA, MAX_USEABLE_CCIDS, LANES, ANTENNA_INTERLEAVE, MIXER_CPS, NUM_AUXILIARY, DATA_IWIDTH, DATA_OWIDTH, TUSER_WIDTH |
| ccf | xlnx,xdfe-cc-filter-1.1 | 0x4000 | NUM_ANTENNA, NUM_CC_PER_ANTENNA, ANTENNA_INTERLEAVE, SWITCHABLE |
| equ | xlnx,xdfe-equalizer-1.0 | 0x4000 | NUM_CHANNELS, DATA_IWIDTH (SampleWidth), COMPLEX_MODE, TUSER_WIDTH. Legacy Tcl also exports DATA_OWIDTH. |
| prach | xlnx,xdfe-nr-prach-2.0 | 0x4000 | NUM_ANTENNA, NUM_CC_PER_ANTENNA, NUM_SLOT_CHANNELS and NUM_SLOTS with suffixes 0, 1, 2. NUM_RACH_LANES, NUM_RACH_CHANNELS, HAS_AXIS_CTRL, HAS_IRQ, NUM_BANDS, IS_ALWAYS_ON (HasContinuousSched). |
| ofdm | xlnx,xdfe-ofdm-2.2 or xlnx,xdfe-ofdm-2.1 | 0x4000 | FREQUENCY_RANGE_INT, NUM_ANTENNA, ANTENNA_INTERLEAVE, PHASE_COMPENSATION (YAML model fields). Legacy Tcl exports only the device ID and base. |

Mix's legacy address parameter is C_S_AXI_BASEADDR. The remaining drivers
use C_BASEADDR. The four 0x4000 checks follow the upstream region constant.
The mixer's NCO banks start at 0x4000 and advance by 0x40, so a 0x4000
mapping would omit them. An aligned Vivado power-of-two mixer window can
use 0x8000 or larger.

## Stock platform/UIO discovery

Bind a Linux platform node to uio_pdrv_genirq (generic-uio matching enabled),
with the driver-compatible string first, followed by "generic-uio". Supply
the real address and size in reg using the parent bus's cells. Populate
interrupts and interrupt-parent when wired. Initialize libmetal through the
same shared library handle, then pass the platform device basename from
/sys/bus/platform/devices to XDfe<Drv>_InstanceInit. Region zero must be the
control registers. Use InstanceClose and metal_finish on this path. Each shared
object binds its internal references locally and carries its own metal state.

Use 32-bit big-endian DT cells under xlnx, with lowercase hyphenated model
names from the table. Account for these differences between Linux LookupConfig
and the Tcl/YAML generator:

- Mix reads xlnx,mode as a string (downlink, uplink or switchable). YAML lists modeint.
- CCF reads xlnx,switchable as a string (true or false). YAML lists switchable-int.
- Equ reads xlnx,data-iwidth for SampleWidth. YAML lists sample-width.
- PRACH Linux reads each of the twelve band-suffixed properties, even for inactive bands, plus the six scalar properties in the table.
- OFDM Linux reads only reg during discovery and uses Configure for the model.
- Mix, CCF, Equ and PRACH apply ntohl to an eight-byte reg read. On little-endian Linux their stored BaseAddr therefore reflects the first 32-bit address cell. OFDM converts the full 64 bits. The direct adapter preserves the supplied 64-bit address.

## Verified exports and binaries

Each library exports the vendor XDfe<Drv> API, including InstanceInit,
InstanceClose, Reset, Configure, GetVersions, register accessors and interrupt
functions. It also exports the two public MMIO functions and the test-only
open_buffer declared in [csrc/tests/xdfe_buffer.h](csrc/tests/xdfe_buffer.h).
Inspect the complete dynamic symbol table with `nm -D --defined-only`.
The AArch64 binaries have dynamic dependencies on glibc and its loader. The
OFDM library also needs libm.

| Shared object | Vendor XDfe text symbols | SHA-256 |
|---|---:|---|
| libxdfemix.so | 49 | `76d516a77bec1367acc117225760e7245866815f95aa916bea41cb60871fcd54` |
| libxdfeccf.so | 49 | `596917027b2d082012a83f4a293b936754cf1a3a964a8856d3b72296a25efd2e` |
| libxdfeequ.so | 30 | `159b667b46d80a68920b38523c10f7771eb75f35c644f8d359400c1e6f60fc13` |
| libxdfeprach.so | 65 | `8ff76559b91bc04114ce78bfc85c83d724ad75144162b8867d082d086460dfad` |
| libxdfeofdm.so | 43 | `390b6452615e0b00ed8b67d5faa95a7f0b140f8cf840b9f16818ff334ad0ad64` |
