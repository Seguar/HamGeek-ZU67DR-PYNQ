# SPDX-License-Identifier: BSD-3-Clause
"""Segment / sequence builder and bit-exact software model of the RF loopback
sequencers. Pure numpy: runs offline (no board, no pynq).

Time grid (all from the single 250 MHz reference):
  word  = one 312.5 MHz cycle = 3.2 ns = 4 units
  unit  = 0.8 ns  (DAC: 8 samples at 10 GS/s; GTY: 16 bits at 20 Gb/s or 8 bits at 10 Gb/s)
Time zero (unit 0) is the first unit of the first word the sequencers can
issue after the start pulse. A fixed, calibrated pipeline latency separates it
from the converter / serializer output.
"""

from dataclasses import dataclass, field
import struct

import numpy as np

UNIT_NS = 0.8
WORD_NS = 3.2
TICK_NS = 4.0
UNITS_PER_WORD = 4
UNITS_PER_TICK = 5

# Hardware geometry (must match rt_core.v; the driver re-reads it from GEOMETRY)
DAC_SEG_WORDS = 4096          # 512-bit words per DAC channel (URAM)
GTY_SEG_WORDS = 8192          # GTW-bit words per GTY lane (URAM)
TABLE_ENTRIES = 1024          # sequence entries per channel / lane (BRAM)
CAP_WORDS = 8192              # 128-bit capture words per ADC channel (BRAM)
DAC_SAMPLES_PER_WORD = 32     # 512 bits / 16
ADC_SAMPLES_PER_WORD = 8
DAC_RATE = 10e9
ADC_RATE = 2.5e9

class Stream:
    """Describes one sequencer type."""

    def __init__(self, kind, gty_gbps=20):
        self.kind = kind
        if kind == "dac":
            self.unit_bits = 128
            self.seg_words = DAC_SEG_WORDS
            self.word_bits = 512
        elif kind == "gty":
            self.word_bits = 64 if gty_gbps == 20 else 32
            self.unit_bits = self.word_bits // 4
            self.seg_words = GTY_SEG_WORDS
        else:
            raise ValueError(kind)
        self.gty_gbps = gty_gbps

    @property
    def samples_per_unit(self):
        return 8 if self.kind == "dac" else self.unit_bits      # DAC samples or GTY bits

    @property
    def per_word(self):
        return 4 * self.samples_per_unit

DAC = Stream("dac")

# --------------------------------------------------------------------------
# Segment library
# --------------------------------------------------------------------------
@dataclass
class Segment:
    name: str
    data: np.ndarray          # DAC: int16 samples; GTY: uint8 bits (0/1)
    kind: str

    def words(self, stream):
        return len(self.data) // stream.per_word

def dac_segment(name, samples):
    """int16 samples at 10 GS/s; length padded with zeros to a multiple of 32."""
    s = np.asarray(samples)
    if s.dtype.kind == "f":
        s = np.round(np.clip(s, -1.0, 1.0) * 32767)
    s = s.astype(np.int16)
    pad = (-len(s)) % DAC_SAMPLES_PER_WORD
    return Segment(name, np.concatenate([s, np.zeros(pad, np.int16)]), "dac")

def tone(freq_hz, n_samples, amplitude=0.9, phase=0.0, rate=DAC_RATE):
    t = np.arange(n_samples) / rate
    return amplitude * np.sin(2 * np.pi * freq_hz * t + phase)

def periodic_tone_length(freq_hz, rate=DAC_RATE, per_word=DAC_SAMPLES_PER_WORD, max_words=4096):
    """Shortest whole-word length that holds an integer number of periods."""
    from fractions import Fraction
    period = Fraction(rate).limit_denominator(10**9) / Fraction(freq_hz).limit_denominator(10**9)
    for words in range(1, max_words + 1):
        cycles = Fraction(words * per_word) / period
        if cycles.denominator == 1:
            return words * per_word
    raise ValueError("no periodic whole-word length below max_words")

