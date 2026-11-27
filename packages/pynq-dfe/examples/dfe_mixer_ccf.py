"""DAC0/J44 to ADC0/J36 loopback using the hard uplink mixer and FIR."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from time import monotonic, sleep
from xml.etree import ElementTree

import numpy as np
from pynq import Overlay, allocate
import xrfdc
from pynq_dfe import lowpass_taps
from lmk_spi import configured_clock


FS = 312_500_000
N = 1024
TONES = ((78.125,), (39.0625,), (117.1875,), (39.0625, 117.1875))
BASES = dict(rfdc=0x82000000, control=0x84000000, dma=0x84010000,
             mixer=0x84040000, ccf=0x84080000)


def verify_pair(bit, manifest):
    hashes = {name: digest for digest, name in
              (line.split() for line in Path(manifest).read_text().splitlines() if line.strip())}
    for path in (bit, bit.with_suffix(".hwh")):
        if sha256(path.read_bytes()).hexdigest() != hashes[path.name]:
            raise ValueError(f"SHA-256 mismatch for {path.name}")


def wait_until(predicate, description, timeout=2):
    deadline = monotonic() + timeout
    while not predicate():
        if monotonic() >= deadline:
            raise TimeoutError(description)
        sleep(0.001)


class MixerCCFOverlay(Overlay):
    @classmethod
    @contextmanager
    def open(cls, bitfile, manifest):
        bit = Path(bitfile).resolve()
        verify_pair(bit, manifest)
        hwh = ElementTree.parse(bit.with_suffix(".hwh"))
        rf_params = {p.get("NAME"): p.get("VALUE") for p in
                     hwh.findall(".//MODULE[@INSTANCE='rfdc']/PARAMETERS/PARAMETER")}
        required = {"DAC_VOP_Mode": "0", "DAC_Output_Current": "0",
                    "DAC_VOP_RTS": "false", "ADC_Decimation_Mode00": "8"}
        if any(rf_params.get(k) != v for k, v in required.items()):
            raise ValueError("Expected the fixed 20 mA, decimate-by-eight overlay")
        ol = cls(str(bit), download=False)
        ol.aligned = hwh.find(".//MODULE[@INSTANCE='capture']/PORTS/PORT[@NAME='mix_tuser']") is not None
        for name, address in BASES.items():
            span = 0x10000 if name in ("control", "dma") else 0x40000
            item = ol.ip_dict[name]
            if (item["phys_addr"], item["addr_range"]) != (address, span):
                raise ValueError(f"Unexpected {name} register aperture")
        profile = Path(__file__).with_name("lmk04828_vco3000.txt")
        words = [int(line, 16) for line in profile.read_text().splitlines()]
        with configured_clock(words):
            ol.download()
            ol.shadow = 0
            ol.control.write(0, 0)
            try:
                ol.prepare()
                yield ol
            finally:
                try:
                    ol.stop_tone()
                finally:
                    for block in ("mix_handle", "fir_handle"):
                        if block in vars(ol):
                            getattr(ol, block).close()

    def prepare(self):
        self.selectable = int(self.ip_dict["control"]["parameters"]["C_GPIO_WIDTH"]) == 5
        self.stop_tone()
        rf = self.rfdc
        if not isinstance(rf, xrfdc.RFdc) or rf.GetTileLayout() != 1:
            raise RuntimeError("Requires DFE xrfdc and the compact tile layout")
        def tile_states():
            status = rf.IPStatus
            return [v["TileState"] for kind, count in (("ADC", 3), ("DAC", 2))
                    for v in status[kind+"TileStatus"][:count]]

        wait_until(lambda: tile_states() == [15]*5, "initial RFDC tile startup", 20)
        rf.adc_tiles[0].StartUp()
        tiles = rf.adc_tiles + rf.dac_tiles
        states = tile_states()
        self.current_ua = [block.OutputCurr for tile in rf.dac_tiles for block in tile.blocks]
        if (states != [15]*5 or any(t.PLLLockStatus != 2 for t in tiles)
                or any(abs(i - 20000) > 43.75 for i in self.current_ua)):
            raise RuntimeError(f"RFDC startup/current check failed: {states}, {self.current_ua}")

        self.mix_handle = self.mixer.dfe
        self.fir_handle = self.ccf.dfe
        for dev, offset, version in ((self.mix_handle, 0x10, (2, 0)),
                                     (self.fir_handle, 0x20, (1, 1))):
            if dev.versions()[1][:2] != version:
                raise RuntimeError(f"Unexpected {dev.driver} hardware version: {dev.versions()}")
            dev.reset()
            dev.configure()
            dev.initialize(Sequence={"Length": 1})
            triggers = dev.new("TriggerCfg")  # All-zero mode selects an immediate trigger.
            if self.aligned and dev.driver == "mix":
                for trigger in (triggers.Activate, triggers.CCUpdate):
                    trigger.Mode = 1  # One-shot on the rising edge of TUSER[0].
                    trigger.TuserEdgeLevel = 3
            dev.set_triggers(triggers)
            dev.activate()
            wait_until(lambda: dev.call("ReadReg", offset) & 1, f"{dev.driver} activation")
        self.taps = lowpass_taps(16, 25e6, FS)
        fir = self.fir_handle
        fir.load_coefficients(1, 8, self.taps)  # PG395: preserve the Q1.15 binary point.
        carrier = fir.new("CarrierCfg", dict(RealCoeffSet=1, ImagCoeffSet=1))
        cfg = fir.empty_cc_config()
        fir.add_cc_to_config(cfg, 0, 1, carrier)
        cfg.AntennaCfg.Enable[0] = 1
        fir.commit_cc_config(cfg)
        wait_until(lambda: fir.status().CCUpdate, "CCF carrier update")
        self.nco_active = False
        self.tune(0)

    def tune(self, mhz):
        if abs(mhz) >= FS/2e6:
            raise ValueError("Mixer NCO frequency exceeds Nyquist")
        mix = self.mix_handle
        # A negative rotation translates the positive-frequency RF image to baseband.
        freq = dict(FrequencyControlWord=round(-mhz*1e6/FS * 2**32) % 2**32,
                    TriggerUpdateFlag=1)
        if self.nco_active:
            cfg = mix.current_cc_config()
            mix.set_nco(cfg, 0, frequency=freq, phase={})
            mix.call("ClearEventStatus", mix.new("Status", {"CCUpdate": 1}))
        else:
            cfg = mix.empty_cc_config()
            carrier = mix.new("CarrierCfg")
            carrier.DUCDDCCfg.CCGain = 3
            mix.add_cc_to_config(cfg, 0, 1, carrier, mix.new("NCO", {"FrequencyCfg": freq}))
            cfg.AntennaCfg.Gain[0] = 1
        mix.commit_cc_config(cfg)
        wait_until(lambda: mix.status().CCUpdate, "mixer CC update")
        if self.aligned and mix.status().CCUpdateError:
            raise RuntimeError("Mixer update missed its activation-aligned boundary")
        self.nco_active = True

    def stop_tone(self):
        self.shadow &= ~1
        self.control.write(0, self.shadow)
        if getattr(self, "selectable", False):
            wait_until(lambda: self.control.read(8) & 1 == 0, "DAC idle")
            if self.control.read(8) & 2:
                raise RuntimeError("DAC playback stalled")

    def play(self, mode=0):
        if mode not in range(len(TONES)) or (mode and not self.selectable):
            raise ValueError("Tone mode unavailable on this bitstream")
        self.stop_tone()
        self.shadow = (self.shadow & 7) | mode << 3
        self.control.write(0, self.shadow)
        sleep(0.001)
        self.shadow |= 1
        self.control.write(0, self.shadow)
        sleep(0.001)
        if self.selectable and self.control.read(8) != 1:
            raise RuntimeError("DAC playback did not start cleanly")

    def capture(self, raw):
        dma = self.dma
        channel = dma.recvchannel
        self.shadow = self.shadow & ~4 | int(raw) << 2
        self.control.write(0, self.shadow)
        sleep(0.001)
        buf = allocate(shape=(N, 2), dtype=np.int16)
        try:
            channel.transfer(buf)
            self.shadow ^= 2
            self.control.write(0, self.shadow)
            wait_until(lambda: channel.idle or channel.error, "S2MM snapshot")
            channel.wait()
            if channel.transferred != buf.nbytes:
                raise RuntimeError(f"Short DMA frame: {channel.transferred}")
            iq = np.asarray(buf).astype(float)
            samples = iq[:, 0] + 1j*iq[:, 1]
        except BaseException:
            self.shadow &= ~1
            self.control.write(0, self.shadow)
            dma.write(0x30, 4)  # Reset S2MM before releasing its DMA buffer.
            wait_until(lambda: not dma.read(0x30) & 4, "DMA reset")
            buf.freebuffer()
            raise
        buf.freebuffer()
        return samples

    def status(self):
        out = {}
        for dev, offset in ((self.mix_handle, 0x10), (self.fir_handle, 0x20)):
            events = dev.status()
            out[dev.driver] = dict(versions=dev.versions(), state=dev.call("GetStateID"),
                                   operational=dev.call("ReadReg", offset),
                                   events={k: getattr(events,k) for k,_ in dev.ffi.typeof(events[0]).fields})
        return out


def spectrum(samples):
    # All generated frequencies and NCO steps land exactly on FFT bins.
    f = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/FS)) / 1e6
    amp = abs(np.fft.fftshift(np.fft.fft(samples))) / (len(samples) * 32768)
    return f, 20*np.log10(np.maximum(amp, 1e-8))
