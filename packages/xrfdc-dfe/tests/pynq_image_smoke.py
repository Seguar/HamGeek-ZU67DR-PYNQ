# SPDX-License-Identifier: BSD-3-Clause
"""Run against the installed wheel and the image's PYNQ 4.0.0 packages."""
import sys
from importlib.metadata import version

import numpy as np
from pynq.overlay import _assign_drivers
from pynq.pl_server.hwh_parser import HWH

import xrfdc


class MemoryDevice:
    def has_capability(self, name):
        return name == "MEMORY_MAPPED"

    def mmap(self, address, length):
        return np.zeros(length // 4, dtype="u4")


if __name__ == "__main__":
    parsed = HWH(sys.argv[1])
    ip = next(ip for ip in parsed.ip_dict.values() if ":usp_rf_data_converter:" in ip["type"])
    _assign_drivers({"hierarchies": {}, "ip": {"rfdc": ip}}, False, MemoryDevice())
    assert ip["driver"] is xrfdc.RFdc
    rfdc = ip["driver"](ip)
    assert [len(tile.blocks) for tile in rfdc.adc_tiles] == [4, 4, 2]
    assert [len(tile.blocks) for tile in rfdc.dac_tiles] == [4, 4]
    assert rfdc.adc_tiles[0].GetMaxSampleRate() == 2950
    assert rfdc.dac_tiles[0].GetMaxSampleRate() == 10000
    rfdc.mmio.write(xrfdc._lib.XRFDC_TILES_ENABLED_OFFSET, 0x37)
    assert rfdc.get_mts_enable(0, 0) is False
    print("Python", sys.version.split()[0], "PYNQ", version("pynq"), "cffi", version("cffi"))
    print("Installed package:", xrfdc.__file__)
    print(ip["type"], "bound to RFdc; RowTiming r5 ADC [4,4,2], DAC [4,4]; MTS read OK")