# --------------------------------------------------------------------------
# Sequences
# --------------------------------------------------------------------------
@dataclass
class Event:
    segment: str
    start_unit: int           # absolute 0.8 ns unit of the first sample / bit
    repeat: int = 1

@dataclass
class Entry:
    gap: int
    offset: int
    length: int
    address: int
    repeat: int

    def pack(self):
        return struct.pack("<IIII", self.gap & 0xFFFFFFFF,
                           (self.offset & 3) | ((self.length & 0xFFFF) << 16),
                           self.address & 0xFFFFFFFF, self.repeat & 0xFFFFFFFF)

@dataclass
class Channel:
    events: list = field(default_factory=list)

    def at_tick(self, segment, tick, repeat=1, unit=0):
        """Start `segment` at a 4 ns tick (plus an optional 0.8 ns unit offset)."""
        self.events.append(Event(segment, tick * UNITS_PER_TICK + unit, repeat))
        return self

    def at_unit(self, segment, unit, repeat=1):
        self.events.append(Event(segment, unit, repeat))
        return self

class Program:
    """Per-channel sequences + segment library for one stream type."""

    def __init__(self, stream, library, n_channels=8):
        self.stream = stream
        self.library = {s.name: s for s in library}
        self.channels = [Channel() for _ in range(n_channels)]
        self.addresses = [dict() for _ in range(n_channels)]
        self.entries = [[] for _ in range(n_channels)]

    def __getitem__(self, ch):
        return self.channels[ch]

    # -- allocation and table generation ------------------------------------
    def compile(self):
        st = self.stream
        for ch, chan in enumerate(self.channels):
            addr = {}
            nxt = 0
            for ev in chan.events:
                seg = self.library[ev.segment]
                if seg.kind != st.kind:
                    raise ValueError(f"segment {seg.name} is {seg.kind}, stream is {st.kind}")
                if ev.segment not in addr:
                    addr[ev.segment] = nxt
                    nxt += seg.words(st)
            if nxt > st.seg_words:
                raise ValueError(f"{st.kind} channel {ch}: {nxt} words > segment memory {st.seg_words}")
            self.addresses[ch] = addr
            entries = []
            prev_end_word = -1        # last issued word of the previous entry
            prev_end_unit = 0         # first free unit after the previous entry
            prev_k = 0
            for ev in sorted(chan.events, key=lambda e: e.start_unit):
                seg = self.library[ev.segment]
                n = seg.words(st)
                if n < 1:
                    raise ValueError(f"segment {seg.name} is empty")
                rep = max(1, int(ev.repeat))
                if ev.start_unit < prev_end_unit:
                    raise ValueError(f"{st.kind} ch {ch}: event {ev.segment} at unit {ev.start_unit} "
                                     f"overlaps the previous one (ends at unit {prev_end_unit})")
                w0, k = divmod(ev.start_unit, UNITS_PER_WORD)
                gap = w0 - prev_end_word - 1
                if gap < 0 or (gap == 0 and k < prev_k):
                    raise ValueError(f"{st.kind} ch {ch}: event {ev.segment} too close to the previous one")
                entries.append(Entry(gap, k, n, addr[ev.segment], rep))
                prev_end_word = w0 + n * rep - 1
                prev_end_unit = ev.start_unit + n * rep * UNITS_PER_WORD
                prev_k = k
            if len(entries) > TABLE_ENTRIES:
                raise ValueError(f"{st.kind} ch {ch}: {len(entries)} entries > {TABLE_ENTRIES}")
            self.entries[ch] = entries
        return self

    # -- DMA images ------------------------------------------------------------
    def segment_rows(self, name):
        """Bytes of one segment in segment-memory order."""
        seg = self.library[name]
        if self.stream.kind == "dac":
            return seg.data.astype("<i2").tobytes()
        return np.packbits(seg.data, bitorder="little").tobytes()

    def load_plan(self):
        """[(mask, start_row, bytes)] grouping identical (segment, address) across channels."""
        groups = {}
        for ch, addr in enumerate(self.addresses):
            for name, a in addr.items():
                groups.setdefault((name, a), 0)
                groups[(name, a)] |= 1 << ch
        plan = [(mask, a, self.segment_rows(name)) for (name, a), mask in groups.items()]
        return sorted(plan, key=lambda p: (p[0], p[1]))

    def table_bytes(self, ch):
        return b"".join(e.pack() for e in self.entries[ch])

    # -- model -------------------------------------------------------------------
    def end_word(self, ch):
        w = -1
        for e in self.entries[ch]:
            w = w + 1 + e.gap + e.length * e.repeat - 1
        return w

    def render(self, ch, n_words=None, idle=0):
        """Bit-exact model of the sequencer output words (units) for channel ch.

        Returns an array of shape (n_words*4, samples_per_unit): DAC int16 or GTY bits.
        """
        st = self.stream
        spu = st.samples_per_unit
        if n_words is None:
            n_words = self.end_word(ch) + 2
        dt = np.int16 if st.kind == "dac" else np.uint8
        out = np.full((n_words * 4, spu), idle, dt)
        lib_words = {}
        for name, a in self.addresses[ch].items():
            lib_words[a] = self.library[name].data.reshape(-1, 4, spu)
        w = -1
        for e in self.entries[ch]:
            s = w + 1 + e.gap
            seg = lib_words[e.address]
            data = np.tile(seg, (e.repeat, 1, 1)).reshape(-1, spu)
            u0 = 4 * s + e.offset
            u1 = min(u0 + len(data), n_words * 4)
            if u0 < u1:
                out[u0:u1] = data[:u1 - u0]
            w = s + e.length * e.repeat - 1
        return out

    def render_flat(self, ch, n_words=None, idle=0):
        return self.render(ch, n_words, idle).reshape(-1)

    # -- budget --------------------------------------------------------------------
    def usage(self):
        st = self.stream
        rows = []
        for ch in range(len(self.channels)):
            used = sum(self.library[n].words(st) for n in self.addresses[ch])
            end = self.end_word(ch)
            rows.append(dict(channel=ch, seg_words=used, seg_capacity=st.seg_words,
                             entries=len(self.entries[ch]), entry_capacity=TABLE_ENTRIES,
                             run_ns=(end + 1) * WORD_NS if end >= 0 else 0.0))
        return rows

