#!/usr/bin/env python3
"""Check the HamGeek ZU67DR J35 external clock and restore stock PLL2 on exit."""
import argparse
from contextlib import contextmanager, nullcontext
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

from fin_lmk import configured_fin
from j32 import analyzer_check, manual_check

MANIFEST = "c3c6e951cad027540c4d867887876ee81f6be0461780bdff69dfba88c12640fa"
BITFILE = "rowtiming250_avtt25.bit"
LOCK = Path("/run/lock/zu67dr-fin-j35.lock")
MTS_LINE = re.compile(r"(DAC|ADC) target=-1 latency=\[(\d+),(\d+)\] offset=\[(-?\d+),(-?\d+)\]")


class WorkerStuck(RuntimeError):
    """A worker could not be stopped safely."""


@contextmanager
def prepared_bundle(source):
    """Verify the release and stage a flat manifest for its r5 Python guards."""
    manifest = (source / "artifacts.sha256").read_bytes()
    if sha256(manifest).hexdigest() != MANIFEST:
        raise ValueError("Use rowtiming-r5-20ma.tar.xz from release v4.0.0-zu67dr.1")
    with TemporaryDirectory(prefix="zu67dr-j35-") as work:
        folder = Path(work)
        entries = []
        for line in manifest.decode("ascii").splitlines():
            digest, path = line.split(maxsplit=1)
            name = Path(path).name
            shutil.copy2(source / name, folder / name)
            entries.append(f"{digest}  {name}\n")
        (folder / "artifacts.sha256").write_text("".join(entries))
        subprocess.run(["sha256sum", "--quiet", "--strict", "-c", "artifacts.sha256"],
                       cwd=folder, check=True, timeout=20)
        yield folder


def parse_mts(stdout):
    result = {}
    for line in stdout.splitlines():
        if match := MTS_LINE.fullmatch(line.strip()):
            kind, first, second, offset0, offset1 = match.groups()
            if kind in result or int(first) == 0 or first != second or [offset0, offset1] != ["0", "0"]:
                raise RuntimeError(f"Unexpected MTS result: {line}")
            result[kind] = dict(latency=[int(first), int(second)], offset=[0, 0])
    if result.keys() != {"DAC", "ADC"}:
        raise RuntimeError(f"Missing ADC or DAC MTS result: {stdout.strip()}")
    return result


def cycle(args, folder, fin=configured_fin):
    from clock_guard import verify_bundle
    from rt250_driver import RowTiming
    from test_loopback import verify_overlay

    bit = args.bundle / BITFILE
    verify_overlay(bit)
    verify_bundle(bit)
    witness = (nullcontext(manual_check) if args.confirm_j32
               else analyzer_check(args.analyzer_host, args.analyzer_port))
    with witness as measure_j32:
        (folder / "lmk-attempted").touch()
        with fin(args.frequency_mhz) as (lmk, read_status):
            # Check physical clock presence after programming Fin, before any PL load.
            result = dict(frequency_mhz=args.frequency_mhz, lmk=lmk, j32_pre_overlay=measure_j32())
            rt = RowTiming(bit, expected_rate=2.5, expected_sysref=6.25, status_only=True)
            streams = rt.rd("RFDC_STREAM_STATUS")
            if streams & 0xF != 0xF:
                raise RuntimeError(f"Expected all four RFDC streams up, got {streams:#x}")
            result.update(clocks=rt.clock_measurements, streams=streams)
            if not args.status_only:
                if not args.confirm_j32:
                    result["j32_pre_rfdc"] = measure_j32()
                rt = RowTiming(bit, download=False, expected_rate=2.5, expected_sysref=6.25)
                try:
                    result["mmcm_resets"] = rt.lock_phase()
                    if not args.confirm_j32:
                        result["j32_pre_mts"] = measure_j32()
                    result["mts"] = parse_mts(rt.mts())
                finally:
                    rt.stop()
            result["lmk_final"] = read_status()
    (folder / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, allow_nan=False), flush=True)


def restore():
    from rt250_lmk_hw import configured_clock

    with configured_clock():
        print("Stock internal 3000 MHz VCO restored and PLL2 locked.", flush=True)


def interrupted(signum, _frame):
    # Unwind Python contexts on TERM/HUP, including the LMK SPI overlay.
    raise SystemExit(128 + signum)


