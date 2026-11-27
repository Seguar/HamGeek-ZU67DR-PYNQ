"""Hardware-free RFdc and RowTiming for exercising the runner and recorder."""
from types import SimpleNamespace
import numpy as np


class Block:
    NyquistZone = 1
    OutputCurr = 20037
    DACDataScaler = 0

    def GetCoupling(self):
        return 1


class Tile:
    PLLLockStatus = 2

    def __init__(self, rate):
        self.blocks = [Block() for _ in range(4)]
        self.PLLConfig = {"SampleRate": rate}
        self.state = 15

    def GetMinSampleRate(self):
        return 500.

    def GetMaxSampleRate(self):
        return self.PLLConfig["SampleRate"] * 1000

    def StartUp(self):
        self.state = 15

    def CustomStartUp(self, start, end):
        assert (start, end) == (1, 15)
        self.state = end


class FakeRF:
    def __init__(self):
        self.adc_tiles = [Tile(rate) for rate in (2.5, 2.5, 5.)]
        self.dac_tiles = [Tile(10.) for _ in range(2)]

    def get_mts_enable(self, kind, tile):
        return tile in (0, 1)

    def GetTileLayout(self):
        return 1

    @property
    def IPStatus(self):
        status = {}
        for kind, tiles in (("ADC", self.adc_tiles), ("DAC", self.dac_tiles)):
            status[kind+"TileStatus"] = [
                dict(IsEnabled=int(i < len(tiles)), PLLState=int(kind == "DAC" or i == 2), TileState=tiles[i].state if i < len(tiles) else 0)
                for i in range(4)]
        return status

    def _mts(self, tiles, latency, offsets):
        return {"Latency": latency, "tiles": {i: dict(Latency=latency, Offset=offsets[i]) for i in tiles}}

    def mts_adc_sync(self, tiles, target_latency):
        return self._mts(tiles, target_latency or 440, [8, 4] if target_latency else [0, 0])

    def mts_dac_sync(self, tiles, target_latency):
        return self._mts(tiles, target_latency or 416, [16, 16] if target_latency else [0, 0])


class FakeRT:
    def __init__(self, bit, **kwargs):
        self.overlay = SimpleNamespace(rfdc=FakeRF())
        self.regs = dict(RFDC_STREAM_STATUS=15)
        self.running = False

    def status(self):
        return dict(busy_dac=self.running, busy_gty=0, armed=0, running=self.running)

    def rd(self, reg):
        return self.regs.get(reg, 0)

    def wr(self, reg, value):
        self.regs[reg] = value

    def lock_phase(self):
        pass

    def mts(self, adc, dac):
        if (adc, dac) == (448, 432):
            return "DAC target=432 latency=[432,432] offset=[16,16]\nADC target=448 latency=[448,448] offset=[8,4]"
        assert adc == dac == -1
        return "DAC target=-1 latency=[416,416] offset=[0,0]\nADC target=-1 latency=[440,440] offset=[0,0]"

    def load_program(self, program):
        assert program.entries[0] and not any(program.entries[1:])

    def run(self, *, dac_enable, gty_enable, adc_delay):
        assert (dac_enable, gty_enable) == (1, 0)
        self.running = True
        self.wr("DAC_ENABLE", dac_enable)

    def readback(self, channel):
        assert self.running and channel == 0
        return np.round(3689 * np.sin(2*np.pi*np.arange(65536)/25))

    def stop(self):
        self.running = False
