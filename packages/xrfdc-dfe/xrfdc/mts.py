# SPDX-License-Identifier: BSD-3-Clause
"""RFdc multi-tile synchronization using the v13 driver ABI."""

from operator import index


_ERRORS = {
    1: "NOT_SUPPORTED", 2: "TIMEOUT", 4: "MARKER_RUN", 8: "MARKER_MISM",
    16: "DELAY_OVER", 32: "TARGET_LOW", 64: "IP_NOT_READY", 128: "DTC_INVALID",
    512: "NOT_ENABLED", 2048: "SYSREF_GATE_ERROR", 4096: "SYSREF_FREQ_NDONE",
    8192: "BAD_REF_TILE",
}


def _check(operation, status):
    if status:
        errors = ["XRFDC_MTS_" + name for bit, name in _ERRORS.items() if status & bit]
        unknown = status & ~sum(_ERRORS)
        if unknown:
            errors.append(f"unknown bits {unknown:#x}")
        raise RuntimeError(f"{operation} returned {status:#x} ({', '.join(errors)})")


def _mask(tiles):
    """Integers are bitmasks. Iterables contain zero-based tile IDs."""
    if isinstance(tiles, int):
        if 0 <= tiles < 16:
            return tiles
        raise ValueError("tile mask must fit in four bits")
    mask = 0
    for tile in tiles:
        if index(tile) not in range(4):
            raise ValueError("tile ID must be in 0..3")
        mask |= 1 << tile
    return mask


class MTSMixin:
    """RFdc supplies _instance. Tests may inject _lib and _ffi on the instance."""

    def _mts_backend(self):
        if hasattr(self, "_lib") and hasattr(self, "_ffi"):
            return self._lib, self._ffi
        from . import _lib, _ffi
        return _lib, _ffi

    def _mts_sync(self, kind, tiles, target_latency):
        mask = _mask(tiles)
        if not mask:
            raise ValueError("select at least one tile")
        target = -1 if target_latency is None else index(target_latency)
        if not -1 <= target <= 0x7fffffff:
            raise ValueError("target latency must be -1 or a nonnegative C int")
        lib, ffi = self._mts_backend()
        cfg = ffi.new("XRFdc_MultiConverter_Sync_Config *")
        ref = (mask & -mask).bit_length() - 1
        _check("MultiConverter_Init", lib.XRFdc_MultiConverter_Init(cfg, ffi.NULL, ffi.NULL, ref))
        cfg.Tiles = mask
        cfg.Target_Latency = target
        _check("MultiConverter_Sync", lib.XRFdc_MultiConverter_Sync(self._instance, kind, cfg))
        per_tile = {
            tile: {"Latency": cfg.Latency[tile], "Offset": cfg.Offset[tile]}
            for tile in range(4) if mask & (1 << tile)
        }
        if kind == 0:
            self._mts_adc_tiles = mask
        else:
            self._mts_dac_tiles = mask
        return {"Latency": max(row["Latency"] for row in per_tile.values()), "tiles": per_tile}

    def mts_adc_sync(self, tiles, target_latency=None):
        return self._mts_sync(0, tiles, target_latency)

    def mts_dac_sync(self, tiles, target_latency=None):
        return self._mts_sync(1, tiles, target_latency)

    def mts_sysref_config(self, enable, dac_tiles=None, adc_tiles=None):
        """Gate SYSREF capture for explicit masks or the last synced tiles of each type."""
        if enable not in (True, False):
            raise ValueError("enable must be 0 or 1")
        lib, ffi = self._mts_backend()
        dac = ffi.new("XRFdc_MultiConverter_Sync_Config *")
        adc = ffi.new("XRFdc_MultiConverter_Sync_Config *")
        dac.Tiles = getattr(self, "_mts_dac_tiles", 0) if dac_tiles is None else _mask(dac_tiles)
        adc.Tiles = getattr(self, "_mts_adc_tiles", 0) if adc_tiles is None else _mask(adc_tiles)
        _check("MTS_Sysref_Config", lib.XRFdc_MTS_Sysref_Config(self._instance, dac, adc, int(enable)))

    def mts_sysref_enable(self, dac_tiles=None, adc_tiles=None):
        self.mts_sysref_config(True, dac_tiles, adc_tiles)

    def mts_sysref_disable(self, dac_tiles=None, adc_tiles=None):
        self.mts_sysref_config(False, dac_tiles, adc_tiles)

    def get_mts_enable(self, type, tile):
        if index(type) not in (0, 1) or index(tile) not in range(4):
            raise ValueError("expected ADC (0) or DAC (1) and tile ID 0..3")
        lib, ffi = self._mts_backend()
        enable = ffi.new("unsigned int *")
        status = lib.XRFdc_GetMTSEnable(self._instance, type, tile, enable)
        if status:
            raise RuntimeError(f"GetMTSEnable returned {status:#x}")
        return bool(enable[0])
