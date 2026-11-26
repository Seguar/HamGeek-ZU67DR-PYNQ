# SPDX-License-Identifier: BSD-3-Clause
"""ADC capture-control register offsets within the AXI-Lite window.

Must match hdl/rt_core.v. Base addresses come from the HWH (see rt250_driver).
"""

REG = {
    "ID": 0x000,            # 0x52543235 "RT25"
    "BUILD": 0x004,         # [7:0] GTY Gb/s, [15:8] GTY word bits, [23:16] version
    "CTRL": 0x008,          # [0] MMCM reset [1] GTY reset [2] core reset
    "STATUS": 0x00C,
    "ARM": 0x010,           # write: arm a run (starts on next PL SYSREF edge + START_DELAY)
    "STOP": 0x014,          # write: stop sequencers and capture
    "START_DELAY": 0x018,   # 312.5 MHz cycles after the SYSREF edge
    "DAC_ENABLE": 0x01C,
    "GTY_ENABLE": 0x020,
    "GTY_IDLE": 0x024,      # idle level per lane
    "LOOP": 0x028,          # [7:0] DAC table loop, [15:8] GTY table loop
    "ADC_DELAY": 0x02C,     # capture start, 312.5 MHz cycles after the start pulse
    "CAP_WORDS": 0x030,     # capture length in 8-sample words
    "SYSREF_COUNT": 0x034,
    "CLK_COUNT": 0x038,     # free-running 312.5 MHz cycle count
    "RUN_COUNT": 0x03C,
    "LOAD_TARGET": 0x040,   # [1:0] 0 DAC seg, 1 DAC table, 2 GTY seg, 3 GTY table; [15:8] channel mask
    "LOAD_ADDR": 0x044,     # write: first memory entry; resets LOAD_ROWS
    "LOAD_ROWS": 0x048,
    "FAULT": 0x04C,         # [7:0] DAC underrun [15:8] GTY underrun [16] ADC tvalid drop [17] DAC tready drop [18] GTY not ready at start
    "RB_CHANNEL": 0x050,
    "RB_ADDR": 0x054,
    "RB_WORDS": 0x058,
    "RB_START": 0x05C,
    "CLEAR_FAULT": 0x060,
    "LOAD_LIMIT": 0x068,    # entries to write after LOAD_ADDR (padding in the last beat is dropped)
    "RFDC_STREAM_STATUS": 0x06C,  # ADC0/1 all TVALID [1:0], DAC0/1 all TREADY [3:2]
    "GEOMETRY": 0x064,      # [7:0] DAC addr bits [15:8] GTY addr bits [23:16] table addr bits [31:24] capture addr bits
}
for _i in range(8):
    REG[f"DAC_N{_i}"] = 0x080 + 4 * _i
    REG[f"GTY_N{_i}"] = 0x0A0 + 4 * _i

STATUS_BITS = {
    "mmcm_locked": 0, "gty_tx_done": 1, "phase_stable": 2, "armed": 5, "running": 6,
    "run_done": 7, "capturing": 8, "cap_done": 9, "load_idle": 10, "rb_active": 11,
    "dac_ready": 12, "gty_bypass_done": 14, "gty_bypass_error": 15,
}
ID_VALUE = 0x52543235
