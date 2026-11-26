"""Exercise the profiles, J32 gate, warm-cycle order and recovery without hardware."""
from contextlib import nullcontext
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import fin_lmk
import j32
import run_ext_clock as run

MTS = "DAC target=-1 latency=[432,432] offset=[0,0]\nADC target=-1 latency=[436,436] offset=[0,0]\n"


def profile(mhz):
    path = fin_lmk.PROFILES[mhz]
    return [int(line, 16) for line in path.read_text().splitlines() if not line.startswith("#")]


class TestFin(unittest.TestCase):
    def test_output_rates_and_only_divider_changes(self):
        regs = [{w >> 8: w & 0xFF for w in profile(mhz)} for mhz in (1500, 3000)]
        changed = {addr for addr in regs[0] if regs[0][addr] != regs[1][addr]}
        self.assertEqual(changed, {*fin_lmk.DIVIDER_REGS, 0x13A, 0x13B})
        for mhz, values in zip((1500, 3000), regs):
            for addr in fin_lmk.DIVIDER_REGS:
                self.assertEqual(mhz * 1e6 / (values[addr] & 0x1F), j32.J32_HZ)
            self.assertEqual(mhz * 1e6 / (256 * values[0x13A] + values[0x13B]), 6.25e6)
            for addr, (value, _) in fin_lmk.CHANGES.items():
                self.assertEqual(values[addr], value)

    def test_program_checks_routing_before_sync_and_marks_los_invalid(self):
        words = profile(1500)
        regs = {0x182: 0, 0x183: 0, 0x184: 2}

        def write(word):
            addr = word >> 8
            if addr not in (0x182, 0x183, 0x184):
                regs[addr] = word & 0xFF

        def sync(write):
            for word in (0x013903, 0x014311, 0x0144FF):
                write(word)

        status = fin_lmk.program_fin(write, regs.__getitem__, words, sync, pause=lambda _: None)
        self.assertFalse(status["pll1_locked"] or status["pll2_locked"])
        self.assertTrue(status["clkin1_los_raw"])
        self.assertFalse(status["los_valid"])

        sync = Mock()
        with self.assertRaisesRegex(RuntimeError, "0x138"):
            fin_lmk.program_fin(write, lambda a: regs[a] if a != 0x138 else 0x21,
                                words, sync, pause=lambda _: None)
        sync.assert_not_called()

    def test_unexpected_pll_lock_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Unexpected LMK lock"):
            fin_lmk.status({0x182: 0, 0x183: 2, 0x184: 0}.__getitem__)


