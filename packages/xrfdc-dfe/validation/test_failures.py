"""Offline regression checks. Supply the pinned bundle as the only argument."""
from contextlib import chdir
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fake
import validate

BUNDLE = Path(sys.argv.pop(1)).resolve()


class FailureChecks(unittest.TestCase):
    def worker(self, rt):
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
            Path("bundle").symlink_to(BUNDLE)
            Path("BOARD.lock").write_text("test")
            with patch.object(fake, "FakeRT", return_value=rt), patch.object(
                    sys, "argv", ["validate.py", "--ticket", "test", "--fake", "--adc-avcc", ".93"]):
                self.assertEqual(validate.main(), 1)
            return json.loads(Path("report.json").read_text())["checks"]

    def test_invalid_current_before_playback(self):
        rt = fake.FakeRT(None)
        rt.overlay.rfdc.dac_tiles[0].blocks[0].OutputCurr = 32000
        rows = self.worker(rt)
        self.assertEqual(next(r for r in rows if r["status"] == "FAIL")["check"],
                         "DAC0.0 output current uA")
        self.assertNotIn("DAC_ENABLE", {k for k, v in rt.regs.items() if v})

    def test_capture_exception(self):
        rt = fake.FakeRT(None)
        with patch.object(rt, "readback", side_effect=RuntimeError("DMA failure")):
            rows = self.worker(rt)
        self.assertIn("DMA failure", str(rows))
        self.assertFalse(any(validate.idle(rt).values()))

    def test_restore_after_zone_readback_error(self):
        class BadRead(fake.Block):
            zone = 1

            @property
            def NyquistZone(self):
                return 99 if self.zone == 2 else self.zone

            @NyquistZone.setter
            def NyquistZone(self, zone):
                self.zone = zone

        rt = fake.FakeRT(None)
        block = BadRead()
        rt.overlay.rfdc.adc_tiles[0].blocks[0] = block
        rows = self.worker(rt)
        self.assertEqual(block.zone, 1)
        self.assertTrue(any(r["check"] == "changed ADC zone" and r["status"] == "FAIL" for r in rows))

    def test_independent_adc_sync_signatures(self):
        rt = fake.FakeRT(None)
        rf = rt.overlay.rfdc
        with tempfile.TemporaryDirectory() as tmp:
            report = validate.Report(Path(tmp), True)
            with patch.object(rf, "mts_adc_sync", return_value=rf._mts([0, 1], 444, [4, 0])):
                validate.sync(rt, rf, report, None, None)
            with patch.object(rf, "mts_adc_sync", return_value=rf._mts([0, 1], 444, [0, 0])):
                with self.assertRaisesRegex(ValueError, "Python latencies and offsets"):
                    validate.sync(rt, rf, report, None, None)

    def test_process_scan(self):
        # Read-only scan on the development machine.
        self.assertNotIn(str(validate.os.getpid()), validate.processes())


if __name__ == "__main__":
    unittest.main()
