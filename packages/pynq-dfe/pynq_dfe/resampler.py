"""Static configuration for the stream-only PG392 core."""
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree

from pynq import DefaultIP


class ResamplerIP(DefaultIP):
    bindto = ["xilinx.com:ip:xdfe_resampler:1.0"]

    def __init__(self, description):
        # No address segment exists. DefaultIP.__init__ would create an MMIO map.
        self.description = description
        parameters = description["parameters"]
        # The HWH stores the numeric enumeration from component.xml.
        ratios = ("2/3", "3/4", "4/5", "5/6", "3/2", "2", "5/2",
                  "3", "7/2", "4", "5", "7")
        rate_code = int(parameters["RATE_CHANGE"])
        if not 0 <= rate_code < len(ratios):
            raise ValueError(f"unknown PG392 rate code {rate_code}")
        self.ratio = Fraction(ratios[rate_code])
        self.input_lanes = int(parameters["INPUT_SAMPLES_PER_CYCLE"])
        self.output_lanes = int(parameters["OUTPUT_SAMPLES_PER_CYCLE"])

    @classmethod
    def from_hwh(cls, filename, instance):
        """Stream-only modules can be absent from Overlay.ip_dict."""
        for module in ElementTree.parse(Path(filename)).iter("MODULE"):
            if (module.get("FULLNAME") == "/" + instance.strip("/")
                    and module.get("VLNV") in cls.bindto):
                params = {p.get("NAME"): p.get("VALUE")
                          for p in module.findall("PARAMETERS/PARAMETER")}
                return cls({"fullpath": instance, "parameters": params})
        raise KeyError(instance)
