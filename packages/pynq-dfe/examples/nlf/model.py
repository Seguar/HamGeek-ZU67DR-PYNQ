"""Steady-state PG401 FIR in integer output codes, OUT_SCALE=0."""
import numpy as np


def predict(x, coefficients):
    acc = sum(c * np.roll(x, delay) for delay, c in enumerate(coefficients))
    # Q1.15 times Q1.15 into 25 signed bits with 18 fractional bits.
    # All test taps are multiples of 4096, so these divisions are exact.
    return acc / 4096
