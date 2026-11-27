# SPDX-License-Identifier: BSD-3-Clause
"""Translate PYNQ's system-wide ClkDistribution property to v13 domains."""
from itertools import groupby


def tile_order(rfdc):
    """Package distribution coordinates count downward from ADC tile 224."""
    for kind, tiles, config, edge in (
        (0, rfdc.adc_tiles, rfdc._config.ADCTile_Config, 7),
        (1, rfdc.dac_tiles, rfdc._config.DACTile_Config, 7 - len(rfdc.adc_tiles)),
    ):
        for index, tile in enumerate(tiles):
            yield edge - index, kind, index, tile, config[index].Enable


def legacy_read(rfdc, ffi, unpack):
    native = ffi.new("XRFdc_Distribution_System_Settings *")
    rfdc._call_function("GetClkDistribution", native)
    pll_zero = unpack(ffi.new("XRFdc_PLL_Settings *"))
    keys = ("MaxDelay", "MinDelay", "IsDelayBalanced", "UpperBound", "LowerBound")
    result = {"ADC": [], "DAC": [], "DistributionStatus": []}
    domains = [d for d in native.Distributions if d.SourceTileId != 255 and d.DistRefClkFreq]
    for domain in domains:
        info = domain.Info
        status = {key: getattr(info, key) for key in keys}
        result["DistributionStatus"].append(dict(status, Enabled=1, DistributionSource=info.Source))
    while len(result["DistributionStatus"]) < 8:
        result["DistributionStatus"].append(dict.fromkeys((*keys, "Enabled", "DistributionSource"), 0))
    for pos, kind, index, tile, enabled in tile_order(rfdc):
        entry = dict(SourceTile=pos, PLLEnable=0, PLLSettings=pll_zero.copy(),
                     DivisionFactor=0, Delay=0, DistributedClock=0)
        for d in domains:
            if enabled and d.Info.LowerBound <= pos <= d.Info.UpperBound:
                c = d.Info.ClkSettings[kind][index]
                entry.update(SourceTile=d.Info.Source, PLLEnable=c.PLLEnable,
                             PLLSettings=tile.PLLConfig, DivisionFactor=c.DivisionFactor,
                             Delay=c.Delay, DistributedClock=c.DistributedClock)
                break
        result[("ADC", "DAC")[kind]].append(entry)
    return result


def native_domains(rfdc, settings):
    tiles = {}
    for pos, kind, index, _, enabled in tile_order(rfdc):
        if enabled:
            entry = settings[("ADC", "DAC")[kind]][index]
            tiles[pos] = (kind, index, entry)
    domains = []
    for source, members in groupby(sorted(tiles), key=lambda pos: tiles[pos][2]["SourceTile"]):
        positions = list(members)
        if source not in positions or positions[-1] - positions[0] + 1 != len(positions):
            raise ValueError("Clock domain must span contiguous tiles including its source")
        src_kind, src_index, entry = tiles[source]
        rates = [[0.] * 4 for _ in range(2)]
        for pos in positions:
            kind, index, member = tiles[pos]
            rates[kind][index] = member["PLLSettings"]["SampleRate"]
        edges = [tiles[positions[0]], tiles[positions[-1]]]
        domains.append(dict(SourceType=src_kind, SourceTileId=src_index,
                            EdgeTypes=[e[0] for e in edges], EdgeTileIds=[e[1] for e in edges],
                            SampleRates=rates, DistRefClkFreq=entry["PLLSettings"]["RefClkFreq"],
                            DistributedClock=entry["DistributedClock"]))
    return domains
