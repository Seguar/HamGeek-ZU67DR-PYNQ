"""Measure the J32 clock manually or with a Keysight X-Series spectrum analyzer."""
from contextlib import closing, contextmanager
from math import isfinite
import socket
from statistics import median
import sys

J32_HZ = 250_000_000
START_HZ, STOP_HZ, POINTS = J32_HZ - 50_000, J32_HZ + 50_000, 401


def check_trace(levels, start_hz, stop_hz):
    if (len(levels) != POINTS or not all(map(isfinite, levels))
            or (start_hz, stop_hz) != (START_HZ, STOP_HZ)):
        raise RuntimeError("Invalid J32 analyzer span or trace")
    index = max(range(POINTS), key=levels.__getitem__)
    hz = start_hz + index * (stop_hz - start_hz) / (POINTS - 1)
    peak, floor = levels[index], median(levels)
    if abs(hz - J32_HZ) > 5000 or not -75 <= peak <= 0 or peak - floor < 15:
        raise RuntimeError(f"J32 clock absent or invalid: {hz:.0f} Hz, "
                           f"{peak:.1f} dBm, trace median {floor:.1f} dBm")
    return dict(peak_hz=hz, peak_dbm=peak, median_dbm=floor)


def manual_check():
    if not sys.stdin.isatty():
        raise RuntimeError("Manual J32 confirmation requires an interactive terminal")
    reply = input("Measure J32 now. Type 250MHz to confirm a stable 250 MHz clock, "
                  "or press Enter to abort: ")
    if reply != "250MHz":
        raise RuntimeError("J32 clock was not confirmed")
    return {"confirmed_by_operator": True}


@contextmanager
def analyzer_check(host, port):
    """Set up a dedicated analyzer and yield a function that takes a fresh sweep."""
    with socket.create_connection((host, port), timeout=12) as sock, closing(sock.makefile("rb")) as reader:
        def send(command):
            sock.sendall((command + "\n").encode("ascii"))

        def query(command):
            send(command)
            reply = reader.readline(65_537)
            if not reply.endswith(b"\n"):
                raise RuntimeError("Incomplete J32 analyzer response")
            return reply.decode("ascii").strip()

        if query(":INST:SEL?").strip('"') != "SA":
            raise RuntimeError("Set the J32 analyzer to spectrum-analyzer mode")
        for command in (
            ":INIT:CONT OFF", ":SENS:POW:RF:ATT:AUTO OFF", ":SENS:POW:RF:ATT 20",
            ":SENS:POW:RF:GAIN OFF", ":FORM:DATA ASC", ":TRAC1:TYPE WRIT",
            ":SENS:DET:TRAC1 POS", ":SENS:AVER:STAT OFF", ":SENS:BAND:RES 1000",
            ":SENS:BAND:VID:AUTO ON", f":SENS:FREQ:CENT {J32_HZ}",
            f":SENS:FREQ:SPAN {STOP_HZ - START_HZ}", f":SENS:SWE:POIN {POINTS}",
        ):
            send(command)

        def measure():
            send(":INIT:IMM")
            if query("*OPC?") != "1":
                raise RuntimeError("J32 analyzer sweep did not complete")
            levels = [float(value) for value in query(":TRAC:DATA? TRACE1").split(",")]
            start = float(query(":SENS:FREQ:STAR?"))
            stop = float(query(":SENS:FREQ:STOP?"))
            if int(query(":SYST:ERR?").split(",", 1)[0]):
                raise RuntimeError("J32 analyzer reported a SCPI error")
            return check_trace(levels, start, stop)

        yield measure
