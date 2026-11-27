"""Vivado HWH parameters from the driver data/*.tcl and SDT schemas."""
FIELDS = {
    "mix": dict(Mode="MODE", NumAntenna="NUM_ANTENNA", MaxUseableCcids="MAX_USEABLE_CCIDS",
                Lanes="LANES", AntennaInterleave="ANTENNA_INTERLEAVE", MixerCps="MIXER_CPS",
                NumAuxiliary="NUM_AUXILIARY", DataIWidth="DATA_IWIDTH", DataOWidth="DATA_OWIDTH",
                TUserWidth="TUSER_WIDTH"),
    "ccf": dict(NumAntenna="NUM_ANTENNA", NumCCPerAntenna="NUM_CC_PER_ANTENNA",
                AntennaInterleave="ANTENNA_INTERLEAVE", Switchable="SWITCHABLE"),
    "equ": dict(NumChannels="NUM_CHANNELS", SampleWidth="SAMPLE_WIDTH",
                ComplexModel="COMPLEX_MODE", TuserWidth="TUSER_WIDTH"),
    "prach": dict(NumAntenna="NUM_ANTENNA{}", NumCCPerAntenna="NUM_CC_PER_ANTENNA{}",
                  NumAntennaChannels="NUM_SLOT_CHANNELS{}", NumAntennaSlots="NUM_SLOTS{}",
                  NumRachLanes="NUM_RACH_LANES", NumRachChannels="NUM_RACH_CHANNELS",
                  HasAxisCtrl="HAS_AXIS_CTRL", HasIrq="HAS_IRQ", NumBands="NUM_BANDS",
                  HasContinuousSched="IS_ALWAYS_ON"),
    "ofdm": dict(FrequencyRange="FREQUENCY_RANGE", NumAntenna="NUM_ANTENNA",
                 AntennaInterleave="ANTENNA_INTERLEAVE", PhaseCompensation="PHASE_COMPENSATION"),
}


def number(value):
    if isinstance(value, str):
        word = value.strip().lower()
        if word in ("true", "enabled"):
            return 1
        if word in ("false", "disabled"):
            return 0
        return int(word, 0)
    return int(value)


def config_fields(driver, params):
    """Return available HWH fields. Hardware supplies any absent fields at Configure."""
    result = {}
    params = {k.upper().removeprefix("CONFIG."): v for k, v in params.items()}
    for field, suffix in FIELDS[driver].items():
        for i in (range(3) if "{}" in suffix else (None,)):
            key = "C_" + suffix.format(i)
            if key not in params:
                key = suffix.format(i)
            if key not in params and driver == "ccf" and field == "NumCCPerAntenna":
                key = "MAX_USEABLE_CCIDS"
            if key not in params and driver == "prach":
                aliases = {"NumCCPerAntenna": f"MAX_USEABLE_CCIDS{i}",
                           "NumRachLanes": "NUM_RACH_OUTPUT_LANES"}
                key = aliases.get(field, key)
            if key not in params:
                continue
            value = params[key]
            enums = {"Mode": {"downlink": 0, "uplink": 1, "switchable": 2},
                     "FrequencyRange": {"fr1": 0, "fr2": 1}}
            value = enums.get(field, {}).get(str(value).lower(), value)
            result[field, i] = number(value)
    return result
