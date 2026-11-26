"""Offline bundle checks and startup guards for the corrected RFDC overlays."""
from hashlib import file_digest
from pathlib import Path
import subprocess
from time import monotonic
from xml.etree import ElementTree as ET


def progress(message):
    print(message, flush=True)


def verify_bundle(bitfile):
    """Reject stale helpers and handoffs before programming the PL."""
    bitfile = Path(bitfile).resolve()
    hwh = bitfile.with_suffix(".hwh")
    if bitfile.with_suffix(".xsa").exists() or bitfile.with_suffix(".xclbin").exists():
        raise RuntimeError("Load from the PYNQ bundle directory containing the matched bit and HWH")
    manifest = bitfile.with_name("artifacts.sha256")
    hashes = {name: digest for digest, name in
              (line.split(maxsplit=1) for line in manifest.read_text().splitlines())}
    for artifact in (bitfile, hwh, bitfile.with_name("synchronize-rfdc")):
        with artifact.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        if hashes.get(artifact.name) != digest:
            raise RuntimeError(f"{artifact.name} does not match {manifest}")
    root = ET.parse(hwh)
    rfdc = root.find(".//MODULE[@INSTANCE='rfdc']")
    def signal(instance, port):
        pin = root.find(f".//MODULE[@INSTANCE='{instance}']/PORTS/PORT[@NAME='{port}']")
        return pin.get("SIGNAME") if pin is not None else None

    ps = "zynq_ultra_ps_e_0"
    ps_clk = signal(ps, "pl_clk0")
    ps_rst = signal(ps, "pl_resetn0")
    if rfdc is None or not ps_clk or not ps_rst:
        raise RuntimeError("HWH does not identify RFDC and PS host clock/reset")
    buses = ("ctrl", "mem") if root.find(".//MODULE[@INSTANCE='ctrl']") is not None else ("axi_lite", "axi_mem")
    clocks_and_resets = {
        "host_firewall": ("aclk", "aresetn"),
        **{bus: ("aclk", "aresetn") for bus in buses},
        "rfdc": ("s_axi_aclk", "s_axi_aresetn"),
        "rowtiming": ("host_clk", "host_resetn"),
        "dma": ("s_axi_lite_aclk", "axi_resetn"),
    }
    modules = {module.get("INSTANCE"): module for module in root.findall("MODULES/MODULE")}
    constants = {}
    for instance, module in modules.items():
        value = module.find("PARAMETERS/PARAMETER[@NAME='CONST_VAL']")
        if module.get("MODTYPE") == "xlconstant" and value is not None:
            constants[signal(instance, "dout")] = int(value.get("VALUE"), 0)
    host_reset = modules.get("host_reset")
    if host_reset is None:
        raise RuntimeError("HWH lacks the PS host reset synchronizer")
    polarity = {p.get("NAME"): p.get("VALUE") for p in host_reset.findall("PARAMETERS/PARAMETER")}
    if (polarity.get("C_EXT_RESET_HIGH"), polarity.get("C_AUX_RESET_HIGH")) != ("0", "1"):
        raise RuntimeError("Host reset must use an active-low PS reset and active-high auxiliary reset")
    if (signal("host_reset", "slowest_sync_clk"), signal("host_reset", "ext_reset_in")) != (ps_clk, ps_rst):
        raise RuntimeError("Host reset must be derived from PS pl_clk0 and pl_resetn0")
    for port, value in (("dcm_locked", 1), ("aux_reset_in", 0), ("mb_debug_sys_rst", 0)):
        if constants.get(signal("host_reset", port)) != value:
            raise RuntimeError(f"Host reset {port} must be tied to {value}")
    host_rst = signal("host_reset", "peripheral_aresetn")
    if not host_rst:
        raise RuntimeError("HWH lacks the synchronized host reset net")
    for instance, (clock, reset) in clocks_and_resets.items():
        if (signal(instance, clock), signal(instance, reset)) != (ps_clk, host_rst):
            raise RuntimeError(f"{instance} must use PS pl_clk0 and the PS host reset")
    if any(signal(ps, port) != ps_clk for port in ("maxihpm0_lpd_aclk", "saxihp0_fpd_aclk")):
        raise RuntimeError("HWH has a PS AXI port clock outside the host domain")
    dma_clocks = ["m_axi_s2mm_aclk"]
    if buses[0] == "axi_lite":
        dma_clocks.append("m_axi_mm2s_aclk")
    for clock in dma_clocks:
        if signal("dma", clock) != ps_clk:
            raise RuntimeError(f"dma/{clock} must use PS pl_clk0")
    values = {p.get("NAME"): p.get("VALUE") for p in rfdc.findall("PARAMETERS/PARAMETER")}
    expected = {"ADC0_Clock_Source": "2", "ADC1_Clock_Source": "2",
                "ADC2_Clock_Dist": "2", "ADC2_PLL_Enable": "true",
                "ADC0_Multi_Tile_Sync": "true", "ADC1_Multi_Tile_Sync": "true"}
    for key, value in expected.items():
        if values.get(key) != value:
            raise RuntimeError(f"HWH {key}={values.get(key)}, expected {value}")
    return float(values["ADC0_Sampling_Rate"]), float(values["ADC0_Fabric_Freq"])


def check_rfdc(folder):
    progress("Check RFDC startup and PLL status through the PS-clocked control aperture")
    subprocess.run([str(folder / "synchronize-rfdc"), "--check-clocks"],
                   timeout=6, check=True)


def check_fabric(rt, want_fabric, want_sysref=None):
    """Use the Gray counters synchronized into PS pl_clk0, with a bounded wait."""
    progress("Check MMCM lock and fabric/SYSREF counters on PS pl_clk0")
    deadline = monotonic() + 2.0
    while True:
        clocks = rt.frequencies(interval=0.1)
        streams = rt.rd("RFDC_STREAM_STATUS")
        if (rt.status()["mmcm_locked"] and streams & 0x3 == 0x3 and
                abs(clocks["fabric_mhz"] / want_fabric - 1) <= 0.02 and
                (want_sysref is None or abs(clocks["sysref_mhz"] / want_sysref - 1) <= 0.02)):
            progress(f"Fabric/SYSREF clock measurements {clocks}, RFDC stream status {streams:#x}")
            return clocks
        if monotonic() >= deadline:
            raise RuntimeError(f"Fabric/SYSREF or ADC stream check failed: {clocks}, status {streams:#x}")