class TestWitness(unittest.TestCase):
    def setUp(self):
        self.levels = [-100] * j32.POINTS

    def test_trace_requires_a_valid_peak(self):
        with self.assertRaisesRegex(RuntimeError, "clock absent"):
            j32.check_trace(self.levels, j32.START_HZ, j32.STOP_HZ)
        self.levels[200] = -49
        self.assertEqual(j32.check_trace(self.levels, j32.START_HZ, j32.STOP_HZ)["peak_hz"],
                         j32.J32_HZ)

    def test_manual_gate_requires_explicit_input(self):
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=["", "250MHz"]):
            with self.assertRaisesRegex(RuntimeError, "was not confirmed"):
                j32.manual_check()
            self.assertTrue(j32.manual_check()["confirmed_by_operator"])

    def test_analyzer_sweeps_over_the_requested_endpoint(self):
        self.levels[200] = -49
        responses = ["SA", "1", ",".join(map(str, self.levels)), str(j32.START_HZ),
                     str(j32.STOP_HZ), '0,"No error"']
        reader = io.BytesIO("".join(value + "\n" for value in responses).encode("ascii"))
        sock = Mock()
        sock.makefile.return_value = reader
        with patch.object(j32.socket, "create_connection", return_value=nullcontext(sock)) as connect:
            with j32.analyzer_check("analyzer", 1234) as check:
                self.assertEqual(check()["peak_dbm"], -49)
        connect.assert_called_once_with(("analyzer", 1234), timeout=12)
        sock.sendall.assert_any_call(b":INIT:IMM\n")


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.status = Mock(clock_measurements={"fabric_mhz": 312.5, "sysref_mhz": 6.25})
        self.status.rd.return_value = 0xF
        self.full = Mock()
        self.full.lock_phase.return_value = 1
        self.full.mts.return_value = MTS
        self.overlay = Mock(side_effect=[self.status, self.full])
        self.fin = Mock(return_value=nullcontext(({}, dict)))
        self.args = SimpleNamespace(bundle=Path("."), status_only=False, confirm_j32=True,
                                    frequency_mhz=1500, cycles=1, adc_avcc=1.0)
        modules = {}
        for module, name, value in (("clock_guard", "verify_bundle", Mock()),
                                    ("test_loopback", "verify_overlay", Mock()),
                                    ("rt250_driver", "RowTiming", self.overlay)):
            stub = modules[module] = ModuleType(module)
            setattr(stub, name, value)
        imports = patch.dict(sys.modules, modules)
        imports.start()
        self.addCleanup(imports.stop)

    def test_missing_j32_never_constructs_overlay(self):
        with TemporaryDirectory() as tmp, patch.object(run, "manual_check", side_effect=RuntimeError("No J32")):
            with self.assertRaisesRegex(RuntimeError, "No J32"):
                run.cycle(self.args, Path(tmp), self.fin)
            self.overlay.assert_not_called()
            self.assertTrue((Path(tmp) / "lmk-attempted").is_file())

    def test_status_only_never_opens_rfdc(self):
        self.args.status_only = True
        with TemporaryDirectory() as tmp, patch.object(run, "manual_check", return_value={}):
            run.cycle(self.args, Path(tmp), self.fin)
            data = json.loads((Path(tmp) / "result.json").read_text())
        self.overlay.assert_called_once_with(Path(run.BITFILE), expected_rate=2.5,
                                             expected_sysref=6.25, status_only=True)
        self.assertEqual(data["streams"], 0xF)

    def test_warm_cycle_checks_j32_before_overlay_and_runs_mts(self):
        order = Mock()
        order.attach_mock(self.fin, "fin")
        order.attach_mock(self.overlay, "overlay")
        order.attach_mock(self.full, "full")
        measure = Mock(return_value={"confirmed_by_operator": True})
        order.attach_mock(measure, "measure")
        with TemporaryDirectory() as tmp, patch.object(run, "manual_check", measure):
            run.cycle(self.args, Path(tmp), self.fin)
            data = json.loads((Path(tmp) / "result.json").read_text())
        self.assertEqual([call[0] for call in order.mock_calls],
                         ["fin", "measure", "overlay", "overlay", "full.lock_phase", "full.mts", "full.stop"])
        self.assertFalse(self.overlay.call_args.kwargs["download"])
        self.assertEqual(data["mts"]["DAC"]["latency"], [432, 432])

    def test_nonzero_offsets_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Unexpected MTS result"):
            run.parse_mts(MTS.replace("offset=[0,0]", "offset=[0,2]"))

    def test_abort_restores_stock_even_after_partial_programming(self):
        def failed_worker(argv, timeout):
            (Path(argv[-1]) / "lmk-attempted").touch()
            raise RuntimeError("J32 gate failed")

        with TemporaryDirectory() as tmp, patch.object(run, "worker", side_effect=failed_worker), \
                patch.object(run, "restore_worker") as restore:
            bundle = Path(tmp)
            self.args.output = bundle / "results"
            with self.assertRaisesRegex(RuntimeError, "J32 gate failed"):
                run.run(self.args, bundle)
            restore.assert_called_once_with(bundle)


@unittest.skipUnless(os.getenv("J35_BUNDLE"), "set J35_BUNDLE for release integration")
class TestReleaseBundle(unittest.TestCase):
    def test_profiles_and_both_original_overlay_guards(self):
        source = Path(os.environ["J35_BUNDLE"])
        script = """
import sys
from pathlib import Path
import fin_lmk
from run_ext_clock import BITFILE
folder = Path(sys.argv[1])
sys.path.insert(0, str(folder))
import clock_guard
import rt250_clock
import test_loopback
stock = rt250_clock.load_profile_file(folder / "lmk04828_vco3000.txt")
for mhz, expected in [(1500, fin_lmk.fin1500_words(stock)), (3000, fin_lmk.fin_words(stock))]:
    assert rt250_clock.load_profile_file(fin_lmk.PROFILES[mhz]) == expected
test_loopback.verify_overlay(folder / BITFILE)
assert clock_guard.verify_bundle(folder / BITFILE) == (2.5, 312.5)
"""
        with run.prepared_bundle(source) as folder:
            subprocess.run([sys.executable, "-c", script, str(folder)], check=True,
                           cwd=Path(__file__).resolve().parent)


if __name__ == "__main__":
    unittest.main()