def memory_budget(gty_gbps=20):
    """Per-channel memory and its share of the XCZU67DR (648 BRAM36, 160 URAM)."""
    gtw = 64 if gty_gbps == 20 else 32
    dac_bits = DAC_SEG_WORDS * 512
    gty_bits = GTY_SEG_WORDS * gtw
    cap_bits = CAP_WORDS * 128
    return {
        "dac_segment": dict(per_channel_words=DAC_SEG_WORDS, samples=DAC_SEG_WORDS * 32,
                            unique_us=DAC_SEG_WORDS * WORD_NS / 1e3, bits=dac_bits,
                            primitive="URAM", primitives_per_channel=8),
        "gty_segment": dict(per_lane_words=GTY_SEG_WORDS, bits=gty_bits,
                            unique_us=GTY_SEG_WORDS * WORD_NS / 1e3,
                            primitive="URAM", primitives_per_lane=2),
        "sequence_table": dict(entries=TABLE_ENTRIES, bits=TABLE_ENTRIES * 128,
                               primitive="BRAM36", primitives_per_table=4, tables=16),
        "adc_capture": dict(per_channel_words=CAP_WORDS, samples=CAP_WORDS * 8,
                            us=CAP_WORDS * WORD_NS / 1e3, bits=cap_bits,
                            primitive="BRAM36", primitives_per_channel=32),
        "device": dict(BRAM36=648, URAM=160),
        "planned_total": dict(URAM=8 * 8 + 8 * 2, BRAM36=16 * 4 + 8 * 32),
    }

def longest_run(entries_used, repeat_max=2**32 - 1, seg_words=1, gap_max=2**32 - 1):
    """Upper bound of a run built from table entries (ns)."""
    per_entry = (gap_max + seg_words * repeat_max) * WORD_NS
    return entries_used * per_entry