def worker(argv, timeout):
    process = subprocess.Popen([sys.executable, "-u", __file__, *argv], start_new_session=True)
    try:
        code = process.wait(timeout=timeout)
    except BaseException:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                continue
            break
        else:
            raise WorkerStuck("Worker did not exit. Keep J35 driven and recover by power cycle.")
        raise
    if code:
        raise RuntimeError(f"Worker exited {code}")


def run(args, bundle):
    args.output.mkdir()
    command = ["run", "--bundle", str(bundle), "--output", str(args.output),
               "--frequency-mhz", str(args.frequency_mhz)]
    if args.confirm_j32:
        command += ["--confirm-j32"]
    else:
        command += ["--analyzer-host", args.analyzer_host, "--analyzer-port", str(args.analyzer_port)]
    if args.status_only:
        command += ["--status-only"]
    else:
        command += ["--adc-avcc", str(args.adc_avcc)]
    rows = []
    stuck = False
    try:
        for index in range(1, args.cycles + 1):
            folder = args.output / f"cycle-{index:03d}"
            folder.mkdir()
            worker([*command, "--worker-cycle", str(folder)], timeout=180)
            rows.append(json.loads((folder / "result.json").read_text()))
        if not args.status_only:
            if any(row["mts"] != rows[0]["mts"] for row in rows[1:]):
                raise RuntimeError("MTS latency changed across warm reloads")
            print(f"{len(rows)}/{args.cycles} warm cycles passed with constant MTS latency.", flush=True)
    except WorkerStuck:
        stuck = True
        raise
    finally:
        if not stuck and any(args.output.glob("cycle-*/lmk-attempted")):
            restore_worker(bundle)


def restore_worker(bundle):
    try:
        worker(["restore", "--bundle", str(bundle), "--worker-restore"], timeout=30)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Stock PLL2 restore could not be confirmed. Keep J35 driven. "
                           "See the recovery instructions.") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("run", help="program Fin, verify J32 and check the r5 overlay")
    stock = commands.add_parser("restore", help="restore the stock LMK profile without loading an overlay")
    for command in (check, stock):
        command.add_argument("--bundle", type=Path, required=True, help="extracted rowtiming-r5-20ma directory")
    check.add_argument("--frequency-mhz", type=int, choices=(1500, 3000), default=1500,
                       help="J35 frequency (1500 verified on warm reloads; 3000 experimental)")
    check.add_argument("--output", type=Path, required=True, help="new directory for per-cycle JSON")
    check.add_argument("--status-only", action="store_true", help="skip RFDC access and MTS")
    check.add_argument("--adc-avcc", type=float, help="measured TP16 in volts, required for MTS")
    check.add_argument("--cycles", type=int, default=1, help="number of warm reloads")
    gate = check.add_mutually_exclusive_group(required=True)
    gate.add_argument("--confirm-j32", action="store_true", help="prompt for a fresh manual measurement each cycle")
    gate.add_argument("--analyzer-host", help="Keysight X-Series analyzer connected to J32")
    check.add_argument("--analyzer-port", type=int, default=5025, help="analyzer raw SCPI TCP port")
    check.add_argument("--worker-cycle", type=Path, help=argparse.SUPPRESS)
    stock.add_argument("--worker-restore", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run on the PYNQ board with sudo and the PYNQ Python interpreter")
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    if args.command == "run":
        if args.cycles < 1 or not 1 <= args.analyzer_port <= 65535:
            parser.error("Specify a positive cycle count and a valid TCP port")
        if not args.status_only and (args.adc_avcc is None or not 0.980 <= args.adc_avcc <= 1.040):
            parser.error("MTS requires --adc-avcc with measured TP16 in the 0.980–1.040 V range")
        if args.confirm_j32 and not sys.stdin.isatty():
            parser.error("--confirm-j32 requires an interactive terminal")
        if args.worker_cycle:
            sys.path.insert(0, str(args.bundle))
            cycle(args, args.worker_cycle)
            return
    elif args.worker_restore:
        sys.path.insert(0, str(args.bundle))
        restore()
        return

    with LOCK.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with prepared_bundle(args.bundle) as bundle:
            if args.command == "restore":
                restore_worker(bundle)
            else:
                run(args, bundle)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
