"""Regression for the four fractional-phase banks in the hard CFR."""
import unittest

from pynq_dfe.cfr import HardCFR


class RegisterFile(dict):
    def write(self, offset, value):
        self[offset] = value

    def read(self, offset):
        return self[offset]


class TestPulseRAM(unittest.TestCase):
    def test_phase_order_padding_and_signed_quadrature(self):
        # Nine taps require three zeros on each side to fill four phase banks.
        left = [(1, -1), (2, -2), (3, -3), (4, -4)]
        taps = left + [(16384, 0)] + [(i, -q) for i, q in reversed(left)]
        mmio = RegisterFile()
        HardCFR(mmio).configure(taps, 12000)
        self.assertEqual(mmio[0], 15)
        self.assertEqual(mmio[0x044], 7)
        expected = [(0, 0), (2, -2), (0, 0), (3, -3),
                    (0, 0), (4, -4), (1, -1), (16384, 0)]
        for address, (i, q) in enumerate(expected):
            self.assertEqual(mmio[0x8000 + 4 * address], (q & 65535) << 16 | i)


if __name__ == '__main__':
    unittest.main()
