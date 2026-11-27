"""Importing this module registers the drivers with the PYNQ overlay loader."""
from pynq import DefaultIP

from .binding import Device, Mixer, ChannelFilter


class DfeIP(DefaultIP):
    bindto = []
    device_type = Device

    def __init__(self, description):
        super().__init__(description)
        self.dfe = self.device_type(self.driver, description)


class MixerIP(DfeIP):
    bindto = ["xilinx.com:ip:xdfe_cc_mixer:2.0"]
    driver, device_type = "mix", Mixer


class ChannelFilterIP(DfeIP):
    bindto = ["xilinx.com:ip:xdfe_cc_filter:1.1"]
    driver, device_type = "ccf", ChannelFilter


class EqualizerIP(DfeIP):
    bindto = ["xilinx.com:ip:xdfe_equalizer:1.0"]
    driver = "equ"


class PrachIP(DfeIP):
    bindto = ["xilinx.com:ip:xdfe_nr_prach:2.0"]
    driver = "prach"


class OfdmIP(DfeIP):
    bindto = ["xilinx.com:ip:xdfe_ofdm:2.2"]
    driver = "ofdm"
