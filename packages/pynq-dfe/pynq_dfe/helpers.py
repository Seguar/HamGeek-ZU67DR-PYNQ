from operator import index

import numpy as np


def sequence_bitmap(sequence, ccid):
    """Bit zero denotes the first AXI sequence slot. None denotes an unused slot."""
    if not 1 <= len(sequence) <= 16 or not 0 <= index(ccid) < 16:
        raise ValueError("Expected 1..16 slots and a CC ID in 0..15")
    if any(slot is not None and not 0 <= index(slot) < 16 for slot in sequence):
        raise ValueError("Invalid sequence slot")
    return sum(1 << pos for pos, slot in enumerate(sequence) if slot == ccid)


def mixer_rate(length, bitmap, antenna_interleave=1, mixer_cps=1):
    """Return the mixer rate register encoding (zero disables a carrier)."""
    if not 1 <= length <= 16 or not 0 <= bitmap < (1 << length):
        raise ValueError("Invalid sequence length or bitmap")
    if antenna_interleave not in (1, 2, 4, 8) or mixer_cps not in (1, 2, 4):
        raise ValueError("Invalid antenna interleave or mixer CPS")
    count = bitmap.bit_count()
    if not count:
        return 0
    ratio, remainder = divmod(antenna_interleave * length, count * mixer_cps)
    if count & (count - 1) or remainder or ratio not in (1, 2, 4, 8, 16):
        raise ValueError("Unsupported mixer conversion ratio")
    return ratio.bit_length()


def lowpass_taps(num_taps, cutoff, sample_rate):
    """Hamming-window lowpass with unity DC gain, rounded to signed Q1.15."""
    if not 1 <= index(num_taps) <= 256 or not 0 < cutoff < sample_rate / 2:
        raise ValueError("Expected 1..256 taps and a cutoff below Nyquist")
    try:
        from scipy.signal import firwin
    except ImportError:
        t = np.arange(num_taps) - (num_taps - 1) / 2
        taps = np.sinc(2 * cutoff / sample_rate * t) * np.hamming(num_taps)
        taps /= taps.sum()
    else:
        taps = firwin(num_taps, cutoff, fs=sample_rate, window="hamming")
    return np.clip(np.rint(32768 * taps), -32768, 32767).astype(np.int16)
